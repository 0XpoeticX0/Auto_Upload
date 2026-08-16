import os
import subprocess
import re
from app.logger import logger

CATEGORY_VOICES = {
    "educational": "en-US-GuyNeural",
    "islamic_knowledge": "en-GB-RyanNeural",
    "crime_thriller": "en-US-SteffanNeural",
    "knowledge": "en-GB-RyanNeural",
    "motivational": "en-US-BrianNeural",
    "love_life_advice": "en-US-AriaNeural",
    "novel_story": "en-US-ChristopherNeural"
}
DEFAULT_VOICE = "en-US-GuyNeural"
ARABIC_VOICE = "ar-SA-HamedNeural" # Native Saudi voice for authentic Arabic recitation

PHONETIC_MAP = {
    "Quran": "Koor-ahn",
    "Qur'an": "Koor-ahn",
    "Hadith": "Ha-deeth",
    "Ahadith": "Aha-deeth",
    "Sahih": "Sa-heeh",
    "Bukhari": "Boo-khah-ree",
    "Muslim": "Moos-lim",
    "Qiyamah": "Kee-yah-mah",
    "Jannah": "Jun-nah",
    "Jahannam": "Ja-hun-num",
    "Dajjal": "Daj-jaal",
    "Sunnah": "Soon-nah",
    "Allah": "Ahl-lah",
    "Muhammad": "Moo-hum-mud",
    "Prophet": "Prophet",
    "Sahabah": "Sa-haa-bah",
    "Dhikr": "Thikr",
    "Dua": "Doo-ah",
    "Halal": "Ha-laal",
    "Haram": "Ha-raam",
    "Imam": "Ee-maam",
    "Mahdi": "Mah-dee",
    "Isa": "Ee-sah",
    "Musa": "Moo-sah",
    "Barakah": "Bah-rah-kah",
    "Surah": "Soo-rah",
    "Ayah": "Ah-yah"
}

def apply_phonetics(text: str) -> str:
    for word, phonetic in PHONETIC_MAP.items():
        text = re.sub(rf'\b{re.escape(word)}\b', phonetic, text, flags=re.IGNORECASE)
    return text

def reverse_phonetics(text: str) -> str:
    for word, phonetic in PHONETIC_MAP.items():
        text = re.sub(rf'\b{re.escape(phonetic)}\b', word, text, flags=re.IGNORECASE)
    return text

def time_to_ms(t_str):
    h, m, s_ms = t_str.split(':')
    # Handle both . and , as decimal separator
    if '.' in s_ms:
        s, ms = s_ms.split('.')
    else:
        s, ms = s_ms.split(',')
    return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)

def ms_to_time(ms):
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    m_sec = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{m_sec:03d}"

def offset_vtt_content(vtt_content, offset_ms):
    lines = vtt_content.splitlines()
    out = []
    # Match both dots and commas for the decimal separator
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})")
    for line in lines:
        match = pattern.search(line)
        if match:
            start = time_to_ms(match.group(1)) + offset_ms
            end = time_to_ms(match.group(2)) + offset_ms
            out.append(f"{ms_to_time(start)} --> {ms_to_time(end)}")
        else:
            if line.strip() != "WEBVTT":
                # Ensure no empty lines at the very beginning of chunk appending
                if line.strip() or len(out) > 0:
                    out.append(line)
    return "\n".join(out)

def get_audio_duration_ms(filepath):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", filepath
    ], capture_output=True, text=True)
    try:
        return int(float(result.stdout.strip()) * 1000)
    except Exception as e:
        logger.error(f"Failed to probe duration for {filepath}: {e}")
        return 0

def generate_chunk_audio(full_text: str, output_filepath: str, voice: str):
    vtt_filepath = output_filepath.replace(".mp3", ".vtt")
    
    # If it's the Arabic voice, it might contain both Arabic and English transliteration e.g. "سُبْحَانَ اللَّهِ (SubhanAllah)"
    # We want the TTS to ONLY read the Arabic (to avoid thick accents), but we want BOTH on the screen.
    tts_text = full_text
    if voice == ARABIC_VOICE:
        # Strip all A-Z, a-z, and parentheses for the audio generation
        tts_text = re.sub(r'[a-zA-Z\(\)]', '', full_text).strip()
        
    try:
        command = [
            "edge-tts",
            "--voice", voice,
            "--text", tts_text,
            "--write-media", output_filepath,
            "--write-subtitles", vtt_filepath
        ]
        
        # Slow down Arabic voice for rhythmic and pleasing recitation
        if voice == ARABIC_VOICE:
            command.insert(1, "--rate=-25%")
            
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"edge-tts failed for chunk: {result.stderr}")
            return False
        if not os.path.exists(output_filepath) or os.path.getsize(output_filepath) < 1024:
            return False
            
        if os.path.exists(vtt_filepath):
            with open(vtt_filepath, "r", encoding="utf-8") as f:
                vtt_content = f.read()
                
            # If it was an Arabic chunk, restore the full text (with English transliteration) into the subtitle
            if voice == ARABIC_VOICE and tts_text != full_text:
                vtt_content = vtt_content.replace(tts_text, full_text)
            # If it was an English chunk, reverse the phonetics back to normal text
            elif voice != ARABIC_VOICE:
                vtt_content = reverse_phonetics(vtt_content)
                
            with open(vtt_filepath, "w", encoding="utf-8") as f:
                f.write(vtt_content)
        return True
    except Exception as e:
        logger.error(f"Failed to generate TTS chunk: {e}")
        return False

def generate_master_audio(full_script_text: str, output_filepath: str, voice: str = DEFAULT_VOICE):
    logger.info(f"Generating Dual-Voice Master TTS...")
    base_dir = os.path.dirname(output_filepath)
    vtt_filepath = output_filepath.replace(".mp3", ".vtt")
    
    # Parse <ARABIC> tags to create chunks
    pattern = re.compile(r'(<ARABIC>.*?</ARABIC>)', re.DOTALL)
    parts = pattern.split(full_script_text)
    
    chunks = []
    for p in parts:
        if p.startswith('<ARABIC>') and p.endswith('</ARABIC>'):
            chunks.append((p[8:-9], ARABIC_VOICE))
        else:
            if p.strip():
                # Apply phonetics only to English parts
                chunks.append((apply_phonetics(p), voice))
                
    chunk_audio_files = []
    chunk_vtt_contents = []
    current_time_offset_ms = 0
    
    for i, (text, chunk_voice) in enumerate(chunks):
        if not text.strip():
            continue
            
        chunk_mp3 = os.path.join(base_dir, f"chunk_{i}.mp3")
        chunk_vtt = os.path.join(base_dir, f"chunk_{i}.vtt")
        
        logger.info(f"Generating chunk {i} ({'ARABIC' if chunk_voice == ARABIC_VOICE else 'ENGLISH'})")
        success = generate_chunk_audio(text, chunk_mp3, chunk_voice)
        
        if success:
            chunk_audio_files.append(chunk_mp3)
            # Read VTT, offset it, and store
            if os.path.exists(chunk_vtt):
                with open(chunk_vtt, "r", encoding="utf-8") as f:
                    raw_vtt = f.read()
                offset_vtt = offset_vtt_content(raw_vtt, current_time_offset_ms)
                chunk_vtt_contents.append(offset_vtt)
            
            # Calculate duration of this chunk to offset the next chunk's VTT
            duration_ms = get_audio_duration_ms(chunk_mp3)
            current_time_offset_ms += duration_ms
        else:
            logger.error(f"Failed to generate audio for chunk {i}")
            return False
            
    # Concatenate audio files using ffmpeg
    concat_list_path = os.path.join(base_dir, "concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for audio_file in chunk_audio_files:
            # Need to write absolute path securely for ffmpeg
            abs_path = os.path.abspath(audio_file)
            escaped_path = abs_path.replace("\\", "/")
            f.write(f"file '{escaped_path}'\n")
            
    logger.info("Concatenating audio chunks...")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
        "-i", concat_list_path, "-c", "copy", output_filepath
    ]
    subprocess.run(concat_cmd, capture_output=True)
    
    if not os.path.exists(output_filepath):
        logger.error("FFmpeg failed to concatenate audio chunks.")
        return False
        
    # Write master VTT
    logger.info("Merging VTT subtitles...")
    with open(vtt_filepath, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for content in chunk_vtt_contents:
            f.write(content + "\n\n")
            
    # Cleanup chunks
    for f in chunk_audio_files:
        try: os.remove(f)
        except: pass
        try: os.remove(f.replace(".mp3", ".vtt"))
        except: pass
    try: os.remove(concat_list_path)
    except: pass
        
    return True

def generate_all_audio(scenes: list, topic_id: int, video_format: str = "short", category: str = "educational"):
    base_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    os.makedirs(base_dir, exist_ok=True)
    
    voice = CATEGORY_VOICES.get(category, DEFAULT_VOICE)
    logger.info(f"Using primary voice: {voice} for category: {category}")
    
    full_text = " ".join([scene.get("narration", "") for scene in scenes if scene.get("narration")])
    master_audio_path = os.path.join(base_dir, "master_audio.mp3")
    
    success = generate_master_audio(full_text, master_audio_path, voice=voice)
    
    if not success:
        return scenes
        
    updated_scenes = []
    for scene in scenes:
        scene["audio_path"] = master_audio_path
        updated_scenes.append(scene)
        
    return updated_scenes
