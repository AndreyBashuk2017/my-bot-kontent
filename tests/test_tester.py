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
