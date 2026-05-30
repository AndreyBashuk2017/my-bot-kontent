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
