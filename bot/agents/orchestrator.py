import json
import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL
from bot.agents.tester import check_post

openai_client = openai.AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)

MAX_RETRIES = 2

INTENT_SYSTEM = """Определи интент пользователя. Ответь ОДНИМ словом:
- write   (написать новый пост)
- edit    (отредактировать существующий текст)
- plan    (контент-план)
- upload  (загрузить файл стиля)
- style   (показать профиль стиля)
- unknown"""

WRITER_SYSTEM = """Ты копирайтер Telegram-канала. Ты пишешь посты точно в стиле автора.
Правила: коротко, хлёстко, по делу. Никакого воды. Никаких шаблонных AI-фраз.
Только текст поста — без подписей, без объяснений."""


async def detect_intent(user_message: str) -> str:
    response = await openai_client.chat.completions.create(
        model="anthropic/claude-opus-4-8",
        max_tokens=10,
        temperature=0.2,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content.strip().lower()


async def write_post(brief: str, style_profile: dict) -> dict:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    best = None

    for _ in range(MAX_RETRIES):
        issues_hint = ""
        if best and not best["check"]["approved"]:
            issues_hint = "\n\nПредыдущая версия получила замечания: " + ", ".join(best["check"]["issues"]) + ". Исправь их."

        response = await openai_client.chat.completions.create(
            model="anthropic/claude-opus-4-8",
            max_tokens=1024,
            temperature=0.2,
            messages=[
                {"role": "system", "content": WRITER_SYSTEM + f"\n\nПрофиль стиля автора:\n{profile_str}"},
                {"role": "user", "content": f"Напиши пост на тему: {brief}{issues_hint}"},
            ],
        )
        post_text = response.choices[0].message.content.strip()
        check = await check_post(post_text, style_profile)
        best = {"text": post_text, "check": check, "approved": check["approved"]}

        if check["approved"]:
            break

    return best


async def edit_post(original: str, instructions: str, style_profile: dict) -> dict:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    best = None

    for _ in range(MAX_RETRIES):
        issues_hint = ""
        if best and not best["check"]["approved"]:
            issues_hint = "\n\nЗамечания: " + ", ".join(best["check"]["issues"]) + ". Исправь."

        response = await openai_client.chat.completions.create(
            model="anthropic/claude-opus-4-8",
            max_tokens=1024,
            temperature=0.2,
            messages=[
                {"role": "system", "content": WRITER_SYSTEM + f"\n\nПрофиль стиля автора:\n{profile_str}"},
                {"role": "user", "content": f"Оригинал:\n{original}\n\nЗадание: {instructions}{issues_hint}"},
            ],
        )
        post_text = response.choices[0].message.content.strip()
        check = await check_post(post_text, style_profile)
        best = {"text": post_text, "check": check, "approved": check["approved"]}

        if check["approved"]:
            break

    return best
