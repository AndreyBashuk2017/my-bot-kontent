from aiogram import Bot, Router, F
from aiogram.types import Message, Document
from pathlib import Path

from bot.config import ALLOWED_USER_ID, EXAMPLES_DIR
from bot.agents.orchestrator import detect_intent, write_post, edit_post
from bot.agents.decomposer import extract_style_patterns, parse_json_export, parse_md_export
from bot.storage.style_profile import read_style_profile, write_style_profile

router = Router()
_pending_edit: dict[int, bool] = {}


def auth(message: Message) -> bool:
    return message.from_user.id == ALLOWED_USER_ID


@router.message(F.document)
async def handle_document(message: Message, bot: Bot):
    if not auth(message):
        return
    doc: Document = message.document
    if not (doc.file_name.endswith(".json") or doc.file_name.endswith(".md")):
        await message.answer("Поддерживаю только .json и .md файлы.")
        return

    await message.answer("Скачиваю файл...")
    Path(EXAMPLES_DIR).mkdir(parents=True, exist_ok=True)
    dest = Path(EXAMPLES_DIR) / doc.file_name
    await bot.download(doc, destination=str(dest))

    content = dest.read_text(encoding="utf-8")
    posts = parse_json_export(content) if doc.file_name.endswith(".json") else parse_md_export(content)

    if not posts:
        await message.answer("Постов не найдено в файле.")
        return

    await message.answer(f"Найдено {len(posts)} постов. Извлекаю стиль...")
    profile = await extract_style_patterns(posts)
    write_style_profile(profile)
    await message.answer(
        f"Профиль стиля сохранён.\nТон: {profile.get('tone')}, средняя длина: {profile.get('avg_length')} символов."
    )


@router.message(F.text)
async def handle_text(message: Message):
    if not auth(message):
        return

    user_id = message.from_user.id
    if _pending_edit.get(user_id):
        _pending_edit[user_id] = False
        profile = read_style_profile()
        if not profile:
            await message.answer("Сначала загрузи примеры стиля через /upload.")
            return
        await message.answer("Редактирую...")
        result = await edit_post(message.text, "Сделай короче, хлёстче, убери воду", profile)
        note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
        await message.answer(result["text"] + note)
        return

    intent = await detect_intent(message.text)

    if intent == "write":
        profile = read_style_profile()
        if not profile:
            await message.answer("Сначала загрузи примеры стиля через /upload.")
            return
        await message.answer("Пишу...")
        result = await write_post(message.text, profile)
        note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
        await message.answer(result["text"] + note)

    elif intent == "edit":
        _pending_edit[user_id] = True
        await message.answer("Отправь текст, который нужно отредактировать.")

    else:
        await message.answer(
            "Не понял запрос. Попробуй:\n"
            "— /write <тема>\n"
            "— /edit (и отправь текст)\n"
            "— /plan, /newplan, /upload, /style"
        )
