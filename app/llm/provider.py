import json
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY
from app.logger import logger

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def generate_text(system_prompt: str, user_prompt: str) -> str:
    if not gemini_client:
        logger.error("GEMINI_API_KEY is not set.")
        return ""
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}"
    
    try:
        logger.info("Attempting to generate text with model: gemini-3.5-flash")
        response = gemini_client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.warning(f"Failed with gemini-3.5-flash (Likely Quota Limit). Falling back to gemini-3.5-flash-lite...")
        try:
            response = gemini_client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
            )
            return response.text
        except Exception as fallback_e:
            logger.error(f"Failed with fallback gemini-3.5-flash-lite: {fallback_e}")
            return ""

def extract_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    if not gemini_client:
        logger.error("GEMINI_API_KEY is not set.")
        return {}
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}"
    
    try:
        logger.info("Attempting to extract JSON with model: gemini-3.5-flash")
        response = gemini_client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        logger.warning(f"Failed with gemini-3.5-flash (Likely Quota Limit). Falling back to gemini-3.5-flash-lite...")
        try:
            response = gemini_client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except Exception as fallback_e:
            logger.error(f"Failed with fallback gemini-3.5-flash-lite: {fallback_e}")
            return {}

