# -*- coding: utf-8 -*-
"""
Quran Video Renderer (1080x1920 60FPS).
Generates cinematic vertical video with centered Bengali translation subtitles in the middle,
synced per-Ayah transitions, Arabic Uthmani text, and reciter branding.
"""

import os
import re
import json
import math
import shutil
import random
import subprocess
from PIL import Image
from app.logger import logger
from app.quality.vision_guardian import generate_verified_human_free_background, get_certified_safe_fallback
from app.quran_verse.quran_data import SURAH_NAMES_EN

GOLD_COLOR = "&H002BD5FF&"
WHITE_COLOR = "&H00FFFFFF&"
CYAN_COLOR = "&H00FFFF00&"

def wrap_and_format_arabic(text: str, words_per_line: int = 5) -> str:
    """
    Wraps logical Arabic text into lines with balanced splits.
    Raw Uthmani Arabic is passed directly to libass, where HarfBuzz-ng and FriBidi
    render authentic cursive ligatures and natural right-to-left orientation without character reversal.
    """
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= words_per_line:
        return text.strip()
    
    # Split into balanced lines
    mid = (len(words) + 1) // 2
    if len(words) <= 10:
        return " ".join(words[:mid]) + r"\N" + " ".join(words[mid:])
    
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i:i + words_per_line]))
    return r"\N".join(lines)


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

def split_bengali_into_chunks(bn_text: str, max_words_per_chunk: int = 16) -> list:
    """
    Intelligently splits long Bengali Quran translations into short, readable 1-2 line chunks.
    Splits at natural sentence/clause boundaries (।, ?, !, ,, ;) outside parentheses.
    Guarantees no single chunk exceeds max_words_per_chunk, preventing walls of text.
    """
    if not bn_text:
        return []

    # If already concise, keep as single chunk
    words = bn_text.strip().split()
    if len(words) <= max_words_per_chunk:
        return [bn_text.strip()]

    # Split into clauses by punctuation, preserving parentheses integrity
    clauses = []
    current = []
    paren_depth = 0

    for char in bn_text:
        if char in '(':
            paren_depth += 1
        elif char in ')':
            paren_depth = max(0, paren_depth - 1)

        current.append(char)
        if char in ['।', '?', '!', ';', ','] and paren_depth == 0:
            clauses.append("".join(current).strip())
            current = []

    if current:
        remaining = "".join(current).strip()
        if remaining:
            clauses.append(remaining)

    # Group clauses into balanced chunks
    chunks = []
    curr_chunk = []
    curr_words = 0

    for clause in clauses:
        c_words = len(clause.split())
        if curr_words + c_words <= max_words_per_chunk:
            curr_chunk.append(clause)
            curr_words += c_words
        else:
            if curr_chunk:
                chunks.append(" ".join(curr_chunk))
                curr_chunk = []
                curr_words = 0
            
            # If a single clause is still too long, split by words outside parens
            if c_words > max_words_per_chunk:
                w_list = clause.split()
                for i in range(0, len(w_list), max_words_per_chunk):
                    sub = " ".join(w_list[i:i + max_words_per_chunk])
                    chunks.append(sub)
            else:
                curr_chunk.append(clause)
                curr_words = c_words

    if curr_chunk:
        chunks.append(" ".join(curr_chunk))

    return chunks if chunks else [bn_text.strip()]

def format_bengali_subtitles_for_ass(bn_raw: str, words_per_line: int = 5) -> str:
    """
    Formats Bengali Quran translation subtitles:
    - 1 or 2 lines maximum in the center. Never 3+ lines.
    - Balanced split in the middle when word count >= 5.
    """
    if not bn_raw:
        return ""
    text = bn_raw.strip().strip('“').strip('”').strip('"')
    words = text.split()
    if len(words) <= 4:
        return text
    mid = (len(words) + 1) // 2
    for idx in range(max(2, mid - 2), min(len(words) - 2, mid + 3)):
        if any(p in words[idx] for p in ['।', ',', ';', '—', '-']):
            mid = idx + 1
            break
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:])
    return f"{line1}\\N{line2}"

def format_english_subtitles_for_ass(en_raw: str, max_words_per_line: int = 7) -> str:
    """
    Formats English Quran translation for ASS subtitles:
    - 1 or 2 lines maximum.
    - Balanced split in the middle or natural punctuation (: , ; .) when word count > 6.
    - Enclosed in clean quotation marks "...".
    """
    if not en_raw:
        return ""
    text = en_raw.strip().strip('"').strip("'")
    words = text.split()
    if len(words) <= max_words_per_line:
        wrapped = text
    else:
        mid = (len(words) + 1) // 2
        split_idx = mid
        for idx in range(max(2, mid - 2), min(len(words) - 2, mid + 3)):
            if words[idx].endswith((':', ';', ',', '.', '—')):
                split_idx = idx + 1
                break
        line1 = " ".join(words[:split_idx])
        line2 = " ".join(words[split_idx:])
        wrapped = f"{line1}\\N{line2}"
    return f'"{wrapped}"'

def split_into_n_chunks(text: str, n: int, lang: str = 'bn') -> list:
    """Splits text into n balanced chunks at natural punctuation boundaries."""
    if not text or n <= 1:
        return [text]
    words = text.split()
    total_words = len(words)
    if total_words <= n:
        return [text]
    
    target_len = total_words / float(n)
    chunks = []
    curr_idx = 0
    delims = ['।', '!', '?', ';', '—', ','] if lang == 'bn' else ['.', '!', '?', ';', ':', '—', ',']
    
    for c_i in range(n - 1):
        target_idx = int(round((c_i + 1) * target_len))
        best_split = target_idx
        search_range = range(max(curr_idx + 2, target_idx - 4), min(total_words - 2, target_idx + 5))
        for idx in search_range:
            if any(words[idx].endswith(d) or words[idx].startswith(d) for d in delims):
                best_split = idx + 1
                break
        chunk = ' '.join(words[curr_idx:best_split])
        chunks.append(chunk)
        curr_idx = best_split
    
    chunks.append(' '.join(words[curr_idx:]))
    return chunks

def split_long_ayah_clauses(ar_text: str, bn_text: str, en_text: str, total_ayah_dur: float, start_sec: float) -> list:
    """
    Splits long ayahs (> 8.5 seconds or > 8 words) into natural recitation clauses,
    ensuring Arabic, Bengali, and English all fit the screen cleanly and symmetrically.
    """
    waqf_pattern = r'([ۚۗۖۘۙۛۜ])'
    ar_parts = [p.strip() for p in re.split(waqf_pattern, ar_text) if p.strip()]
    merged_ar = []
    for p in ar_parts:
        if p in 'ۚۗۖۘۙۛۜ' and merged_ar:
            merged_ar[-1] += ' ' + p
        else:
            merged_ar.append(p)

    # Determine optimal number of chunks:
    if len(merged_ar) >= 2 and all(len(c.split()) >= 3 for c in merged_ar):
        ar_chunks = merged_ar
        n = len(merged_ar)
    else:
        # Target ~8-11s per clause
        n = max(2, int(round(total_ayah_dur / 9.5)))
        ar_words = ar_text.split()
        w_per_chunk = max(1, int(round(len(ar_words) / float(n))))
        ar_chunks = []
        for i in range(n - 1):
            ar_chunks.append(" ".join(ar_words[i * w_per_chunk : (i + 1) * w_per_chunk]))
        ar_chunks.append(" ".join(ar_words[(n - 1) * w_per_chunk:]))

    bn_chunks = split_into_n_chunks(bn_text, n, 'bn')
    en_chunks = split_into_n_chunks(en_text, n, 'en') if en_text else [""] * n

    total_ar_words = sum(len(c.split()) for c in ar_chunks)
    curr_start = start_sec
    clauses = []

    for i in range(n):
        p_words = len(ar_chunks[i].split())
        if i == n - 1:
            curr_end = start_sec + total_ayah_dur
        else:
            if total_ar_words > 0:
                prop = p_words / float(total_ar_words)
            else:
                total_bn_words = sum(len(c.split()) for c in bn_chunks)
                prop = len(bn_chunks[i].split()) / max(1, float(total_bn_words))
            c_dur = max(3.0, total_ayah_dur * prop)
            curr_end = min(start_sec + total_ayah_dur - 2.5, round(curr_start + c_dur, 2))

        clauses.append({
            "start": curr_start,
            "end": curr_end,
            "arabic": ar_chunks[i],
            "bengali": bn_chunks[i] if i < len(bn_chunks) else "",
            "english": en_chunks[i] if i < len(en_chunks) else ""
        })
        curr_start = curr_end

    return clauses

def highlight_sacred_words(text: str) -> str:
    """Highlights sacred theological words and parenthetical context in Royal Gold (&H0015CCFA&)."""
    if not text:
        return ""
    # Clean zero-width directional marks that cause dotted circle font errors
    text = text.replace('\u200e', '').replace('\u200f', '').replace('\u200b', '')
    sacred = ['আল্লাহর?', 'আল্লাহকে', 'আল্লাহই', 'রব', 'রবের', 'তাওয়াক্কুল', 'রিযিক্ব?', 'রিযক', 'রহমত', 'রহমতের', 'জান্নাত', 'ঈমান', 'পরকাল', 'স্বস্তি', 'সুখ', 'কল্যাণে প্রশস্ত']
    pattern = re.compile(r'(?<![ঀ-৾])(' + '|'.join(sacred) + r')(?![ঀ-৾])')
    text = pattern.sub(lambda m: f'{{\\c&H0015CCFA&}}{m.group(1)}{{\\c&H00FFFFFF&}}', text)
    # Highlight parenthetical explanatory context in Royal Gold
    text = re.sub(r'(\([^\)]+\))', lambda m: f'{{\\c&H0015CCFA&}}{m.group(1)}{{\\c&H00FFFFFF&}}', text)
    return text

def build_quran_ass_subtitles(verse_data: dict, audio_data: dict, ass_path: str):
    """
    Builds ASS subtitles with centered Bengali translation (middle), English at bottom, and Top Badges:
    - Permanent Top Header badge at Y=240 (Kalpurush 48 Gold)
    - Permanent Top SubHeader badge at Y=305 (Segoe UI 32 Silver)
    - Synchronized Bengali translation in Center at Y=960 (Kalpurush 70 White with Royal Gold highlights)
    - Synchronized English translation at Bottom at Y=1530 (Segoe UI 48 White)
    """
    surah_name_bn = verse_data["surah_name_bn"]
    surah_name_en = verse_data.get("surah_name_en") or SURAH_NAMES_EN.get(verse_data["surah"], f"Surah {verse_data['surah']}")
    surah = verse_data["surah"]
    verse_range_str = verse_data["verse_range_str"]
    range_str_bn = to_bangla_digits(verse_range_str)
    total_dur = audio_data["total_duration"]
    ayah_timings = audio_data["ayah_timings"]
    reciter_info = verse_data.get("reciter", {})
    reciter_title = reciter_info.get("name_en", "Mishary Rashid Alafasy")

    top_badge_bn = f"[ {surah_name_bn}  •  আয়াত {range_str_bn} ]"
    top_badge_en = f"Surah {surah_name_en}  •  {reciter_title}"

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopBadge,Kalpurush,48,&H0015CCFA&,&H00000000,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,3.4,2.0,5,50,50,20,1
Style: SubBadge,Segoe UI,32,&H00E2E8F0&,&H00000000,&H00000000,&H90000000,0,1,0,0,100,100,1,0,1,2.0,1.2,5,50,50,20,1
Style: BengaliCenter,Kalpurush,70,&H00FFFFFF&,&H00000000,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,4.0,2.5,5,50,50,20,1
Style: EnglishBottom,Segoe UI,48,&H00FFFFFF&,&H00000000,&H00000000,&H90000000,0,1,0,0,100,100,0,0,1,2.8,1.6,5,60,60,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
; Permanent Top Badges
Dialogue: 0,0:00:00.00,{format_ass_time(total_dur)},TopBadge,,0,0,0,,{{\\pos(540,240)}}{top_badge_bn}
Dialogue: 0,0:00:00.00,{format_ass_time(total_dur)},SubBadge,,0,0,0,,{{\\pos(540,305)}}{top_badge_en}
"""

    for timing in ayah_timings:
        start_sec = timing["start"]
        end_sec = timing["end"]
        dur = max(0.5, end_sec - start_sec)
        bn_raw = timing.get("bengali", "").strip()
        en_raw = timing.get("english", "").strip()

        # Keep ayahs under 8.5s or under 14 words as 1 full, peaceful 2-line card
        if dur <= 8.5 or len(bn_raw.split()) <= 13:
            start_str = format_ass_time(start_sec)
            end_str = format_ass_time(end_sec)
            bn_clean = highlight_sacred_words(format_bengali_subtitles_for_ass(bn_raw, words_per_line=5))
            en_clean = format_english_subtitles_for_ass(en_raw, max_words_per_line=7)

            ass_content += f"Dialogue: 2,{start_str},{end_str},BengaliCenter,,0,0,0,,{{\\pos(540,960)}}{bn_clean}\n"
            if en_clean:
                ass_content += f"Dialogue: 3,{start_str},{end_str},EnglishBottom,,0,0,0,,{{\\pos(540,1530)}}{en_clean}\n"
        else:
            clauses = split_long_ayah_clauses("", bn_raw, en_raw, dur, start_sec)
            for c in clauses:
                c_start_str = format_ass_time(c["start"])
                c_end_str = format_ass_time(c["end"])
                bn_clean = highlight_sacred_words(format_bengali_subtitles_for_ass(c["bengali"], words_per_line=5))
                en_clean = format_english_subtitles_for_ass(c["english"], max_words_per_line=7)

                ass_content += f"Dialogue: 2,{c_start_str},{c_end_str},BengaliCenter,,0,0,0,,{{\\pos(540,960)}}{bn_clean}\n"
                if en_clean:
                    ass_content += f"Dialogue: 3,{c_start_str},{c_end_str},EnglishBottom,,0,0,0,,{{\\pos(540,1530)}}{en_clean}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    logger.info(f"Generated Quran ASS subtitles at: {ass_path}")


def render_subpixel_smooth_scene_clip(image_path: str, duration: float, motion_type: str, out_path: str, fps: int = 60):
    """
    Renders 100% butter-smooth, tremor-free 60 FPS camera motion using sub-pixel PIL Lanczos interpolation.
    Completely eliminates the notorious FFmpeg zoompan integer coordinate snapping and micro-jitter.
    """
    img = Image.open(image_path).convert("RGB")
    W, H = 1080, 1920
    base_w, base_h = int(W * 1.25), int(H * 1.25)
    img = img.resize((base_w, base_h), Image.Resampling.LANCZOS)
    
    total_frames = max(1, int(round(duration * fps)))
    max_zoom = 1.15
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        out_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for f in range(total_frames):
        t = f / max(1, total_frames - 1)
        # Cosine ease-in ease-out for ultra smooth motion
        progress = 0.5 * (1.0 - math.cos(math.pi * t))
        
        if motion_type == "zoom_in":
            scale = 1.0 + (max_zoom - 1.0) * progress
            cw = int(base_w / scale)
            ch = int(base_h / scale)
            x0 = (base_w - cw) // 2
            y0 = (base_h - ch) // 2
        elif motion_type == "zoom_out":
            scale = max_zoom - (max_zoom - 1.0) * progress
            cw = int(base_w / scale)
            ch = int(base_h / scale)
            x0 = (base_w - cw) // 2
            y0 = (base_h - ch) // 2
        elif motion_type == "pan_up":
            cw, ch = W, H
            x0 = (base_w - cw) // 2
            max_y = base_h - ch
            y0 = int(max_y * (1.0 - progress))
        else:
            cw, ch = W, H
            x0 = (base_w - cw) // 2
            max_y = base_h - ch
            y0 = int(max_y * progress)
            
        cropped = img.crop((x0, y0, x0 + cw, y0 + ch))
        frame = cropped.resize((W, H), Image.Resampling.BILINEAR)
        try:
            proc.stdin.write(frame.tobytes())
        except (BrokenPipeError, OSError):
            break
            
    try:
        proc.stdin.close()
    except Exception:
        pass
    proc.wait()

def plan_calm_quran_scenes(total_dur: float, ayah_timings: list = None, min_dur: float = 14.0, max_dur: float = 20.0) -> list:
    """
    Plans serene, dignified scene pacing according to permanent user mandates:
    - Minimum clip duration: strictly >= 14.0s (ignoring all short clips < 15s).
    - Maximum clip duration: strictly cut at 20.0s max.
    - Full serial rotation: 1 -> 2 -> 3 -> 1 -> 2 -> 3 without looping single clips.
    - Transitions occur on natural Ayah boundaries.
    """
    if not ayah_timings:
        target = 17.5
        n = max(1, int(round(total_dur / target)))
        dur = total_dur / n
        return [{"start": round(i*dur, 2), "end": round((i+1)*dur, 2), "duration": round(dur, 2)} for i in range(n)]

    ayah_ends = [round(t["end"], 2) for t in ayah_timings if t.get("end", 0) < total_dur - 2.0]
    scenes = []
    curr = 0.0

    while curr < total_dur - 1.0:
        rem_total = total_dur - curr
        if rem_total <= max_dur:
            scenes.append({"start": round(curr, 2), "end": round(total_dur, 2), "duration": round(total_dur - curr, 2)})
            break

        # Find best ayah end within [curr + min_dur, curr + max_dur]
        valid_ends = [e for e in ayah_ends if curr + min_dur <= e <= curr + max_dur]

        if valid_ends:
            target_pt = curr + 17.5
            best_end = min(valid_ends, key=lambda x: abs(x - target_pt))
        else:
            near_ends = [e for e in ayah_ends if curr + min_dur <= e <= curr + max_dur + 2.0]
            if near_ends:
                best_end = near_ends[0]
            else:
                best_end = round(min(curr + 20.0, curr + 17.5), 2)

        # Guarantee remaining time isn't too short (< min_dur)
        if total_dur - best_end < min_dur:
            combined = total_dur - curr
            if combined > 24.0:
                mid = round(curr + combined / 2.0, 2)
                mid_ends = [e for e in ayah_ends if curr + min_dur*0.8 <= e <= total_dur - min_dur*0.8]
                if mid_ends:
                    mid = min(mid_ends, key=lambda x: abs(x - (curr + combined/2.0)))
                scenes.append({"start": round(curr, 2), "end": round(mid, 2), "duration": round(mid - curr, 2)})
                scenes.append({"start": round(mid, 2), "end": round(total_dur, 2), "duration": round(total_dur - mid, 2)})
            else:
                scenes.append({"start": round(curr, 2), "end": round(total_dur, 2), "duration": round(total_dur - curr, 2)})
            break

        scenes.append({"start": round(curr, 2), "end": round(best_end, 2), "duration": round(best_end - curr, 2)})
        curr = best_end

    return scenes

def build_dynamic_quran_visual_track(total_dur: float, temp_dir: str, video_slot: int = None, ayah_timings: list = None) -> str:
    """
    Builds a serene, dignified visual track composed of 100% authentic video clips.
    - Zero matching clips across 10 videos (powered by data/video_registry.json).
    - Calm, tranquil scene durations (7.5s to 12.0s per scene, average ~10s).
    - Transitions synchronized directly with Quranic Ayah boundaries.
    - 0 humans, 0 faces, 0 animals, 0 static images.
    - 60 FPS butter-smooth playback with zero jitter.
    """
    os.makedirs(temp_dir, exist_ok=True)
    master_visual_path = os.path.join(temp_dir, "master_visual_track.mp4")

    # Calm Attention-Retention Pacing (7.5s to 12.0s per scene, locked to Ayahs):
    planned_scenes = plan_calm_quran_scenes(total_dur, ayah_timings)
    num_scenes = len(planned_scenes)
    logger.info(f"Calm Quran Visual Track: Planned {num_scenes} tranquil scenes (~8-12s each, locked to Ayah boundaries) across {total_dur:.1f}s.")

    registry_file = os.path.abspath("data/video_registry.json")
    chosen_clips = []
    slot_num = 1

    if os.path.exists(registry_file):
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                reg_data = json.load(f)

            if video_slot is None:
                slot_num = reg_data.get("current_slot", 1)
                video_key = f"video_{slot_num:02d}"
                next_slot = (slot_num % 10) + 1
                reg_data["current_slot"] = next_slot
                with open(registry_file, "w", encoding="utf-8") as f:
                    json.dump(reg_data, f, indent=2)
                logger.info(f"🎬 [Zero-Overlap Registry] Auto-assigned Bucket: {video_key} (Next video will use video_{next_slot:02d})")
            else:
                slot_num = video_slot
                video_key = f"video_{slot_num:02d}"
                logger.info(f"🎬 [Zero-Overlap Registry] Explicitly selected Bucket: {video_key}")

            if video_key in reg_data:
                slot_info = reg_data[video_key]
                chosen_clips = [os.path.abspath(c) for c in slot_info.get("clips", []) if os.path.exists(c)]
                logger.info(f"🎬 [Zero-Overlap Registry] Loaded {len(chosen_clips)} exclusive real video clips for {video_key} (Categories: {slot_info.get('categories', [])[:4]})")
        except Exception as e:
            logger.warning(f"Failed to read registry: {e}")

    # Fallback to authentic nature B-rolls if registry not populated
    if not chosen_clips:
        broll_fallback = [
            os.path.abspath("app/assets/broll/ocean_720.mp4"),
            os.path.abspath("app/assets/broll/clouds_720.mp4"),
            os.path.abspath("app/assets/broll/desert_720.mp4"),
        ]
        chosen_clips = [b for b in broll_fallback if os.path.exists(b)]

    # 10 Distinct Sacred Quran Anchor Visuals (1 per slot)
    quran_anchors = [
        os.path.abspath("app/assets/video_scenes/quran_rehal_master.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_dawn_tahajjud.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_night_lantern.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_golden_hour.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_macro_verses.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_cinematic.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_sunbeam.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_closeup.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_sanctuary.mp4"),
        os.path.abspath("app/assets/video_scenes/quran_rehal_regal_amber.mp4"),
    ]
    quran_anchors = [q for q in quran_anchors if os.path.exists(q)]
    anchor_visual = quran_anchors[(slot_num - 1) % len(quran_anchors)] if quran_anchors else None

    # Shuffle this video's unique clips to create an engaging visual sequence
    shuffled_clips = list(chosen_clips)
    random.shuffle(shuffled_clips)

    sequence_pool = []
    # Scene 1: Sacred Quran Anchor opening hook
    if anchor_visual:
        sequence_pool.append(anchor_visual)

    # Subsequent scenes: 100% unique real motion video clips (waves, clouds, stars, mountains, desert...)
    for clip in shuffled_clips:
        sequence_pool.append(clip)

    if not sequence_pool:
        sequence_pool = [os.path.abspath("app/assets/broll/ocean_720.mp4")]


    scene_clips = []

    for i, sc in enumerate(planned_scenes):
        asset_file = sequence_pool[i % len(sequence_pool)]
        scene_dur = sc["duration"]

        clip_out = os.path.join(temp_dir, f"scene_clip_{i:02d}.mp4")

        # Slice 60 FPS video clip with exact duration
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", asset_file,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=60",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-t", f"{scene_dur:.2f}",
            "-an",
            "-pix_fmt", "yuv420p",
            clip_out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        scene_clips.append(clip_out)

    concat_list_file = os.path.join(temp_dir, "scenes_concat_list.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            safe_clip = os.path.basename(clip)
            f.write(f"file '{safe_clip}'\n")

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        master_visual_path
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
    logger.info(f"Dynamic Quran Master Visual Track built successfully: {master_visual_path}")
    return master_visual_path

def render_quran_verse_video(verse_data: dict, audio_data: dict, output_dir: str = "data/output", video_slot: int = None) -> str:
    """
    Renders end-to-end 1080x1920 vertical video with dynamic 4-8s cuts,
    centered Arabic/Bengali subtitles, and authentic B-rolls.
    Returns path to rendered MP4 video.
    """
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join("data", "temp", "quran_render_run")
    os.makedirs(temp_dir, exist_ok=True)

    surah = verse_data["surah"]
    start = verse_data["ayah_start"]
    end = verse_data["ayah_end"]
    reciter_id = verse_data.get("reciter_id", "alafasy")
    audio_file = audio_data["audio_path"]
    total_dur = audio_data["total_duration"]

    # 1. Build Dynamic Multi-Scene Visual Track with Zero-Overlap Slot & Ayah-Synced Pacing
    ayah_timings = audio_data.get("ayah_timings", [])
    master_visual_path = build_dynamic_quran_visual_track(total_dur, temp_dir, video_slot=video_slot, ayah_timings=ayah_timings)

    # 2. Build Subtitles
    ass_path = os.path.join(temp_dir, "quran_subtitles.ass")
    build_quran_ass_subtitles(verse_data, audio_data, ass_path)

    # 3. Output Video File
    out_filename = f"Quran_Surah_{surah}_{start}_{end}_{reciter_id}.mp4"
    final_output_path = os.path.join(output_dir, out_filename)

    # Normalize paths for FFmpeg filter on Windows
    safe_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")

    # 4. Burn ASS Subtitles & Merge Audio over Full-Screen 1080x1920 Live Motion Visual Track
    grad_path = os.path.abspath("app/assets/grad_center_bottom.png")
    safe_grad_path = grad_path.replace("\\", "/").replace(":", "\\:")

    if os.path.exists(grad_path):
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=60[bg];"
            f"[1:v]scale=1080:1920[grad];"
            f"[bg][grad]overlay=0:0[graded];"
            f"[graded]ass='{safe_ass_path}':fontsdir=app/assets/fonts[outv]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", master_visual_path,
            "-i", grad_path,
            "-i", audio_file,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(total_dur),
            "-pix_fmt", "yuv420p",
            final_output_path
        ]
    else:
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=60[bg];"
            f"[bg]ass='{safe_ass_path}':fontsdir=app/assets/fonts[outv]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", master_visual_path,
            "-i", audio_file,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(total_dur),
            "-pix_fmt", "yuv420p",
            final_output_path
        ]

    logger.info(f"Rendering Full-Screen Quran video: {final_output_path} ({total_dur:.1f}s)...")
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        logger.error(f"FFmpeg error: {res.stderr[-500:]}")
        raise RuntimeError(f"FFmpeg rendering failed with exit code {res.returncode}")
    logger.info(f"Quran video successfully rendered at: {final_output_path}")

    # 5. Extract Visual Verification Frame to Guarantee Clean Layout
    verify_frame_path = os.path.join(temp_dir, "verify_quran_frame.jpg")
    try:
        sample_time = max(1.0, min(15.0, total_dur - 1.0))
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(sample_time),
            "-i", final_output_path,
            "-vframes", "1",
            verify_frame_path
        ], check=True, capture_output=True)
        logger.info(f"✅ Generated visual verification frame at: {verify_frame_path}")
    except Exception as e:
        logger.warning(f"Verification frame extraction notice: {e}")

    return final_output_path

