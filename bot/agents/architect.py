import json
from bot.agents.client import chat

ARCHITECT_SYSTEM = """Ты контент-стратег Telegram-канала. Ты помогаешь планировать контент в стиле автора.
Будь конкретен: реальные темы, реальные форматы. Без воды."""


async def suggest_topics(style_profile: dict, n: int = 5) -> list[str]:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    content = await chat(
        messages=[
            {"role": "system", "content": ARCHITECT_SYSTEM},
            {"role": "user", "content": f"Профиль стиля автора:\n{profile_str}\n\nПредложи {n} тем для постов. Каждая тема — одна строка с номером."},
        ],
        max_tokens=512,
        temperature=0.5,
    )
    lines = content.splitlines()
    topics = []
    for line in lines:
        line = line.strip()
        if line and line[0].isdigit():
            topic = line.split(".", 1)[-1].strip()
            topics.append(topic)
    return topics[:n]


async def create_content_plan(style_profile: dict, topics: list[str]) -> str:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    topics_str = "\n".join(f"- {t}" for t in topics)
    return await chat(
        messages=[
            {"role": "system", "content": ARCHITECT_SYSTEM},
            {"role": "user", "content": f"Профиль стиля:\n{profile_str}\n\nТемы:\n{topics_str}\n\nСоставь контент-план на 2 недели в формате Markdown. Распредели темы по дням, укажи формат каждого поста."},
        ],
        max_tokens=600,
        temperature=0.5,
    )
