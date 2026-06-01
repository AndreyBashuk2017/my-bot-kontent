import json
from bot.agents.client import chat
from bot.agents.tester import check_post

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
    result = await chat(
        messages=[
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        max_tokens=10,
        temperature=0.2,
    )
    return result.lower()


async def write_post(brief: str, style_profile: dict) -> dict:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    best = None

    for _ in range(MAX_RETRIES):
        issues_hint = ""
        if best and not best["check"]["approved"]:
            issues_hint = "\n\nПредыдущая версия получила замечания: " + ", ".join(best["check"]["issues"]) + ". Исправь их."

        post_text = await chat(
            messages=[
                {"role": "system", "content": WRITER_SYSTEM + f"\n\nПрофиль стиля автора:\n{profile_str}"},
                {"role": "user", "content": f"Напиши пост на тему: {brief}{issues_hint}"},
            ],
            max_tokens=600,
            temperature=0.2,
        )
        check = await check_post(post_text, style_profile)
        best = {"text": post_text, "check": check, "approved": check["approved"]}

        if check["approved"]:
            break

    return best


async def refine_post(post_text: str, instruction: str, style_profile: dict) -> str:
    """Single-pass quick refinement — no scoring loop."""
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    return await chat(
        messages=[
            {"role": "system", "content": WRITER_SYSTEM + f"\n\nПрофиль стиля автора:\n{profile_str}"},
            {"role": "user", "content": f"Вот пост:\n\n{post_text}\n\nЗадание: {instruction}\n\nВерни только готовый текст поста."},
        ],
        max_tokens=700,
        temperature=0.5,
    )


async def edit_post(original: str, instructions: str, style_profile: dict) -> dict:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    best = None

    for _ in range(MAX_RETRIES):
        issues_hint = ""
        if best and not best["check"]["approved"]:
            issues_hint = "\n\nЗамечания: " + ", ".join(best["check"]["issues"]) + ". Исправь."

        post_text = await chat(
            messages=[
                {"role": "system", "content": WRITER_SYSTEM + f"\n\nПрофиль стиля автора:\n{profile_str}"},
                {"role": "user", "content": f"Оригинал:\n{original}\n\nЗадание: {instructions}{issues_hint}"},
            ],
            max_tokens=600,
            temperature=0.2,
        )
        check = await check_post(post_text, style_profile)
        best = {"text": post_text, "check": check, "approved": check["approved"]}

        if check["approved"]:
            break

    return best
