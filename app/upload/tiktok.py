# -*- coding: utf-8 -*-
import os
import time
from app.logger import logger

def upload_to_tiktok(video_path: str, caption: str, tags: list = None) -> dict:
    """
    Automated TikTok Uploader:
    1. Primary: Direct Session / Cookie Upload via tiktok-uploader (Zero developer portal / review needed).
    2. Fallback: Official Content Posting API if TIKTOK_ACCESS_TOKEN is set.
    """
    if not os.path.exists(video_path):
        logger.error(f"TikTok upload failed: Video file not found at {video_path}")
        return {"status": "error", "message": "Video not found"}

    # Format caption with tags
    full_caption = caption.strip()
    if tags:
        clean_tags = [f"#{t.lstrip('#')}" for t in tags if t.strip()]
        full_caption = f"{full_caption} {' '.join(clean_tags)}"
    full_caption = full_caption[:2000]

    # 1. Look for TikTok Cookies
    cookie_path = os.path.abspath("tiktok_cookies.txt")
    env_cookies = os.getenv("TIKTOK_COOKIES_TXT")
    
    # If cookies are in environment secret, write them to temporary file
    if env_cookies and not os.path.exists(cookie_path):
        try:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(env_cookies)
            logger.info("Injected TIKTOK_COOKIES_TXT from environment secret.")
        except Exception as e:
            logger.warning(f"Could not write env cookies: {e}")

    # --- PRIMARY METHOD: Cookie-based Automated Upload ---
    if os.path.exists(cookie_path):
        logger.info(f"Uploading to TikTok using direct session cookies for: '{full_caption[:50]}...'")
        try:
            from tiktok_uploader.upload import upload_video
            
            # Run upload with cookies
            failed_videos = upload_video(
                filename=video_path,
                description=full_caption,
                cookies=cookie_path,
                headless=True
            )
            
            if not failed_videos:
                logger.info("✅ Video successfully uploaded and published to TikTok!")
                return {"status": "success", "method": "cookie_session"}
            else:
                logger.warning(f"TikTok upload returned failure list: {failed_videos}")
                return {"status": "error", "details": failed_videos}
                
        except Exception as e:
            logger.error(f"TikTok cookie upload error: {e}")
            return {"status": "error", "error": str(e)}

    # --- FALLBACK METHOD: Official Content Posting API ---
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    if access_token:
        logger.info("Attempting TikTok upload via Content Posting API...")
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            video_size = os.path.getsize(video_path)
            init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            init_payload = {
                "post_info": {
                    "title": full_caption,
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_stitch": False,
                    "disable_comment": False
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": video_size,
                    "total_chunk_count": 1
                }
            }
            res = requests.post(init_url, headers=headers, json=init_payload, timeout=30)
            init_data = res.json()
            if res.status_code == 200 and init_data.get("error", {}).get("code") == "ok":
                upload_url = init_data["data"]["upload_url"]
                with open(video_path, "rb") as f:
                    v_bytes = f.read()
                up_res = requests.put(
                    upload_url,
                    headers={"Content-Range": f"bytes 0-{video_size - 1}/{video_size}", "Content-Type": "video/mp4"},
                    data=v_bytes,
                    timeout=120
                )
                if up_res.status_code in (200, 201):
                    logger.info("✅ Video published to TikTok via API!")
                    return {"status": "success", "method": "api"}
        except Exception as e:
            logger.error(f"TikTok API upload error: {e}")

    logger.warning("⚠️ TikTok upload skipped: Neither tiktok_cookies.txt nor TIKTOK_ACCESS_TOKEN found.")
    return {"status": "skipped", "message": "No TikTok credentials configured"}

if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else "data/output/sample.mp4"
    if os.path.exists(test_file):
        print(upload_to_tiktok(test_file, "ফজরের ৩টি বিশেষ আমল 🌿 #DailyDos #Islam #Shorts"))
    else:
        print(f"Sample test file not found at {test_file}")
