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
