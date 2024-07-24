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


def compute_distances_from_embeddings(
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
    distances = np.zeros((n, n))

    # compute the distance matrix
    for i in range(n):
        for j in range(i + 1, n):
            distances[i, j] = distances[j, i] = distance_metrics[distance_metric](
                embeddings[i], embeddings[j]
            )

    return distances


def indices_of_nearest_neighbors_from_distances(distances) -> np.ndarray:
    return np.argsort(distances, axis=1)


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

    distances = compute_distances_from_embeddings(embeddings)
    # for each embedding, find its nearest neighbors
    indices_of_nn = indices_of_nearest_neighbors_from_distances(distances)

    # for each md file, find its TOP-3 nearest neighbor
    top_3_nn = dict()
    for i in range(len(md_filepaths)):
        top_3_nn[http_paths[i]] = ":".join(
            [md_filepaths[j] for j in indices_of_nn[i, 1:4]]
        )

    with open("static/data/top_3_nn.json", "w") as f:
        json.dump(top_3_nn, f)
