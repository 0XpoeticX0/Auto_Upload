# -*- coding: utf-8 -*-
"""
Automated 4-Day Instagram Reels Scheduler for 'তাওয়াক্কুলের পরীক্ষা' (Parts 1, 2, 3, 4).
Runs as a background service to auto-publish each part to Instagram at 18:00 BST / 12:00 UTC
with verified high-CTR custom 9:16 thumbnails and pinned first comments.
"""
import os
import sys
import time
import json
import requests
from datetime import datetime, timezone

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from app.logger import logger
from app.upload.instagram import upload_reel_to_instagram
from app.upload.facebook import get_page_access_token

VIDEO_DIR = os.path.abspath(r"incoming_audio\rendered_videos")
STATE_FILE = os.path.abspath(r"data\instagram_schedule_state.json")

SCHEDULE_CONFIG = {
    1: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_1_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_1.jpg"),
        "fb_reel_id": "4547015068903683",
        "publish_at_iso": "2026-09-11T12:00:00Z",       # 11 Sep, 18:00 BST
        "target_unix": 1789128000,
        "caption": (
            "তাওয়াক্কুলের পরীক্ষা (পর্ব ১): ১০০০ স্বর্ণমুদ্রা ও অদ্ভুত শর্ত 🌿\n\n"
            "সহীহ বুখারীতে বর্ণিত তাওয়াক্কুলের এক অবিশ্বাস্য সত্য ঘটনা (পর্ব ১)। "
            "বনী ইসরাঈলের এক ব্যক্তি ১০০০ স্বর্ণমুদ্রা ঋণ চাইল। কিন্তু কোনো সাক্ষী বা জামিনদার দিতে পারল না। "
            "সে বলল—'আল্লাহই আমার সাক্ষী, আল্লাহই আমার জামিনদার!'\n\n"
            "➡️ নির্দিষ্ট দিনে কোনো জাহাজ না পেয়ে কী করল ঋণগ্রহীতা? বাকি অংশ দেখুন পর্ব ২-তে!\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Tawakkul #Reels #Shorts #DailyDosOfIslam #Iman #Allah"
        ),
        "first_comment": "📌 নির্দিষ্ট দিনে কোনো জাহাজ না পেয়ে কী করল ঋণগ্রহীতা? দেখতে পর্ব ২-এর জন্য সাথে থাকুন! ❤️\nসূত্র: সহীহ বুখারী ২২৯১।"
    },
    2: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_2_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_2.jpg"),
        "fb_reel_id": "945769278583594",
        "publish_at_iso": "2026-09-12T12:00:00Z",       # 12 Sep, 18:00 BST
        "target_unix": 1789214400,
        "caption": (
            "তাওয়াক্কুলের পরীক্ষা (পর্ব ২): সাগরে কাঠের গুঁড়ি ভাসিয়ে দিল! 🌊\n\n"
            "সহীহ বুখারীতে বর্ণিত তাওয়াক্কুলের সেই অলৌকিক কাঠের গুঁড়ি (পর্ব ২)। "
            "ঋণ পরিশোধের নির্দিষ্ট দিনে কোনো জাহাজ না পেয়ে সে একটি কাঠের গুঁড়ি নিল। কুড়াল দিয়ে তা ফাঁপা করে "
            "ভেতরে ১০০০ স্বর্ণমুদ্রা ও চিঠি ভরে সমুদ্রের তীরে দাঁড়িয়ে উত্তাল সাগরে ভাসিয়ে দিল...\n\n"
            "➡️ সাগরে ভাসিয়ে দেওয়া সেই কাঠ কি পৌঁছাবে অপর তীরে? দেখুন পর্ব ৩-তে!\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Part2 #Tawakkul #Reels #Shorts #DailyDosOfIslam #Iman"
        ),
        "first_comment": "📌 সাগরে ভাসিয়ে দেওয়া সেই কাঠ কি পৌঁছাবে অপর তীরে? দেখতে পর্ব ৩-এর জন্য সাথে থাকুন! ❤️\nসূত্র: সহীহ বুখারী ২২৯১।"
    },
    3: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_3_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_3.jpg"),
        "fb_reel_id": "1096312049793364",
        "publish_at_iso": "2026-09-13T12:00:00Z",       # 13 Sep, 18:00 BST
        "target_unix": 1789300800,
        "caption": (
            "তাওয়াক্কুলের পরীক্ষা (পর্ব ৩): কাঠের ভেতর অদ্ভুত আওয়াজ! তীরে কী এল? 🪵\n\n"
            "সহীহ বুখারীতে বর্ণিত সেই ভাসমান কাঠের অলৌকিক যাত্রা (পর্ব ৩)। "
            "অপর তীরে দাঁড়িয়ে ঋণদাতা ব্যাকুল হয়ে জাহাজের প্রতীক্ষায় অপেক্ষা করছিল। কোনো জাহাজ এলো না, কিন্তু "
            "ঢেউয়ের সাথে তীরে ভেসে এল একটি ভারী কাঠের গুঁড়ি। সে জ্বালানি কাঠের জন্য তা নিয়ে যাওয়ার সিদ্ধান্ত নিল...\n\n"
            "➡️ কাঠের ভেতরে কী লুকিয়ে ছিল? দেখুন শেষ পর্ব ৪-তে!\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Part3 #Tawakkul #Reels #Shorts #DailyDosOfIslam #Iman"
        ),
        "first_comment": "📌 কাঠের ভেতর থেকে কী বেরিয়ে এল? দেখতে শেষ পর্ব ৪-এর জন্য সাথে থাকুন! ❤️\nসূত্র: সহীহ বুখারী ২২৯১।"
    },
    4: {
        "file": os.path.join(VIDEO_DIR, "bukhari_1000_dinars_part_4_9_16.mp4"),
        "thumbnail": os.path.join(VIDEO_DIR, "thumbnail_bukhari_part_4.jpg"),
        "fb_reel_id": "2884742438592065",
        "publish_at_iso": "2026-09-14T12:00:00Z",       # 14 Sep, 18:00 BST
        "target_unix": 1789387200,
        "caption": (
            "তাওয়াক্কুলের পরীক্ষা (পর্ব ৪ - সমাপ্তি): কাঠ চেরার পর ১০০০ স্বর্ণমুদ্রা উদ্ধার! 👑\n\n"
            "সহীহ বুখারী ২২৯১ নম্বর হাদিসের সমাপ্তি পর্ব (পর্ব ৪ সমাপ্ত)। "
            "কুড়াল দিয়ে কাঠটি চেরা মাত্রই ঝনঝন শব্দে রাশি রাশি স্বর্ণমুদ্রা ও চিঠি ছড়িয়ে পড়ল! কিছুদিন পর "
            "ঋণগ্রহীতা আবারও ১০০০ দিনার নিয়ে হাজির হয়ে বলল—'জাহাজ না পেয়ে আমি কাঠের গুঁড়িতে ভাসিয়ে দিয়েছিলাম।' "
            "তখন ঋণদাতা জানাল—'আল্লাহ তোমার হয়ে ঋণ আগেই পরিশোধ করে দিয়েছেন!'\n\n"
            "মানুষ যখন খাঁটি অন্তরে আল্লাহর ওপর পূর্ণ ভরসা রাখে, তখন স্বয়ং আল্লাহ অসম্ভবকে সম্ভব করে তার পথ খুলে দেন।\n\n"
            "📌 হাদিস সূত্র: সহীহ বুখারী (হাদিস নং ২২৯১)।\n\n"
            "#IslamicStories #SahihBukhari #Part4 #Tawakkul #Reels #Shorts #DailyDosOfIslam #Iman #Allah"
        ),
        "first_comment": "হে আল্লাহ! আমাদের জীবনেও এমন অবিচল তাওয়াক্কুল ও সততা নসিব করুন। আমিন। ❤️\n\n📌 হাদিস রেফারেন্স: সহীহ বুখারী (হাদিস নং ২২৯১)।"
    }
}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_fb_thumbnail_url(fb_reel_id):
    """Retrieves the high-res CDN thumbnail URL from Facebook for the Reel."""
    try:
        page_id = os.getenv("FB_PAGE_ID")
        base_token = os.getenv("FB_ACCESS_TOKEN")
        page_token = get_page_access_token(page_id, base_token)
        url = f"https://graph.facebook.com/v20.0/{fb_reel_id}/thumbnails?access_token={page_token}"
        r = requests.get(url, timeout=15).json()
        for item in r.get("data", []):
            if item.get("is_preferred"):
                return item.get("uri")
        if r.get("data"):
            return r["data"][0].get("uri")
    except Exception as e:
        logger.warning(f"Could not retrieve FB thumbnail CDN URL for Reel {fb_reel_id}: {e}")
    return None

def publish_instagram_part(part_num: int):
    cfg = SCHEDULE_CONFIG[part_num]
    state = load_state()
    
    if state.get(str(part_num), {}).get("status") == "published":
        logger.info(f"Part {part_num} already published to Instagram. Post ID: {state[str(part_num)]['post_id']}")
        return state[str(part_num)]["post_id"]

    v_path = cfg["file"]
    if not os.path.exists(v_path):
        logger.error(f"Video file missing: {v_path}")
        return False

    print("\n" + "=" * 65)
    print(f" 📸 PUBLISHING PART {part_num} TO INSTAGRAM REELS")
    print(f" Video: {v_path}")
    print(f" Thumbnail File: {cfg['thumbnail']}")
    print("=" * 65)

    cover_url = get_fb_thumbnail_url(cfg["fb_reel_id"])
    if cover_url:
        logger.info(f"Found Facebook CDN cover image for Instagram Reel: {cover_url[:70]}...")
    else:
        logger.warning("Facebook CDN cover image not found; proceeding with native video cover.")

    # Upload Reel to Instagram
    post_id = upload_reel_to_instagram(v_path, cfg["caption"], cover_url=cover_url)
    
    if post_id:
        print(f"✅ Part {part_num} Instagram Reel published successfully! Post ID: {post_id}")
        print(f"   Instagram Link: https://www.instagram.com/reel/{post_id}/")

        # Post Pinned First Comment on Instagram
        try:
            base_token = os.getenv("FB_ACCESS_TOKEN")
            if cfg.get("first_comment") and base_token:
                c_resp = requests.post(
                    f"https://graph.facebook.com/v20.0/{post_id}/comments",
                    data={'message': cfg["first_comment"], 'access_token': base_token},
                    timeout=15
                )
                if c_resp.status_code == 200:
                    print("✅ Instagram auto-first comment posted successfully!")
        except Exception as e:
            logger.warning(f"Instagram comment notice: {e}")

        # Update persistent state
        state[str(part_num)] = {
            "status": "published",
            "post_id": post_id,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "cover_url": cover_url
        }
        save_state(state)
        return post_id
    else:
        print(f"❌ Part {part_num} Instagram Reel publish failed.")
        state[str(part_num)] = {
            "status": "failed",
            "failed_at": datetime.now(timezone.utc).isoformat()
        }
        save_state(state)
        return False

def show_status():
    state = load_state()
    now_utc = datetime.now(timezone.utc)
    now_ts = int(now_utc.timestamp())

    print("\n" + "=" * 75)
    print(" 📸 INSTAGRAM 4-DAY REELS SCHEDULE STATUS:")
    print(f" Current UTC: {now_utc.isoformat()} | Current Local: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    for p in range(1, 5):
        cfg = SCHEDULE_CONFIG[p]
        p_state = state.get(str(p), {})
        st = p_state.get("status", "pending")
        target_ts = cfg["target_unix"]
        target_iso = cfg["publish_at_iso"]
        diff_min = (target_ts - now_ts) / 60.0
        
        if st == "published":
            print(f" Part {p}: ✅ PUBLISHED | Post ID: {p_state.get('post_id')} | Link: https://www.instagram.com/reel/{p_state.get('post_id')}/")
        else:
            if diff_min > 0:
                print(f" Part {p}: ⏳ SCHEDULED for {target_iso} (in {diff_min / 60.0:.1f} hours / {int(diff_min)} minutes)")
            else:
                print(f" Part {p}: 🚀 READY TO PUBLISH NOW (was due at {target_iso})")
    print("=" * 75)

def run_scheduler_daemon():
    print("=" * 75, flush=True)
    print(" 🚀 STARTING INSTAGRAM REELS BACKGROUND SCHEDULER DAEMON", flush=True)
    print(" Automatically checks every 30s and publishes scheduled parts to Instagram.", flush=True)
    print("=" * 75, flush=True)
    logger.info("Instagram Reels background scheduler daemon started.")

    while True:
        try:
            state = load_state()
            now_ts = int(datetime.now(timezone.utc).timestamp())
            all_done = True

            for p in range(1, 5):
                cfg = SCHEDULE_CONFIG[p]
                p_state = state.get(str(p), {})
                st = p_state.get("status", "pending")

                if st != "published":
                    all_done = False
                    if now_ts >= cfg["target_unix"]:
                        logger.info(f"Target timestamp reached for Part {p} ({cfg['publish_at_iso']}). Publishing now...")
                        publish_instagram_part(p)

            if all_done:
                print("\n🎉 ALL 4 PARTS HAVE BEEN PUBLISHED TO INSTAGRAM REELS! Daemon shutting down.")
                break

            time.sleep(30)
        except KeyboardInterrupt:
            print("\nScheduler daemon stopped by user.")
            break
        except Exception as e:
            logger.error(f"Scheduler daemon loop error: {e}")
            time.sleep(60)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Instagram Reels 4-Day Scheduler")
    parser.add_argument("--daemon", action="store_true", help="Run in continuous background daemon mode")
    parser.add_argument("--status", action="store_true", help="Check status of scheduled Instagram parts")
    parser.add_argument("--publish", type=int, choices=[1, 2, 3, 4], help="Publish a specific part immediately")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.publish:
        publish_instagram_part(args.publish)
    elif args.daemon:
        run_scheduler_daemon()
    else:
        show_status()
        print("\nTo run the continuous scheduler, use: python schedule_instagram_parts.py --daemon")

if __name__ == "__main__":
    main()
