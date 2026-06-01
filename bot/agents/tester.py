import json
from bot.agents.client import chat

PASS_THRESHOLD = 7

SYSTEM_PROMPT = """Ты строгий редактор Telegram-канала. Оцени пост по шкале 0–10 и найди конкретные проблемы.

Критерии оценки:
- Соответствие стилю автора (тон, длина, обороты)
- Краткость и хлёсткость
- Человечность (не AI-шаблонный текст)

Ответь ТОЛЬКО валидным JSON без markdown-блоков:
{"score": <число>, "issues": [<строка>, ...]}

Если issues пустой — верни пустой массив."""


async def check_post(post: str, style_profile: dict) -> dict:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    content = await chat(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Профиль стиля:\n{profile_str}\n\nПост для проверки:\n{post}"},
        ],
        max_tokens=256,
        temperature=0.1,
    )
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    result = json.loads(content)
    result["approved"] = result["score"] >= PASS_THRESHOLD
    return result
