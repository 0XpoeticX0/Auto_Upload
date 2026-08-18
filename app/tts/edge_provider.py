import os
import re
import subprocess
from app.logger import logger

BANGLA_VOICE = "bn-IN-BashkarNeural"
ARABIC_VOICE = "ar-SA-HamedNeural"

DHIKR_REPLACEMENTS = {
    r'(?<!<ARABIC>)সুবহানাল্লাহ(?!</ARABIC>)': '<ARABIC>سُبْحَانَ اللَّهِ\n(সুবহানাল্লাহ)</ARABIC>',
    r'(?<!<ARABIC>)আলহামদুলিল্লাহ(?!</ARABIC>)': '<ARABIC>الْحَمْدُ لِلَّهِ\n(আলহামদুলিল্লাহ)</ARABIC>',
    r'(?<!<ARABIC>)আল্লাহু আকবার(?!</ARABIC>)': '<ARABIC>اللَّهُ أَكْبَرُ\n(আল্লাহু আকবার)</ARABIC>',
    r'(?<!<ARABIC>)মাশাআল্লাহ(?!</ARABIC>)': '<ARABIC>مَا شَاءَ اللَّهُ\n(মাশাআল্লাহ)</ARABIC>',
    r'(?<!<ARABIC>)ইনশাআল্লাহ(?!</ARABIC>)': '<ARABIC>إِنْ شَاءَ اللَّهُ\n(ইনশাআল্লাহ)</ARABIC>',
    r'(?<!<ARABIC>)আস্তাগফিরুল্লাহ(?!</ARABIC>)': '<ARABIC>أَسْتَغْفِرُ اللَّهَ\n(আস্তাগফিরুল্লাহ)</ARABIC>',
    r'(?<!<ARABIC>)লা ইলাহা ইল্লাল্লাহ(?!</ARABIC>)': '<ARABIC>لَا إِلٰهَ إِلَّا اللّٰهُ\n(লা ইলাহা ইল্লাল্লাহ)</ARABIC>'
}

HONORIFIC_SPOKEN_REPLACEMENTS = {
    # Replace abbreviations for TTS audio only (so voice does not say awkward initials)
    r'\(\s*সা[\.\:\s]*\)': ' সাল্লাল্লাহু আলাইহি ওয়া সাল্লাম ',
    r'\(\s*সাঃ\s*\)': ' সাল্লাল্লাহু আলাইহি ওয়া সাল্লাম ',
    r'\(\s*আ[\.\:\s]*\)': ' আলাইহিস সালাম ',
    r'\(\s*আঃ\s*\)': ' আলাইহিস সালাম ',
    r'\(\s*রা[\.\:\s]*\)': ' রাদিয়াল্লাহু আনহু ',
    r'\(\s*রাঃ\s*\)': ' রাদিয়াল্লাহু আনহু ',
    r'\(\s*রহ[\.\:\s]*\)': ' রাহিমাহুল্লাহ ',
    r'\(\s*রহঃ\s*\)': ' রাহিমাহুল্লাহ ',
    r'ﷺ': ' সাল্লাল্লাহু আলাইহি ওয়া সাল্লাম ',
    r'ﷻ': ' জাল্লা জালালুহু ',
}

PHONETIC_CLEANUPS = {
    "হইয়ো না": "হবেন না",
    "হইও না": "হবেন না",
    "হৃদয়": "অন্তর",
    "হৃদয়ে": "অন্তরে",
    "পবিত্র পবিত্র কুরআনে": "পবিত্র কুরআনে",
    "পবিত্র পবিত্র কোরআনে": "পবিত্র কুরআনে",
    "নিশ্চয়ই": "নিশ্চয়ই",
    "স্বস্তি": "শান্তি",
    "তাআলা": "তা'আলা",
    "সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম": "সাল্লাল্লাহু আলাইহি ওয়া সাল্লাম",
}

def time_to_ms(t_str):
    h, m, s_ms = t_str.split(':')
    if '.' in s_ms:
        s, ms = s_ms.split('.')
    else:
        s, ms = s_ms.split(',')
    return int(h)*3600000 + int(m)*60000 + int(s)*1000 + int(ms)

def ms_to_time(ms):
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    remainder_ms = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{remainder_ms:03d}"

def clean_arabic_for_audio(raw_arabic: str) -> str:
    lines = raw_arabic.strip().split("\n")
    pure_arabic_lines = [l for l in lines if any('\u0600' <= c <= '\u06FF' for c in l)]
    if pure_arabic_lines:
        return " ".join(pure_arabic_lines).strip()
    return lines[0].strip()

def synthesize_segment(text: str, voice: str, rate: str, pitch: str, out_mp3: str, out_vtt: str) -> bool:
    # Filter out punctuation-only text
    if not any(c.isalnum() or ('\u0600' <= c <= '\u06FF') for c in text):
        return False
    cmd = [
        "edge-tts",
        f"--voice={voice}",
        f"--text={text}",
        f"--rate={rate}",
        f"--pitch={pitch}",
        f"--write-media={out_mp3}",
        f"--write-subtitles={out_vtt}"
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100
    except Exception as e:
        logger.warning(f"edge-tts synthesis warning for text '{text[:25]}...': {e}")
        return False

def generate_scene_audio(text: str, scene_idx: int, temp_dir: str):
    os.makedirs(temp_dir, exist_ok=True)
    
    # 1. Normalize all possible tag variants (<arabic>, <ARABIC>, [arabic], etc.)
    text = re.sub(r'<\s*arabic\s*>', '<ARABIC>', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*arabic\s*>', '</ARABIC>', text, flags=re.IGNORECASE)
    
    # Auto-tag common Dhikr if untagged
    for pattern, repl in DHIKR_REPLACEMENTS.items():
        text = re.sub(pattern, repl, text)
        
    parts = re.split(r'(<ARABIC>.*?</ARABIC>)', text, flags=re.DOTALL | re.IGNORECASE)
    segments = []
    
    for part in parts:
        clean_part = part.strip()
        if not clean_part:
            continue
        if clean_part.upper().startswith("<ARABIC>") and clean_part.upper().endswith("</ARABIC>"):
            raw_arabic_block = clean_part[8:-9].strip()
            # Strip any accidental nested tags
            raw_arabic_block = re.sub(r'</?[a-zA-Z0-9_-]+>', '', raw_arabic_block).strip()
            spoken_text = clean_arabic_for_audio(raw_arabic_block)
            display_text = raw_arabic_block
            if any(c.isalnum() or ('\u0600' <= c <= '\u06FF') for c in spoken_text):
                segments.append({
                    "type": "arabic",
                    "voice": ARABIC_VOICE,
                    "spoken_text": spoken_text,
                    "display_text": display_text,
                    "rate": "-15%",
                    "pitch": "-2Hz"
                })
        else:
            # Strip any stray tags or 'arabic:' prefixes
            clean_bangla = re.sub(r'</?[a-zA-Z0-9_-]+>', '', clean_part)
            clean_bangla = re.sub(r'^\s*(arabic|bangla|english)\s*:\s*', '', clean_bangla, flags=re.IGNORECASE).strip()
            
            # 1. Visual display text (keeps (সা.), (রা.), (আ.) exact and untouched for subtitles)
            display_text = clean_bangla
            
            # 2. Spoken text for AI voice: expand initials into natural honorifics for fluent audio
            spoken_bangla = clean_bangla
            for pattern, repl in HONORIFIC_SPOKEN_REPLACEMENTS.items():
                spoken_bangla = re.sub(pattern, repl, spoken_bangla)
                
            for k, v in PHONETIC_CLEANUPS.items():
                spoken_bangla = spoken_bangla.replace(k, v)
                
            spoken_bangla = spoken_bangla.replace('।', '। ').replace(',', ', ').replace('?', '? ')
            # Remove isolated brackets from spoken audio so AI doesn't stumble
            spoken_bangla = re.sub(r'[\(\)\[\]]', ' ', spoken_bangla).strip()
            
            # Ensure text contains actual letters/words, not just stray punctuation
            if any(c.isalnum() for c in spoken_bangla):
                segments.append({
                    "type": "bangla",
                    "voice": BANGLA_VOICE,
                    "spoken_text": spoken_bangla,
                    "display_text": display_text,
                    "rate": "+5%",
                    "pitch": "-1Hz"
                })
            
    seg_mp3s = []
    seg_cues = []
    current_offset_ms = 0
    
    for idx, seg in enumerate(segments):
        s_mp3 = os.path.join(temp_dir, f"scene_{scene_idx}_seg_{idx}.mp3")
        s_vtt = os.path.join(temp_dir, f"scene_{scene_idx}_seg_{idx}.vtt")
        
        ok = synthesize_segment(seg["spoken_text"], seg["voice"], seg["rate"], seg["pitch"], s_mp3, s_vtt)
        if not ok or not os.path.exists(s_mp3):
            continue
            
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", s_mp3]
        dur_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        seg_dur_ms = int(float(dur_res.stdout.strip()) * 1000)
        
        # Always use pristine display_text for the subtitles on screen
        seg_cues.append({
            "start_ms": current_offset_ms,
            "end_ms": current_offset_ms + seg_dur_ms,
            "text": seg["display_text"]
        })
                
        seg_mp3s.append(s_mp3)
        current_offset_ms += seg_dur_ms
        
    scene_mp3 = os.path.join(temp_dir, f"scene_{scene_idx}_audio.mp3")
    concat_list = os.path.join(temp_dir, f"scene_{scene_idx}_concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for m in seg_mp3s:
            safe_m = os.path.abspath(m).replace("\\", "/")
            f.write(f"file '{safe_m}'\n")
            
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", scene_mp3], check=True, capture_output=True)
    return scene_mp3, seg_cues, current_offset_ms

def generate_all_audio(scenes_or_script, topic_id: int = 0, video_format: str = "master", category: str = "islamic_knowledge") -> list:
    """Master audio synthesizer for all scenes with dual-voice stitching and VTT/ASS export."""
    if isinstance(scenes_or_script, dict):
        scenes = scenes_or_script.get("scenes", [])
    else:
        scenes = scenes_or_script
        
    temp_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    os.makedirs(temp_dir, exist_ok=True)
    
    all_scene_mp3s = []
    global_cues = []
    global_offset_ms = 0
    
    for idx, sc in enumerate(scenes):
        narration = sc.get("narration", sc.get("narration_bn", ""))
        sc_mp3, sc_cues, sc_dur_ms = generate_scene_audio(narration, idx, temp_dir)
        all_scene_mp3s.append(sc_mp3)
        
        for cue in sc_cues:
            global_cues.append({
                "start_ms": global_offset_ms + cue["start_ms"],
                "end_ms": global_offset_ms + cue["end_ms"],
                "text": cue["text"]
            })
        global_offset_ms += sc_dur_ms
        
    master_mp3 = os.path.join(temp_dir, "master_audio.mp3")
    master_vtt = os.path.join(temp_dir, "master_audio.vtt")
    master_concat = os.path.join(temp_dir, "master_concat.txt")
    
    with open(master_concat, "w", encoding="utf-8") as f:
        for m in all_scene_mp3s:
            safe_m = os.path.abspath(m).replace("\\", "/")
            f.write(f"file '{safe_m}'\n")
            
    raw_master_mp3 = os.path.join(temp_dir, "master_raw.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", master_concat, "-c", "copy", raw_master_mp3], check=True, capture_output=True)
    
    # Apply vocal warmth and presence mastering chain
    vocal_filter = "equalizer=f=200:width_type=h:width=120:g=2,equalizer=f=4000:width_type=h:width=1000:g=1.5,aecho=0.8:0.9:25:0.1"
    subprocess.run(["ffmpeg", "-y", "-i", raw_master_mp3, "-af", vocal_filter, "-b:a", "192k", master_mp3], check=True, capture_output=True)
    try: os.remove(raw_master_mp3)
    except: pass
    
    with open(master_vtt, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for cue in global_cues:
            f.write(f"{ms_to_time(cue['start_ms'])} --> {ms_to_time(cue['end_ms'])}\n{cue['text']}\n\n")
            
    logger.info(f"Master Dual-Voice audio generated: {master_mp3} ({global_offset_ms/1000:.1f}s)")
    
    for sc in scenes:
        sc["audio_path"] = master_mp3
        sc["vtt_path"] = master_vtt
        sc["duration"] = global_offset_ms / 1000.0
        
    return scenes
