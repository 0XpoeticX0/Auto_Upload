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

_DF_MODEL = None
_DF_STATE = None

def get_deepfilter_model():
    """Initializes and caches the DeepFilterNet3 model for lightning-fast neural enhancement."""
    global _DF_MODEL, _DF_STATE
    if _DF_MODEL is None:
        try:
            from df.enhance import init_df
            _DF_MODEL, _DF_STATE, _ = init_df()
            logger.info("DeepFilterNet3 neural voice enhancement model initialized successfully.")
        except Exception as e:
            logger.warning(f"DeepFilterNet3 initialization failed, falling back to standard audio DSP: {e}")
            _DF_MODEL = False
    return _DF_MODEL, _DF_STATE

def enhance_with_resemble_ai(input_path: str, output_wav: str) -> bool:
    """
    Applies Resemble Enhance (Full Neural Studio AI) via Cloud Gradio Client:
    - Stage 1: Deep acoustic de-reverberation (removes cavernous mosque echo).
    - Stage 2: CFM (Conditional Flow Matching) ODE speech restoration (reconstructs lost high harmonics).
    Returns True if successful, False otherwise.
    """
    try:
        from gradio_client import Client, handle_file
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

        # Try ZeroGPU A10G high-speed space first, then standard CPU space
        spaces = [
            ("multimodalart/resemble-enhance-zerogpu", "/predict", 64),
            ("ulimilani/resemble-enhance", "/partial", 32)
        ]

        for space_name, api_endpoint, nfe in spaces:
            try:
                logger.info(f"Attempting Resemble Enhance on space: {space_name}...")
                client = Client(space_name, token=token) if token else Client(space_name)
                result = client.predict(
                    path=handle_file(input_path),
                    solver="Midpoint",
                    nfe=nfe,
                    tau=0.5,
                    denoising=True,
                    api_name=api_endpoint
                )
                enhanced_file = result[1] if isinstance(result, (list, tuple)) else result
                if enhanced_file and os.path.exists(enhanced_file):
                    import shutil
                    shutil.copy2(enhanced_file, output_wav)
                    logger.info(f"Resemble Enhance studio speech restoration succeeded via {space_name}!")
                    return True
            except Exception as space_err:
                logger.warning(f"Resemble Enhance attempt on {space_name} notice: {space_err}")
                continue
    except Exception as e:
        logger.warning(f"Resemble Enhance client unavailable: {e}")
    return False

def apply_neural_studio_enhancement(input_path: str, output_path: str) -> str:
    """
    Applies Permanent Studio Vocal Mastering:
    1. Primary: Resemble Enhance (Full Neural Studio AI) with De-Reverb + Harmonics synthesis.
    2. Fallback: DeepFilterNet3 local neural de-reverberation.
    3. Broadcast Master: Clean, comfortable -18 LUFS normalization with zero harshness.
    """
    temp_resemble_wav = input_path + ".resemble_enhanced.wav"
    temp_df_wav = input_path + ".df_enhanced.wav"
    source_to_master = input_path

    # Step 1: Attempt Resemble Enhance
    if enhance_with_resemble_ai(input_path, temp_resemble_wav):
        source_to_master = temp_resemble_wav
    else:
        # Step 2: Fallback to DeepFilterNet3
        model, df_state = get_deepfilter_model()
        if model and df_state:
            try:
                from df.enhance import enhance, load_audio, save_audio
                logger.info("Applying DeepFilterNet3 Local Neural De-Reverberation (atten_lim_db=18.0dB)...")
                audio, _ = load_audio(input_path, sr=df_state.sr())
                enhanced = enhance(model, df_state, audio, atten_lim_db=18.0)
                save_audio(temp_df_wav, enhanced, df_state.sr())
                source_to_master = temp_df_wav
                logger.info("DeepFilterNet3 enhancement completed.")
            except Exception as e:
                logger.warning(f"DeepFilterNet3 notice: {e}, using direct audio.")
                source_to_master = input_path

    # Clean, Relaxed & Transparent Studio Mastering (Zero Distortion / Zero Harshness):
    master_filter = (
        "highpass=f=75,"
        "equalizer=f=350:width_type=q:w=1.5:g=-2.0,"
        "loudnorm=I=-18.0:TP=-2.0:LRA=11.0"
    )
    cmd_master = [
        "ffmpeg", "-y", "-i", source_to_master,
        "-af", master_filter,
        "-c:a", "libmp3lame", "-b:a", "256k",
        output_path
    ]
    subprocess.run(cmd_master, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Cleanup temp wavs
    for p in [temp_resemble_wav, temp_df_wav]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    return output_path





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

    # Apply 300% Studio Gold Standard Vocal Mastering (Neural AI De-Reverb + Broadcast Mastering)
    mastered_path = os.path.join(output_dir, f"mastered_{surah}_{start}_{end}_{reciter_id}.mp3")
    apply_neural_studio_enhancement(raw_merged, mastered_path)

    return {
        "audio_path": mastered_path,
        "total_duration": total_dur,
        "ayah_timings": ayah_timings,
        "reciter": reciter
    }

