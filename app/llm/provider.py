import json
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, GEMINI_POST_API_KEY, GEMINI_BACKUP_API_KEY
from app.logger import logger

MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash"
]

GLOBAL_RULE = "\n\nCRITICAL SYSTEM RULE: You must cross-check all Islamic claims with authentic Quranic verses and Sahih Hadith. Do not output any misinformation, unverified stories, or false claims. All claims must be backed by authentic sources."

def get_api_keys_pool(for_posts: bool = False) -> list:
    """Returns an ordered pool of available Gemini API keys for seamless fallback."""
    keys = []
    if for_posts and GEMINI_POST_API_KEY:
        keys.append(GEMINI_POST_API_KEY)
    if GEMINI_API_KEY and GEMINI_API_KEY not in keys:
        keys.append(GEMINI_API_KEY)
    if GEMINI_BACKUP_API_KEY and GEMINI_BACKUP_API_KEY not in keys:
        keys.append(GEMINI_BACKUP_API_KEY)
    return [k for k in keys if k]

def generate_text(system_prompt: str, user_prompt: str, for_posts: bool = False) -> str:
    key_pool = get_api_keys_pool(for_posts=for_posts)
    if not key_pool:
        logger.error("No Gemini API keys available.")
        return ""
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"
    
    for key in key_pool:
        try:
            client = genai.Client(api_key=key)
            for model_name in MODELS:
                try:
                    logger.info(f"Attempting to generate text with model: {model_name}")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    if response.text:
                        return response.text
                except Exception as e:
                    logger.warning(f"Failed with {model_name} ({e}). Falling back to next model...")
        except Exception as ke:
            logger.warning(f"API key failed ({ke}). Trying backup key...")
            
    logger.error("All Gemini models and API keys failed.")
    return ""

def extract_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000, for_posts: bool = False) -> dict:
    key_pool = get_api_keys_pool(for_posts=for_posts)
    if not key_pool:
        logger.error("No Gemini API keys available.")
        return {}
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"
    
    for key in key_pool:
        try:
            client = genai.Client(api_key=key)
            for model_name in MODELS:
                try:
                    logger.info(f"Attempting to extract JSON with model: {model_name}")
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
                    raw_text = raw_text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                    return json.loads(raw_text.strip())
                except Exception as e:
                    logger.warning(f"Failed with {model_name} ({e}). Falling back to next model...")
        except Exception as ke:
            logger.warning(f"API key failed ({ke}). Trying backup key...")
            
    logger.error("All Gemini models and API keys failed.")
    return {}
