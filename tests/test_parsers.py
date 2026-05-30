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
