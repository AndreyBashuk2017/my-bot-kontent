import json
import uuid
from aiogram import Bot, Router, F
from aiogram.types import Message, Document, InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path

from bot.config import ALLOWED_USER_ID, EXAMPLES_DIR
from bot.agents.orchestrator import detect_intent, write_post, edit_post
from bot.agents.architect import create_content_plan, suggest_topics
from bot.agents.decomposer import extract_style_patterns, parse_json_export, parse_md_export
from bot.agents.trendscout import search_by_niche, search_by_topic
from bot.storage.style_profile import read_style_profile, write_style_profile
from bot.storage.content_plan import read_content_plan, write_content_plan
from bot.state import pending_edit, pending_write, pending_trends, trends_cache
from bot.handlers.commands import image_keyboard, TRENDS_SUBMENU

router = Router()


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
    try:
        posts = parse_json_export(content) if doc.file_name.endswith(".json") else parse_md_export(content)
    except Exception:
        await message.answer("Не удалось прочитать файл — он повреждён или не завершён. Дождись окончания экспорта и загрузи снова.")
        return

    if not posts:
        await message.answer("Постов не найдено в файле.")
        return

    await message.answer(f"Найдено {len(posts)} постов. Извлекаю стиль...")
    try:
        profile = await extract_style_patterns(posts)
    except Exception as e:
        await message.answer(f"Ошибка при обращении к AI: {e}")
        return
    write_style_profile(profile)
    await message.answer(
        f"Профиль стиля сохранён.\nТон: {profile.get('tone')}, средняя длина: {profile.get('avg_length')} символов."
    )


@router.message(F.text)
async def handle_text(message: Message):
    if not auth(message):
        return

    user_id = message.from_user.id

    # ── Main keyboard buttons ──────────────────────────────────────────────────

    if message.text == "✍️ Написать пост":
        pending_write[user_id] = True
        await message.answer("Напиши тему поста:")
        return

    if message.text == "🔥 Тренды":
        await message.answer("Выбери режим поиска:", reply_markup=TRENDS_SUBMENU)
        return

    if message.text == "✏️ Редактировать":
        pending_edit[user_id] = True
        await message.answer("Отправь текст, который нужно отредактировать.")
        return

    if message.text == "📋 Контент-план":
        plan = read_content_plan()
        if not plan:
            await message.answer("Контент-плана пока нет. Нажми «🆕 Новый план».")
        else:
            await message.answer(plan)
        return

    if message.text == "🆕 Новый план":
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
        return

    if message.text == "📊 Мой стиль":
        profile = read_style_profile()
        if not profile:
            await message.answer("Профиль стиля не загружен. Используй /upload.")
        else:
            await message.answer(
                f"<pre>{json.dumps(profile, ensure_ascii=False, indent=2)}</pre>",
                parse_mode="HTML",
            )
        return

    # Awaiting niche/topic input after user chose a search mode
    if pending_trends.get(user_id):
        mode = pending_trends.pop(user_id)
        await message.answer("🔍 Ищу тренды...")
        try:
            if mode == "niche":
                trends = await search_by_niche(message.text)
            else:
                trends = await search_by_topic(message.text)
        except Exception as e:
            err = str(e)
            if "402" in err or "credits" in err.lower():
                await message.answer(
                    "Для поиска трендов нужны кредиты OpenRouter.\n"
                    "Пополни баланс на openrouter.ai/settings/credits (хватит $1)."
                )
            else:
                await message.answer(f"Ошибка поиска трендов: {e}")
            return

        if not trends:
            await message.answer("Не удалось найти тренды. Попробуй другой запрос.")
            return

        key = str(uuid.uuid4())[:8]
        trends_cache[key] = trends

        text = "🔥 Трендовые темы:\n\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(trends))
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=f"✍️ Пост {i+1}", callback_data=f"tw:{key}:{i}")
            for i in range(len(trends))
        ]])
        await message.answer(text, reply_markup=keyboard)
        return

    if pending_write.get(user_id):
        pending_write[user_id] = False
        profile = read_style_profile()
        if not profile:
            await message.answer("Сначала загрузи примеры стиля через /upload.")
            return
        await message.answer("Пишу...")
        try:
            result = await write_post(message.text, profile)
        except Exception as e:
            await message.answer(f"Ошибка генерации: {e}")
            return
        note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
        await message.answer(result["text"] + note, reply_markup=image_keyboard(result["text"]))
        return

    if pending_edit.get(user_id):
        pending_edit[user_id] = False
        profile = read_style_profile()
        if not profile:
            await message.answer("Сначала загрузи примеры стиля через /upload.")
            return
        await message.answer("Редактирую...")
        try:
            result = await edit_post(message.text, "Сделай короче, хлёстче, убери воду", profile)
        except Exception as e:
            await message.answer(f"Ошибка редактирования: {e}")
            return
        note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
        await message.answer(result["text"] + note, reply_markup=image_keyboard(result["text"]))
        return

    try:
        intent = await detect_intent(message.text)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        return

    if intent == "write":
        profile = read_style_profile()
        if not profile:
            await message.answer("Сначала загрузи примеры стиля через /upload.")
            return
        await message.answer("Пишу...")
        try:
            result = await write_post(message.text, profile)
        except Exception as e:
            await message.answer(f"Ошибка генерации: {e}")
            return
        note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
        await message.answer(result["text"] + note, reply_markup=image_keyboard(result["text"]))

    elif intent == "edit":
        pending_edit[user_id] = True
        await message.answer("Отправь текст, который нужно отредактировать.")

    else:
        await message.answer(
            "Не понял запрос. Попробуй:\n"
            "— /write <тема>\n"
            "— /edit (и отправь текст)\n"
            "— /plan, /newplan, /upload, /style, /trends"
        )
