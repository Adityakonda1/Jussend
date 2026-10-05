import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8787"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-mini")

LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "14"))
MAX_CANDIDATES = int(os.getenv("MAX_CANDIDATES", "10"))
MAX_DRAFTS_PER_SCAN = int(os.getenv("MAX_DRAFTS_PER_SCAN", "5"))
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "60"))

CREDENTIALS_FILE = ROOT / "credentials.json"
TOKEN_FILE = ROOT / "token.json"
DATA_DIR = ROOT / "data"
DB_FILE = DATA_DIR / "jussend.db"

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

DATA_DIR.mkdir(exist_ok=True)
