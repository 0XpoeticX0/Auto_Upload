import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_POST_API_KEY = os.getenv("GEMINI_POST_API_KEY", GEMINI_API_KEY)
GEMINI_BACKUP_API_KEY = os.getenv("GEMINI_BACKUP_API_KEY", "AQ.Ab8RN6LXG-lJXSn7eLyJ80hTHHSaHlvS27etoOpw9xIJnRwnyg")

VIDEO_TYPE = os.getenv("VIDEO_TYPE", "educational")
TARGET_DURATION_SEC = int(os.getenv("TARGET_DURATION_SEC", 30))
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
DB_PATH = os.getenv("DB_PATH", "data/database.sqlite")
