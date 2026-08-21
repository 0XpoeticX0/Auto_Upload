import os
import requests
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

from app.upload.instagram import upload_reel_to_instagram

def _post_facebook_comment(page_id: str, access_token: str, video_id: str, comment_text: str):
    """Posts an automatic first comment on the newly uploaded Facebook Reel / Video."""
    if not comment_text or not video_id:
        return
    try:
        url = f"https://graph.facebook.com/v20.0/{video_id}/comments"
        payload = {
            'message': comment_text,
            'access_token': access_token
        }
        res = requests.post(url, data=payload, timeout=15)
        if res.status_code == 200:
            logger.info(f"✅ Auto-first comment posted on Facebook: {res.json().get('id')}")
        else:
            logger.warning(f"Facebook comment notice: {res.text}")
    except Exception as e:
        logger.warning(f"Failed to post auto-first comment on Facebook: {e}")

def upload_to_facebook(video_path: str, metadata: dict, video_type: str = "auto"):
    logger.info(f"Starting Facebook & Instagram Upload for {video_path}")
    
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_ACCESS_TOKEN")
    ig_user_id = os.getenv("IG_USER_ID")
    
    if not page_id or not access_token:
        logger.warning("Facebook Upload Skipped: FB_PAGE_ID or FB_ACCESS_TOKEN not set in .env")
        return False

    description = metadata.get("description", "")
    title = metadata.get("facebook_title", metadata.get("youtube_title", ""))
    full_caption = f"{title}\n\n{description}".strip()
    
    # Determine pinned comment
    pinned_comment = metadata.get("pinned_comment")
    if not pinned_comment:
        if "কুইজ" in title or "quiz" in title.lower():
            pinned_comment = "আজকের কুইজে আপনার স্কোর ৫-এ কত হলো? ৫/৫, ৪/৫ নাকি ৩/৫? কমেন্টে জানান! 👇"
        else:
            pinned_comment = "কমেন্টে একবার 'সুবহানাল্লাহ' / 'আলহামদুলিল্লাহ' লিখে সদকায়ে জারিয়া হিসেবে বন্ধুদের সাথে শেয়ার করুন 🌿"

    # Auto-detect: if filename contains "_short" or video_type forced to "reel", use Reels API
    is_reel = video_type == "reel" or "_short" in video_path or "quiz" in video_path.lower()

    if is_reel:
        logger.info("Uploading as Facebook REEL (shown to non-followers automatically!)")
        success, video_id = _upload_as_reel(page_id, access_token, video_path, title, description)
    else:
        logger.info("Uploading as Facebook VIDEO (shown on Page timeline)")
        success, video_id = _upload_as_video(page_id, access_token, video_path, title, description)

    # Post auto-first comment
    if success and video_id and pinned_comment:
        _post_facebook_comment(page_id, access_token, video_id, pinned_comment)

    # Cross-post to Instagram Reels if IG_USER_ID is configured
    if is_reel and ig_user_id:
        try:
            logger.info(f"Starting Instagram REEL cross-posting for @{ig_user_id}...")
            upload_reel_to_instagram(video_path, full_caption)
        except Exception as e:
            logger.warning(f"Instagram Reel auto-post encountered an issue: {e}")

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
            vid = result.get('id')
            logger.info(f"Facebook Video uploaded! Video ID: {vid}")
            return True, vid
        else:
            logger.error(f"Facebook video upload failed: {response.text}")
            return False, None
    except Exception as e:
        logger.error(f"Error uploading video to Facebook: {e}")
        return False, None

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
            return False, None

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
            return False, None
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
            logger.info(f"🎉 Facebook REEL published! Video ID: {upload_session_id}")
            return True, upload_session_id
        else:
            logger.error(f"Reel publish failed: {finish_resp.text}")
            return False, None

    except Exception as e:
        logger.error(f"Error uploading Reel to Facebook: {e}")
        return False, None
