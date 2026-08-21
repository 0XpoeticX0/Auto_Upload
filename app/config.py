import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_POST_API_KEY = os.getenv("GEMINI_POST_API_KEY", GEMINI_API_KEY)
GEMINI_BACKUP_API_KEY = os.getenv("GEMINI_BACKUP_API_KEY", "AQ.Ab8RN6LXG-lJXSn7eLyJ80hTHHSaHlvS27etoOpw9xIJnRwnyg")
GEMINI_KEY_3 = os.getenv("GEMINI_KEY_3", "AQ.Ab8RN6K4etu26VDAdgGRxFJYOOHWUaG_KNF8-8608wxh608pCA")
GEMINI_KEY_4 = os.getenv("GEMINI_KEY_4", "AQ.Ab8RN6IqbrtQWlwYwelnZlhfyaYeSksaf_PXSnhRTok40Mfbaw")
GEMINI_KEY_5 = os.getenv("GEMINI_KEY_5", "AQ.Ab8RN6KyEFOn3gKTfvtLpg4J_cxNVD_ugR-Lm3U0t4M0Kv8GXA")

# TikTok Content Posting API Config
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_OPEN_ID = os.getenv("TIKTOK_OPEN_ID")

VIDEO_TYPE = os.getenv("VIDEO_TYPE", "educational")
TARGET_DURATION_SEC = int(os.getenv("TARGET_DURATION_SEC", 30))
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
DB_PATH = os.getenv("DB_PATH", "data/database.sqlite")
