# Telegram Copywriter Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить Telegram-бота (aiogram 3) с командой из 4 агентов Claude через OpenRouter, который пишет контент в стиле пользователя на основе выгруженных постов из его канала.

**Architecture:** Динамическая маршрутизация — Оркестратор принимает все сообщения из Telegram, определяет интент и вызывает только нужных агентов. Стиль извлекается один раз из загруженных файлов и хранится в `style_profile.json`. Каждый пост перед отправкой проверяется Тестировщиком (до 2 попыток).

**Tech Stack:** Python 3.11+, aiogram 3.x, openai SDK (OpenRouter backend), python-dotenv, pytest, pytest-asyncio

**OpenRouter:** все Claude-модели вызываются через `https://openrouter.ai/api/v1` с `openai` SDK. Модели: `anthropic/claude-opus-4-8`, `anthropic/claude-sonnet-4-6`, `anthropic/claude-haiku-4-5`.

---

## File Structure

```
my-bot-kontent/
├── bot/
│   ├── __init__.py
│   ├── main.py                  # точка входа, polling
│   ├── config.py                # настройки из .env
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py          # /start /plan /newplan /write /edit /upload /style
│   │   └── messages.py          # свободный текст → Оркестратор
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # маршрутизация + написание/редактура постов
│   │   ├── architect.py         # контент-план
│   │   ├── decomposer.py        # парсинг файлов + извлечение стиля
│   │   └── tester.py            # оценка качества поста
│   └── storage/
│       ├── __init__.py
│       ├── style_profile.py     # read/write data/style_profile.json
│       └── content_plan.py      # read/write data/content_plan.md
├── data/
│   ├── examples/                # загруженные MD/JSON выгрузки
│   ├── style_profile.json       # извлечённый профиль стиля
│   └── content_plan.md          # контент-план
├── tests/
│   ├── conftest.py
│   ├── test_storage.py
│   ├── test_parsers.py
│   ├── test_tester.py
│   ├── test_decomposer.py
│   ├── test_architect.py
│   └── test_orchestrator.py
├── .env.example
├── requirements.txt
└── agents.md                    # уже создан
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `bot/__init__.py`
- Create: `bot/config.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Создать requirements.txt**

```
aiogram==3.13.0
openai==1.56.0
python-dotenv==1.0.1
pytest==8.3.4
pytest-asyncio==0.24.0
```

- [ ] **Step 2: Создать .env.example**

```
BOT_TOKEN=your_telegram_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
ALLOWED_USER_ID=your_telegram_user_id_here
```

- [ ] **Step 3: Создать bot/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
OPENROUTER_API_KEY: str = os.environ["OPENROUTER_API_KEY"]
ALLOWED_USER_ID: int = int(os.environ["ALLOWED_USER_ID"])

DATA_DIR = "data"
EXAMPLES_DIR = f"{DATA_DIR}/examples"
STYLE_PROFILE_PATH = f"{DATA_DIR}/style_profile.json"
CONTENT_PLAN_PATH = f"{DATA_DIR}/content_plan.md"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
```

- [ ] **Step 4: Создать tests/conftest.py**

```python
import pytest

pytest_plugins = ["pytest_asyncio"]
```

- [ ] **Step 5: Создать пустые __init__.py и директории**

```bash
mkdir -p bot/handlers bot/agents bot/storage data/examples tests
touch bot/__init__.py bot/handlers/__init__.py bot/agents/__init__.py bot/storage/__init__.py
```

- [ ] **Step 6: Установить зависимости и скопировать .env**

```bash
pip install -r requirements.txt
cp .env.example .env
# заполни .env реальными значениями (BOT_TOKEN, OPENROUTER_API_KEY, ALLOWED_USER_ID)
```

- [ ] **Step 7: Commit**

```bash
git init
git add requirements.txt .env.example bot/ data/ tests/
git commit -m "feat: project scaffold with OpenRouter config"
```

---

## Task 2: Storage Layer

**Files:**
- Create: `bot/storage/style_profile.py`
- Create: `bot/storage/content_plan.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Написать тесты для storage**

```python
# tests/test_storage.py
import json
import pytest
from bot.storage.style_profile import read_style_profile, write_style_profile
from bot.storage.content_plan import read_content_plan, write_content_plan


@pytest.fixture(autouse=True)
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setattr("bot.storage.style_profile.STYLE_PROFILE_PATH",
                        str(tmp_path / "style_profile.json"))
    monkeypatch.setattr("bot.storage.content_plan.CONTENT_PLAN_PATH",
                        str(tmp_path / "content_plan.md"))


def test_style_profile_missing_returns_none():
    assert read_style_profile() is None


def test_style_profile_roundtrip():
    data = {"tone": "direct", "avg_length": 120, "patterns": ["—", "."]}
    write_style_profile(data)
    assert read_style_profile() == data


def test_content_plan_missing_returns_empty():
    assert read_content_plan() == ""


def test_content_plan_roundtrip():
    plan = "## Неделя 1\n- Пост о Python\n- Пост о Claude"
    write_content_plan(plan)
    assert read_content_plan() == plan
```

- [ ] **Step 2: Запустить тесты — убедиться, что падают**

```bash
pytest tests/test_storage.py -v
```
Ожидаем: `ModuleNotFoundError` или `ImportError`.

- [ ] **Step 3: Реализовать bot/storage/style_profile.py**

```python
import json
from pathlib import Path
from bot.config import STYLE_PROFILE_PATH


def read_style_profile() -> dict | None:
    path = Path(STYLE_PROFILE_PATH)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_style_profile(profile: dict) -> None:
    path = Path(STYLE_PROFILE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Реализовать bot/storage/content_plan.py**

```python
from pathlib import Path
from bot.config import CONTENT_PLAN_PATH


def read_content_plan() -> str:
    path = Path(CONTENT_PLAN_PATH)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_content_plan(plan: str) -> None:
    path = Path(CONTENT_PLAN_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan, encoding="utf-8")
```

- [ ] **Step 5: Запустить тесты — убедиться, что проходят**

```bash
pytest tests/test_storage.py -v
```
Ожидаем: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add bot/storage/ tests/test_storage.py
git commit -m "feat: storage layer for style profile and content plan"
```

---

## Task 3: Telegram Export Parsers

**Files:**
- Create: `bot/agents/decomposer.py` (только функции парсинга; AI-агент — в Task 5)
- Create: `tests/test_parsers.py`
- Create: `tests/fixtures/sample_export.json`
- Create: `tests/fixtures/sample_export.md`

- [ ] **Step 1: Создать тестовые фикстуры**

`tests/fixtures/sample_export.json`:
```json
{
  "name": "My Channel",
  "messages": [
    {"id": 1, "type": "message", "text": "Первый пост. Коротко и по делу."},
    {"id": 2, "type": "message", "text": "Второй — ещё короче."},
    {"id": 3, "type": "service", "text": ""}
  ]
}
```

`tests/fixtures/sample_export.md`:
```
# My Channel Export

---
**Пост 1**
Первый пост. Коротко и по делу.

---
**Пост 2**
Второй — ещё короче.
```

- [ ] **Step 2: Написать тесты парсеров**

```python
# tests/test_parsers.py
import pytest
from pathlib import Path
from bot.agents.decomposer import parse_json_export, parse_md_export

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_json_returns_list_of_strings():
    content = (FIXTURES / "sample_export.json").read_text(encoding="utf-8")
    posts = parse_json_export(content)
    assert isinstance(posts, list)
    assert len(posts) == 2  # service messages filtered out
    assert "Первый пост" in posts[0]


def test_parse_json_filters_empty():
    content = '{"messages": [{"type": "message", "text": ""}, {"type": "message", "text": "OK"}]}'
    posts = parse_json_export(content)
    assert posts == ["OK"]


def test_parse_md_returns_list_of_strings():
    content = (FIXTURES / "sample_export.md").read_text(encoding="utf-8")
    posts = parse_md_export(content)
    assert isinstance(posts, list)
    assert len(posts) >= 1
    assert any("Первый пост" in p for p in posts)
```

- [ ] **Step 3: Запустить тесты — убедиться, что падают**

```bash
pytest tests/test_parsers.py -v
```
Ожидаем: `ImportError`.

- [ ] **Step 4: Реализовать parse_json_export и parse_md_export в bot/agents/decomposer.py**

```python
import json
import re


def parse_json_export(content: str) -> list[str]:
    data = json.loads(content)
    messages = data.get("messages", [])
    posts = []
    for m in messages:
        if m.get("type") != "message":
            continue
        text = m.get("text", "")
        if isinstance(text, list):
            text = "".join(part if isinstance(part, str) else part.get("text", "") for part in text)
        text = text.strip()
        if text:
            posts.append(text)
    return posts


def parse_md_export(content: str) -> list[str]:
    blocks = re.split(r"\n---+\n", content)
    posts = []
    for block in blocks:
        lines = [
            l for l in block.strip().splitlines()
            if not l.startswith("#") and not l.startswith("**Пост")
        ]
        text = "\n".join(lines).strip()
        if text:
            posts.append(text)
    return posts
```

- [ ] **Step 5: Запустить тесты — убедиться, что проходят**

```bash
pytest tests/test_parsers.py -v
```
Ожидаем: 3 PASSED.

- [ ] **Step 6: Commit**

```bash
git add bot/agents/decomposer.py tests/test_parsers.py tests/fixtures/
git commit -m "feat: telegram export parsers (MD and JSON)"
```

---

## Task 4: Tester Agent

**Files:**
- Create: `bot/agents/tester.py`
- Create: `tests/test_tester.py`

**Context:** Тестировщик использует `openai` SDK с OpenRouter base URL. Модель: `anthropic/claude-haiku-4-5`. Ответ: `response.choices[0].message.content`.

- [ ] **Step 1: Написать тесты для Тестировщика**

```python
# tests/test_tester.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.agents.tester import check_post


@pytest.mark.asyncio
async def test_check_post_pass():
    style_profile = {"tone": "direct", "avg_length": 100, "patterns": ["—"]}
    mock_message = MagicMock()
    mock_message.content = '{"score": 8, "issues": []}'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("bot.agents.tester.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await check_post("Хороший пост — по делу.", style_profile)

    assert result["score"] == 8
    assert result["issues"] == []
    assert result["approved"] is True


@pytest.mark.asyncio
async def test_check_post_fail():
    style_profile = {"tone": "direct", "avg_length": 100, "patterns": ["—"]}
    mock_message = MagicMock()
    mock_message.content = '{"score": 5, "issues": ["слишком длинно", "нет конкретики"]}'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("bot.agents.tester.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        result = await check_post("Очень длинный и размытый текст без смысла...", style_profile)

    assert result["score"] == 5
    assert len(result["issues"]) == 2
    assert result["approved"] is False
```

- [ ] **Step 2: Запустить тесты — убедиться, что падают**

```bash
pytest tests/test_tester.py -v
```
Ожидаем: `ImportError`.

- [ ] **Step 3: Реализовать bot/agents/tester.py**

```python
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
```

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

```bash
pytest tests/test_tester.py -v
```
Ожидаем: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add bot/agents/tester.py tests/test_tester.py
git commit -m "feat: tester agent with style quality check via OpenRouter"
```

---

## Task 5: Decomposer Agent

**Files:**
- Modify: `bot/agents/decomposer.py` (добавить AI-клиент и `extract_style_patterns`)
- Create: `tests/test_decomposer.py`

**Context:** Добавляем `openai_client` и функцию `extract_style_patterns` к уже существующим `parse_json_export` / `parse_md_export`. Модель: `anthropic/claude-sonnet-4-6`.

- [ ] **Step 1: Написать тест для extract_style_patterns**

```python
# tests/test_decomposer.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.agents.decomposer import extract_style_patterns


@pytest.mark.asyncio
async def test_extract_style_patterns_returns_dict():
    posts = ["Коротко и ясно.", "Факты — без воды. Сразу к делу."]

    mock_message = MagicMock()
    mock_message.content = '''{
        "tone": "direct",
        "avg_length": 45,
        "patterns": ["—", "Факты"],
        "vocabulary": ["без воды", "к делу"],
        "structure": "short_declarative"
    }'''
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("bot.agents.decomposer.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        profile = await extract_style_patterns(posts)

    assert profile["tone"] == "direct"
    assert profile["avg_length"] == 45
    assert isinstance(profile["patterns"], list)
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

```bash
pytest tests/test_decomposer.py -v
```
Ожидаем: `ImportError` или `AttributeError`.

- [ ] **Step 3: Добавить openai_client и extract_style_patterns в начало bot/agents/decomposer.py**

Полное содержимое файла после изменений:

```python
import json
import re
import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

openai_client = openai.AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)

STYLE_EXTRACTION_PROMPT = """Ты аналитик текстового стиля. Проанализируй посты автора и извлеки паттерны стиля.

Ответь ТОЛЬКО валидным JSON без markdown-блоков:
{
  "tone": "<direct|conversational|professional|ironic>",
  "avg_length": <среднее число символов в посте>,
  "patterns": [<список характерных речевых оборотов и пунктуационных паттернов>],
  "vocabulary": [<список характерных слов и фраз>],
  "structure": "<описание типичной структуры поста>"
}"""


async def extract_style_patterns(posts: list[str]) -> dict:
    posts_text = "\n---\n".join(posts[:50])
    response = await openai_client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=1024,
        temperature=0.3,
        messages=[
            {"role": "system", "content": STYLE_EXTRACTION_PROMPT},
            {"role": "user", "content": f"Посты автора:\n{posts_text}"},
        ],
    )
    return json.loads(response.choices[0].message.content)


def parse_json_export(content: str) -> list[str]:
    data = json.loads(content)
    messages = data.get("messages", [])
    posts = []
    for m in messages:
        if m.get("type") != "message":
            continue
        text = m.get("text", "")
        if isinstance(text, list):
            text = "".join(part if isinstance(part, str) else part.get("text", "") for part in text)
        text = text.strip()
        if text:
            posts.append(text)
    return posts


def parse_md_export(content: str) -> list[str]:
    blocks = re.split(r"\n---+\n", content)
    posts = []
    for block in blocks:
        lines = [
            l for l in block.strip().splitlines()
            if not l.startswith("#") and not l.startswith("**Пост")
        ]
        text = "\n".join(lines).strip()
        if text:
            posts.append(text)
    return posts
```

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

```bash
pytest tests/test_decomposer.py tests/test_parsers.py -v
```
Ожидаем: 4 PASSED.

- [ ] **Step 5: Commit**

```bash
git add bot/agents/decomposer.py tests/test_decomposer.py
git commit -m "feat: decomposer agent — style extraction from telegram exports"
```

---

## Task 6: Architect Agent

**Files:**
- Create: `bot/agents/architect.py`
- Create: `tests/test_architect.py`

**Context:** Архитектор использует `anthropic/claude-sonnet-4-6` через OpenRouter для генерации тем и контент-плана.

- [ ] **Step 1: Написать тесты для Архитектора**

```python
# tests/test_architect.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.agents.architect import create_content_plan, suggest_topics


def make_mock_response(text: str) -> MagicMock:
    mock_message = MagicMock()
    mock_message.content = text
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.mark.asyncio
async def test_suggest_topics_returns_list():
    style_profile = {"tone": "direct", "vocabulary": ["без воды", "факты"]}
    mock_response = make_mock_response(
        "1. Python-трюки для продуктивности\n2. Как читать код быстрее\n3. Инструменты, которые я использую каждый день"
    )

    with patch("bot.agents.architect.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        topics = await suggest_topics(style_profile, n=3)

    assert isinstance(topics, list)
    assert len(topics) == 3


@pytest.mark.asyncio
async def test_create_content_plan_returns_string():
    style_profile = {"tone": "direct"}
    topics = ["Python-трюки", "Как читать код", "Мои инструменты"]
    mock_response = make_mock_response("## Контент-план\n\n**Неделя 1**\n- Python-трюки")

    with patch("bot.agents.architect.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        plan = await create_content_plan(style_profile, topics)

    assert isinstance(plan, str)
    assert len(plan) > 0
```

- [ ] **Step 2: Запустить тесты — убедиться, что падают**

```bash
pytest tests/test_architect.py -v
```
Ожидаем: `ImportError`.

- [ ] **Step 3: Реализовать bot/agents/architect.py**

```python
import json
import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

openai_client = openai.AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
)

ARCHITECT_SYSTEM = """Ты контент-стратег Telegram-канала. Ты помогаешь планировать контент в стиле автора.
Будь конкретен: реальные темы, реальные форматы. Без воды."""


async def suggest_topics(style_profile: dict, n: int = 5) -> list[str]:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    response = await openai_client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=512,
        temperature=0.5,
        messages=[
            {"role": "system", "content": ARCHITECT_SYSTEM},
            {"role": "user", "content": f"Профиль стиля автора:\n{profile_str}\n\nПредложи {n} тем для постов. Каждая тема — одна строка с номером."},
        ],
    )
    lines = response.choices[0].message.content.strip().splitlines()
    topics = []
    for line in lines:
        line = line.strip()
        if line and line[0].isdigit():
            topic = line.split(".", 1)[-1].strip()
            topics.append(topic)
    return topics[:n]


async def create_content_plan(style_profile: dict, topics: list[str]) -> str:
    profile_str = json.dumps(style_profile, ensure_ascii=False)
    topics_str = "\n".join(f"- {t}" for t in topics)
    response = await openai_client.chat.completions.create(
        model="anthropic/claude-sonnet-4-6",
        max_tokens=1024,
        temperature=0.5,
        messages=[
            {"role": "system", "content": ARCHITECT_SYSTEM},
            {"role": "user", "content": f"Профиль стиля:\n{profile_str}\n\nТемы:\n{topics_str}\n\nСоставь контент-план на 2 недели в формате Markdown. Распредели темы по дням, укажи формат каждого поста."},
        ],
    )
    return response.choices[0].message.content.strip()
```

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

```bash
pytest tests/test_architect.py -v
```
Ожидаем: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add bot/agents/architect.py tests/test_architect.py
git commit -m "feat: architect agent — content plan and topic suggestions"
```

---

## Task 7: Orchestrator Agent

**Files:**
- Create: `bot/agents/orchestrator.py`
- Create: `tests/test_orchestrator.py`

**Context:** Оркестратор использует `anthropic/claude-opus-4-8`. Функция `write_post` вызывает `check_post` из tester и повторяет до MAX_RETRIES=2 при fail. Импортирует `check_post` из `bot.agents.tester`.

- [ ] **Step 1: Написать тесты для Оркестратора**

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.agents.orchestrator import detect_intent, write_post, edit_post


def make_mock_response(text: str) -> MagicMock:
    mock_message = MagicMock()
    mock_message.content = text
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.mark.asyncio
async def test_detect_intent_write():
    with patch("bot.agents.orchestrator.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=make_mock_response("write"))
        intent = await detect_intent("Напиши пост про Python")
    assert intent == "write"


@pytest.mark.asyncio
async def test_detect_intent_edit():
    with patch("bot.agents.orchestrator.openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(return_value=make_mock_response("edit"))
        intent = await detect_intent("Сделай этот текст короче")
    assert intent == "edit"


@pytest.mark.asyncio
async def test_write_post_retries_on_fail():
    style_profile = {"tone": "direct", "avg_length": 100, "patterns": ["—"]}
    call_count = 0

    async def mock_create(**kwargs):
        nonlocal call_count
        call_count += 1
        return make_mock_response("Пост о Python.")

    async def mock_check(post, profile):
        if call_count == 1:
            return {"score": 5, "issues": ["слишком коротко"], "approved": False}
        return {"score": 8, "issues": [], "approved": True}

    with patch("bot.agents.orchestrator.openai_client") as mock_client:
        mock_client.chat.completions.create = mock_create
        with patch("bot.agents.orchestrator.check_post", mock_check):
            result = await write_post("Python", style_profile)

    assert result["approved"] is True
    assert call_count == 2
```

- [ ] **Step 2: Запустить тесты — убедиться, что падают**

```bash
pytest tests/test_orchestrator.py -v
```
Ожидаем: `ImportError`.

- [ ] **Step 3: Реализовать bot/agents/orchestrator.py**

```python
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
        best = {"text": post_text, "check": check}

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
        best = {"text": post_text, "check": check}

        if check["approved"]:
            break

    return best
```

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

```bash
pytest tests/test_orchestrator.py -v
```
Ожидаем: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
git add bot/agents/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: orchestrator agent with intent detection and retry loop"
```

---

## Task 8: Bot Handlers

**Files:**
- Create: `bot/handlers/commands.py`
- Create: `bot/handlers/messages.py`

**Context:** Aiogram 3 handlers. Нет unit-тестов для handlers (требуют полного event loop aiogram). Тестируем вручную в Task 9. `bot: Bot` в `handle_document` — aiogram 3 dependency injection.

- [ ] **Step 1: Реализовать bot/handlers/commands.py**

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import ALLOWED_USER_ID
from bot.agents.orchestrator import write_post
from bot.agents.architect import create_content_plan, suggest_topics
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
        "/write <тема> — написать пост\n"
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
        await message.answer("Укажи тему: /write <тема>")
        return
    profile = read_style_profile()
    if not profile:
        await message.answer("Сначала загрузи примеры стиля через /upload.")
        return
    await message.answer("Пишу...")
    result = await write_post(brief, profile)
    note = "" if result["check"]["approved"] else f"\n\n⚠️ Оценка: {result['check']['score']}/10"
    await message.answer(result["text"] + note)


@router.message(Command("upload"))
async def cmd_upload(message: Message):
    if not auth(message):
        return
    await message.answer("Отправь файл (MD или JSON) — выгрузку своего Telegram-канала.")
```

- [ ] **Step 2: Реализовать bot/handlers/messages.py**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add bot/handlers/
git commit -m "feat: telegram bot handlers — commands and message routing"
```

---

## Task 9: Main Entry Point & Integration

**Files:**
- Create: `bot/main.py`

- [ ] **Step 1: Реализовать bot/main.py**

```python
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.handlers.commands import router as commands_router
from bot.handlers.messages import router as messages_router

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(commands_router)
    dp.include_router(messages_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Запустить все тесты**

```bash
pytest tests/ -v
```
Ожидаем: все тесты PASSED.

- [ ] **Step 3: Запустить бота (убедиться, что .env заполнен)**

```bash
python -m bot.main
```
Ожидаем в логах: `Started polling`.

- [ ] **Step 4: Проверить вручную в Telegram**

Последовательность:
1. `/start` → получить инструкцию
2. Отправить файл (.json или .md) → ответ "Профиль стиля сохранён"
3. `/style` → увидеть JSON профиля
4. `/write Как я использую Claude каждый день` → получить пост
5. `/newplan` → получить контент-план
6. `/plan` → увидеть сохранённый план
7. `/edit` → отправить текст → получить отредактированный пост

- [ ] **Step 5: Финальный коммит**

```bash
git add bot/main.py
git commit -m "feat: main entry point — bot is fully operational"
```

---

## Summary

| Task | Что строим | Тесты |
|---|---|---|
| 1 | Скаффолд, конфиг OpenRouter | — |
| 2 | Storage layer | 4 unit |
| 3 | Парсеры MD/JSON | 3 unit |
| 4 | Tester agent | 2 unit |
| 5 | Decomposer agent | 1 unit |
| 6 | Architect agent | 2 unit |
| 7 | Orchestrator agent | 3 unit |
| 8 | Handlers | — |
| 9 | Main + ручное тестирование | ручное |
