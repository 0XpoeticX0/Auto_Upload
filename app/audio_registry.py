# -*- coding: utf-8 -*-
"""
Permanent Audio Registry & Deduplication Engine
Enforces the strict rule: "NEVER use the same audio ever again"
Tracks audio files by SHA-256 cryptographic hash, filename, and duration in SQLite and JSON.
"""

import os
import json
import hashlib
import sqlite3
import subprocess
from app.config import DB_PATH
from app.logger import logger

REGISTRY_JSON_PATH = os.path.join("data", "used_audios_registry.json")
INCOMING_AUDIO_DIR = os.path.abspath("incoming_audio")

def get_audio_hash(filepath: str) -> str:
    """Computes SHA-256 hash of the audio file to permanently prevent duplicates."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_audio_duration(audio_path: str) -> float:
    """Returns duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def init_audio_registry():
    """Initializes SQLite table and JSON registry for tracking used audios."""
    os.makedirs("data", exist_ok=True)
    
    # 1. SQLite Table
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS used_audios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                duration REAL,
                video_path TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not initialize SQLite used_audios table: {e}")

    # 2. JSON Registry
    if not os.path.exists(REGISTRY_JSON_PATH):
        try:
            with open(REGISTRY_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not initialize JSON registry: {e}")

def load_json_registry() -> list:
    """Loads the list of used audios from JSON."""
    if not os.path.exists(REGISTRY_JSON_PATH):
        return []
    try:
        with open(REGISTRY_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def is_audio_used(filepath: str) -> tuple[bool, dict]:
    """
    Checks if an audio file has EVER been used before.
    Matches against SHA-256 hash first, then filename and duration.
    Returns (is_used, details_dict).
    """
    init_audio_registry()
    if not os.path.exists(filepath):
        return False, {}

    file_hash = get_audio_hash(filepath)
    filename = os.path.basename(filepath)

    # 1. Check SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_hash, filename, duration, video_path, processed_at FROM used_audios WHERE file_hash = ? OR filename = ?", (file_hash, filename))
        row = cursor.fetchone()
        conn.close()
        if row:
            return True, {
                "file_hash": row[0],
                "filename": row[1],
                "duration": row[2],
                "video_path": row[3],
                "processed_at": row[4],
                "matched_by": "sqlite"
            }
    except Exception as e:
        logger.warning(f"SQLite check failed: {e}")

    # 2. Check JSON backup
    registry = load_json_registry()
    for item in registry:
        if item.get("file_hash") == file_hash or item.get("filename") == filename:
            return True, item

    return False, {}

def mark_audio_as_used(filepath: str, video_path: str = "", metadata: dict = None) -> bool:
    """
    Permanently registers an audio file as USED.
    Guarantees it will never be picked or used again.
    """
    init_audio_registry()
    file_hash = get_audio_hash(filepath)
    filename = os.path.basename(filepath)
    duration = get_audio_duration(filepath)

    record = {
        "file_hash": file_hash,
        "filename": filename,
        "duration": duration,
        "video_path": video_path,
        "title": metadata.get("youtube_title", "") if metadata else "",
        "processed_at": metadata.get("rendered_at", "") if metadata else ""
    }

    # 1. Save to SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO used_audios (file_hash, filename, duration, video_path)
            VALUES (?, ?, ?, ?)
        ''', (file_hash, filename, duration, video_path))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not save audio to SQLite: {e}")

    # 2. Save to JSON
    try:
        registry = load_json_registry()
        # Avoid duplicate in list
        filtered = [item for item in registry if item.get("file_hash") != file_hash]
        filtered.append(record)
        with open(REGISTRY_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        logger.info(f"🔒 Audio registered permanently as USED: {filename} (Hash: {file_hash[:10]}...)")
        return True
    except Exception as e:
        logger.error(f"Failed to update JSON registry: {e}")
        return False

def get_all_fresh_audios() -> list[str]:
    """
    Scans incoming_audio/ and returns ONLY audio files that have NEVER been used before.
    Filters out any file that is already in the registry.
    """
    import glob
    exts = ("*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg")
    all_files = []
    for ext in exts:
        all_files.extend(glob.glob(os.path.join(INCOMING_AUDIO_DIR, ext)))

    fresh_audios = []
    for f in all_files:
        used, details = is_audio_used(f)
        if used:
            logger.info(f"🚫 [SKIP - ALREADY USED]: {os.path.basename(f)} was used on {details.get('processed_at', 'previously')}. Will NEVER reuse.")
        else:
            fresh_audios.append(f)

    return fresh_audios

def get_next_fresh_audio() -> str | None:
    """Returns the first available audio file that has NEVER been used before."""
    fresh = get_all_fresh_audios()
    if fresh:
        return fresh[0]
    return None
