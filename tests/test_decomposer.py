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
