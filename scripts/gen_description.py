import frontmatter
import json
import autocorrect_py as autocorrect

from frontmatter.default_handlers import TOMLHandler
from openai import OpenAI
from utils import find_md_files


class InvalidAIOutputFormatError(Exception):
    def __init__(self, content, message="Invalid AI output format"):
        super().__init__(message)
        self.content = content

    def __str__(self) -> str:
        return f"{self.args[0]} (Content: {self.content})"


class OpenAIChat:
    CHAT_MODEL = "gpt-4o"
    client = OpenAI()

    def ask(self, prompt, model=CHAT_MODEL):
        messages = [
            {
                "role": "system",
                "content": "你是 Search Engine Optimization 專家，請用 SEO 的技巧幫忙總結文章，並使用指定的 Format 和台灣正體回答。",
            },
            {"role": "user", "content": prompt},
        ]
        try:
            return self._ask(messages, model=model)
        except InvalidAIOutputFormatError as e:
            print(e)
            messages.extend(
                [
                    {"role": "assistant", "content": e.content},
                    {
                        "role": "user",
                        "content": "你的回應不是 JSON，請重新輸出只包含 JSON 的回應。",
                    },
                ]
            )
            return self._ask(messages, model=model)

    def _ask(self, messages, model=CHAT_MODEL):
        try:
            content = (
                self.client.chat.completions.create(model=model, messages=messages)
                .choices[0]
                .message.content
            )
            return json.loads(content)
        except json.decoder.JSONDecodeError:
            raise InvalidAIOutputFormatError(content=content)


GEN_DESCRIPTION_PROMPT = """
請生成一個適合 Open Graph 的文章描述，遵循以下步驟：

1. 確定文章的主題和主要內容。
2. 識別文章中的重要關鍵詞。
3. 用簡明扼要的語言總結文章的主要要點。
4. 使用引人入勝的語言吸引讀者點擊。
5. 確保描述在 160 個字符以內。

文章主題："<title>"
文章內容：
```
<article>
```

Output Format: Json (Don't have ```json``` in the output)
Schema:
{
    description: str
}

確認 Output 只包含一個 Json 物件
"""

ignore_md_files = [
    "content/_index.md",
    "content/blog/_index.md",
    "content/blog/experiments/_index.md",
    "content/wisdom/_index.md",
    "content/wisdom/podcasts/_index.md",
    "content/wisdom/templates/_index.md",
    "content/wisdom/articles/_index.md",
    "content/wisdom/lists/_index.md",
    "content/wisdom/mental-models/_index.md",
    "content/wisdom/methods/_index.md",
    "content/wisdom/videos/_index.md",
]

chat = OpenAIChat()
for md_file in find_md_files("content"):
    if md_file in ignore_md_files:
        continue
    post = frontmatter.load(md_file)
    if "description" in post:
        continue

    print(f"Generating description for {md_file}")
    prompt = f"Prompt: {GEN_DESCRIPTION_PROMPT.replace('<title>', post['title']).replace('<article>', post.content)}"
    response_json = chat.ask(prompt)
    post["description"] = response_json["description"]

    with open(md_file, "w") as f:
        s = autocorrect.format(frontmatter.dumps(post))
        if not s.endswith("\n"):
            s += "\n"
        f.write(s)
