from aiogram import Router
from aiogram.types import CallbackQuery, BufferedInputFile

from bot.config import ALLOWED_USER_ID
from bot.state import post_cache, pending_trends, trends_cache
from bot.agents.image_generator import generate_image
from bot.agents.orchestrator import write_post
from bot.storage.style_profile import read_style_profile
from bot.handlers.commands import image_keyboard, TRENDS_SUBMENU

router = Router()


def _auth(callback: CallbackQuery) -> bool:
    return callback.from_user.id == ALLOWED_USER_ID


# ── image generation ──────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("img:"))
async def handle_image_button(callback: CallbackQuery):
    if not _auth(callback):
        await callback.answer()
        return

    key = callback.data[4:]
    post_text = post_cache.get(key)
    if not post_text:
        await callback.answer("Пост не найден, сгенерируй заново.")
        return

    await callback.answer("Генерирую...")
    await callback.message.answer("Генерирую картинку...")
    try:
        image_bytes = await generate_image(post_text)
        photo = BufferedInputFile(image_bytes, filename="post_image.jpg")
        await callback.message.answer_photo(photo)
    except Exception as e:
        await callback.message.answer(f"Ошибка генерации картинки: {e}")


# ── trends menu ───────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data == "tm")
async def handle_trends_menu(callback: CallbackQuery):
    if not _auth(callback):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer("Выбери режим поиска:", reply_markup=TRENDS_SUBMENU)


@router.callback_query(lambda c: c.data == "tn")
async def handle_trends_niche(callback: CallbackQuery):
    if not _auth(callback):
        await callback.answer()
        return
    pending_trends[callback.from_user.id] = "niche"
    await callback.answer()
    await callback.message.answer(
        "Введи нишу (например: «строительство», «инвестиции», «здоровье»):"
    )


@router.callback_query(lambda c: c.data == "tt")
async def handle_trends_topic(callback: CallbackQuery):
    if not _auth(callback):
        await callback.answer()
        return
    pending_trends[callback.from_user.id] = "topic"
    await callback.answer()
    await callback.message.answer(
        "Введи тему (например: «ипотека», «ChatGPT», «осенний ремонт»):"
    )


# ── write post from trend ─────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith("tw:"))
async def handle_write_trend(callback: CallbackQuery):
    if not _auth(callback):
        await callback.answer()
        return

    parts = callback.data.split(":")
    key, idx = parts[1], int(parts[2])
    result = trends_cache.get(key)
    if not result:
        await callback.answer("Темы устарели — поищи заново.")
        return

    topics = result["topics"] if isinstance(result, dict) else result
    if idx >= len(topics):
        await callback.answer("Тема не найдена — поищи заново.")
        return

    topic = topics[idx]
    await callback.answer("Пишу...")
    await callback.message.answer(f"Пишу пост по теме:\n{topic}")

    profile = read_style_profile()
    if not profile:
        await callback.message.answer("Сначала загрузи примеры стиля через /upload.")
        return

    try:
        result = await write_post(topic, profile)
    except Exception as e:
        await callback.message.answer(f"Ошибка генерации: {e}")
        return

    note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
    await callback.message.answer(result["text"] + note, reply_markup=image_keyboard(result["text"]))
