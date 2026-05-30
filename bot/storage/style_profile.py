import json
from pathlib import Path
from typing import Optional
from bot.config import STYLE_PROFILE_PATH


def read_style_profile() -> Optional[dict]:
    path = Path(STYLE_PROFILE_PATH)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_style_profile(profile: dict) -> None:
    path = Path(STYLE_PROFILE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
