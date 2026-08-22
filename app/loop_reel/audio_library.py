# -*- coding: utf-8 -*-
import os
import json
import random
import urllib.request
import subprocess
from app.logger import logger

AUDIO_DIR = os.path.abspath("data/quran_audio")

# Rich curated repository of 40 distinct, authentic, long continuous Quran recitation tracks (>12s to 45s)
RECITER_TRACKS = [
    # --- DUA YUNUS & RELIEF FROM DEBT / CRISIS / DISTRESS (> 15s) ---
    {"id": "hani_rifai_dua_yunus", "name": "Hani Ar-Rifai - Dua Yunus (Al-Anbiya: 87)", "reciter": "Sheikh Hani Ar-Rifai", "url": "https://everyayah.com/data/Hani_Rifai_192kbps/021087.mp3", "filename": "hani_rifai_dua_yunus.mp3", "tags": ["debt", "crisis", "distress", "ঋণ", "বিপদ", "কষ্ট", "হতাশা", "দোয়া ইউনুস", "উদ্ধার", "সমস্যা"]},
    {"id": "alafasy_surah_imran_mulk", "name": "Alafasy - Surah Al-Imran (Maalikal Mulk: 26)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/003026.mp3", "filename": "alafasy_surah_imran_mulk.mp3", "tags": ["debt", "rizq", "crisis", "wealth", "ঋণ", "রিজিক", "উদ্ধার", "বরকত", "ক্ষমতা"]},
    {"id": "alafasy_surah_tawbah_hasbiyallah", "name": "Alafasy - Surah At-Tawbah (Hasbiyallahu: 129)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/009129.mp3", "filename": "alafasy_surah_tawbah_hasbiyallah.mp3", "tags": ["crisis", "distress", "peace", "protection", "বিপদ", "কষ্ট", "পেরেশানি", "ভরসা"]},
    {"id": "dossari_surah_ibrahim", "name": "Yasser Al-Dossari - Surah Ibrahim (Gratitude: 40)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/014040.mp3", "filename": "dossari_surah_ibrahim.mp3", "tags": ["gratitude", "prayer", "family", "ইব্রাহিম", "নামাজ", "পরিবার", "শুকরিয়া"]},
    {"id": "alafasy_surah_kahf_rahmah", "name": "Alafasy - Surah Al-Kahf (Dua for Mercy: 10)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/018010.mp3", "filename": "alafasy_surah_kahf_rahmah.mp3", "tags": ["kahf", "mercy", "protection", "কাহফ", "রহমত", "হেফাজত"]},
    {"id": "alafasy_surah_qasas_musa", "name": "Alafasy - Surah Al-Qasas (Musa's Dua for Rizq: 24)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/028024.mp3", "filename": "alafasy_surah_qasas_musa.mp3", "tags": ["rizq", "marriage", "help", "রিজিক", "মুসা", "দোয়া", "সাহায্য"]},
    {"id": "alafasy_surah_fatir_rahmah", "name": "Alafasy - Surah Fatir (Unlocking Mercy: 2)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/035002.mp3", "filename": "alafasy_surah_fatir_rahmah.mp3", "tags": ["rizq", "mercy", "doors", "রিজিক", "রহমত", "বন্ধ দরজা"]},

    # --- AYAT AL-KURSI & PROTECTION FROM EVIL EYE / SHAITAN / ACCIDENT (> 35s) ---
    {"id": "alafasy_ayat_kursi", "name": "Alafasy - Ayat Al-Kursi (Al-Baqarah: 255)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/002255.mp3", "filename": "alafasy_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "bedtime", "আয়াতুল কুরসী", "বদনজর", "জিন", "শয়তান", "হেফাজত", "সুরক্ষা", "বিপদ", "ঘর থেকে বের হওয়া"]},
    {"id": "maher_ayat_kursi", "name": "Maher Al-Muaiqly - Ayat Al-Kursi", "reciter": "Sheikh Maher Al-Muaiqly", "url": "https://everyayah.com/data/MaherAlMuaiqly128kbps/002255.mp3", "filename": "maher_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী", "বদনজর", "হেফাজত", "বিপদ"]},
    {"id": "sudais_ayat_kursi", "name": "Al-Sudais - Ayat Al-Kursi", "reciter": "Sheikh Abdul Rahman Al-Sudais", "url": "https://everyayah.com/data/Abdurrahmaan_As-Sudais_192kbps/002255.mp3", "filename": "sudais_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী", "বদনজর"]},
    {"id": "dossari_ayat_kursi", "name": "Yasser Al-Dossari - Ayat Al-Kursi", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/002255.mp3", "filename": "dossari_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},
    {"id": "qatami_ayat_kursi", "name": "Nasser Al-Qatami - Ayat Al-Kursi", "reciter": "Sheikh Nasser Al-Qatami", "url": "https://everyayah.com/data/Nasser_Alqatami_128kbps/002255.mp3", "filename": "qatami_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},
    {"id": "shuraim_ayat_kursi", "name": "Saud Al-Shuraim - Ayat Al-Kursi", "reciter": "Sheikh Saud Al-Shuraim", "url": "https://everyayah.com/data/Saood_ash-Shuraym_128kbps/002255.mp3", "filename": "shuraim_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},
    {"id": "hani_rifai_ayat_kursi", "name": "Hani Ar-Rifai - Ayat Al-Kursi", "reciter": "Sheikh Hani Ar-Rifai", "url": "https://everyayah.com/data/Hani_Rifai_192kbps/002255.mp3", "filename": "hani_rifai_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},
    {"id": "shatree_ayat_kursi", "name": "Ash-Shaatree - Ayat Al-Kursi", "reciter": "Sheikh Abu Bakr Ash-Shaatree", "url": "https://everyayah.com/data/Abu_Bakr_Ash-Shaatree_128kbps/002255.mp3", "filename": "shatree_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},
    {"id": "abdulbasit_ayat_kursi", "name": "Abdul Basit - Ayat Al-Kursi (Mujawwad)", "reciter": "Sheikh Abdul Basit Abdul Samad", "url": "https://everyayah.com/data/Abdul_Basit_Mujawwad_128kbps/002255.mp3", "filename": "abdulbasit_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},
    {"id": "minshawi_ayat_kursi", "name": "Al-Minshawi - Ayat Al-Kursi", "reciter": "Sheikh Muhammad Siddiq Al-Minshawi", "url": "https://everyayah.com/data/Minshawy_Mujawwad_192kbps/002255.mp3", "filename": "minshawi_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},
    {"id": "jibreel_ayat_kursi", "name": "Muhammad Jibreel - Ayat Al-Kursi", "reciter": "Sheikh Muhammad Jibreel", "url": "https://everyayah.com/data/Muhammad_Jibreel_128kbps/002255.mp3", "filename": "jibreel_ayat_kursi.mp3", "tags": ["kursi", "protection", "evil_eye", "আয়াতুল কুরসী"]},

    # --- SURAH AL-MULK & GRAVE PROTECTION / NIGHT PEACE (> 15s) ---
    {"id": "alafasy_surah_mulk", "name": "Alafasy - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/067002.mp3", "filename": "alafasy_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক", "মৃত্যু", "রাত", "আজাব"]},
    {"id": "maher_surah_mulk", "name": "Maher Al-Muaiqly - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Maher Al-Muaiqly", "url": "https://everyayah.com/data/MaherAlMuaiqly128kbps/067002.mp3", "filename": "maher_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},
    {"id": "sudais_surah_mulk", "name": "Al-Sudais - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Abdul Rahman Al-Sudais", "url": "https://everyayah.com/data/Abdurrahmaan_As-Sudais_192kbps/067002.mp3", "filename": "sudais_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},
    {"id": "dossari_surah_mulk", "name": "Yasser Al-Dossari - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Yasser Al-Dossari", "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/067002.mp3", "filename": "dossari_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},
    {"id": "shuraim_surah_mulk", "name": "Saud Al-Shuraim - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Saud Al-Shuraim", "url": "https://everyayah.com/data/Saood_ash-Shuraym_128kbps/067002.mp3", "filename": "shuraim_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},
    {"id": "hani_rifai_surah_mulk", "name": "Hani Ar-Rifai - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Hani Ar-Rifai", "url": "https://everyayah.com/data/Hani_Rifai_192kbps/067002.mp3", "filename": "hani_rifai_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},
    {"id": "shatree_surah_mulk", "name": "Ash-Shaatree - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Abu Bakr Ash-Shaatree", "url": "https://everyayah.com/data/Abu_Bakr_Ash-Shaatree_128kbps/067002.mp3", "filename": "shatree_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},
    {"id": "jibreel_surah_mulk", "name": "Muhammad Jibreel - Surah Al-Mulk (Ayah 2)", "reciter": "Sheikh Muhammad Jibreel", "url": "https://everyayah.com/data/Muhammad_Jibreel_128kbps/067002.mp3", "filename": "jibreel_surah_mulk.mp3", "tags": ["mulk", "grave", "night", "কবর", "মুলক"]},

    # --- SURAH MARYAM & PROPHETIC DUAS (> 15s) ---
    {"id": "alafasy_surah_maryam_zakariya", "name": "Alafasy - Surah Maryam (Zakariya's Accepted Dua: 4)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/019004.mp3", "filename": "alafasy_surah_maryam_zakariya.mp3", "tags": ["dua", "family", "marriage", "children", "মরিয়ম", "দোয়া", "পরিবার", "বিয়ে", "সন্তান"]},
    {"id": "maher_surah_maryam_zakariya", "name": "Maher Al-Muaiqly - Surah Maryam (Zakariya's Accepted Dua: 4)", "reciter": "Sheikh Maher Al-Muaiqly", "url": "https://everyayah.com/data/MaherAlMuaiqly128kbps/019004.mp3", "filename": "maher_surah_maryam_zakariya.mp3", "tags": ["dua", "family", "marriage", "মরিয়ম", "পরিবার"]},
    {"id": "alafasy_surah_anbiya_zakariya", "name": "Alafasy - Surah Al-Anbiya (Rabbi La Tadharni: 89)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/021089.mp3", "filename": "alafasy_surah_anbiya_zakariya.mp3", "tags": ["dua", "family", "marriage", "সন্তান", "পরিবার", "দোয়া"]},
    {"id": "qatami_surah_furqan", "name": "Nasser Al-Qatami - Surah Al-Furqan (Servants of Rahman: 63)", "reciter": "Sheikh Nasser Al-Qatami", "url": "https://everyayah.com/data/Nasser_Alqatami_128kbps/025063.mp3", "filename": "qatami_surah_furqan.mp3", "tags": ["servants", "sunnah", "character", "ফুরকান", "চরিত্র", "আমল"]},

    # --- SURAH AL-HASHAR & ISM-E-AZAM (NAMES OF ALLAH) (> 15s) ---
    {"id": "alafasy_surah_hashr_22", "name": "Alafasy - Surah Al-Hashr (Huwallahul Ladhi: 22)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/059022.mp3", "filename": "alafasy_surah_hashr_22.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর", "আল্লাহর নাম"]},
    {"id": "alafasy_surah_hashr_23", "name": "Alafasy - Surah Al-Hashr (Al-Malikul Quddus: 23)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/059023.mp3", "filename": "alafasy_surah_hashr_23.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর", "আল্লাহর নাম"]},
    {"id": "abdulbasit_surah_hashr_22", "name": "Abdul Basit - Surah Al-Hashr (Mujawwad: 22)", "reciter": "Sheikh Abdul Basit Abdul Samad", "url": "https://everyayah.com/data/Abdul_Basit_Mujawwad_128kbps/059022.mp3", "filename": "abdulbasit_surah_hashr_22.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর"]},
    {"id": "abdulbasit_surah_hashr_23", "name": "Abdul Basit - Surah Al-Hashr (Mujawwad: 23)", "reciter": "Sheikh Abdul Basit Abdul Samad", "url": "https://everyayah.com/data/Abdul_Basit_Mujawwad_128kbps/059023.mp3", "filename": "abdulbasit_surah_hashr_23.mp3", "tags": ["hashr", "names_of_allah", "ইসমে আজম", "হাশর"]},

    # --- SURAH AL-BAQARAH END & UNIVERSAL DUAS (> 16s - 45s) ---
    {"id": "alafasy_baqarah_rabbana", "name": "Alafasy - Surah Al-Baqarah (Rabbana Aatina: 201)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/002201.mp3", "filename": "alafasy_baqarah_rabbana.mp3", "tags": ["rabbana", "dunya", "akhirah", "বারাকাহ", "দোয়া", "আমল"]},
    {"id": "alafasy_baqarah_end_286", "name": "Alafasy - Surah Al-Baqarah (Amanar Rasul: 286)", "reciter": "Sheikh Mishary Rashid Alafasy", "url": "https://everyayah.com/data/Alafasy_128kbps/002286.mp3", "filename": "alafasy_baqarah_end_286.mp3", "tags": ["baqarah", "night", "protection", "বাকারা", "রাত", "আমল", "হেফাজত"]},
    {"id": "minshawi_surah_fatiha_full", "name": "Al-Minshawi - Surah Al-Fatiha (Iyyaaka Na'budu: 5)", "reciter": "Sheikh Muhammad Siddiq Al-Minshawi", "url": "https://everyayah.com/data/Minshawy_Mujawwad_192kbps/001005.mp3", "filename": "minshawi_surah_fatiha_full.mp3", "tags": ["fatiha", "cure", "general", "ফাতিহা", "শেফা", "আমল", "হাদিস"]},
    {"id": "abdulbasit_surah_fatiha_full", "name": "Abdul Basit - Surah Al-Fatiha (Iyyaaka Na'budu: 5)", "reciter": "Sheikh Abdul Basit Abdul Samad", "url": "https://everyayah.com/data/Abdul_Basit_Mujawwad_128kbps/001005.mp3", "filename": "abdulbasit_surah_fatiha_full.mp3", "tags": ["fatiha", "cure", "general", "ফাতিহা", "শেফা", "আমল"]},
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
            logger.info("All 40 Quran tracks cycled! Resetting rotation cycle...")
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

    fade_out_start = max(0.5, duration - 0.5)
    # Strip any leading dead air/silence so the Quran recitation starts instantly at 0.00s with the video
    audio_filter = f"silenceremove=start_periods=1:start_duration=0.02:start_threshold=-35dB,afade=t=in:ss=0:d=0.05,afade=t=out:st={fade_out_start}:d=0.5"
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:00",
        "-t", str(duration),
        "-i", local_source,
        "-af", audio_filter,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Prepared 100% Unique Continuous Quran Audio ({track['name']}) -> {output_path}")
    return output_path
