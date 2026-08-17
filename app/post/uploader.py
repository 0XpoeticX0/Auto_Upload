import os
import requests
from app.logger import logger
from app.upload.instagram import upload_photo_to_instagram
from dotenv import load_dotenv

load_dotenv()

def upload_post_to_facebook(image_path: str, caption: str) -> bool:
    """
    Publishes a photo post with rich caption to Facebook Page and linked Instagram account.
    """
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_ACCESS_TOKEN")
    ig_user_id = os.getenv("IG_USER_ID")
    
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
            photo_id = res_data.get('id')
            post_id = res_data.get('post_id') or photo_id
            logger.info(f"Facebook Photo Post successfully published! Post ID: {post_id}")
            
            # If Instagram account is connected, cross-post to Instagram using Facebook CDN URL
            if ig_user_id and photo_id:
                try:
                    logger.info("Fetching Facebook CDN image URL for Instagram publishing...")
                    img_query_url = f"https://graph.facebook.com/v20.0/{photo_id}?fields=images&access_token={access_token}"
                    img_resp = requests.get(img_query_url, timeout=15)
                    images_data = img_resp.json().get('images', [])
                    
                    if images_data and len(images_data) > 0:
                        cdn_image_url = images_data[0].get('source')
                        logger.info(f"Uploading to Instagram @{ig_user_id}...")
                        upload_photo_to_instagram(cdn_image_url, caption)
                except Exception as e:
                    logger.warning(f"Instagram auto-post attempt encountered an issue: {e}")
            
            return True
        else:
            logger.error(f"Facebook photo upload failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error publishing photo post to Facebook: {e}")
        return False
