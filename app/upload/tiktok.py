# -*- coding: utf-8 -*-
import os
import time
import requests
import json
from app.logger import logger
from app.config import TIKTOK_ACCESS_TOKEN, TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_OPEN_ID

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

def upload_to_tiktok(video_path: str, caption: str, tags: list = None, privacy_level: str = "PUBLIC_TO_EVERYONE") -> dict:
    """
    Uploads and publishes a vertical video (9:16) to TikTok using TikTok Content Posting API v2.
    
    Parameters:
    - video_path: Path to the MP4 video file.
    - caption: Video description/title (can include hashtags).
    - tags: List of hashtag strings (optional).
    - privacy_level: 'PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'SELF_ONLY'.
    
    Returns:
    - Dict with publish_id and status.
    """
    if not os.path.exists(video_path):
        logger.error(f"TikTok upload failed: Video file not found at {video_path}")
        return {"status": "error", "message": "Video file not found"}

    token = os.getenv("TIKTOK_ACCESS_TOKEN", TIKTOK_ACCESS_TOKEN)
    if not token:
        logger.warning(
            "⚠️ TIKTOK_ACCESS_TOKEN is not set in environment. "
            "Skipping TikTok upload. (To enable, add TIKTOK_ACCESS_TOKEN in your GitHub Repository Secrets or .env)"
        )
        return {
            "status": "skipped",
            "message": "TIKTOK_ACCESS_TOKEN not configured"
        }

    # Format caption with tags
    full_caption = caption.strip()
    if tags:
        clean_tags = [f"#{t.lstrip('#')}" for t in tags if t.strip()]
        full_caption = f"{full_caption} {' '.join(clean_tags)}"
    
    # TikTok title limit is 2200 characters in v2 (or 150 for basic title)
    full_caption = full_caption[:2000]

    video_size = os.path.getsize(video_path)
    logger.info(f"Initializing TikTok Direct Post for '{full_caption[:50]}...' ({video_size / (1024*1024):.2f} MB)")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8"
    }

    # 1. Initialize Direct Post Upload
    init_url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
    init_payload = {
        "post_info": {
            "title": full_caption,
            "privacy_level": privacy_level,
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False,
            "video_cover_timestamp_ms": 1000
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1
        }
    }

    try:
        init_res = requests.post(init_url, headers=headers, json=init_payload, timeout=30)
        init_data = init_res.json()
        
        if init_res.status_code != 200 or init_data.get("error", {}).get("code") != "ok":
            err_msg = init_data.get("error", {}).get("message", init_res.text)
            logger.error(f"TikTok initialization failed: {err_msg}")
            return {"status": "error", "error": err_msg}

        publish_id = init_data["data"]["publish_id"]
        upload_url = init_data["data"]["upload_url"]
        logger.info(f"TikTok publish initialized. Publish ID: {publish_id}")

        # 2. Upload Video Binary to Presigned URL
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        upload_headers = {
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            "Content-Type": "video/mp4"
        }

        upload_res = requests.put(upload_url, headers=upload_headers, data=video_bytes, timeout=120)
        if upload_res.status_code not in (200, 201):
            logger.error(f"TikTok binary upload failed with status code {upload_res.status_code}: {upload_res.text}")
            return {"status": "error", "error": f"Upload failed ({upload_res.status_code})"}

        logger.info(f"✅ Video successfully uploaded to TikTok! (Publish ID: {publish_id})")

        # 3. Check Publishing Status
        time.sleep(2)
        status_url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"
        status_payload = {"publish_id": publish_id}
        status_res = requests.post(status_url, headers=headers, json=status_payload, timeout=20)
        
        if status_res.status_code == 200:
            status_data = status_res.json()
            pub_status = status_data.get("data", {}).get("status", "PROCESSING_DOWNLOAD")
            logger.info(f"TikTok publishing status: {pub_status}")
            return {
                "status": "success",
                "publish_id": publish_id,
                "publish_status": pub_status
            }

        return {
            "status": "success",
            "publish_id": publish_id
        }

    except Exception as e:
        logger.error(f"TikTok upload exception: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import sys
    test_video = sys.argv[1] if len(sys.argv) > 1 else "data/output/sample.mp4"
    if os.path.exists(test_video):
        print(upload_to_tiktok(test_video, "ফজরের ৩টি বরকতময় আমল 🌿 #DailyDos #Islam"))
    else:
        print(f"Test video not found at {test_video}")
