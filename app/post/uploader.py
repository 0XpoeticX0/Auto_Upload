import os
import requests
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

def upload_post_to_facebook(image_path: str, caption: str) -> bool:
    """
    Publishes a photo post with rich caption to the Facebook Page via Graph API.
    """
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        logger.warning("Facebook Post Upload Skipped: FB_PAGE_ID or FB_ACCESS_TOKEN not set.")
        return False
        
    logger.info(f"Publishing Photo Post to Facebook Page ID: {page_id}...")
    url = f"https://graph.facebook.com/v20.0/{page_id}/photos"
    
    payload = {
        'message': caption,
        'published': 'true',
        'access_token': access_token
    }
    
    try:
        with open(image_path, 'rb') as img_file:
            files = {'source': ('post_image.jpg', img_file, 'image/jpeg')}
            response = requests.post(url, data=payload, files=files, timeout=60)
            
        if response.status_code == 200:
            res_data = response.json()
            post_id = res_data.get('id') or res_data.get('post_id')
            logger.info(f"Facebook Photo Post successfully published! Post ID: {post_id}")
            return True
        else:
            logger.error(f"Facebook photo upload failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error publishing photo post to Facebook: {e}")
        return False
