from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import ALLOWED_USER_ID
from bot.agents.orchestrator import write_post
from bot.agents.architect import create_content_plan, suggest_topics
from bot.state import pending_edit
from bot.storage.style_profile import read_style_profile
from bot.storage.content_plan import read_content_plan, write_content_plan

router = Router()


def auth(message: Message) -> bool:
    return message.from_user.id == ALLOWED_USER_ID


@router.message(Command("start"))
async def cmd_start(message: Message):
    if not auth(message):
        return
    await message.answer(
        "Привет! Я твой копирайтер.\n\n"
        "/upload — загрузи выгрузку канала (MD или JSON)\n"
        "/style — посмотри профиль стиля\n"
        "/plan — текущий контент-план\n"
        "/newplan — создать новый план\n"
        "/write [тема] — написать пост\n"
        "/edit — отредактировать текст (отправь следом)\n\n"
        "Или просто напиши что нужно — разберусь."
    )


@router.message(Command("style"))
async def cmd_style(message: Message):
    if not auth(message):
        return
    import json
    profile = read_style_profile()
    if not profile:
        await message.answer("Профиль стиля не загружен. Используй /upload.")
        return
    await message.answer(
        f"<pre>{json.dumps(profile, ensure_ascii=False, indent=2)}</pre>",
        parse_mode="HTML",
    )


@router.message(Command("plan"))
async def cmd_plan(message: Message):
    if not auth(message):
        return
    plan = read_content_plan()
    if not plan:
        await message.answer("Контент-плана нет. Используй /newplan.")
        return
    await message.answer(plan)


@router.message(Command("newplan"))
async def cmd_newplan(message: Message):
    if not auth(message):
        return
    profile = read_style_profile()
    if not profile:
        await message.answer("Сначала загрузи примеры стиля через /upload.")
        return
    await message.answer("Генерирую темы...")
    topics = await suggest_topics(profile, n=10)
    await message.answer("Составляю план...")
    plan = await create_content_plan(profile, topics)
    write_content_plan(plan)
    await message.answer(f"Контент-план готов:\n\n{plan}")


@router.message(Command("write"))
async def cmd_write(message: Message):
    if not auth(message):
        return
    brief = message.text.removeprefix("/write").strip()
    if not brief:
        await message.answer("Укажи тему: /write [тема]")
        return
    profile = read_style_profile()
    if not profile:
        await message.answer("Сначала загрузи примеры стиля через /upload.")
        return
    await message.answer("Пишу...")
    result = await write_post(brief, profile)
    note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
    await message.answer(result["text"] + note)


@router.message(Command("edit"))
async def cmd_edit(message: Message):
    if not auth(message):
        return
    pending_edit[message.from_user.id] = True
    await message.answer("Отправь текст, который нужно отредактировать.")


@router.message(Command("upload"))
async def cmd_upload(message: Message):
    if not auth(message):
        return
    await message.answer("Отправь файл (MD или JSON) — выгрузку своего Telegram-канала.")
