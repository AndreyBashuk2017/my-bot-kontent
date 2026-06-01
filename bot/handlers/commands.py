import uuid
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)

from bot.config import ALLOWED_USER_ID
from bot.agents.orchestrator import write_post
from bot.agents.architect import create_content_plan, suggest_topics
from bot.state import pending_edit, pending_write, post_cache
from bot.storage.style_profile import read_style_profile
from bot.storage.content_plan import read_content_plan, write_content_plan


def image_keyboard(post_text: str) -> InlineKeyboardMarkup:
    key = str(uuid.uuid4())[:8]
    post_cache[key] = post_text
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🖼 Картинка", callback_data=f"img:{key}")
    ]])


MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔥 Тренды")]],
    resize_keyboard=True,
    is_persistent=True,
)

TRENDS_SUBMENU = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="🎯 По нише", callback_data="tn"),
    InlineKeyboardButton(text="📌 По теме", callback_data="tt"),
]])

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
        "/edit — отредактировать текст (отправь следом)\n"
        "/trends — найти трендовые темы\n\n"
        "Или просто напиши что нужно — разберусь.",
        reply_markup=MAIN_KEYBOARD,
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
    try:
        topics = await suggest_topics(profile, n=10)
        await message.answer("Составляю план...")
        plan = await create_content_plan(profile, topics)
    except Exception as e:
        await message.answer(f"Ошибка генерации плана: {e}")
        return
    write_content_plan(plan)
    await message.answer(f"Контент-план готов:\n\n{plan}")


@router.message(Command("write"))
async def cmd_write(message: Message):
    if not auth(message):
        return
    brief = message.text.removeprefix("/write").strip()
    if not brief:
        pending_write[message.from_user.id] = True
        await message.answer("Напиши тему поста:")
        return
    profile = read_style_profile()
    if not profile:
        await message.answer("Сначала загрузи примеры стиля через /upload.")
        return
    await message.answer("Пишу...")
    try:
        result = await write_post(brief, profile)
    except Exception as e:
        await message.answer(f"Ошибка генерации: {e}")
        return
    note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
    await message.answer(result["text"] + note, reply_markup=image_keyboard(result["text"]))


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


@router.message(Command("trends"))
async def cmd_trends(message: Message):
    if not auth(message):
        return
    await message.answer("Выбери режим поиска:", reply_markup=TRENDS_SUBMENU)
