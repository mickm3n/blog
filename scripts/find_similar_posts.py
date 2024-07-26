from collections import defaultdict
from openai import OpenAI
from bs4 import BeautifulSoup
from scipy import spatial

import commonmark
import re
import os
import pickle
import pandas as pd
import numpy as np
import json

EMBEDDING_MODEL = "text-embedding-3-large"


class OpenAIEmbeddingProvider:
    client = OpenAI()

    def get_embedding(self, text, model=EMBEDDING_MODEL):
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(input=[text], model=model).data[0].embedding
        )


class EmbeddingRepository:
    EMBEDDING_CACHE_PATH = "data/post_embedding_cache.pkl"

    def __init__(self, embedding_provider):
        self.embedding_provider = embedding_provider
        try:
            self.embedding_cache = pd.read_pickle(self.EMBEDDING_CACHE_PATH)
        except FileNotFoundError:
            self.embedding_cache = {}

    def get_embedding(self, key, text: str, model: str = EMBEDDING_MODEL):
        if (key, model) not in self.embedding_cache.keys():
            self.embedding_cache[(key, model)] = self.embedding_provider.get_embedding(
                text, model
            )
            self.persist_cache()
        return self.embedding_cache[(key, model)]

    def persist_cache(self):
        with open(self.EMBEDDING_CACHE_PATH, "wb") as embedding_cache_file:
            pickle.dump(self.embedding_cache, embedding_cache_file)


def parse_post_and_render_html(file_path):
    with open(file_path, "r") as rf:
        content = rf.read()

    # Split front matter and markdown content
    match = re.match(r"\+\+\+.*\+\+\+(.*)", content, re.DOTALL)

    if match:
        markdown_content = match.groups()[0]
    else:
        markdown_content = content

    # Parse markdown content
    parser = commonmark.Parser()
    ast = parser.parse(markdown_content)

    renderer = commonmark.HtmlRenderer()
    html = renderer.render(ast)

    return html


def extract_text_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return "".join(soup.find_all(string=True))


def find_similar_pairs(similarities: np.ndarray, threshold: float = 0.6) -> list[tuple]:
    n = similarities.shape[0]
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            if similarities[i, j] >= threshold:
                pairs.append((i, j, similarities[i, j]))
    return pairs


def compute_similarities_from_embeddings(
    embeddings: list[list[float]],
    distance_metric="cosine",
) -> list[list]:
    distance_metrics = {
        "cosine": spatial.distance.cosine,
        "L1": spatial.distance.cityblock,
        "L2": spatial.distance.euclidean,
        "Linf": spatial.distance.chebyshev,
    }
    n = len(embeddings)
    similarities = np.zeros((n, n))

    # compute the distance matrix
    for i in range(n):
        for j in range(i + 1, n):
            dist = distance_metrics[distance_metric](embeddings[i], embeddings[j])
            if distance_metric == "cosine":
                similarity = 1 - dist
            else:
                similarity = 1 / (1 + dist)
            similarities[i, j] = similarities[j, i] = similarity

    return similarities


def find_md_files(root_dir):
    md_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files


def get_http_path_from_file_path(file_path: str):
    parts = file_path.split("/")
    if parts[-1] == "index.md":
        return "/" + "/".join(parts[1:-1]) + "/"
    elif parts[-1] == "_index.md":
        return ""
    else:
        parts[-1] = parts[-1].replace(".md", "")
        return "/" + "/".join(parts[1:]) + "/"


if __name__ == "__main__":
    openai_embedding_provider = OpenAIEmbeddingProvider()
    embedding_repository = EmbeddingRepository(openai_embedding_provider)

    all_mds = find_md_files("content")
    md_filepaths = []
    http_paths = []
    embeddings = []
    for md in all_mds:
        if md.endswith("_index.md"):
            continue
        http_path = get_http_path_from_file_path(md)
        html = parse_post_and_render_html(md)
        text = extract_text_from_html(html)

        embedding = embedding_repository.get_embedding(http_path, text)

        md_filepaths.append(md.replace("content/", ""))
        http_paths.append(http_path)
        embeddings.append(embedding)

    similarities = compute_similarities_from_embeddings(embeddings)
    similar_pairs = find_similar_pairs(similarities)

    similar_posts = defaultdict(list)
    for i, j, similarity in similar_pairs:
        similar_posts[http_paths[i]].append((md_filepaths[j], similarity))
        similar_posts[http_paths[j]].append((md_filepaths[i], similarity))

    similar_post_with_similarity = dict()
    for k, v in similar_posts.items():
        v.sort(key=lambda x: (-x[1], x[0]))
        similar_post_with_similarity[k] = ":".join(f"{x[0]}|{x[1]*100:.0f}%" for x in v)

    with open("static/data/similar_posts.json", "w") as f:
        json.dump(similar_post_with_similarity, f, sort_keys=True)
