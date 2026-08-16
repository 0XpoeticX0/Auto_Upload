import os
import requests
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

def upload_to_facebook(video_path: str, metadata: dict, video_type: str = "auto"):
    logger.info(f"Starting Facebook Page Upload for {video_path}")
    
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_ACCESS_TOKEN")
    
    if not page_id or not access_token:
        logger.warning("Facebook Upload Skipped: FB_PAGE_ID or FB_ACCESS_TOKEN not set in .env")
        return False

    description = metadata.get("description", "")
    title = metadata.get("facebook_title", metadata.get("youtube_title", ""))

    # Auto-detect: if filename contains "_short" or video_type forced to "reel", use Reels API
    is_reel = video_type == "reel" or "_short" in video_path

    if is_reel:
        logger.info("Uploading as Facebook REEL (shown to non-followers automatically!)")
        success = _upload_as_reel(page_id, access_token, video_path, title, description)
    else:
        logger.info("Uploading as Facebook VIDEO (shown on Page timeline)")
        success = _upload_as_video(page_id, access_token, video_path, title, description)

    return success


def _upload_as_video(page_id, access_token, video_path, title, description):
    url = f"https://graph.facebook.com/v20.0/{page_id}/videos"
    payload = {
        'title': title,
        'description': f"{title}\n\n{description}",
        'published': 'true',
        'no_story': 'false',
        'access_token': access_token
    }
    try:
        with open(video_path, 'rb') as video_file:
            response = requests.post(url, data=payload, files={'source': video_file}, timeout=600)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Facebook Video uploaded! Video ID: {result.get('id')}")
            return True
        else:
            logger.error(f"Facebook video upload failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error uploading video to Facebook: {e}")
        return False


def _upload_as_reel(page_id, access_token, video_path, title, description):
    """
    Upload using Facebook Reels API - reaches non-followers organically.
    Step 1: Initialize upload session
    Step 2: Upload video binary
    Step 3: Publish the Reel
    """
    try:
        file_size = os.path.getsize(video_path)

        # Step 1: Start upload session
        start_url = f"https://graph.facebook.com/v20.0/{page_id}/video_reels"
        start_payload = {
            'upload_phase': 'start',
            'access_token': access_token
        }
        start_resp = requests.post(start_url, data=start_payload, timeout=30)
        if start_resp.status_code != 200:
            logger.error(f"Reel session init failed: {start_resp.text}")
            return False

        upload_session_id = start_resp.json().get('video_id')
        logger.info(f"Reel upload session started. Session ID: {upload_session_id}")

        # Step 2: Upload binary
        upload_url = f"https://rupload.facebook.com/video-upload/v20.0/{upload_session_id}"
        headers = {
            'Authorization': f'OAuth {access_token}',
            'offset': '0',
            'file_size': str(file_size),
        }
        with open(video_path, 'rb') as video_file:
            upload_resp = requests.post(upload_url, headers=headers, data=video_file, timeout=600)
        if not upload_resp.json().get('success'):
            logger.error(f"Reel binary upload failed: {upload_resp.text}")
            return False
        logger.info("Reel binary uploaded successfully. Publishing...")

        # Step 3: Publish the Reel
        finish_payload = {
            'upload_phase': 'finish',
            'video_id': upload_session_id,
            'access_token': access_token,
            'video_state': 'PUBLISHED',
            'description': f"{title}\n\n{description}",
        }
        finish_resp = requests.post(start_url, data=finish_payload, timeout=30)
        if finish_resp.status_code == 200:
            logger.info(f"Facebook REEL published! It will now be shown to non-followers.")
            return True
        else:
            logger.error(f"Reel publish failed: {finish_resp.text}")
            return False

    except Exception as e:
        logger.error(f"Error uploading Reel to Facebook: {e}")
        return False
