# -*- coding: utf-8 -*-
import os
import random
import urllib.request
import subprocess
from app.logger import logger

AUDIO_DIR = os.path.abspath("data/quran_audio")

# Rich curated repository of authentic, soulful Quran recitations
RECITER_TRACKS = [
    {
        "name": "Alafasy_Ayat_Al_Kursi",
        "reciter": "Sheikh Mishary Rashid Alafasy",
        "url": "https://everyayah.com/data/Alafasy_128kbps/002255.mp3",
        "filename": "alafasy_ayat_kursi.mp3"
    },
    {
        "name": "Alafasy_Surah_Mulk",
        "reciter": "Sheikh Mishary Rashid Alafasy",
        "url": "https://everyayah.com/data/Alafasy_128kbps/067001.mp3",
        "filename": "alafasy_surah_mulk_1.mp3"
    },
    {
        "name": "Alafasy_Surah_Rahman",
        "reciter": "Sheikh Mishary Rashid Alafasy",
        "url": "https://everyayah.com/data/Alafasy_128kbps/055001.mp3",
        "filename": "alafasy_rahman.mp3"
    },
    {
        "name": "Alafasy_Surah_Fatiha",
        "reciter": "Sheikh Mishary Rashid Alafasy",
        "url": "https://everyayah.com/data/Alafasy_128kbps/001001.mp3",
        "filename": "alafasy_surah_fatiha.mp3"
    },
    {
        "name": "Sudais_Surah_Fatiha",
        "reciter": "Sheikh Abdul Rahman Al-Sudais",
        "url": "https://everyayah.com/data/Abdurrahmaan_As-Sudais_192kbps/001001.mp3",
        "filename": "sudais_surah_fatiha.mp3"
    },
    {
        "name": "Muaiqly_Ayat_Kursi",
        "reciter": "Sheikh Maher Al-Muaiqly",
        "url": "https://everyayah.com/data/MaherAlMuaiqly128kbps/002255.mp3",
        "filename": "muaiqly_ayat_kursi.mp3"
    },
    {
        "name": "Muaiqly_Surah_Mulk",
        "reciter": "Sheikh Maher Al-Muaiqly",
        "url": "https://everyayah.com/data/MaherAlMuaiqly128kbps/067001.mp3",
        "filename": "muaiqly_mulk.mp3"
    },
    {
        "name": "Dossari_Surah_Fatiha",
        "reciter": "Sheikh Yasser Al-Dossari",
        "url": "https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/001001.mp3",
        "filename": "dossari_fatiha.mp3"
    },
    {
        "name": "Qatami_Ayat_Kursi",
        "reciter": "Sheikh Nasser Al-Qatami",
        "url": "https://everyayah.com/data/Nasser_Alqatami_128kbps/002255.mp3",
        "filename": "qatami_ayat_kursi.mp3"
    }
]

def get_or_download_quran_audio(duration: float = 8.0, output_path: str = None) -> str:
    """Selects a soothing authentic Quran recitation, downloads if needed, and trims with soft fade."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    track = random.choice(RECITER_TRACKS)
    local_source = os.path.join(AUDIO_DIR, track["filename"])
    
    if not os.path.exists(local_source) or os.path.getsize(local_source) < 1000:
        logger.info(f"Downloading authentic recitation by {track['reciter']} ({track['name']})...")
        try:
            urllib.request.urlretrieve(track["url"], local_source)
        except Exception as e:
            logger.warning(f"Error downloading recitation {track['name']}: {e}")
            existing = [f for f in os.listdir(AUDIO_DIR) if f.endswith(".mp3")]
            if existing:
                local_source = os.path.join(AUDIO_DIR, existing[0])
            else:
                raise RuntimeError(f"No Quran audio available: {e}")

    if not output_path:
        output_path = os.path.join(AUDIO_DIR, f"trimmed_{int(duration)}s.mp3")

    fade_out_start = max(0.5, duration - 0.5)
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:00",
        "-t", str(duration),
        "-i", local_source,
        "-af", f"afade=t=in:ss=0:d=0.5,afade=t=out:st={fade_out_start}:d=0.5",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Prepared authentic Quran recitation audio ({track['reciter']} - {track['name']}) -> {output_path}")
    return output_path
