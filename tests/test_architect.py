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
