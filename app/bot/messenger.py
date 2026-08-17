import os
import requests
from app.logger import logger

FB_GRAPH_URL = "https://graph.facebook.com/v20.0"

def get_page_access_token():
    return os.environ.get("FB_ACCESS_TOKEN")

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
            logger.error(f"Facebook Send API Error: {res_data}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Messenger reply: {e}")
        return False
