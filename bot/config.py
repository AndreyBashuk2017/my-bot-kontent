import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Required environment variable '{key}' is not set. Check your .env file.")
    return value


BOT_TOKEN: str = _require("BOT_TOKEN")
OPENROUTER_API_KEY: str = _require("OPENROUTER_API_KEY")

try:
    ALLOWED_USER_ID: int = int(_require("ALLOWED_USER_ID"))
except ValueError as e:
    if "ALLOWED_USER_ID" in str(e):
        raise
    raise ValueError("ALLOWED_USER_ID must be a valid integer (your Telegram user ID)") from e

DATA_DIR = "data"
EXAMPLES_DIR = f"{DATA_DIR}/examples"
STYLE_PROFILE_PATH = f"{DATA_DIR}/style_profile.json"
CONTENT_PLAN_PATH = f"{DATA_DIR}/content_plan.md"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
