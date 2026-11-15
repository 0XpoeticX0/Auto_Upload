import os
import requests
from app.logger import logger

FB_GRAPH_URL = "https://graph.facebook.com/v20.0"

_CACHED_PAGE_TOKEN = None

def get_page_access_token() -> str:
    """
    Get the Page Access Token.
    If FB_ACCESS_TOKEN is a User Token, automatically resolve and cache
    the specific Page Access Token for FB_PAGE_ID via /me/accounts.
    """
    global _CACHED_PAGE_TOKEN
    if _CACHED_PAGE_TOKEN:
        return _CACHED_PAGE_TOKEN

    base_token = os.environ.get("FB_ACCESS_TOKEN", "").strip()
    target_page_id = os.environ.get("FB_PAGE_ID", "103994582489858").strip()

    if not base_token:
        return ""

    try:
        url = f"{FB_GRAPH_URL}/me/accounts"
        res = requests.get(url, params={"access_token": base_token}, timeout=10)
        data = res.json()
        for page in data.get("data", []):
            if str(page.get("id")) == str(target_page_id) and page.get("access_token"):
                _CACHED_PAGE_TOKEN = page["access_token"]
                logger.info(f"Successfully resolved Page Access Token for {page.get('name')} ({target_page_id})")
                return _CACHED_PAGE_TOKEN
        
        # Fallback to first page if ID didn't match
        if data.get("data") and data["data"][0].get("access_token"):
            _CACHED_PAGE_TOKEN = data["data"][0]["access_token"]
            return _CACHED_PAGE_TOKEN
    except Exception as e:
        logger.warning(f"Could not resolve Page Access Token from /me/accounts: {e}")

    # Fallback to the environment token
    _CACHED_PAGE_TOKEN = base_token
    return _CACHED_PAGE_TOKEN

def send_typing_indicator(recipient_id: str, action: str = "typing_on") -> bool:
    """Send sender_action like 'mark_seen', 'typing_on', or 'typing_off'."""
    access_token = get_page_access_token()
    if not access_token:
        return False
        
    url = f"{FB_GRAPH_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "sender_action": action
    }
    params = {"access_token": access_token}
    try:
        requests.post(url, json=payload, params=params, timeout=10)
        return True
    except Exception as e:
        logger.warning(f"Failed to send typing indicator: {e}")
        return False

def send_messenger_reply(recipient_id: str, message_text: str) -> bool:
    """Send text message reply to a Facebook Messenger recipient (PSID)."""
    access_token = get_page_access_token()
    if not access_token:
        logger.error("FB_ACCESS_TOKEN not set in environment.")
        return False
        
    url = f"{FB_GRAPH_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "messaging_type": "RESPONSE"
    }
    params = {"access_token": access_token}
    
    try:
        response = requests.post(url, json=payload, params=params, timeout=15)
        res_data = response.json()
        
        if response.status_code == 200 and "message_id" in res_data:
            logger.info(f"Auto-reply sent successfully to recipient {recipient_id}: {res_data['message_id']}")
            return True
        else:
            err = res_data.get("error", {})
            err_code = err.get("code")
            err_msg = err.get("message", "")
            
            if err_code == 10:
                logger.error(
                    f"[META DEV MODE BLOCK] Error Code 10: Meta App is in 'Development Mode'. "
                    f"Recipient {recipient_id} must be added as a Tester in developers.facebook.com "
                    f"OR switch App Mode from 'Development' to 'Live'. Details: {err_msg}"
                )
            else:
                logger.error(f"Facebook Send API Error: {res_data}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Messenger reply: {e}")
        return False
