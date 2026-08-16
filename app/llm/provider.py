import json
import google.generativeai as genai
from app.config import GEMINI_API_KEY
from app.logger import logger

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_text(system_prompt: str, user_prompt: str) -> str:
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return ""
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}"
    
    try:
        logger.info("Attempting to generate text with model: gemini-3.5-flash")
        model = genai.GenerativeModel('gemini-3.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.warning(f"Failed with gemini-3.5-flash (Likely Quota Limit). Falling back to gemini-3.5-flash-lite...")
        try:
            model = genai.GenerativeModel('gemini-3.5-flash-lite')
            response = model.generate_content(prompt)
            return response.text
        except Exception as fallback_e:
            logger.error(f"Failed with fallback gemini-3.5-flash-lite: {fallback_e}")
            return ""

def extract_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return {}
        
    prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}"
    
    try:
        logger.info("Attempting to extract JSON with model: gemini-3.5-flash")
        model = genai.GenerativeModel('gemini-3.5-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        logger.warning(f"Failed with gemini-3.5-flash (Likely Quota Limit). Falling back to gemini-3.5-flash-lite...")
        try:
            model = genai.GenerativeModel('gemini-3.5-flash-lite', generation_config={"response_mime_type": "application/json"})
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as fallback_e:
            logger.error(f"Failed with fallback gemini-3.5-flash-lite: {fallback_e}")
            return {}
