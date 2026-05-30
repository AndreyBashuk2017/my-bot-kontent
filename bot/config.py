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
