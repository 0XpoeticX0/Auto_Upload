# -*- coding: utf-8 -*-
"""
Automated Incoming Audio Processor & Storytelling Video Creator
1. Detects newly dropped audio files in incoming_audio/
2. Uses Gemini to analyze the theme and design multi-scene visual prompts
3. Enforces STRICT ZERO LIVING BEINGS policy (checked with Gemini Vision Guardian)
4. Renders smooth 9:16 cinematic video with Ken Burns pan/zoom animations
5. Generates high-CTR metadata & saves video to incoming_audio/rendered_videos/
6. Awaits user review and approval before publishing to YouTube, Facebook, and TikTok
"""

import os
import sys
import time
import json
import glob
import math
import shutil
import argparse
import subprocess
from app.logger import logger
from app.llm.provider import extract_json
from app.quality.vision_guardian import generate_verified_human_free_background, get_certified_safe_fallback
from app.upload.youtube import upload_to_youtube
from app.upload.facebook import upload_to_facebook
from app.upload.tiktok import upload_to_tiktok
from app.audio_registry import (
    is_audio_used,
    mark_audio_as_used,
    get_all_fresh_audios,
    get_next_fresh_audio
)

INCOMING_AUDIO_DIR = os.path.abspath("incoming_audio")
RENDERED_DIR = os.path.join(INCOMING_AUDIO_DIR, "rendered_videos")
PROCESSED_DIR = os.path.join(INCOMING_AUDIO_DIR, "processed")

os.makedirs(INCOMING_AUDIO_DIR, exist_ok=True)
os.makedirs(RENDERED_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

def get_audio_duration(audio_path: str) -> float:
    """Returns duration of audio file in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not get audio duration with ffprobe ({e}); defaulting to 60s")
        return 60.0

def plan_scenes_with_gemini(topic_title: str, total_duration: float) -> list:
    """
    Uses Google Gemini to plan cinematic visual scenes matching the audio's emotional theme.
    Calculates number of scenes (each ~12-16s) and specifies smooth motion type.
    """
    logger.info(f"Directing Gemini to plan visual scenes for '{topic_title}' ({total_duration:.1f}s)...")
    
    # Target 12 to 16 seconds per scene
    scene_target_sec = 14.0
    num_scenes = max(3, min(12, int(round(total_duration / scene_target_sec))))
    actual_scene_duration = total_duration / num_scenes
    
    system_prompt = f"""You are a master cinematic art director for vertical 9:16 Islamic storytelling videos.
Your task is to plan {num_scenes} sequential, deeply atmospheric visual scenes for a video based on an emotional Islamic audio.

CRITICAL RULES (SHARIAH COMPLIANT):
1. ABSOLUTELY NO LIVING BEINGS. NO humans, NO faces, NO prophets, NO companions, NO mother/father figures, NO silhouettes, NO animals, NO birds, NO living creatures.
2. Atmospheric & Symbolic visual storytelling only:
   - Ancient prayer corners with soft crimson rugs and glowing brass oil lamps
   - Majestic 7th-century Moorish and Madinah stone archways with golden sunbeams
   - Quiet night sanctuary with starlight through celestial dome
   - Serene morning date palm oasis with gentle dew and crystal clear flowing stream
   - Ancient handwritten Arabic manuscripts on carved dark cedar wood tables
   - Warm golden rain falling softly on polished courtyard marble under lanterns
3. Each scene MUST specify 'motion_type': one of ['zoom_in', 'zoom_out', 'pan_up', 'pan_down'].
4. Ensure sequential emotional progression (e.g. grief/remorse -> quiet supplication -> divine comfort -> dawn of forgiveness & peace).

Output ONLY valid JSON:
{{
    "theme": "Brief English theme description",
    "scenes": [
        {{
            "scene_number": 1,
            "title_bn": "দৃশ্য ১ এর বাংলা বিবরণ",
            "visual_prompt": "vertical 9:16, majestic grand mosque interior at twilight, ornate islamic archways, glowing brass lantern, warm golden god rays, empty of people, no living beings, 8k octane render",
            "motion_type": "zoom_in"
        }}
    ]
}}"""

    user_prompt = f"Audio Title / Topic: {topic_title}\nTotal Video Duration: {total_duration:.1f} seconds\nRequired Number of Scenes: {num_scenes}\nPlan breathtaking, highly atmospheric scenes."

    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=2500)
        scenes = data.get("scenes", [])
        if scenes and len(scenes) >= 2:
            # Assign computed duration
            for sc in scenes:
                sc["duration"] = actual_scene_duration
            logger.info(f"Gemini successfully planned {len(scenes)} visual scenes.")
            return scenes
    except Exception as e:
        logger.warning(f"Failed to plan scenes via Gemini: {e}")

    # Fallback scenes if Gemini json fails
    logger.info("Using curated fallback Islamic scenes...")
    fallback_prompts = [
        ("vertical 9:16, majestic grand mosque interior at twilight, ornate islamic archways, glowing brass lanterns, warm golden light rays, dark emerald and gold palette, empty of people, no living beings, 8k render", "zoom_in"),
        ("vertical 9:16, intimate ancient prayer corner with handwoven crimson rug, glowing brass oil lamp on ancient stone, peaceful contemplation, deep moody shadows, no people, no living beings, 8k", "zoom_out"),
        ("vertical 9:16, celestial golden divine light beam showering down into an ancient stone sanctuary dome, soft golden dust motes, peaceful awe, no living beings, 8k render", "pan_up"),
        ("vertical 9:16, open carved cedar wood archway looking out into a tranquil date palm oasis at sunrise, gentle golden morning glow, clear sky, serene, no people, no living beings, 8k", "pan_down"),
        ("vertical 9:16, ancient holy manuscript on carved dark mahogany lectern, warm candlelight, deep amber and bronze atmospheric glow, cinematic depth of field, no people, no living beings, 8k", "zoom_in"),
        ("vertical 9:16, vast calm desert oasis under glowing crescent moon, starry night sky, ancient stone fountain reflection, serene peace, no people, no living beings, 8k", "zoom_out"),
    ]
    scenes = []
    for i in range(num_scenes):
        prompt, motion = fallback_prompts[i % len(fallback_prompts)]
        scenes.append({
            "scene_number": i + 1,
            "title_bn": f"দৃশ্য {i+1}",
            "visual_prompt": prompt,
            "motion_type": motion,
            "duration": actual_scene_duration
        })
    return scenes

def render_scene_clip(image_path: str, duration: float, motion_type: str, output_path: str) -> bool:
    """
    Renders an image into a 1080x1920 30fps video clip with smooth Ken Burns animation.
    """
    frames = int(math.ceil(duration * FPS))
    
    if motion_type == "zoom_in":
        vf = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},zoompan=z='min(zoom+0.0010,1.20)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}"
    elif motion_type == "zoom_out":
        vf = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},zoompan=z='if(lte(zoom,1.0),1.18,max(1.001,zoom-0.0010))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}"
    elif motion_type == "pan_up":
        vf = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},zoompan=z='1.12':d={frames}:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),ih-ih/zoom,max(0,y-0.8))':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}"
    else:  # pan_down
        vf = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},zoompan=z='1.12':d={frames}:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min(ih-ih/zoom,y+0.8))':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={FPS}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-vf", vf,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 10000
    except Exception as e:
        logger.error(f"Failed to render scene clip ({output_path}): {e}")
        return False

def generate_video_metadata(topic_title: str, audio_path: str) -> dict:
    """Uses Gemini to generate high-CTR metadata, authentic Hadith caption, and tags."""
    system_prompt = """You are a master Islamic content strategist for YouTube Shorts, Facebook Reels, and Instagram Reels.
Generate high-converting, deeply respectful, authentic metadata for an emotional Islamic audio/story.

MANDATORY RULES:
1. Title: Catchy, curiosity-driven (under 60 chars) with relevant emojis and #Shorts in Bengali.
2. Description: Hook in first line, emotional Islamic context, authentic Quran/Hadith reference (e.g. Surah Al-Isra 23-24 or Sahih Bukhari / Muslim for parents), followed by authentic Dawah CTA.
3. Authentic CTA: Use 'রাসূলুল্লাহ (ﷺ) বলেছেন: যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়। [সহীহ মুসলিম: ১৮৯৩] 🌿'
4. Pinned Comment: An emotional question or prayer reminder for parents/forgiveness.
5. Tags: 8-10 relevant tags.

Output ONLY valid JSON:
{
    "youtube_title": "মা-বাবার জন্য এই ১টি দোয়া কখনো ভুলবেন না 🥺 #Shorts",
    "facebook_title": "মায়ের ঋণ কখনো শোধ করা যায় না 🥺 অশ্রুসজল দোয়া",
    "description": "ভিডিওর ক্যাপশন ও কোরআন-হাদিসের সুন্দর নসিহত...",
    "pinned_comment": "আল্লাহ আমাদের সবার মা-বাবাকে নেক হায়াত ও জান্নাতুল ফিরদাউস নসিব করুন। কমেন্টে বলুন 'আমিন' 🤲",
    "tags": ["Shorts", "Maa", "IslamicReminder", "Dua", "ParentsInIslam", "BanglaWaz", "ReelsViral", "সহীহ_হাদিস"]
}"""

    user_prompt = f"Audio Title / Topic: {topic_title}\nGenerate authentic metadata in Bengali."
    try:
        data = extract_json(system_prompt, user_prompt, max_tokens=1000)
        if data and isinstance(data, dict):
            return data
    except Exception as e:
        logger.warning(f"Could not generate metadata with Gemini: {e}")

    return {
        "youtube_title": f"{topic_title[:55]} 🥺 #Shorts",
        "facebook_title": f"{topic_title[:60]}",
        "description": f"✨ {topic_title} ✨\n\nরাসূলুল্লাহ (ﷺ) বলেছেন: ‘যে ব্যক্তি কোনো ভালো কাজের পথ দেখায়, সে তার সমপরিমাণ সওয়াব পায়।’ [সহীহ মুসলিম: ১৮৯৩] 🌿\n\n#Shorts #IslamicReminder #Dua",
        "pinned_comment": "দোয়াটি নিজে আমল করুন এবং বন্ধুদের মাঝে শেয়ার করে সওয়াবের অংশীদার হোন 🌿",
        "tags": ["Shorts", "IslamicReminder", "Dua", "BanglaWaz", "সহীহ_হাদিস"]
    }

def process_audio_file(audio_path: str) -> dict:
    """
    Main workflow:
    1. Read audio duration & topic
    2. Plan scenes via Gemini
    3. Generate human-free images via Vision Guardian
    4. Render smooth Ken Burns motion clips
    5. Concat and mux with original audio
    6. Generate metadata
    7. HOLD for approval (does NOT upload)
    """
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    
    # 0. STRICT DEDUPLICATION: NEVER USE THE SAME AUDIO EVER AGAIN
    used, details = is_audio_used(audio_path)
    if used:
        logger.warning(f"🚫 [DUPLICATE BLOCKED]: Audio '{base_name}' was already used previously ({details.get('processed_at')}). Skipping.")
        print(f"\n[BLOCKED] Audio '{base_name}' was ALREADY used previously! Skipping to ensure zero duplicate content.\n")
        return None

    logger.info(f"==================================================")
    logger.info(f"PROCESSING INCOMING AUDIO: {base_name}")
    logger.info(f"==================================================")

    duration = get_audio_duration(audio_path)
    logger.info(f"Audio Duration: {duration:.2f}s ({duration/60:.1f} mins)")

    timestamp = int(time.time())
    temp_dir = os.path.join("data", "temp", f"audio_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)

    # 1. Plan scenes with Gemini
    scenes = plan_scenes_with_gemini(base_name, duration)
    logger.info(f"Total scenes to render: {len(scenes)}")

    # 2. Generate zero-human images & render clips
    rendered_clips = []
    for idx, sc in enumerate(scenes, 1):
        logger.info(f"--- Generating Scene {idx}/{len(scenes)}: {sc.get('title_bn', '')} ---")
        img_path = os.path.join(temp_dir, f"scene_{idx}.jpg")
        clip_path = os.path.join(temp_dir, f"clip_{idx}.mp4")

        # Visual generation through Vision Guardian (Guaranteed 0 living beings)
        prompt = sc.get("visual_prompt", "")
        success = generate_verified_human_free_background(prompt, img_path, max_checks=2)
        if not success or not os.path.exists(img_path):
            logger.warning(f"Using certified fallback for scene {idx}")
            get_certified_safe_fallback(img_path)

        # Render animated clip
        sc_duration = sc.get("duration", duration / len(scenes))
        motion = sc.get("motion_type", "zoom_in")
        logger.info(f"Rendering animated clip {idx} ({motion}, {sc_duration:.1f}s)...")
        clip_ok = render_scene_clip(img_path, sc_duration, motion, clip_path)
        if clip_ok:
            rendered_clips.append(clip_path)
        else:
            logger.error(f"Failed to render clip for scene {idx}")

    if not rendered_clips:
        logger.error("No scene clips rendered successfully!")
        return None

    # 3. Concatenate video clips
    concat_txt = os.path.join(temp_dir, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in rendered_clips:
            f.write(f"file '{os.path.abspath(c).replace(chr(92), '/')}'\n")

    # 4. Final Mux with Original Audio
    clean_title_slug = "".join([c if c.isalnum() else "_" for c in base_name])[:40]
    final_filename = f"{clean_title_slug}_{timestamp}_cinematic_9_16.mp4"
    final_video_path = os.path.join(RENDERED_DIR, final_filename)

    logger.info(f"Muxing smooth video with original audio -> {final_video_path}")
    mux_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        final_video_path
    ]
    subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    if not os.path.exists(final_video_path):
        logger.error("Final video file not created!")
        return None

    # 5. Generate high-CTR metadata
    metadata = generate_video_metadata(base_name, audio_path)
    metadata["source_audio"] = audio_path
    metadata["video_path"] = final_video_path
    metadata["duration_seconds"] = duration
    metadata["rendered_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    metadata["status"] = "PENDING_USER_APPROVAL"

    metadata_file = os.path.splitext(final_video_path)[0] + "_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved review metadata to: {metadata_file}")
    logger.info(f"=== COMPLETED VIDEO (AWAITING APPROVAL): {final_video_path} ===")

    # Permanently register audio so it is NEVER reused ever again
    mark_audio_as_used(audio_path, final_video_path, metadata)

    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    return {
        "video_path": final_video_path,
        "metadata_path": metadata_file,
        "metadata": metadata,
        "audio_path": audio_path
    }

def approve_and_upload(video_path: str, metadata_path: str = None) -> bool:
    """
    Called ONLY when the user approves the video.
    Uploads to YouTube, Facebook, Instagram, and TikTok, then archives original audio.
    """
    logger.info(f"=== EXECUTING APPROVED UPLOAD FOR: {os.path.basename(video_path)} ===")
    
    if not os.path.exists(video_path):
        logger.error(f"Video not found: {video_path}")
        return False

    metadata = {}
    if not metadata_path:
        metadata_path = os.path.splitext(video_path)[0] + "_metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    # 1. YouTube Shorts Upload
    try:
        logger.info("Uploading to YouTube Shorts...")
        yt_ok = upload_to_youtube(video_path, metadata)
        logger.info(f"YouTube Upload Status: {yt_ok}")
    except Exception as e:
        logger.warning(f"YouTube upload error: {e}")

    # 2. Facebook & Instagram Reels Upload
    try:
        logger.info("Uploading to Facebook & Instagram Reels...")
        fb_ok = upload_to_facebook(video_path, metadata, video_type="reel")
        logger.info(f"Facebook / Instagram Upload Status: {fb_ok}")
    except Exception as e:
        logger.warning(f"Facebook upload error: {e}")

    # 3. TikTok Upload
    try:
        logger.info("Uploading to TikTok...")
        tt_res = upload_to_tiktok(
            video_path,
            caption=metadata.get("youtube_title", os.path.basename(video_path)),
            tags=metadata.get("tags", [])
        )
        logger.info(f"TikTok Upload Status: {tt_res.get('status')}")
    except Exception as e:
        logger.warning(f"TikTok upload error: {e}")

    # 4. Archive Source Audio
    source_audio = metadata.get("source_audio")
    if source_audio and os.path.exists(source_audio):
        dest_audio = os.path.join(PROCESSED_DIR, os.path.basename(source_audio))
        try:
            if os.path.exists(dest_audio):
                os.remove(dest_audio)
            shutil.move(source_audio, dest_audio)
            logger.info(f"Archived source audio to: {dest_audio}")
        except Exception as e:
            logger.warning(f"Could not archive audio: {e}")

    # Update metadata status
    metadata["status"] = "PUBLISHED"
    metadata["published_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info("=== UPLOAD & ARCHIVAL COMPLETE ===")
    return True

def list_pending_reviews() -> list:
    """Lists all rendered videos awaiting user approval."""
    json_files = glob.glob(os.path.join(RENDERED_DIR, "*_metadata.json"))
    pending = []
    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("status") == "PENDING_USER_APPROVAL":
                pending.append(data)
        except Exception:
            pass
    return pending

def approve_all_pending():
    """Approves and uploads all videos currently awaiting approval."""
    pending = list_pending_reviews()
    if not pending:
        logger.info("No pending videos to approve.")
        return
    logger.info(f"Found {len(pending)} pending video(s) to approve.")
    for item in pending:
        v_path = item.get("video_path")
        if v_path and os.path.exists(v_path):
            approve_and_upload(v_path)

def scan_and_process_incoming():
    """Scans incoming_audio/ for audio files that have NEVER been used before."""
    fresh_audios = get_all_fresh_audios()
    if not fresh_audios:
        logger.info(f"No fresh un-used audio files found in {INCOMING_AUDIO_DIR}")
        print(f"\n[INFO] No fresh audio files found in incoming_audio/. All present files have ALREADY been used!\n")
        return []

    logger.info(f"Found {len(fresh_audios)} fresh un-used audio file(s) in {INCOMING_AUDIO_DIR}")
    results = []
    for f in fresh_audios:
        res = process_audio_file(f)
        if res:
            results.append(res)
    return results

def process_single_fresh_audio():
    """Picks the next audio that has NEVER been used before and processes it."""
    fresh = get_next_fresh_audio()
    if not fresh:
        logger.info(f"No fresh un-used audio found in {INCOMING_AUDIO_DIR}")
        print(f"\n[INFO] No fresh audio available. All audio in incoming_audio/ has already been used previously!\n")
        return None
    logger.info(f"Selected fresh un-used audio: {os.path.basename(fresh)}")
    return process_audio_file(fresh)

def watch_incoming_audio(poll_interval: int = 10):
    """
    Continuously monitors incoming_audio/ for newly downloaded audio files (Ctrl+C to stop).
    Whenever fresh audio is detected, it processes it sequentially and ignores already used audios.
    """
    logger.info(f"🎧 Watching '{INCOMING_AUDIO_DIR}' for new audio downloads (every {poll_interval}s)...")
    logger.info("Drop ANY fresh audio (.mp3, .wav, .m4a) here at any time. It will auto-render and await your approval.")
    while True:
        try:
            scan_and_process_incoming()
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("Stopped audio watcher.")
            break
        except Exception as e:
            logger.error(f"Audio watcher error: {e}")
            time.sleep(poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process incoming audio into cinematic 9:16 Islamic story videos")
    parser.add_argument("--file", type=str, help="Process a specific audio file")
    parser.add_argument("--fresh", action="store_true", help="Pick and process the next audio that has NEVER been used before")
    parser.add_argument("--approve", type=str, help="Approve and upload a rendered video file")
    parser.add_argument("--approve-all", action="store_true", help="Approve and upload all pending videos")
    parser.add_argument("--list-pending", action="store_true", help="List all rendered videos waiting for approval")
    parser.add_argument("--watch", action="store_true", help="Continuously monitor incoming_audio/ folder for new audios")
    parser.add_argument("--scan", action="store_true", help="Scan incoming_audio/ and process all new fresh audios")
    args = parser.parse_args()

    if args.approve_all:
        approve_all_pending()
    elif args.approve:
        approve_and_upload(args.approve)
    elif args.list_pending:
        items = list_pending_reviews()
        print(f"\n--- PENDING VIDEOS FOR APPROVAL ({len(items)}) ---")
        for i, it in enumerate(items, 1):
            print(f"{i}. Video: {it.get('video_path')}")
            print(f"   Title: {it.get('youtube_title')}")
            print(f"   Duration: {it.get('duration_seconds', 0):.1f}s | Rendered: {it.get('rendered_at')}\n")
    elif args.watch:
        watch_incoming_audio()
    elif args.fresh:
        process_single_fresh_audio()
    elif args.file:
        process_audio_file(args.file)
    else:
        scan_and_process_incoming()
