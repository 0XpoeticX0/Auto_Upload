# -*- coding: utf-8 -*-
"""
Interactive YouTube Login and Video Upload Script.
1. Authenticates YouTube with Google OAuth (opens browser).
2. Verifies channel info.
3. Uploads the latest rendered Quran recitation video (Surah Ash-Sharh 1-8).
"""
import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from app.logger import logger
from app.upload.youtube import get_authenticated_service, upload_to_youtube
from app.quran_verse.quran_data import fetch_verse_data, RECITERS_CONFIG as RECITERS
from app.quran_verse.metadata import generate_quran_metadata

def main():
    print("=" * 60)
    print("YouTube Authentication and Video Uploader")
    print("=" * 60)

    # 1. Authenticate YouTube
    print("\n[1/3] Authenticating YouTube Service...")
    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to obtain YouTube service. Please check client_secrets.json.")
        return False

    # Check Channel Name
    try:
        resp = youtube.channels().list(part="snippet,statistics", mine=True).execute()
        items = resp.get("items", [])
        if items:
            ch_title = items[0]["snippet"]["title"]
            sub_count = items[0]["statistics"].get("subscriberCount", "N/A")
            print(f"Successfully connected to YouTube channel:")
            print(f"   Channel: {ch_title}")
            print(f"   Subscribers: {sub_count}")
        else:
            print("YouTube connected successfully!")
    except Exception as e:
        print(f"Warning reading channel info: {e}")

    # 2. Identify Video to Upload
    video_path = os.path.join("data", "output", "Quran_Surah_94_1_8_alafasy.mp4")
    if not os.path.exists(video_path):
        out_dir = os.path.join("data", "output")
        candidates = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("Quran_") and f.endswith(".mp4")]
        if candidates:
            candidates.sort(key=os.path.getmtime, reverse=True)
            video_path = candidates[0]
        else:
            print(f"Video file not found: {video_path}")
            return False

    print(f"\n[2/3] Target Video: {video_path}")

    # 3. Generate Metadata
    print("\n[3/3] Generating SEO Metadata and Captions...")
    verse_data = fetch_verse_data(94, 1, 8)
    audio_data = {
        "reciter": RECITERS["alafasy"],
        "total_duration": 33.7
    }
    metadata = generate_quran_metadata(verse_data, audio_data)
    print(f"   Title: {metadata['title']}")
    print(f"   Tags: {', '.join(metadata['tags'][:6])}...")

    upload_meta = {
        "youtube_title": metadata["title"],
        "description": metadata["description"],
        "pinned_comment": metadata["pinned_comment"],
        "tags": metadata["tags"],
        "category": "educational"
    }

    print("\nUploading to YouTube Shorts now...")
    success = upload_to_youtube(video_path, upload_meta)
    if success:
        print("\n" + "=" * 60)
        print("YOUTUBE UPLOAD COMPLETE AND VERIFIED!")
        print("=" * 60)
    else:
        print("\nUpload failed. Please check logs for details.")

    return success

if __name__ == '__main__':
    main()
