# Trends Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a TrendScout feature that lets the user find 3 trending topics via Perplexity and instantly write a post about any of them.

**Architecture:** A new `trendscout.py` agent calls `perplexity/sonar` directly via OpenRouter (no fallback chain — non-search models cannot find real trends). State dicts `pending_trends` and `trends_cache` track what the user asked for and store the results. The main "🔥 Тренды" entry point is a persistent ReplyKeyboard button; inline keyboards handle the submenu and write-from-trend actions.

**Tech Stack:** Python 3.9, aiogram 3.13, openai SDK → OpenRouter, `perplexity/sonar` model.

---

## File Structure

| File | Action | What changes |
|---|---|---|
| `bot/agents/trendscout.py` | **Create** | TrendScout agent — two search functions using `perplexity/sonar` |
| `bot/state.py` | **Modify** | Add `pending_trends`, `trends_cache` dicts |
| `bot/handlers/commands.py` | **Modify** | Add `MAIN_KEYBOARD`, update `/start`, add `/trends` command |
| `bot/handlers/callbacks.py` | **Modify** | Add 4 handlers: `tm`, `tn`, `tt`, `tw:KEY:N` |
| `bot/handlers/messages.py` | **Modify** | Add "🔥 Тренды" text trap and `pending_trends` handler |

---

## Task 1: TrendScout agent

**Files:**
- Create: `bot/agents/trendscout.py`

- [ ] **Step 1: Create the file**

```python
# bot/agents/trendscout.py
import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

_client = openai.AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

_NICHE_PROMPT = """Find 3 trending topics for Telegram posts in the niche: {niche}.

Requirements:
- Topics are relevant right now (last 1-2 weeks)
- Each is a concrete post idea, not a generic category
- Reply in Russian

Respond with EXACTLY 3 lines, one topic per line, no numbering, no extra text."""

_TOPIC_PROMPT = """Find 3 trending angles for writing about: {topic}.

Requirements:
- Tied to real events or discussions from the last 1-2 weeks
- Unexpected or interesting angles for a Telegram post
- Reply in Russian

Respond with EXACTLY 3 lines, one angle per line, no numbering, no extra text."""


async def search_by_niche(niche: str) -> list[str]:
    return await _search(_NICHE_PROMPT.format(niche=niche))


async def search_by_topic(topic: str) -> list[str]:
    return await _search(_TOPIC_PROMPT.format(topic=topic))


async def _search(prompt: str) -> list[str]:
    response = await _client.chat.completions.create(
        model="perplexity/sonar",
        max_tokens=300,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cleaned = []
    for line in lines:
        if line and line[0].isdigit() and len(line) > 2 and line[1] in '.) ':
            line = line[2:].strip()
        cleaned.append(line)
    return cleaned[:3]
```

- [ ] **Step 2: Smoke-test that the module imports without error**

```bash
cd /Users/andrey/Documents/PROJECTS/my-bot-kontent
python3 -c "from bot.agents.trendscout import search_by_niche, search_by_topic; print('OK')"
```
Expected output: `OK`

- [ ] **Step 3: Commit**

```bash
git add bot/agents/trendscout.py
git commit -m "feat: add TrendScout agent using perplexity/sonar"
```

---

## Task 2: State additions

**Files:**
- Modify: `bot/state.py`

- [ ] **Step 1: Add two new dicts to state.py**

Replace the full file with:

```python
pending_edit: dict[int, bool] = {}
pending_write: dict[int, bool] = {}
pending_trends: dict[int, str] = {}   # user_id -> "niche" | "topic"
post_cache: dict[str, str] = {}
trends_cache: dict[str, list[str]] = {}  # uuid8 -> [trend1, trend2, trend3]
```

- [ ] **Step 2: Verify import**

```bash
python3 -c "from bot.state import pending_trends, trends_cache; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add bot/state.py
git commit -m "feat: add pending_trends and trends_cache to state"
```

---

## Task 3: Main menu button + /trends command

**Files:**
- Modify: `bot/handlers/commands.py`

Current `/start` handler sends plain text. We add a persistent `ReplyKeyboardMarkup` with one button ("🔥 Тренды") and add a `/trends` command that shows the inline submenu.

- [ ] **Step 1: Add imports and MAIN_KEYBOARD constant**

At the top of `bot/handlers/commands.py`, add to the existing imports block:

```python
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
```

(Replace the existing `from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton` line.)

Then add this constant right after the imports, before `router = Router()`:

```python
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔥 Тренды")]],
    resize_keyboard=True,
    is_persistent=True,
)

TRENDS_SUBMENU = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="🎯 По нише", callback_data="tn"),
    InlineKeyboardButton(text="📌 По теме", callback_data="tt"),
]])
```

- [ ] **Step 2: Update cmd_start to send MAIN_KEYBOARD**

Replace the `cmd_start` body:

```python
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
```

- [ ] **Step 3: Add /trends command at the end of the file**

```python
@router.message(Command("trends"))
async def cmd_trends(message: Message):
    if not auth(message):
        return
    await message.answer("Выбери режим поиска:", reply_markup=TRENDS_SUBMENU)
```

- [ ] **Step 4: Verify the module imports cleanly**

```bash
python3 -c "from bot.handlers.commands import MAIN_KEYBOARD, TRENDS_SUBMENU, cmd_trends; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add bot/handlers/commands.py
git commit -m "feat: add Trends button to main keyboard and /trends command"
```

---

## Task 4: Callback handlers for trends flow

**Files:**
- Modify: `bot/handlers/callbacks.py`

Four new handlers:
- `tm` — show TRENDS_SUBMENU (kept for future use from inline context)
- `tn` — set `pending_trends = "niche"` and ask for niche text
- `tt` — set `pending_trends = "topic"` and ask for topic text
- `tw:KEY:N` — look up `trends_cache[KEY][N]`, write post, send with image button

- [ ] **Step 1: Rewrite callbacks.py with all handlers**

```python
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
    trends = trends_cache.get(key)
    if not trends or idx >= len(trends):
        await callback.answer("Темы устарели — поищи заново.")
        return

    topic = trends[idx]
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
```

- [ ] **Step 2: Verify import**

```bash
python3 -c "from bot.handlers.callbacks import router; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add bot/handlers/callbacks.py
git commit -m "feat: add trends callback handlers (menu, niche, topic, write from trend)"
```

---

## Task 5: Message handler — trends entry point + pending_trends

**Files:**
- Modify: `bot/handlers/messages.py`

Add two checks at the TOP of `handle_text` (before `pending_write`):
1. If `message.text == "🔥 Тренды"` → show submenu inline keyboard
2. If `pending_trends.get(user_id)` → run search and show results

- [ ] **Step 1: Add imports to messages.py**

Replace:
```python
from bot.state import pending_edit, pending_write
```
With:
```python
import uuid
from aiogram.types import Message, Document, InlineKeyboardMarkup, InlineKeyboardButton
from bot.state import pending_edit, pending_write, pending_trends, trends_cache
from bot.agents.trendscout import search_by_niche, search_by_topic
from bot.handlers.commands import TRENDS_SUBMENU
```

Also add `InlineKeyboardMarkup, InlineKeyboardButton` to the existing `from aiogram.types import` line (or replace it as shown above — the full import line must stay consistent with what's already there).

The full updated import block for messages.py:
```python
from aiogram import Bot, Router, F
from aiogram.types import Message, Document, InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
import uuid

from bot.config import ALLOWED_USER_ID, EXAMPLES_DIR
from bot.agents.orchestrator import detect_intent, write_post, edit_post
from bot.agents.decomposer import extract_style_patterns, parse_json_export, parse_md_export
from bot.agents.trendscout import search_by_niche, search_by_topic
from bot.storage.style_profile import read_style_profile, write_style_profile
from bot.state import pending_edit, pending_write, pending_trends, trends_cache
from bot.handlers.commands import image_keyboard, TRENDS_SUBMENU
```

- [ ] **Step 2: Add the two new checks inside handle_text**

The full updated `handle_text` function — paste this to replace the existing one:

```python
@router.message(F.text)
async def handle_text(message: Message):
    if not auth(message):
        return

    user_id = message.from_user.id

    # Main menu "Тренды" button
    if message.text == "🔥 Тренды":
        await message.answer("Выбери режим поиска:", reply_markup=TRENDS_SUBMENU)
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
```

- [ ] **Step 3: Verify import**

```bash
python3 -c "from bot.handlers.messages import router; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add bot/handlers/messages.py
git commit -m "feat: handle 🔥 Тренды button and pending_trends state in message handler"
```

---

## Task 6: Restart and end-to-end test

- [ ] **Step 1: Restart the bot**

```bash
pkill -f "bot.main" 2>/dev/null; sleep 1
python3 -m bot.main >> /tmp/bot_debug.log 2>&1 &
sleep 3 && tail -5 /tmp/bot_debug.log
```
Expected last line: `INFO:aiogram.dispatcher:Run polling for bot @NM_kontent_bot`

- [ ] **Step 2: Test that all modules import cleanly**

```bash
python3 -c "
from bot.agents.trendscout import search_by_niche, search_by_topic
from bot.handlers.callbacks import router as cb
from bot.handlers.commands import MAIN_KEYBOARD, TRENDS_SUBMENU
from bot.handlers.messages import router as msg
from bot.state import pending_trends, trends_cache
print('All imports OK')
"
```
Expected: `All imports OK`

- [ ] **Step 3: Check that /trends command is registered**

```bash
python3 -c "
from bot.handlers.commands import router
names = [h.filters[0].commands if hasattr(h, 'filters') else '' for h in router.message.handlers]
print([str(r) for r in router.message.handlers])
" 2>&1 | head -5
```
(This is a sanity check — just confirm no import errors.)

- [ ] **Step 4: Final commit with push**

```bash
git push origin main
```
