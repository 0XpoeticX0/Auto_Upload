# -*- coding: utf-8 -*-
"""
Audio Manager for Quran Recitations.
Downloads authentic per-Ayah MP3s from EveryAyah, concatenates them seamlessly,
tracks exact per-Ayah start/end timings, and applies studio vocal mastering.
"""

import os
import json
import urllib.request
import subprocess
from app.logger import logger
from app.quran_verse.quran_data import RECITERS_CONFIG

AUDIO_CACHE_DIR = os.path.abspath("data/quran_audio/cache")

def get_ayah_audio_path(reciter_folder: str, surah: int, ayah: int) -> tuple[str, float]:
    """
    Downloads or retrieves cached audio file for a single Ayah,
    and returns (file_path, duration_seconds).
    """
    os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
    filename = f"{reciter_folder}_{surah:03d}{ayah:03d}.mp3"
    local_path = os.path.join(AUDIO_CACHE_DIR, filename)

    if not os.path.exists(local_path) or os.path.getsize(local_path) < 1000:
        url = f"https://everyayah.com/data/{reciter_folder}/{surah:03d}{ayah:03d}.mp3"
        logger.info(f"Downloading recitation for {surah}:{ayah} from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            with open(local_path, "wb") as f:
                f.write(data)

    # Probe duration using ffprobe
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        local_path
    ]
    try:
        dur = float(subprocess.check_output(cmd).decode().strip())
    except Exception as e:
        logger.warning(f"Failed to probe duration for {local_path}: {e}")
        dur = 5.0

    return local_path, dur

def prepare_recitation_audio(verse_data: dict, output_dir: str = "data/temp/quran_verse_audio") -> dict:
    """
    Downloads all Ayahs in the verse range, concatenates them if multiple,
    applies professional studio vocal mastering, and returns:
    {
        "audio_path": mastered_file_path,
        "total_duration": float,
        "ayah_timings": [
            {"ayah": int, "start": float, "end": float, "duration": float, "arabic": str, "bengali": str}
        ]
    }
    """
    os.makedirs(output_dir, exist_ok=True)
    reciter_id = verse_data.get("reciter_id", "alafasy")
    reciter = RECITERS_CONFIG.get(reciter_id, RECITERS_CONFIG["alafasy"])
    reciter_folder = reciter["folder"]

    surah = verse_data["surah"]
    start = verse_data["ayah_start"]
    end = verse_data["ayah_end"]

    ayah_files = []
    ayah_timings = []
    current_time = 0.0

    verses_lookup = {v["ayah_number"]: v for v in verse_data.get("verses", [])}

    for ayah_num in range(start, end + 1):
        fpath, dur = get_ayah_audio_path(reciter_folder, surah, ayah_num)
        ayah_files.append(fpath)

        v_info = verses_lookup.get(ayah_num, {})
        timing_entry = {
            "ayah": ayah_num,
            "start": round(current_time, 2),
            "end": round(current_time + dur, 2),
            "duration": round(dur, 2),
            "arabic": v_info.get("arabic", ""),
            "bengali": v_info.get("bengali", ""),
            "english": v_info.get("english", "")
        }
        ayah_timings.append(timing_entry)
        current_time += dur

    total_dur = current_time
    logger.info(f"Total recitation duration for {surah}:{start}-{end} by {reciter['name_bn']}: {total_dur:.1f}s")

    if total_dur > 90.0:
        logger.warning(f"Passage duration ({total_dur:.1f}s) exceeds 90s limit!")

    # Merge audio if multiple ayahs
    raw_merged = os.path.join(output_dir, f"raw_{surah}_{start}_{end}_{reciter_id}.mp3")
    if len(ayah_files) == 1:
        import shutil
        shutil.copy2(ayah_files[0], raw_merged)
    else:
        concat_txt = os.path.join(output_dir, "concat_list.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in ayah_files:
                # Escape backslashes for ffmpeg concat
                safe_p = p.replace("\\", "/")
                f.write(f"file '{safe_p}'\n")

        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_txt, "-c", "copy", raw_merged
        ]
        subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Apply Studio Vocal Mastering:
    # 1. Gentle highpass (removes sub-bass mic rumble)
    # 2. Loudnorm (EBU R128 standard: loud, crisp, clear on mobile phones)
    mastered_path = os.path.join(output_dir, f"mastered_{surah}_{start}_{end}_{reciter_id}.mp3")
    cmd_master = [
        "ffmpeg", "-y", "-i", raw_merged,
        "-af", "highpass=f=60,loudnorm=I=-16:TP=-1.5:LRA=11",
        "-b:a", "192k",
        mastered_path
    ]
    subprocess.run(cmd_master, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    return {
        "audio_path": mastered_path,
        "total_duration": total_dur,
        "ayah_timings": ayah_timings,
        "reciter": reciter
    }
