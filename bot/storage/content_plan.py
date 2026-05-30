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
