import json
import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

openai_client = openai.AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)

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
    response = await openai_client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        max_tokens=256,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Профиль стиля:\n{profile_str}\n\nПост для проверки:\n{post}"},
        ],
    )
    result = json.loads(response.choices[0].message.content)
    result["approved"] = result["score"] >= PASS_THRESHOLD
    return result
