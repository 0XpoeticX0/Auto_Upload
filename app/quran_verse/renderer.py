# -*- coding: utf-8 -*-
"""
Quran Video Renderer (1080x1920 60FPS).
Generates cinematic vertical video with centered Bengali translation subtitles in the middle,
synced per-Ayah transitions, Arabic Uthmani text, and reciter branding.
"""

import os
import re
import subprocess
from app.logger import logger
from app.quality.vision_guardian import generate_verified_human_free_background, get_certified_safe_fallback

GOLD_COLOR = "&H002BD5FF&"
WHITE_COLOR = "&H00FFFFFF&"
CYAN_COLOR = "&H00FFFF00&"

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_RESHAPER = True
except ImportError:
    HAS_ARABIC_RESHAPER = False

def format_arabic_for_ass(text: str) -> str:
    """Properly connects and aligns RTL Arabic text for libass rendering."""
    if not text:
        return ""
    if HAS_ARABIC_RESHAPER:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    return text

def format_ass_time(seconds: float) -> str:
    """Formats float seconds to ASS timestamp (H:MM:SS.cs)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

def to_bangla_digits(text: str) -> str:
    """Converts standard digits to Bengali numerals."""
    bn_map = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}
    return "".join(bn_map.get(ch, ch) for ch in str(text))

def wrap_text(text: str, words_per_line: int = 5) -> str:
    """Wraps text into clean balanced lines for subtitle rendering."""
    if not text:
        return ""
    words = text.strip().split()
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i:i + words_per_line]))
    return r"\N".join(lines)

def format_bengali_subtitles_for_ass(bn_raw: str, words_per_line: int = 5) -> str:
    """
    Formats Bengali Quran translation subtitles with high-visibility styling:
    - Preserves 100% of the authentic translation words without omitting or altering any content.
    - The text between ( ) is styled in luminous Royal Gold (&H002BD5FF&) at font size \\fs46
      so anyone looking at the screen can see and distinguish it clearly at a single glance.
    - The main verse text outside ( ) is displayed in bold, high-contrast White (\\fs58).
    """
    if not bn_raw:
        return ""

    text = bn_raw.strip()

    # Wrap lines cleanly (5 words per line) preserving all words
    words = text.split()
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i:i + words_per_line]))
    wrapped = r"\N".join(lines)

    # Highlight all text between ( ) in luminous Gold & distinct font size
    # GOLD_COLOR is &H002BD5FF&, WHITE_COLOR is &H00FFFFFF&
    styled = re.sub(
        r'([\(\（][^\)\）]+[\)\）])',
        r'{\\c' + GOLD_COLOR + r'\\fs46}\1{\\c' + WHITE_COLOR + r'\\fs58}',
        wrapped
    )

    return f"“{styled}”"

def build_quran_ass_subtitles(verse_data: dict, audio_data: dict, ass_path: str):
    """
    Builds an advanced ASS subtitle file with:
    - Top Surah & Ayah Badge (Bengali numerals)
    - Arabic Uthmani text with proper cursive shaping & Tashkeel
    - Centered, large, high-contrast Bengali translation subtitle in the middle
      with golden highlight on parenthetical context for instant readability
    - Bottom Reciter Credit & Save/Share CTA
    """
    surah_name = verse_data["surah_name_bn"]
    range_str = to_bangla_digits(verse_data["verse_range_str"])
    reciter_name = audio_data["reciter"]["name_bn"]
    total_dur = audio_data["total_duration"]
    ayah_timings = audio_data["ayah_timings"]

    top_badge_text = f"✦ {surah_name} • আয়াত {range_str} ✦"
    reciter_text = f"🎙️ তিলাওয়াত: {reciter_name}"
    cta_text = "🔖 নিয়মিত তিলাওয়াত শোনার জন্য Save ও Share করুন 🤲"

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopBadge,Noto Sans Bengali,42,{GOLD_COLOR},&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,3.5,2.0,8,60,60,200,1
Style: ArabicVerse,Traditional Arabic,56,&H00E8FFFF&,&H000000FF,&H00000000,&HD0000000,-1,0,0,0,100,100,1,0,1,4.5,3.0,5,80,80,180,1
Style: BengaliCenter,Noto Sans Bengali,58,{WHITE_COLOR},&H000000FF,&H00000000,&HE0000000,-1,0,0,0,100,100,0,0,1,5.0,3.5,5,70,70,0,1
Style: ReciterBottom,Noto Sans Bengali,34,{GOLD_COLOR},&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,1,3.0,2.0,2,60,60,340,1
Style: DawahBottom,Noto Sans Bengali,28,{WHITE_COLOR},&H000000FF,&H00000000,&HB0000000,0,0,0,0,100,100,0,0,1,2.5,1.5,2,60,60,270,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    total_str = format_ass_time(total_dur)

    # Permanent Static Elements throughout the video
    ass_content += f"Dialogue: 0,0:00:00.00,{total_str},TopBadge,,0,0,0,,{top_badge_text}\n"
    ass_content += f"Dialogue: 0,0:00:00.00,{total_str},ReciterBottom,,0,0,0,,{reciter_text}\n"
    ass_content += f"Dialogue: 0,0:00:00.00,{total_str},DawahBottom,,0,0,0,,{cta_text}\n"

    # Dynamic Per-Ayah Synchronized Transitions
    for timing in ayah_timings:
        start_str = format_ass_time(timing["start"])
        end_str = format_ass_time(timing["end"])

        ar_raw = timing.get("arabic", "").strip()
        # Shape Arabic text properly with cursive connections and RTL ordering
        ar_shaped = format_arabic_for_ass(ar_raw)
        ar_clean = wrap_text(ar_shaped, words_per_line=5)

        bn_raw = timing.get("bengali", "").strip()
        bn_clean = format_bengali_subtitles_for_ass(bn_raw, words_per_line=5)

        # Arabic text placed above center
        ass_content += f"Dialogue: 1,{start_str},{end_str},ArabicVerse,,0,0,160,,{{\\pos(540,820)}}{ar_clean}\n"

        # Prominent Bengali Translation placed right in the CENTER
        ass_content += f"Dialogue: 2,{start_str},{end_str},BengaliCenter,,0,0,0,,{{\\pos(540,1080)}}{bn_clean}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    logger.info(f"Generated Quran ASS subtitles at: {ass_path}")

def render_quran_verse_video(verse_data: dict, audio_data: dict, output_dir: str = "data/output") -> str:
    """
    Renders end-to-end 60 FPS 1080x1920 vertical video with centered subtitles.
    Returns path to rendered MP4 video.
    """
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join("data", "temp", "quran_render_run")
    os.makedirs(temp_dir, exist_ok=True)

    surah = verse_data["surah"]
    start = verse_data["ayah_start"]
    end = verse_data["ayah_end"]
    reciter_id = verse_data.get("reciter_id", "alafasy")

    # 1. Background Image with Vision Guardian
    bg_path = os.path.join(temp_dir, "quran_bg.jpg")
    visual_prompt = (
        "vertical 9:16, inside a majestic ancient Andalusian Islamic sanctuary, "
        "intricate Moorish geometric arched wooden windows, soft morning dawn golden light rays "
        "illuminating an antique carved wooden rehal holding the Holy Quran on an emerald velvet prayer rug, "
        "floating glowing dust particles in cinematic god rays, photorealistic 8k, architectural digest, "
        "high aesthetic, deeply spiritual, no people, no living beings"
    )

    downloaded = generate_verified_human_free_background(visual_prompt, bg_path, max_checks=2)
    if not downloaded or not os.path.exists(bg_path) or os.path.getsize(bg_path) < 5000:
        logger.warning("[Vision Guardian] Deploying certified safe fallback background.")
        get_certified_safe_fallback(bg_path)

    # 2. Build Subtitles
    ass_path = os.path.join(temp_dir, "quran_subtitles.ass")
    build_quran_ass_subtitles(verse_data, audio_data, ass_path)

    # 3. Output Video File
    out_filename = f"Quran_Surah_{surah}_{start}_{end}_{reciter_id}.mp4"
    final_output_path = os.path.join(output_dir, out_filename)

    audio_file = audio_data["audio_path"]
    total_dur = audio_data["total_duration"]

    # Normalize paths for FFmpeg filter on Windows
    safe_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")

    # 4. FFmpeg Video Filter:
    # Scale & crop to 1080x1920, apply smooth 1.15x slow zoompan, subtle dark vignette for text readability, and burn ASS subtitles
    vf_filter = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0003,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(total_dur*60)}:s=1080x1920:fps=60,"
        f"colorlevels=rimin=0.03:gimin=0.03:bimin=0.03:rimax=0.92:gimax=0.92:bimax=0.92,"
        f"ass='{safe_ass_path}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", bg_path,
        "-i", audio_file,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(total_dur),
        "-pix_fmt", "yuv420p",
        final_output_path
    ]

    logger.info(f"Rendering Quran video: {final_output_path} ({total_dur:.1f}s, 60fps)...")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        logger.error(f"FFmpeg render error: {res.stderr[-500:]}")
        raise RuntimeError(f"FFmpeg rendering failed with code {res.returncode}")

    logger.info(f"Quran video successfully rendered at: {final_output_path}")
    return final_output_path
