import os
import requests
import json
from app.logger import logger
from app.upload.instagram import upload_photo_to_instagram, upload_carousel_to_instagram
from dotenv import load_dotenv

load_dotenv()

def upload_post_to_facebook(image_paths: list[str] | str, caption: str) -> bool:
    """
    Publishes a Multi-Card Carousel / Album post to Facebook Page and linked Instagram account.
    Supports both a single image path or a list of image paths (4 slides).
    """
    if isinstance(image_paths, str):
        image_paths = [image_paths]

    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_ACCESS_TOKEN")
    ig_user_id = os.getenv("IG_USER_ID")
    
    if not page_id or not access_token:
        logger.warning("Facebook Post Upload Skipped: FB_PAGE_ID or FB_ACCESS_TOKEN not set.")
        return False
        
    logger.info(f"Publishing {len(image_paths)}-Slide Carousel Post to Facebook Page ID: {page_id}...")
    
    # 1. Single Image Legacy Fallback
    if len(image_paths) == 1:
        url = f"https://graph.facebook.com/v20.0/{page_id}/photos"
        payload = {
            'message': caption,
            'published': 'true',
            'access_token': access_token
        }
        try:
            with open(image_paths[0], 'rb') as img_file:
                files = {'source': ('post_image.jpg', img_file, 'image/jpeg')}
                response = requests.post(url, data=payload, files=files, timeout=60)
            if response.status_code == 200:
                photo_id = response.json().get('id')
                logger.info(f"Facebook Single Photo published! ID: {photo_id}")
                if ig_user_id and photo_id:
                    img_resp = requests.get(f"https://graph.facebook.com/v20.0/{photo_id}?fields=images&access_token={access_token}", timeout=15)
                    images_data = img_resp.json().get('images', [])
                    if images_data:
                        upload_photo_to_instagram(images_data[0].get('source'), caption)
                return True
            else:
                logger.error(f"Facebook photo upload failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error publishing photo to Facebook: {e}")
            return False

    # 2. Multi-Photo Carousel / Album Post
    photo_ids = []
    cdn_image_urls = []
    
    for idx, img_p in enumerate(image_paths):
        upload_url = f"https://graph.facebook.com/v20.0/{page_id}/photos"
        payload = {
            'published': 'false',
            'access_token': access_token
        }
        try:
            with open(img_p, 'rb') as img_file:
                files = {'source': (f'slide_{idx+1}.jpg', img_file, 'image/jpeg')}
                resp = requests.post(upload_url, data=payload, files=files, timeout=60)
            if resp.status_code == 200:
                p_id = resp.json().get('id')
                photo_ids.append(p_id)
                logger.info(f"Uploaded slide {idx+1}/{len(image_paths)} (ID: {p_id})")
                
                # Query CDN URL for Instagram
                if ig_user_id:
                    img_query_url = f"https://graph.facebook.com/v20.0/{p_id}?fields=images&access_token={access_token}"
                    img_q_resp = requests.get(img_query_url, timeout=15)
                    images_data = img_q_resp.json().get('images', [])
                    if images_data:
                        cdn_image_urls.append(images_data[0].get('source'))
            else:
                logger.error(f"Failed to upload slide {idx+1}: {resp.text}")
        except Exception as e:
            logger.error(f"Error uploading slide {idx+1}: {e}")

    if not photo_ids:
        logger.error("Failed to upload any carousel slides to Facebook.")
        return False

    # Publish Multi-Card Feed Post on Facebook
    feed_url = f"https://graph.facebook.com/v20.0/{page_id}/feed"
    attached_media = [{"media_fbid": str(pid)} for pid in photo_ids]
    feed_payload = {
        'message': caption,
        'attached_media': json.dumps(attached_media),
        'access_token': access_token
    }
    
    fb_success = False
    try:
        f_resp = requests.post(feed_url, data=feed_payload, timeout=60)
        if f_resp.status_code == 200:
            post_id = f_resp.json().get('id')
            logger.info(f"🎉 Facebook {len(photo_ids)}-Slide Carousel Post published! Post ID: {post_id}")
            fb_success = True
        else:
            logger.error(f"Facebook Carousel post publishing failed: {f_resp.text}")
    except Exception as e:
        logger.error(f"Error creating Facebook Carousel post: {e}")

    # Cross-post Carousel to Instagram
    if ig_user_id and len(cdn_image_urls) >= 2:
        try:
            logger.info(f"Starting Instagram Carousel cross-posting ({len(cdn_image_urls)} slides)...")
            upload_carousel_to_instagram(cdn_image_urls, caption)
        except Exception as e:
            logger.warning(f"Instagram Carousel auto-post encountered an issue: {e}")

    return fb_success
