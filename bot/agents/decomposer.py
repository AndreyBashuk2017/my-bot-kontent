import json
import re


def parse_json_export(content: str) -> list[str]:
    data = json.loads(content)
    messages = data.get("messages", [])
    posts = []
    for m in messages:
        if m.get("type") != "message":
            continue
        text = m.get("text", "")
        if isinstance(text, list):
            text = "".join(part if isinstance(part, str) else part.get("text", "") for part in text)
        text = text.strip()
        if text:
            posts.append(text)
    return posts


def parse_md_export(content: str) -> list[str]:
    blocks = re.split(r"\n---+\n", content)
    posts = []
    for block in blocks:
        lines = [
            l for l in block.strip().splitlines()
            if not l.startswith("#") and not l.startswith("**Пост")
        ]
        text = "\n".join(lines).strip()
        if text:
            posts.append(text)
    return posts
