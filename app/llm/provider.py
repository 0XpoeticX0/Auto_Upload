import json
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY
from app.logger import logger

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-pro-exp-02-05",
    "gemini-2.0-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b"
]

GLOBAL_RULE = "\n\nCRITICAL SYSTEM RULE: You must cross-check all Islamic claims with authentic Quranic verses and Sahih Hadith. Do not output any misinformation, unverified stories, or false claims. All claims must be backed by authentic sources."

def generate_text(system_prompt: str, user_prompt: str) -> str:
    if not gemini_client:
        logger.error("GEMINI_API_KEY is not set.")
        return ""
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"
    
    for model_name in MODELS:
        try:
            logger.info(f"Attempting to generate text with model: {model_name}")
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.warning(f"Failed with {model_name} (Likely Quota Limit). Falling back...")
            
    logger.error("All Gemini models failed. Quota exhausted.")
    return ""

def extract_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    if not gemini_client:
        logger.error("GEMINI_API_KEY is not set.")
        return {}
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}{GLOBAL_RULE}\n\nUSER PROMPT:\n{user_prompt}"
    
    for model_name in MODELS:
        try:
            logger.info(f"Attempting to extract JSON with model: {model_name}")
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.warning(f"Failed with {model_name} (Likely Quota Limit). Falling back...")
            
    logger.error("All Gemini models failed. Quota exhausted.")
    return {}
