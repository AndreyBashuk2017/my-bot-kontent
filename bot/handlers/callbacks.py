from aiogram import Router
from aiogram.types import CallbackQuery, BufferedInputFile

from bot.config import ALLOWED_USER_ID
from bot.state import post_cache
from bot.agents.image_generator import generate_image

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("img:"))
async def handle_image_button(callback: CallbackQuery):
    if callback.from_user.id != ALLOWED_USER_ID:
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
