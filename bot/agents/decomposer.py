import json
import re
from bot.agents.client import chat

STYLE_EXTRACTION_PROMPT = """Ты аналитик текстового стиля. Проанализируй посты автора и извлеки паттерны стиля.

Ответь ТОЛЬКО валидным JSON без markdown-блоков:
{
  "tone": "<direct|conversational|professional|ironic>",
  "avg_length": <среднее число символов в посте>,
  "patterns": [<список характерных речевых оборотов и пунктуационных паттернов>],
  "vocabulary": [<список характерных слов и фраз>],
  "structure": "<описание типичной структуры поста>"
}"""


async def extract_style_patterns(posts: list[str]) -> dict:
    posts_text = "\n---\n".join(posts[:20])
    content = await chat(
        messages=[
            {"role": "system", "content": STYLE_EXTRACTION_PROMPT},
            {"role": "user", "content": f"Посты автора:\n{posts_text}"},
        ],
        max_tokens=1024,
        temperature=0.3,
    )
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(content)


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
