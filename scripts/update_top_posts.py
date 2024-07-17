import json
import os
import re

SHOW_TOP_N_POSTS = 10
TITLE_PATTERN = 'title = "(.*?)"'

with open("static/data/view_counts.json", "r") as rf:
    view_counts = json.load(rf)


with open("content/_index.md.template", "r") as rf:
    content = rf.read()

top_posts = dict(
    sorted(view_counts.items(), key=lambda item: int(item[1]), reverse=True)[
        :SHOW_TOP_N_POSTS
    ]
)

replace_str = ""
for top_post, view_count in top_posts.items():
    if os.path.exists("content" + top_post + "index.md"):
        path = "content" + top_post + "index.md"
    else:
        path = "content" + re.sub(r"/$", ".md", top_post)
    with open(path, "r") as rf:
        title = re.findall(TITLE_PATTERN, rf.read())[0]
    replace_str += (
        f'* [{title}]({top_post}) <span class="view-count">({view_count})</span>\n'
    )

content = content.replace("<replace>", replace_str)

with open("content/_index.md", "w") as wf:
    wf.write(content)
