# -*- coding: utf-8 -*-
"""
End-to-End Generator for Quran Mix (Arabic + Spoken Bangla) Videos.
Features:
- Dual Recitation: Sheikh Mishary Rashid Alafasy + Zayed Iqbal (Islamic Foundation translation).
- 100% Real Live-Motion 60 FPS Footage (3-clip Triplet Rotator, zero still photos).
- Unified Stable Subtitles (Zero mid-verse jumping, perfectly locked layout).
- High-precision audio alignment and broadcast loudness (-18.0 LUFS).
"""

import os
import sys
import json
import random
import subprocess
from app.logger import logger
from app.quran_verse.mix_catalog import (
    MIX_SHORTS_CATALOG,
    get_or_download_mix_audio,
    get_verified_timings,
    format_ass_time,
    highlight_sacred_words
)
from app.quran_verse.triplet_rotator import get_next_video_scenes
from app.quran_verse.renderer import ensure_local_clip

STATE_FILE = os.path.abspath("data/quran_mix_state.json")

def load_or_init_mix_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load mix state: {e}")

    default_plan = list(MIX_SHORTS_CATALOG.keys())
    random.shuffle(default_plan)
    state = {
        "cycle": 1,
        "current_index": 0,
        "plan": default_plan,
        "history": []
    }
    save_mix_state(state)
    return state

def save_mix_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_next_mix_surah(forced_surah: int = None) -> int:
    if forced_surah and forced_surah in MIX_SHORTS_CATALOG:
        return forced_surah

    state = load_or_init_mix_state()
    plan = state.get("plan", [])
    idx = state.get("current_index", 0)

    if idx >= len(plan):
        state["cycle"] = state.get("cycle", 1) + 1
        state["current_index"] = 0
        random.shuffle(plan)
        state["plan"] = plan
        idx = 0

    surah = plan[idx]
    state["current_index"] = idx + 1
    state.setdefault("history", []).append({
        "surah": surah,
        "timestamp": os.getenv("GITHUB_RUN_ID", "local")
    })
    save_mix_state(state)
    logger.info(f"Selected Surah {surah} for Quran Mix Slot (Index {idx+1}/{len(plan)}, Cycle {state.get('cycle', 1)})")
    return surah

def build_ass_subtitles(surah: int, timings: list[dict], total_dur: float, ass_out_path: str):
    meta = MIX_SHORTS_CATALOG.get(surah, {})
    title_bn = meta.get("title_bn", f"সূরা {surah}")

    header = f"""[Script Info]
Title: Quran Mix Subtitles - {title_bn}
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ArabicStable,Amiri,64,&H002BD5FF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3.6,2.0,5,60,60,0,1
Style: BanglaStable,Kalpurush,58,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3.4,2.0,5,70,70,0,1
Style: TopBadge,Kalpurush,42,&H0015CCFA,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3.0,1.5,5,50,50,0,1
Style: SubBadge,Kalpurush,30,&H00E0E0E0,&H000000FF,&H00000000,&H80000000,0,1,0,0,100,100,0,0,1,2.0,1.0,5,50,50,0,1
Style: EnglishSmall,Arial,28,&H00C0C0C0,&H000000FF,&H00000000,&H80000000,0,1,0,0,100,100,0,0,1,2.0,1.0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(ass_out_path, "w", encoding="utf-8") as f:
        f.write(header)
        # Static Badges
        f.write(f"Dialogue: 0,0:00:00.00,{format_ass_time(total_dur)},TopBadge,,0,0,0,,{{\\pos(540,240)}}[ {title_bn} • তিলাওয়াত ও অনুবাদ ]\\N\n")
        f.write(f"Dialogue: 0,0:00:00.00,{format_ass_time(total_dur)},SubBadge,,0,0,0,,{{\\pos(540,295)}}ক্বারী: মিশারি রশিদ • বাচনিক: জায়েদ ইকবাল (ইফাবা)\\N\n")

        for item in timings:
            st = item["full_start"]
            en = item["full_end"]
            ar_text = item.get("ar", "")
            bn_fmt = highlight_sacred_words(item.get("bn", ""))
            en_text = item.get("en", "")

            # Unified Stable Card: Arabic at \pos(540,880), Bangla at \pos(540,1020)
            # ZERO displacement or resizing when voice changes
            f.write(f"Dialogue: 0,{format_ass_time(st)},{format_ass_time(en)},ArabicStable,,0,0,0,,{{\\pos(540,880)}}{ar_text}\\N\n")
            f.write(f"Dialogue: 0,{format_ass_time(st)},{format_ass_time(en)},BanglaStable,,0,0,0,,{{\\pos(540,1020)}}{bn_fmt}\\N\n")
            if en_text:
                f.write(f"Dialogue: 0,{format_ass_time(st)},{format_ass_time(en)},EnglishSmall,,0,0,0,,{{\\pos(540,1650)}}\"{en_text}\"\\N\n")

def assemble_live_motion_track(total_dur: float, temp_dir: str) -> str:
    """Assembles a 60 FPS live-motion background video cycling 3 Halal clips."""
    os.makedirs(temp_dir, exist_ok=True)
    out_visual = os.path.join(temp_dir, "master_visual.mp4")

    # Get 3 diverse clips from Triplet Rotator
    triplet_info = get_next_video_scenes(advance=True)
    raw_clips = triplet_info.get("clips", [])
    
    clips_dir = os.path.join(temp_dir, "clips")
    local_clips = []
    for c in raw_clips:
        try:
            local_clips.append(ensure_local_clip(c, clips_dir))
        except Exception as e:
            logger.warning(f"Could not load clip: {e}")

    # Fallback to authentic nature B-rolls if needed
    if len(local_clips) < 3:
        fallbacks = [
            os.path.abspath("app/assets/broll/ocean_720.mp4"),
            os.path.abspath("app/assets/broll/clouds_720.mp4"),
            os.path.abspath("app/assets/broll/desert_720.mp4")
        ]
        for fb in fallbacks:
            if os.path.exists(fb) and fb not in local_clips:
                local_clips.append(fb)

    # 15s to 20s scenes in round robin
    scene_dur = 16.0
    num_scenes = max(2, int(total_dur / scene_dur) + 1)
    dur_per_scene = total_dur / num_scenes

    scene_files = []
    for i in range(num_scenes):
        chosen_clip = local_clips[i % len(local_clips)]
        scene_out = os.path.join(temp_dir, f"scene_{i:02d}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", chosen_clip,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=60",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-t", f"{dur_per_scene:.2f}",
            "-an", "-pix_fmt", "yuv420p",
            scene_out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        scene_files.append(scene_out)

    concat_txt = os.path.join(temp_dir, "scenes_concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for s in scene_files:
            safe_s = os.path.basename(s)
            f.write(f"file '{safe_s}'\n")

    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-c", "copy", out_visual
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_visual

def generate_quran_mix_video(surah: int = None, output_dir: str = "data/output") -> dict:
    """
    Renders end-to-end Quran Mix video under 85s with matching audio and subtitles.
    """
    chosen_surah = get_next_mix_surah(forced_surah=surah)
    meta = MIX_SHORTS_CATALOG[chosen_surah]
    title_bn = meta["title_bn"]
    title_en = meta["title_en"]

    logger.info(f"=== GENERATING QURAN MIX VIDEO: {title_bn} ({title_en}) ===")

    # 1. Audio
    raw_audio_path, raw_dur = get_or_download_mix_audio(chosen_surah)
    total_dur = min(raw_dur, meta.get("duration", raw_dur))

    # 2. Timings & Subtitles
    timings = get_verified_timings(chosen_surah, raw_audio_path)
    
    temp_dir = os.path.abspath(f"data/temp/quran_mix_render_{chosen_surah}")
    os.makedirs(temp_dir, exist_ok=True)
    ass_path = os.path.join(temp_dir, "subtitles.ass")
    build_ass_subtitles(chosen_surah, timings, total_dur, ass_path)

    # 3. Visual Track (100% Live Motion, 60 FPS)
    master_visual = assemble_live_motion_track(total_dur, temp_dir)

    # 4. Render Final Video with Broadcast Audio (-18.0 LUFS)
    os.makedirs(output_dir, exist_ok=True)
    out_video_name = f"Quran_Mix_Surah_{chosen_surah}_{title_en.replace(' ', '_')}.mp4"
    final_output_path = os.path.join(output_dir, out_video_name)

    grad_path = os.path.abspath("app/assets/grad_center_bottom.png")
    safe_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")

    logger.info(f"Encoding final video with broadcast audio and ASS subtitles: {final_output_path}...")
    cmd_render = [
        "ffmpeg", "-y",
        "-i", master_visual,
        "-i", grad_path,
        "-i", raw_audio_path,
        "-filter_complex", (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=60[bg];"
            f"[1:v]scale=1080:1920[grad];"
            f"[bg][grad]overlay=0:0[graded];"
            f"[graded]ass='{safe_ass_path}':fontsdir=app/assets/fonts[outv];"
            f"[2:a]loudnorm=I=-18.0:TP=-2.0:LRA=11.0[outa]"
        ),
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{total_dur:.2f}",
        final_output_path
    ]
    subprocess.run(cmd_render, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    logger.info(f"Video rendered successfully: {final_output_path} ({os.path.getsize(final_output_path)/(1024*1024):.2f} MB)")

    # 5. Extract Thumbnail
    thumb_path = os.path.join(output_dir, f"Quran_Mix_Surah_{chosen_surah}_thumb.jpg")
    try:
        sample_t = min(3.0, total_dur - 1.0)
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(sample_t), "-i", final_output_path,
            "-vframes", "1", "-q:v", "2", thumb_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        logger.warning(f"Thumbnail extraction notice: {e}")

    # 6. Metadata
    metadata = {
        "title": f"{title_bn} (তিলাওয়াত ও বাংলা অনুবাদ) | {title_en} | Sheikh Mishary Alafasy #Shorts",
        "description": (
            f"{title_bn} ({title_en}) - আরবি তিলাওয়াত ও প্রাঞ্জল বাংলা বাচিক অনুবাদ।\n\n"
            f"আরবি ক্বারী: শায়খ মিশারি রশিদ আল-আফাসি (Sheikh Mishary Rashid Alafasy)\n"
            f"বাংলা বাচনিক কণ্ঠ: জায়েদ ইকবাল (Zayed Iqbal)\n"
            f"অনুবাদ: ইসলামিক ফাউন্ডেশন বাংলাদেশ (Islamic Foundation Bangladesh)\n\n"
            f"#Quran #QuranBangla #{title_en.replace(' ', '')} #IslamicShorts #MisharyAlafasy #Bangladesh"
        ),
        "tags": ["Quran", "Quran Bangla", title_en, title_bn, "Mishary Alafasy", "Islamic Foundation Bangladesh", "Shorts", "Reels"],
        "pinned_comment": f"সুবহানাল্লাহ! {title_bn}-এর মধুর তিলাওয়াত ও মর্মস্পর্শী বাংলা অর্থ হৃদয় ছুঁয়ে যায়। চ্যানেলটি সাবস্ক্রাইব করে দ্বীনের দাওয়াত ছড়িয়ে দিন।"
    }

    return {
        "video_path": final_output_path,
        "thumbnail_path": thumb_path if os.path.exists(thumb_path) else None,
        "metadata": metadata,
        "surah": chosen_surah,
        "duration": total_dur
    }
