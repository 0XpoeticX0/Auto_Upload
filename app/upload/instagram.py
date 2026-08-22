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

def upload_carousel_to_instagram(item_urls: list[str], caption: str, is_video: bool = False) -> bool:
    """
    Publishes a Multi-Item Carousel post to Instagram via the Instagram Graph API.
    Step 1: Create individual item containers with is_carousel_item=true.
    Step 2: Create a CAROUSEL container with children IDs and caption.
    Step 3: Publish the carousel container.
    """
    token, ig_user_id = get_instagram_credentials()
    if not token or not ig_user_id:
        logger.warning("Instagram Carousel Upload Skipped: FB_ACCESS_TOKEN or IG_USER_ID not set.")
        return False

    if not item_urls or len(item_urls) < 2:
        logger.error(f"Instagram Carousel requires at least 2 items. Given: {len(item_urls) if item_urls else 0}")
        return False

    logger.info(f"Creating Instagram Carousel ({len(item_urls)} items) for @{ig_user_id}...")
    container_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"
    
    child_ids = []
    for idx, url in enumerate(item_urls):
        try:
            logger.info(f"Creating carousel item {idx+1}/{len(item_urls)}...")
            payload = {
                'is_carousel_item': 'true',
                'access_token': token
            }
            if is_video:
                payload['media_type'] = 'VIDEO'
                payload['video_url'] = url
            else:
                payload['image_url'] = url
                
            resp = requests.post(container_url, data=payload, timeout=30)
            res_data = resp.json()
            if resp.status_code == 200 and 'id' in res_data:
                child_id = res_data['id']
                child_ids.append(child_id)
                logger.info(f"Carousel item {idx+1} container created (ID: {child_id})")
            else:
                logger.error(f"Failed to create carousel item {idx+1}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error creating carousel item {idx+1}: {e}")
            return False
            
    # Wait for all child items to be ready
    time.sleep(5)
    
    # Step 2: Create Carousel Parent Container
    try:
        logger.info(f"Creating parent CAROUSEL container with children: {child_ids}...")
        carousel_payload = {
            'media_type': 'CAROUSEL',
            'children': child_ids,
            'caption': caption,
            'access_token': token
        }
        car_resp = requests.post(container_url, json=carousel_payload, timeout=30)
        car_data = car_resp.json()
        
        if car_resp.status_code != 200 or 'id' not in car_data:
            logger.error(f"Instagram Carousel parent container creation failed: {car_resp.text}")
            return False
            
        carousel_id = car_data['id']
        logger.info(f"Carousel parent container created (ID: {carousel_id}). Publishing in 5s...")
        time.sleep(5)
        
        # Step 3: Publish Carousel
        publish_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
        pub_payload = {
            'creation_id': carousel_id,
            'access_token': token
        }
        pub_resp = requests.post(publish_url, data=pub_payload, timeout=30)
        pub_data = pub_resp.json()
        
        if pub_resp.status_code == 200 and 'id' in pub_data:
            logger.info(f"🎉 Instagram CAROUSEL successfully published! Post ID: {pub_data['id']}")
            return True
        else:
            logger.error(f"Instagram Carousel publish failed: {pub_resp.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error publishing Carousel to Instagram: {e}")
        return False

def upload_reel_to_instagram(video_path: str, caption: str) -> bool:
    """
    Publishes a 9:16 vertical video as an Instagram REEL via Instagram Graph API.
    Step 1: Initialize resumable container (media_type=REELS, upload_type=resumable)
    Step 2: Upload video binary to rupload URI
    Step 3: Wait for video processing (status_code == 'FINISHED')
    Step 4: Publish the Reel via media_publish
    """
    token, ig_user_id = get_instagram_credentials()
    if not token or not ig_user_id:
        logger.warning("Instagram Reel Upload Skipped: FB_ACCESS_TOKEN or IG_USER_ID not set.")
        return False

    if not os.path.exists(video_path):
        logger.error(f"Instagram Reel Upload failed: Video file not found at {video_path}")
        return False

    file_size = os.path.getsize(video_path)
    logger.info(f"Starting Instagram REEL upload for @{ig_user_id} ({file_size / 1024 / 1024:.2f} MB)...")

    try:
        # Step 1: Create Resumable Reel Container
        init_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"
        init_payload = {
            'media_type': 'REELS',
            'upload_type': 'resumable',
            'caption': caption,
            'access_token': token
        }
        init_resp = requests.post(init_url, data=init_payload, timeout=30)
        init_data = init_resp.json()
        
        if init_resp.status_code != 200 or 'id' not in init_data:
            logger.error(f"Instagram Reel container creation failed: {init_resp.text}")
            return False

        container_id = init_data['id']
        rupload_uri = init_data.get('uri')
        if not rupload_uri:
            rupload_uri = f"https://rupload.facebook.com/ig-video-upload/v20.0/{container_id}"

        logger.info(f"Instagram Reel container created (ID: {container_id}). Uploading video binary...")

        # Step 2: Upload Video Binary
        headers = {
            'Authorization': f'OAuth {token}',
            'offset': '0',
            'file_size': str(file_size),
        }
        with open(video_path, 'rb') as vf:
            upload_resp = requests.post(rupload_uri, headers=headers, data=vf, timeout=600)
            
        if upload_resp.status_code not in [200, 201]:
            logger.error(f"Instagram Reel binary upload failed: {upload_resp.text}")
            return False

        logger.info("Instagram Reel binary uploaded. Waiting for Instagram processing...")

        # Step 3: Poll status until FINISHED (up to 60 seconds)
        status_url = f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code&access_token={token}"
        for _ in range(12):
            time.sleep(5)
            status_resp = requests.get(status_url, timeout=15)
            status_data = status_resp.json()
            status_code = status_data.get('status_code')
            logger.info(f"Instagram Reel processing status: {status_code}")
            
            if status_code == 'FINISHED':
                break
            elif status_code == 'ERROR':
                logger.error(f"Instagram Reel processing failed: {status_resp.text}")
                return False

        # Step 4: Publish Reel
        publish_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
        pub_payload = {
            'creation_id': container_id,
            'access_token': token
        }
        pub_resp = requests.post(publish_url, data=pub_payload, timeout=30)
        pub_data = pub_resp.json()

        if pub_resp.status_code == 200 and 'id' in pub_data:
            logger.info(f"Instagram REEL successfully published! Post ID: {pub_data['id']}")
            return True
        else:
            logger.error(f"Instagram Reel publish failed: {pub_resp.text}")
            return False

    except Exception as e:
        logger.error(f"Error uploading Reel to Instagram: {e}")
        return False
