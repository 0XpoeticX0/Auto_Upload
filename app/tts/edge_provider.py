import os
import re
import json
import base64
import subprocess
import urllib.request
import urllib.error
from app.logger import logger

# ── Sarvam AI — 5 key rotation (Bengali) + Edge TTS (Arabic + free fallback) ─
# Keys are tried in order. If all fail → falls back to free Edge TTS.
# In local testing (not GitHub Actions), skip Sarvam to preserve credits.
SARVAM_KEYS = [
    "sk_m0zfsvef_944TQcASUziwTjZ7fHXOEMrz",   # Key 1
    "sk_i3inlhio_lNzyuWuTNALNG7vAheJuxx5O",   # Key 2
    "sk_1qnvr0q6_j0pYTUeQ45kSSPeTQT7JLY22",   # Key 3
    "sk_dhpmrsnd_oZ5OSS5XDBwz4yTxJC6rgGoT",   # Key 4
    "sk_d6swnxed_eG6fTmwk1onerXj203QMwfQQ",   # Key 5
]
SARVAM_URL     = "https://api.sarvam.ai/text-to-speech"
SARVAM_SPEAKER = "ritu"       # calm, warm — best for Islamic content
SARVAM_MODEL   = "bulbul:v3"  # highest quality
SARVAM_PACE    = 0.88         # slightly slower = more calming

# Only use Sarvam in GitHub Actions (production). Local runs use free Edge TTS.
IS_CI = os.environ.get("GITHUB_ACTIONS", "").lower() == "true" or \
        os.environ.get("CI", "").lower() == "true"

BANGLA_VOICE = "bn-IN-BashkarNeural"  # Edge TTS free fallback for Bengali
ARABIC_VOICE = "ar-SA-HamedNeural"   # Edge TTS — kept for Arabic recitation


DHIKR_REPLACEMENTS = {
    r'\bসুবহানাল্লাহ\b': '<ARABIC>سُبْحَانَ اللَّهِ\n(সুবহানাল্লাহ)</ARABIC>',
    r'\bআলহামদুলিল্লাহ\b': '<ARABIC>الْحَمْدُ لِلَّهِ\n(আলহামদুলিল্লাহ)</ARABIC>',
    r'\bআল্লাহু আকবার\b': '<ARABIC>اللَّهُ أَكْبَرُ\n(আল্লাহু আকবার)</ARABIC>',
    r'\bমাশাআল্লাহ\b': '<ARABIC>مَا شَاءَ اللَّهُ\n(মাশাআল্লাহ)</ARABIC>',
    r'\bইনশাআল্লাহ\b': '<ARABIC>إِنْ شَاءَ اللَّهُ\n(ইনশাআল্লাহ)</ARABIC>',
    r'\bআস্তাগফিরুল্লাহ\b': '<ARABIC>أَسْتَغْفِرُ اللَّهَ\n(আস্তাগফিরুল্লাহ)</ARABIC>',
    r'\bলা ইলাহা ইল্লাল্লাহ\b': '<ARABIC>لَا إِلٰهَ إِلَّا اللّٰهُ\n(লা ইলাহা ইল্লাল্লাহ)</ARABIC>'
}

def auto_tag_dhikr(text: str) -> str:
    parts = re.split(r'(<ARABIC>.*?</ARABIC>)', text, flags=re.DOTALL | re.IGNORECASE)
    res = []
    for p in parts:
        if p.upper().startswith("<ARABIC>") and p.upper().endswith("</ARABIC>"):
            res.append(p)
        else:
            for pattern, repl in DHIKR_REPLACEMENTS.items():
                p = re.sub(pattern, repl, p)
            res.append(p)
    return "".join(res)

HONORIFIC_SPOKEN_REPLACEMENTS = {
    # For audio: drop honorific abbreviations entirely — they show on screen,
    # but Sarvam cannot pronounce "সাল্লাল্লাহু আলাইহি ওয়া সাল্লাম" cleanly.
    # Viewers read it on screen. Audio stays clean.
    r'\(\s*সা[\.\:\s]*\)': '',
    r'\(\s*সাঃ\s*\)': '',
    r'\(\s*আ[\.\:\s]*\)': '',
    r'\(\s*আঃ\s*\)': '',
    r'\(\s*রা[\.\:\s]*\)': '',
    r'\(\s*রাঃ\s*\)': '',
    r'\(\s*রহ[\.\:\s]*\)': '',
    r'\(\s*রহঃ\s*\)': '',
    r'ﷺ': '',
    r'ﷻ': '',
    # Also clean up the full written-out form if Gemini writes it
    r'সাল্লাল্লাহু আলাইহি ওয়া সাল্লাম': '',
    r'সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম': '',
    r'আলাইহিস সালাম': '',
    r'রাদিয়াল্লাহু আনহু': '',
    r'রাহিমাহুল্লাহ': '',
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

def should_speak_bangla_translation(clean_trans: str) -> bool:
    short_dhikrs = {'সুবহানাল্লাহ', 'আলহামদুলিল্লাহ', 'আল্লাহু আকবার', 'আস্তাগফিরুল্লাহ', 'মাশাআল্লাহ', 'ইনশাআল্লাহ', 'লা ইলাহা ইল্লাল্লাহ'}
    words = clean_trans.strip().split()
    if len(words) <= 2 and any(d in clean_trans for d in short_dhikrs):
        return False
    return len(clean_trans.strip()) > 3

def _synthesize_bangla_edge_free(text: str, out_mp3: str) -> bool:
    """Free Edge TTS fallback for Bengali (used during local testing)."""
    out_vtt = out_mp3.replace(".mp3", ".vtt")
    cmd = [
        "edge-tts",
        f"--voice={BANGLA_VOICE}",
        f"--text={text}",
        "--rate=+5%",
        "--pitch=-1Hz",
        f"--write-media={out_mp3}",
        f"--write-subtitles={out_vtt}"
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100
    except Exception as e:
        logger.warning(f"Edge TTS Bengali fallback error: {e}")
        return False


def synthesize_bangla_sarvam(text: str, out_mp3: str) -> bool:
    """Synthesize Bengali with Sarvam AI — 5 key rotation, Edge TTS fallback.
    
    Rules:
    - Local testing (not CI): always use free Edge TTS, never burn API credits
    - GitHub Actions (CI=true): try all 5 keys in order → fallback to Edge TTS
    """
    if not any(c.isalnum() for c in text):
        return False

    # ── Local testing: use free Edge TTS to preserve credits ──────────────────
    if not IS_CI:
        logger.info("Local run — using free Edge TTS for Bengali (Sarvam credits preserved)")
        return _synthesize_bangla_edge_free(text, out_mp3)

    # ── Production (GitHub Actions): try 5 Sarvam keys in order ──────────────
    payload = json.dumps({
        "inputs": [text],
        "target_language_code": "bn-IN",
        "speaker": SARVAM_SPEAKER,
        "model": SARVAM_MODEL,
        "enable_preprocessing": True,
        "pace": SARVAM_PACE
    }).encode("utf-8")

    for idx, key in enumerate(SARVAM_KEYS, 1):
        try:
            req = urllib.request.Request(SARVAM_URL, data=payload, headers={
                "api-subscription-key": key,
                "Content-Type": "application/json"
            }, method="POST")
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                audio_b64 = data.get("audios", [None])[0]
                if not audio_b64:
                    continue
                audio_bytes = base64.b64decode(audio_b64)
                tmp_wav = out_mp3.replace(".mp3", "_sarvam.wav")
                with open(tmp_wav, "wb") as f:
                    f.write(audio_bytes)
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_wav, "-b:a", "192k", out_mp3],
                    check=True, capture_output=True
                )
                try:
                    os.remove(tmp_wav)
                except Exception:
                    pass
                if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100:
                    logger.info(f"Sarvam Key #{idx} OK for '{text[:30]}'")
                    return True
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            if e.code == 429 or "quota" in err.lower() or "limit" in err.lower():
                logger.warning(f"Sarvam Key #{idx} quota reached — trying next key")
            else:
                logger.warning(f"Sarvam Key #{idx} error ({e.code}): {err[:80]}")
        except Exception as e:
            logger.warning(f"Sarvam Key #{idx} failed: {e}")

    # ── All 5 keys failed → free Edge TTS fallback ────────────────────────────
    logger.warning("All 5 Sarvam keys failed — falling back to free Edge TTS for Bengali")
    return _synthesize_bangla_edge_free(text, out_mp3)


def synthesize_arabic_edge(text: str, rate: str, pitch: str, out_mp3: str, out_vtt: str) -> bool:
    """Synthesize Arabic text using Edge TTS (kept — good quality for Arabic)."""
    if not any(c.isalnum() or ('\u0600' <= c <= '\u06FF') for c in text):
        return False
    cmd = [
        "edge-tts",
        f"--voice={ARABIC_VOICE}",
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
        logger.warning(f"Edge TTS Arabic warning for '{text[:25]}': {e}")
        return False


def synthesize_segment(text: str, voice: str, rate: str, pitch: str, out_mp3: str, out_vtt: str) -> bool:
    """Unified synthesizer — routes Bangla to Sarvam (or free fallback), Arabic to Edge TTS."""
    if not any(c.isalnum() or ('\u0600' <= c <= '\u06FF') for c in text):
        return False
    # Arabic segments → always Edge TTS
    if voice == ARABIC_VOICE:
        return synthesize_arabic_edge(text, rate, pitch, out_mp3, out_vtt)
    # Bangla segments → Sarvam (CI) or Edge TTS free (local)
    return synthesize_bangla_sarvam(text, out_mp3)



def generate_scene_audio(text: str, scene_idx: int, temp_dir: str):
    os.makedirs(temp_dir, exist_ok=True)
    
    # 1. Normalize all possible tag variants (<arabic>, <ARABIC>, [arabic], etc.)
    text = re.sub(r'<\s*arabic\s*>', '<ARABIC>', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*arabic\s*>', '</ARABIC>', text, flags=re.IGNORECASE)
    
    # Auto-tag common Dhikr if untagged outside <ARABIC> tags
    text = auto_tag_dhikr(text)
        
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
            
            lines = [l.strip() for l in raw_arabic_block.split('\n') if l.strip()]
            arabic_lines = [l for l in lines if any('\u0600' <= c <= '\u06FF' for c in l)]
            bangla_lines = [l for l in lines if not any('\u0600' <= c <= '\u06FF' for c in l)]
            
            spoken_arabic = clean_arabic_for_audio(raw_arabic_block)
            # The entire card (Arabic + transliteration + translation) stays displayed together continuously
            display_card = raw_arabic_block
            
            # Extract ONLY the translation to speak (skip the transliteration/spelling line)
            spoken_translation = ""
            if len(bangla_lines) >= 2:
                # First bangla line is spelling/pronunciation (DO NOT SPEAK)
                # Second bangla line is translation (SPEAK THIS)
                raw_trans = ' '.join(bangla_lines[1:]).strip()
                clean_trans = re.sub(r'[\(\)\[\]]', '', raw_trans).strip()
                clean_trans = re.sub(r'^(বাংলা অর্থ|অর্থ|উচ্চারণ|অনুবাদ)\s*[:ঃ\-—]\s*', '', clean_trans).strip()
                spoken_translation = clean_trans
            elif len(bangla_lines) == 1:
                line = bangla_lines[0].strip()
                # If the only Bangla line is in parentheses → it's the pronunciation/spelling
                # line (e.g. "(আলহামদুলিল্লাহ)"). NEVER speak this — it shows on screen only.
                is_pronunciation = line.startswith('(') and line.endswith(')')
                if not is_pronunciation:
                    # It's an actual translation line without parens — speak it
                    if '—' in line or '–' in line or '-' in line or ':' in line:
                        parts_split = re.split(r'[—–\-:]', line, maxsplit=1)
                        clean_trans = re.sub(r'[\(\)\[\]]', '', parts_split[1]).strip()
                        spoken_translation = clean_trans
                    else:
                        clean_trans = re.sub(r'[\(\)\[\]]', '', line).strip()
                        short_dhikrs = {'সুবহানাল্লাহ', 'আলহামদুলিল্লাহ', 'আল্লাহু আকবার', 'আস্তাগফিরুল্লাহ', 'মাশাআল্লাহ', 'ইনশাআল্লাহ', 'লা ইলাহা ইল্লাল্লাহ'}
                        if len(clean_trans.split()) > 2 or not any(d in clean_trans for d in short_dhikrs):
                            spoken_translation = clean_trans
                        
            if any(c.isalnum() or ('\u0600' <= c <= '\u06FF') for c in spoken_arabic):
                segments.append({
                    "type": "arabic",
                    "voice": ARABIC_VOICE,
                    "spoken_text": spoken_arabic,
                    "display_text": display_card,
                    "rate": "-15%",
                    "pitch": "-2Hz"
                })
                
            # If translation text exists, speak ONLY the Bangla translation with the same display_card
            if spoken_translation and should_speak_bangla_translation(spoken_translation):
                spoken_bangla_trans = spoken_translation
                for p, r in HONORIFIC_SPOKEN_REPLACEMENTS.items():
                    spoken_bangla_trans = re.sub(p, r, spoken_bangla_trans)
                for k, v in PHONETIC_CLEANUPS.items():
                    spoken_bangla_trans = spoken_bangla_trans.replace(k, v)
                spoken_bangla_trans = spoken_bangla_trans.replace('।', '। ').replace(',', ', ').replace('?', '? ')
                spoken_bangla_trans = re.sub(r'[\(\)\[\]]', ' ', spoken_bangla_trans).strip()
                
                if any(c.isalnum() for c in spoken_bangla_trans):
                    segments.append({
                        "type": "bangla",
                        "voice": BANGLA_VOICE,
                        "spoken_text": spoken_bangla_trans,
                        "display_text": display_card,
                        "rate": "+5%",
                        "pitch": "-1Hz"
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
        
        start_t = current_offset_ms
        end_t = current_offset_ms + seg_dur_ms
        
        # Merge cues if display text is identical (prevents frame skipping/jumping)
        if seg_cues and seg_cues[-1]["text"] == seg["display_text"]:
            seg_cues[-1]["end_ms"] = end_t
        else:
            seg_cues.append({
                "start_ms": start_t,
                "end_ms": end_t,
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
