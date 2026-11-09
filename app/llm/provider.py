import os
import json
import re
import time
from google import genai
from google.genai import types
from app.config import (
    GEMINI_API_KEY,
    GEMINI_POST_API_KEY,
    GEMINI_BACKUP_API_KEY,
    GEMINI_KEY_3,
    GEMINI_KEY_4,
    GEMINI_KEY_5
)
from app.logger import logger

MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",        # Blazing fast, low latency
    "gemini-3.5-flash",        # Highly reliable & stable
    "gemini-3.7-flash",        # Advanced reasoning
    "gemini-flash-lite-latest",# Canonical alias for lite
    "gemini-flash-latest",     # Canonical alias for flash
]

GLOBAL_RULE = "\n\nCRITICAL SYSTEM RULE: You must cross-check all Islamic claims with authentic Quranic verses and Sahih Hadith. Do not output any misinformation, unverified stories, or false claims. All claims must be backed by authentic sources."

KEY_LOCK_STATE_FILE = os.path.abspath("data/gemini_key_lock_state.json")
_CURRENT_LOCKED_KEY_INDEX = 0

def get_api_keys_pool(for_posts: bool = False) -> list:
    """
    Returns an ordered pool of all available unique Gemini API keys.
    Collects standard config keys plus any other GEMINI_*KEY* found in environment.
    """
    keys = []
    candidates = [
        GEMINI_KEY_5,
        GEMINI_API_KEY,
        GEMINI_KEY_3,
        GEMINI_KEY_4,
        GEMINI_BACKUP_API_KEY,
        GEMINI_POST_API_KEY,
    ]
    # Dynamically scan os.environ for any additional configured Gemini keys
    for env_k, env_v in os.environ.items():
        if ("GEMINI" in env_k and "KEY" in env_k) and env_v:
            if env_v not in candidates:
                candidates.append(env_v)

    for k in candidates:
        if k and k not in keys:
            keys.append(k)
    return keys

def get_locked_key_index() -> int:
    """Returns the index of the currently locked active key."""
    global _CURRENT_LOCKED_KEY_INDEX
    if os.path.exists(KEY_LOCK_STATE_FILE):
        try:
            with open(KEY_LOCK_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _CURRENT_LOCKED_KEY_INDEX = data.get("locked_key_index", _CURRENT_LOCKED_KEY_INDEX)
        except Exception:
            pass
    return _CURRENT_LOCKED_KEY_INDEX

def save_locked_key_index(idx: int):
    """
    Locks the active working key index.
    Subsequent API calls will immediately start with this key until its quota is exhausted.
    """
    global _CURRENT_LOCKED_KEY_INDEX
    _CURRENT_LOCKED_KEY_INDEX = idx
    try:
        os.makedirs(os.path.dirname(KEY_LOCK_STATE_FILE), exist_ok=True)
        with open(KEY_LOCK_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "locked_key_index": idx,
                "timestamp": int(time.time())
            }, f, indent=2)
    except Exception as e:
        logger.debug(f"Failed to persist locked key index: {e}")

def get_ordered_key_candidates(for_posts: bool = False) -> list[tuple[int, str]]:
    """
    Returns (key_index, key_value) tuples ordered so the currently LOCKED key
    is tried FIRST, followed round-robin by all other available keys as fallback.
    """
    pool = get_api_keys_pool(for_posts=for_posts)
    if not pool:
        return []
    start_idx = get_locked_key_index() % len(pool)
    ordered = []
    for i in range(len(pool)):
        idx = (start_idx + i) % len(pool)
        ordered.append((idx, pool[idx]))
    return ordered

# Session memory: Blacklist model+key pairs that fail with persistent errors (not transient 503s)
# Key: (model_name, key)  Value: timestamp of failure
_SESSION_FAILED_PAIRS: dict = {}
_BLACKLIST_EXPIRY_SEC = 45

def _is_blacklisted(model_name: str, key: str) -> bool:
    entry = _SESSION_FAILED_PAIRS.get((model_name, key))
    if entry is None:
        return False
    if time.time() - entry > _BLACKLIST_EXPIRY_SEC:
        del _SESSION_FAILED_PAIRS[(model_name, key)]
        return False
    return True

def generate_text(system_prompt: str, user_prompt: str, for_posts: bool = False) -> str:
    global _SESSION_FAILED_PAIRS
    key_candidates = get_ordered_key_candidates(for_posts=for_posts)
    if not key_candidates:
        logger.error("No Gemini API keys available.")
        return ""

    key_pool = [k for _, k in key_candidates]

    # Auto-recovery: If all candidate pairs are blacklisted, reset the blacklist
    unblacklisted = sum(1 for m in MODELS for k in key_pool if not _is_blacklisted(m, k))
    if unblacklisted == 0:
        logger.warning("All Gemini model+key pairs were blacklisted. Resetting blacklist and pausing 3s...")
        _SESSION_FAILED_PAIRS.clear()
        time.sleep(3)

    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"

    for model_name in MODELS:
        for idx, key in key_candidates:
            if _is_blacklisted(model_name, key):
                continue

            try:
                logger.info(f"Attempting model '{model_name}' on Key #{idx+1}/{len(key_pool)} (Active Lock: #{get_locked_key_index()+1})")
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response.text:
                    if idx != get_locked_key_index():
                        logger.info(f"🔒 [Gemini Key Manager] Success on Key #{idx+1}! Locking as active key.")
                        save_locked_key_index(idx)
                    else:
                        logger.info(f"Success with '{model_name}' on locked Key #{idx+1}!")
                    return response.text
            except Exception as e:
                err_str = str(e)
                is_503 = "503" in err_str or "UNAVAILABLE" in err_str
                is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
                if is_503:
                    logger.warning(f"Model '{model_name}' temporary 503 spike on Key #{idx+1}. Pausing 2s...")
                    time.sleep(2)
                    _SESSION_FAILED_PAIRS[(model_name, key)] = time.time()
                elif is_quota:
                    logger.warning(f"⚠️ Key #{idx+1} quota/rate limit exhausted (429). Blacklisting and advancing active lock...")
                    _SESSION_FAILED_PAIRS[(model_name, key)] = time.time() + 180
                    # Advance lock immediately to the next available key
                    next_idx = (idx + 1) % len(key_pool)
                    save_locked_key_index(next_idx)
                else:
                    logger.warning(f"Model '{model_name}' failed on Key #{idx+1} ({err_str[:120]}). Blacklisting for {_BLACKLIST_EXPIRY_SEC}s...")
                    _SESSION_FAILED_PAIRS[(model_name, key)] = time.time()

    logger.error("All Gemini models and API keys failed.")
    return ""

def _parse_dirty_json(text: str) -> dict:
    """Robustly parse JSON from LLM response even with control chars or markdown."""
    raw = text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    # First try standard loads with strict=False
    try:
        return json.loads(raw, strict=False)
    except Exception:
        pass

    # Second try: extract outermost { ... }
    m = re.search(r'(\{.*\})', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1), strict=False)
        except Exception:
            pass

    # Third try: sanitize unescaped newlines and control chars inside strings
    try:
        clean = re.sub(r'[\x00-\x1F\x7F]', lambda match: ' ' if match.group(0) in '\n\r\t' else '', raw)
        return json.loads(clean, strict=False)
    except Exception:
        pass

    # Fourth try: escape literal newlines
    try:
        fixed = re.sub(r'(?<!\\)\r?\n', r'\\n', raw)
        return json.loads(fixed, strict=False)
    except Exception:
        pass

    return {}

def extract_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000, for_posts: bool = False) -> dict:
    global _SESSION_FAILED_PAIRS
    key_candidates = get_ordered_key_candidates(for_posts=for_posts)
    if not key_candidates:
        logger.error("No Gemini API keys available.")
        return {}

    key_pool = [k for _, k in key_candidates]

    # Auto-recovery: If all candidate pairs are blacklisted, reset the blacklist
    unblacklisted = sum(1 for m in MODELS for k in key_pool if not _is_blacklisted(m, k))
    if unblacklisted == 0:
        logger.warning("All Gemini model+key pairs were blacklisted. Resetting blacklist and pausing 3s...")
        _SESSION_FAILED_PAIRS.clear()
        time.sleep(3)

    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"

    for model_name in MODELS:
        for idx, key in key_candidates:
            if _is_blacklisted(model_name, key):
                continue

            try:
                logger.info(f"Attempting model '{model_name}' on Key #{idx+1}/{len(key_pool)} (Active Lock: #{get_locked_key_index()+1})")
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        max_output_tokens=max_tokens
                    )
                )
                raw_text = response.text
                if not raw_text:
                    continue
                parsed = _parse_dirty_json(raw_text)
                if parsed:
                    if idx != get_locked_key_index():
                        logger.info(f"🔒 [Gemini Key Manager] Success on Key #{idx+1}! Locking as active key.")
                        save_locked_key_index(idx)
                    else:
                        logger.info(f"Success with '{model_name}' on locked Key #{idx+1}!")
                    return parsed
            except Exception as e:
                err_str = str(e)
                is_503 = "503" in err_str or "UNAVAILABLE" in err_str
                is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
                if is_503:
                    logger.warning(f"Model '{model_name}' temporary 503 spike on Key #{idx+1}. Pausing 2s...")
                    time.sleep(2)
                    _SESSION_FAILED_PAIRS[(model_name, key)] = time.time()
                elif is_quota:
                    logger.warning(f"⚠️ Key #{idx+1} quota/rate limit exhausted (429). Blacklisting and advancing active lock...")
                    _SESSION_FAILED_PAIRS[(model_name, key)] = time.time() + 180
                    next_idx = (idx + 1) % len(key_pool)
                    save_locked_key_index(next_idx)
                else:
                    logger.warning(f"Model '{model_name}' failed on Key #{idx+1} ({err_str[:120]}). Blacklisting for {_BLACKLIST_EXPIRY_SEC}s...")
                    _SESSION_FAILED_PAIRS[(model_name, key)] = time.time()

    logger.error("All Gemini models and API keys failed.")
    return {}
