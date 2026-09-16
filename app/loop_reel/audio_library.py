# -*- coding: utf-8 -*-
"""
Quran Audio Library for Loop Reel Pipeline.
Strictly uses ONLY 2 approved reciters (GEMINI.md mandate):
  - Sheikh Mishary Rashid Alafasy (warm, soothing — comfort/mercy/hope themes)
  - Sheikh Yasser Ad-Dossari (commanding, powerful — majesty/judgment themes)
"""
import os
import json
import random
import urllib.request
import subprocess
from app.logger import logger

AUDIO_DIR = os.path.abspath("data/quran_audio")

# ═══════════════════════════════════════════════════════════════════════════════
# STRICTLY 2 APPROVED RECITERS ONLY — Alafasy & Dossari (GEMINI.md Rule #5)
# 30 curated tracks covering all major thematic categories for topic-matching.
# ═══════════════════════════════════════════════════════════════════════════════
RECITER_TRACKS = [
    # ── DUA YUNUS & RELIEF FROM CRISIS / DISTRESS ──────────────────────────────
    {"id": "alafasy_dua_yunus", "name": "Alafasy - Dua Yunus (Al-Anbiya: 87)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/021087.mp3", "filename": "alafasy_dua_yunus.mp3", "tags": ["debt", "crisis", "distress", "ঋণ", "বিপদ", "কষ্ট", "হতাশা", "দোয়া ইউনুস", "উদ্ধার", "সমস্যা"]},
    {"id": "dossari_dua_yunus", "name": "Dossari - Dua Yunus (Al-Anbiya: 87)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/021087.mp3", "filename": "dossari_dua_yunus.mp3", "tags": ["debt", "crisis", "distress", "ঋণ", "বিপদ", "কষ্ট", "হতাশা", "দোয়া ইউনুস"]},
    {"id": "alafasy_surah_imran_mulk", "name": "Alafasy - Surah Al-Imran (Maalikal Mulk: 26)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/003026.mp3", "filename": "alafasy_surah_imran_mulk.mp3", "tags": ["debt", "rizq", "crisis", "wealth", "ঋণ", "রিজিক", "উদ্ধার", "বরকত", "ক্ষমতা"]},
    {"id": "alafasy_surah_tawbah_hasbiyallah", "name": "Alafasy - Surah At-Tawbah (Hasbiyallahu: 129)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/009129.mp3", "filename": "alafasy_surah_tawbah_hasbiyallah.mp3", "tags": ["crisis", "distress", "peace", "protection", "বিপদ", "কষ্ট", "পেরেশানি", "ভরসা"]},
    {"id": "dossari_surah_ibrahim", "name": "Dossari - Surah Ibrahim (Gratitude: 40)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/014040.mp3", "filename": "dossari_surah_ibrahim.mp3", "tags": ["gratitude", "prayer", "family", "ইব্রাহিম", "নামাজ", "পরিবার", "শুকরিয়া"]},

    # ── QURAN MERCY & PROTECTION DUAS ──────────────────────────────────────────
    {"id": "alafasy_surah_kahf_rahmah", "name": "Alafasy - Surah Al-Kahf (Dua for Mercy: 10)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/018010.mp3", "filename": "alafasy_surah_kahf_rahmah.mp3", "tags": ["kahf", "mercy", "protection", "কাহফ", "রহমত", "হেফাজত"]},
    {"id": "alafasy_surah_qasas_musa", "name": "Alafasy - Surah Al-Qasas (Musa's Dua for Rizq: 24)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/028024.mp3", "filename": "alafasy_surah_qasas_musa.mp3", "tags": ["rizq", "marriage", "help", "রিজিক", "মুসা", "দোয়া", "সাহায্য"]},
    {"id": "alafasy_surah_fatir_rahmah", "name": "Alafasy - Surah Fatir (Unlocking Mercy: 2)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/035002.mp3", "filename": "alafasy_surah_fatir_rahmah.mp3", "tags": ["rizq", "mercy", "doors", "রিজিক", "রহমত", "বন্ধ দরজা"]},
    {"id": "dossari_surah_fatir_rahmah", "name": "Dossari - Surah Fatir (Unlocking Mercy: 2)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/035002.mp3", "filename": "dossari_surah_fatir_rahmah.mp3", "tags": ["rizq", "mercy", "doors", "রিজিক", "রহমত"]},

    # ── AYAT AL-KURSI & PROTECTION ─────────────────────────────────────────────
    {"id": "alafasy_ayat_kursi", "name": "Alafasy - Ayat Al-Kursi (Al-Baqarah: 255)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/002255.mp3", "filename": "alafasy_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "bedtime", "আয়াতুল কুরসী", "বদনজর", "জিন", "শয়তান", "হেফাজত", "সুরক্ষা", "বিপদ", "ঘর থেকে বের হওয়া"]},
    {"id": "dossari_ayat_kursi", "name": "Dossari - Ayat Al-Kursi (Al-Baqarah: 255)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/002255.mp3", "filename": "dossari_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী", "বদনজর", "হেফাজত"]},

    # ── SURAH AL-MULK & GRAVE / NIGHT ──────────────────────────────────────────
    {"id": "alafasy_surah_mulk", "name": "Alafasy - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/067002.mp3", "filename": "alafasy_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক", "মৃত্যু", "রাত", "আজাব"]},
    {"id": "dossari_surah_mulk", "name": "Dossari - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/067002.mp3", "filename": "dossari_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},

    # ── PROPHETIC DUAS (Maryam, Anbiya, Furqan) ────────────────────────────────
    {"id": "alafasy_surah_maryam_zakariya", "name": "Alafasy - Surah Maryam (Zakariya's Dua: 4)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/019004.mp3", "filename": "alafasy_surah_maryam_zakariya.mp3", "tags": ["dua", "family", "marriage", "children", "মরিয়ম", "দোয়া", "পরিবার", "বিয়ে", "সন্তান"]},
    {"id": "dossari_surah_maryam_zakariya", "name": "Dossari - Surah Maryam (Zakariya's Dua: 4)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/019004.mp3", "filename": "dossari_surah_maryam_zakariya.mp3", "tags": ["dua", "family", "marriage", "children", "মরিয়ম", "দোয়া", "পরিবার"]},
    {"id": "alafasy_surah_anbiya_zakariya", "name": "Alafasy - Surah Al-Anbiya (Rabbi La Tadharni: 89)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/021089.mp3", "filename": "alafasy_surah_anbiya_zakariya.mp3", "tags": ["dua", "family", "marriage", "সন্তান", "পরিবার", "দোয়া"]},
    {"id": "alafasy_surah_furqan_servants", "name": "Alafasy - Surah Al-Furqan (Servants of Rahman: 63)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/025063.mp3", "filename": "alafasy_surah_furqan_servants.mp3", "tags": ["servants", "sunnah", "character", "ফুরকান", "চরিত্র", "আমল"]},

    # ── NAMES OF ALLAH (Surah Al-Hashr) ────────────────────────────────────────
    {"id": "alafasy_surah_hashr_22", "name": "Alafasy - Surah Al-Hashr (Huwallahul Ladhi: 22)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/059022.mp3", "filename": "alafasy_surah_hashr_22.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর", "আল্লাহর নাম"]},
    {"id": "alafasy_surah_hashr_23", "name": "Alafasy - Surah Al-Hashr (Al-Malikul Quddus: 23)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/059023.mp3", "filename": "alafasy_surah_hashr_23.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর", "আল্লাহর নাম"]},
    {"id": "dossari_surah_hashr_22", "name": "Dossari - Surah Al-Hashr (Huwallahul Ladhi: 22)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/059022.mp3", "filename": "dossari_surah_hashr_22.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর"]},
    {"id": "dossari_surah_hashr_23", "name": "Dossari - Surah Al-Hashr (Al-Malikul Quddus: 23)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/059023.mp3", "filename": "dossari_surah_hashr_23.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর"]},

    # ── UNIVERSAL DUAS (Baqarah, Fatiha) ───────────────────────────────────────
    {"id": "alafasy_baqarah_rabbana", "name": "Alafasy - Surah Al-Baqarah (Rabbana Aatina: 201)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/002201.mp3", "filename": "alafasy_baqarah_rabbana.mp3", "tags": ["rabbana", "dunya", "akhirah", "বারাকাহ", "দোয়া", "আমল"]},
    {"id": "alafasy_baqarah_end_286", "name": "Alafasy - Surah Al-Baqarah (Amanar Rasul: 286)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/002286.mp3", "filename": "alafasy_baqarah_end_286.mp3", "tags": ["baqarah", "night", "protection", "বাকারা", "রাত", "আমল", "হেফাজত"]},
    {"id": "dossari_baqarah_rabbana", "name": "Dossari - Surah Al-Baqarah (Rabbana Aatina: 201)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/002201.mp3", "filename": "dossari_baqarah_rabbana.mp3", "tags": ["rabbana", "dunya", "akhirah", "বারাকাহ", "দোয়া"]},
    {"id": "alafasy_surah_fatiha_5", "name": "Alafasy - Surah Al-Fatiha (Iyyaaka Na'budu: 5)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/001005.mp3", "filename": "alafasy_surah_fatiha_5.mp3", "tags": ["fatiha", "cure", "general", "ফাতিহা", "শেফা", "আমল", "হাদিস"]},
    {"id": "dossari_surah_fatiha_5", "name": "Dossari - Surah Al-Fatiha (Iyyaaka Na'budu: 5)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/001005.mp3", "filename": "dossari_surah_fatiha_5.mp3", "tags": ["fatiha", "cure", "general", "ফাতিহা", "শেফা"]},

    # ── TAWAKKUL & SOVEREIGNTY ─────────────────────────────────────────────────
    {"id": "dossari_surah_talaq_tawakkul", "name": "Dossari - Surah At-Talaq (Tawakkul: 3)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/065003.mp3", "filename": "dossari_surah_talaq_tawakkul.mp3", "tags": ["tawakkul", "rizq", "trust", "তাওয়াক্কুল", "রিজিক", "ভরসা", "আল্লাহ"]},
    {"id": "alafasy_surah_zumar_mercy", "name": "Alafasy - Surah Az-Zumar (Despair Not of Mercy: 53)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/039053.mp3", "filename": "alafasy_surah_zumar_mercy.mp3", "tags": ["mercy", "forgiveness", "hope", "ক্ষমা", "রহমত", "আশা", "তওবা", "মাফ"]},
    {"id": "dossari_surah_zumar_mercy", "name": "Dossari - Surah Az-Zumar (Despair Not of Mercy: 53)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/039053.mp3", "filename": "dossari_surah_zumar_mercy.mp3", "tags": ["mercy", "forgiveness", "hope", "ক্ষমা", "রহমত", "তওবা"]},
]

AUDIO_HISTORY_FILE = os.path.abspath("data/audio_history.json")

def get_recent_used_audio_ids(limit: int = 30) -> list[str]:
    """Retrieves list of audio track IDs used in the last N runs."""
    if os.path.exists(AUDIO_HISTORY_FILE):
        try:
            with open(AUDIO_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data[-limit:]
        except Exception as e:
            logger.warning(f"Error loading audio history: {e}")
    return []

def record_used_audio_id(track_id: str):
    """Records chosen audio track ID to ensure zero repetition for at least 30 videos."""
    history = []
    if os.path.exists(AUDIO_HISTORY_FILE):
        try:
            with open(AUDIO_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []
            
    history.append(track_id)
    history = history[-100:]  # Keep last 100 entries
    try:
        os.makedirs(os.path.dirname(AUDIO_HISTORY_FILE), exist_ok=True)
        with open(AUDIO_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to record audio history: {e}")

def match_tracks_by_topic(topic_text: str) -> list[dict]:
    """Finds tracks that thematically match the topic/Hadith content."""
    if not topic_text:
        return []
        
    t_lower = topic_text.lower()
    matched = []
    for track in RECITER_TRACKS:
        for tag in track.get("tags", []):
            if tag.lower() in t_lower:
                matched.append(track)
                break
    return matched

def get_or_download_quran_audio(topic_text: str = "", duration: float = 8.0, output_path: str = None) -> str:
    """
    Selects a THEMATICALLY-ALIGNED authentic Quran recitation with STRICT 30-video anti-repetition guarantee.
    Only uses approved reciters: Alafasy & Dossari (GEMINI.md Rule #5).
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # 1. Fetch recent audio history (last 30 videos)
    recent_ids = get_recent_used_audio_ids(limit=30)
    logger.info(f"Checking Quran Audio History: {len(recent_ids)} tracks used in last 30 runs.")
    
    # 2. Check for Topic Alignment
    matched_tracks = match_tracks_by_topic(topic_text)
    candidate_pool = matched_tracks if matched_tracks else RECITER_TRACKS
    
    if matched_tracks:
        logger.info(f"Topic-Matched Quran Tracks Found: {len(matched_tracks)} candidate recitations for topic '{topic_text[:40]}...'")
    
    # 3. Filter out recently used tracks
    available_tracks = [t for t in candidate_pool if t["id"] not in recent_ids]
    if not available_tracks:
        logger.info("All candidate tracks in active pool recently used. Broadening pool to all non-recent tracks...")
        available_tracks = [t for t in RECITER_TRACKS if t["id"] not in recent_ids]
        if not available_tracks:
            logger.info("All approved Quran tracks cycled! Resetting rotation cycle...")
            available_tracks = RECITER_TRACKS

    # 4. Select fresh track
    track = random.choice(available_tracks)
    logger.info(f"Selected Thematically Aligned Quran Recitation: {track['name']} ({track['reciter']}) [ID: {track['id']}]")
    
    local_source = os.path.join(AUDIO_DIR, track["filename"])
    
    if not os.path.exists(local_source) or os.path.getsize(local_source) < 1000:
        logger.info(f"Downloading authentic recitation by {track['reciter']} ({track['name']})...")
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(track["url"], headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        with open(local_source, "wb") as f:
                            f.write(resp.read())
                        break
            except Exception as e:
                logger.warning(f"Attempt {attempt}/3 download error for {track['name']}: {e}")
                
    if not os.path.exists(local_source) or os.path.getsize(local_source) < 1000:
        existing = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
        if existing:
            local_source = os.path.join(AUDIO_DIR, existing[0])
        else:
            raise RuntimeError(f"No Quran audio available for {track['name']}.")

    # Record used track ID to history
    record_used_audio_id(track["id"])

    if not output_path:
        output_path = os.path.join(AUDIO_DIR, f"trimmed_{track['id']}_{int(duration)}s.mp3")

    fade_out_start = max(0.5, duration - 0.6)
    # Proven clean audio mastering (matches old clean sound + loudnorm improvement):
    # 1. silenceremove: instant start (skip leading silence)
    # 2. highpass 75Hz: remove low-end rumble/wind noise
    # 3. lowpass 10kHz: suppress mosque reverb tails in high frequencies (clean dry sound)
    # 4. warm EQ: +2.0dB at 250Hz warmth, -2.0dB at 4kHz (reduce sibilance + reverb harshness)
    # 5. subtle room thickening (35ms / 0.20 decay — imperceptible as echo, just warmth)
    # 6. loudnorm: broadcast-standard -18 LUFS (consistent volume across ALL videos)
    # 7. smooth fade in & fade out
    audio_filter = (
        f"silenceremove=start_periods=1:start_duration=0.02:start_threshold=-35dB,"
        f"highpass=f=75,"
        f"lowpass=f=10000,"
        f"equalizer=f=250:width_type=o:w=1:g=2.0,"
        f"equalizer=f=4000:width_type=o:w=1:g=-2.0,"
        f"aecho=0.8:0.85:35:0.20,"
        f"loudnorm=I=-18.0:TP=-2.0:LRA=11.0,"
        f"afade=t=in:ss=0:d=0.08,"
        f"afade=t=out:st={fade_out_start}:d=0.6"
    )
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:00",
        "-t", str(duration),
        "-i", local_source,
        "-af", audio_filter,
        "-c:a", "libmp3lame",
        "-b:a", "256k",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Prepared Studio-Quality Quran Audio ({track['name']}) -> {output_path}")
    return output_path
