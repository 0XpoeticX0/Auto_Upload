import os
import time
import requests
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

def get_instagram_credentials():
    token = os.getenv("FB_ACCESS_TOKEN")
    ig_user_id = os.getenv("IG_USER_ID")
    return token, ig_user_id

def upload_photo_to_instagram(image_url: str, caption: str) -> bool:
    """
    Publishes a photo post to Instagram via the Instagram Graph API.
    Step 1: Create media container with public image_url and caption.
    Step 2: Publish the media container.
    """
    token, ig_user_id = get_instagram_credentials()
    if not token or not ig_user_id:
        logger.warning("Instagram Upload Skipped: FB_ACCESS_TOKEN or IG_USER_ID not set.")
        return False

    logger.info(f"Creating Instagram photo container for @{ig_user_id}...")
    container_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': token
    }
    
    try:
        resp = requests.post(container_url, data=payload, timeout=30)
        res_data = resp.json()
        
        if resp.status_code != 200 or 'id' not in res_data:
            logger.error(f"Instagram media container creation failed: {resp.text}")
            return False
            
        creation_id = res_data['id']
        logger.info(f"Instagram container created (ID: {creation_id}). Publishing...")
        time.sleep(3)
        
        # Publish
        publish_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
        pub_payload = {
            'creation_id': creation_id,
            'access_token': token
        }
        pub_resp = requests.post(publish_url, data=pub_payload, timeout=30)
        pub_data = pub_resp.json()
        
        if pub_resp.status_code == 200 and 'id' in pub_data:
            logger.info(f"Instagram Photo successfully published! Post ID: {pub_data['id']}")
            return True
        else:
            logger.error(f"Instagram media publish failed: {pub_resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error publishing photo to Instagram: {e}")
        return False
