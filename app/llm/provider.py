import json
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, GEMINI_POST_API_KEY
from app.logger import logger

def get_gemini_client(for_posts: bool = False):
    api_key = GEMINI_POST_API_KEY if (for_posts and GEMINI_POST_API_KEY) else GEMINI_API_KEY
    if not api_key:
        api_key = GEMINI_API_KEY
    return genai.Client(api_key=api_key) if api_key else None

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

def generate_text(system_prompt: str, user_prompt: str, for_posts: bool = False) -> str:
    client = get_gemini_client(for_posts=for_posts)
    if not client:
        logger.error("GEMINI_API_KEY is not set.")
        return ""
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"
    
    for model_name in MODELS:
        try:
            logger.info(f"Attempting to generate text with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.warning(f"Failed with {model_name} ({e}). Falling back to next model...")
            
    logger.error("All Gemini models failed. Quota exhausted.")
    return ""

def extract_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000, for_posts: bool = False) -> dict:
    client = get_gemini_client(for_posts=for_posts)
    if not client:
        logger.error("GEMINI_API_KEY is not set.")
        return {}
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"
    
    for model_name in MODELS:
        try:
            logger.info(f"Attempting to extract JSON with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
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
            
    logger.error("All Gemini models failed to extract JSON.")
    return {}
