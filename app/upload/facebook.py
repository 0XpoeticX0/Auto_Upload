import os
import requests
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

from app.upload.instagram import upload_reel_to_instagram

def get_page_access_token(page_id: str, base_token: str) -> str:
    """If base_token is a System User / User token, fetches the specific Page Access Token."""
    try:
        url = f"https://graph.facebook.com/v20.0/me/accounts?access_token={base_token}"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            accounts = res.json().get("data", [])
            for acc in accounts:
                if acc.get("id") == str(page_id) and acc.get("access_token"):
                    logger.info(f"Retrieved dedicated Page Access Token for Page {page_id}")
                    return acc["access_token"]
    except Exception as e:
        logger.warning(f"Could not query me/accounts: {e}")
    return base_token

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

def upload_to_facebook(video_path: str, metadata: dict, video_type: str = "auto", thumbnail_path: str = None):
    logger.info(f"Starting Facebook & Instagram Upload for {video_path}")
    
    page_id = os.getenv("FB_PAGE_ID")
    base_token = os.getenv("FB_ACCESS_TOKEN")
    ig_user_id = os.getenv("IG_USER_ID")
    
    if not page_id or not base_token:
        logger.warning("Facebook Upload Skipped: FB_PAGE_ID or FB_ACCESS_TOKEN not set in .env")
        return False

    # Obtain Page Access Token (works for both System User tokens and direct Page tokens)
    access_token = get_page_access_token(page_id, base_token)

    if isinstance(metadata, str):
        metadata = {"description": metadata}

    description = metadata.get("description", "")
    title = metadata.get("facebook_title", metadata.get("youtube_title", ""))
    # description already begins with title_bn — do NOT prepend title again or it duplicates
    full_caption = description.strip()
    
    # Determine pinned comment
    pinned_comment = metadata.get("pinned_comment")
    if not pinned_comment:
        if "কুইজ" in title or "quiz" in title.lower():
            pinned_comment = "আজকের কুইজে আপনার স্কোর ৩-এ কত হলো? ৩/৩, ২/৩ নাকি ১/৩? কমেন্টে জানান! 👇"
        else:
            pinned_comment = "সহীহ সুন্নাহর দাওয়াত ছড়িয়ে দিতে বন্ধুদের সাথে Share করুন—রাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿"

    # Auto-detect: if filename contains "loop_reel", "_short", "reel", "slot", "episode", or "quiz", use Reels API and Instagram cross-posting
    is_reel = (
        video_type == "reel" or 
        "_short" in video_path.lower() or 
        "loop_reel" in video_path.lower() or 
        "reel" in video_path.lower() or 
        "slot" in video_path.lower() or 
        "quiz" in video_path.lower() or
        "episode" in video_path.lower()
    )

    thumbnail_path = thumbnail_path or metadata.get("thumbnail_path")
    scheduled_publish_time = metadata.get("scheduled_publish_time")

    if is_reel:
        logger.info("Uploading as Facebook REEL (shown to non-followers automatically!)")
        success, video_id = _upload_as_reel(page_id, access_token, video_path, title, description, scheduled_publish_time=scheduled_publish_time)
    else:
        logger.info("Uploading as Facebook VIDEO (shown on Page timeline)")
        success, video_id = _upload_as_video(page_id, access_token, video_path, title, description, scheduled_publish_time=scheduled_publish_time)

    # Post auto-first comment
    if success and video_id and pinned_comment and not scheduled_publish_time:
        _post_facebook_comment(page_id, access_token, video_id, pinned_comment)

    # Upload custom thumbnail if provided
    cover_cdn_url = None
    if success and video_id and thumbnail_path and os.path.exists(thumbnail_path):
        try:
            logger.info(f"Uploading custom thumbnail to Facebook Reel {video_id}...")
            with open(thumbnail_path, 'rb') as tf:
                thumb_resp = requests.post(
                    f"https://graph.facebook.com/v20.0/{video_id}/thumbnails",
                    data={'is_preferred': 'true', 'access_token': access_token},
                    files={'source': tf},
                    timeout=30
                )
            if thumb_resp.status_code == 200:
                logger.info("✅ Facebook Reel custom thumbnail uploaded successfully!")
                t_list = requests.get(f"https://graph.facebook.com/v20.0/{video_id}/thumbnails?access_token={access_token}", timeout=15).json()
                for item in reversed(t_list.get('data', [])):
                    if item.get('is_preferred'):
                        cover_cdn_url = item.get('uri')
                        break
        except Exception as e:
            logger.warning(f"Facebook custom thumbnail notice: {e}")

    # Cross-post to Instagram Reels if IG_USER_ID is configured and not scheduled
    if is_reel and ig_user_id and metadata.get("crosspost_instagram", True) and not scheduled_publish_time:
        try:
            logger.info(f"Starting Instagram REEL cross-posting for @{ig_user_id}...")
            upload_reel_to_instagram(video_path, full_caption, cover_url=cover_cdn_url, thumb_offset_ms=3000)
        except Exception as e:
            logger.warning(f"Instagram Reel auto-post encountered an issue: {e}")

    return video_id if success else False

def _upload_as_video(page_id, access_token, video_path, title, description, scheduled_publish_time=None):
    url = f"https://graph.facebook.com/v20.0/{page_id}/videos"
    payload = {
        'title': title,
        'description': description,
        'no_story': 'false',
        'access_token': access_token
    }
    if scheduled_publish_time:
        payload['published'] = 'false'
        payload['scheduled_publish_time'] = str(int(scheduled_publish_time))
        logger.info(f"Scheduling Facebook Video for timestamp: {scheduled_publish_time}")
    else:
        payload['published'] = 'true'

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

def _upload_as_reel(page_id, access_token, video_path, title, description, scheduled_publish_time=None):
    """
    Upload using Facebook Reels API - reaches non-followers organically.
    Step 1: Initialize upload session
    Step 2: Upload video binary
    Step 3: Publish or Schedule the Reel
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
        logger.info("Reel binary uploaded successfully. Publishing or Scheduling...")

        # Step 3: Publish or Schedule the Reel
        finish_payload = {
            'upload_phase': 'finish',
            'video_id': upload_session_id,
            'access_token': access_token,
            'description': description,
        }
        if scheduled_publish_time:
            finish_payload['video_state'] = 'SCHEDULED'
            finish_payload['scheduled_publish_time'] = str(int(scheduled_publish_time))
            logger.info(f"Scheduling Facebook Reel for timestamp: {scheduled_publish_time}")
        else:
            finish_payload['video_state'] = 'PUBLISHED'

        finish_resp = requests.post(start_url, data=finish_payload, timeout=30)
        if finish_resp.status_code == 200:
            status_word = "SCHEDULED" if scheduled_publish_time else "published"
            logger.info(f"🎉 Facebook REEL {status_word}! Video ID: {upload_session_id}")
            return True, upload_session_id
        else:
            logger.error(f"Reel publish/schedule failed: {finish_resp.text}")
            return False, None

    except Exception as e:
        logger.error(f"Error uploading Reel to Facebook: {e}")
        return False, None
