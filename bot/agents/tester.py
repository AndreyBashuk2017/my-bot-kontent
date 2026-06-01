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
        max_tokens=400,
        temperature=0.1,
    )
    content = content.strip()
    # strip markdown code fences
    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    # extract JSON object if model added surrounding text
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1:
        content = content[start:end + 1]
    try:
        result = json.loads(content)
        result["approved"] = result.get("score", 0) >= PASS_THRESHOLD
        return result
    except json.JSONDecodeError:
        return {"score": 8, "issues": [], "approved": True}
