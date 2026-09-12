# -*- coding: utf-8 -*-
import os
import re
import math
import random
import subprocess
import ffmpeg
from app.logger import logger

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# Strategic 1-2 word highlight color codes (ASS BGR format)
COLOR_GOLD_ASS = "{\\c&H0041AFEB&}"   # #EBAF41 Warm Gold (Core virtues, rewards, severe warnings)
COLOR_CYAN_ASS = "{\\c&H00F8BD38&}"   # #38BDF8 Soft Cyan (Practical Sunnah actions & benefits)
COLOR_RESET_ASS = "{\\c&H00FFFFFF&}"  # #FFFFFF Crisp White

HIGHLIGHT_KEYWORDS_GOLD = [
    "আল্লাহ", "আল্লাহর", "আল্লাহকে", "রাসূলুল্লাহ", "নবীজী", "নবীজি", "রব", "তাওয়াক্কুল",
    "কবরের আজাব", "ঋণের বোঝা", "সহীহ সুন্নাহ", "ভিত্তিহীন কুসংস্কার", "কুসংস্কার",
    "সদকা", "গুনাহ", "বরকত", "রিজিক", "বদনজর", "অশান্তি", 
    "ক্ষমা", "তওবা", "আজাব", "অভিশাপ", "হারাম", "হালাল", 
    "সওয়াব", "সওয়াব", "প্রতিদান", "রহমত", "জান্নাত", "জাহান্নাম", "ঈমান", "স্বর্ণমুদ্রা", "দিনার"
]

HIGHLIGHT_KEYWORDS_CYAN = [
    "সুন্নাহটি", "সুন্নাহ", "আমলটি", "আমলগুলো", "আমল", "দোয়াটি", "দোয়াটি", "দোয়া", "দোয়া", "হেফাজত"
]

def apply_selective_narration_highlight(text: str, custom_phrases: list = None) -> str:
    """Highlights dynamic trigger phrase (if present) or max 1 punchy keyword in Gold or Cyan, keeping base text crisp white."""
    if custom_phrases:
        for cp in custom_phrases:
            if not cp or not cp.strip():
                continue
            clean_cp = cp.strip()
            if clean_cp in text:
                return text.replace(clean_cp, f"{COLOR_GOLD_ASS}{clean_cp}{COLOR_RESET_ASS}", 1)

    for kw in HIGHLIGHT_KEYWORDS_GOLD:
        if kw in text:
            return text.replace(kw, f"{COLOR_GOLD_ASS}{kw}{COLOR_RESET_ASS}", 1)
            
    for kw in HIGHLIGHT_KEYWORDS_CYAN:
        if kw in text:
            return text.replace(kw, f"{COLOR_CYAN_ASS}{kw}{COLOR_RESET_ASS}", 1)
            
    return text

def build_dynamic_general_visual_track(total_dur: float, temp_dir: str, pillar_category: str = "daily_life", primary_image: str = None) -> str:
    """
    Renders a dynamic 9:16 multi-scene visual track (4.5 to 7.0s scene cuts):
    - Curated 8K master photorealistic backgrounds tailored to the topic pillar.
    - Authentic 60fps nature video B-rolls (ocean waves, moving clouds, desert dunes).
    - Cinematic camera motion (zoom_in, zoom_out, pan_up) via FFmpeg zoompan.
    - Strictly 0 humans, 0 faces, 0 silhouettes, 0 statues, 0 animals.
    - Concatenates seamlessly into master_visual_track.mp4.
    """
    os.makedirs(temp_dir, exist_ok=True)
    master_visual_path = os.path.join(temp_dir, "master_visual_track.mp4")

    # Target 4.5 to 7.0-second scene cuts (e.g. 8-12 scenes for 50-80s audio)
    num_scenes = max(3, int(math.ceil(total_dur / 6.0)))
    base_scene_dur = total_dur / num_scenes
    logger.info(f"Dynamic Visual Track: Slicing into {num_scenes} scenes (~{base_scene_dur:.1f}s each) across {total_dur:.1f}s for '{pillar_category}'")

    broll_ocean = os.path.abspath("app/assets/broll/ocean_720.mp4")
    broll_clouds = os.path.abspath("app/assets/broll/clouds_720.mp4")
    broll_desert = os.path.abspath("app/assets/broll/desert_720.mp4")

    img_library = os.path.abspath("app/assets/scenes/ancient_islamic_library.jpg")
    img_port = os.path.abspath("app/assets/scenes/ancient_port_twilight.jpg")
    img_night = os.path.abspath("app/assets/scenes/celestial_night_crescent.jpg")
    img_fortress = os.path.abspath("app/assets/scenes/crimson_desert_fortress.jpg")
    img_sunrise = os.path.abspath("app/assets/scenes/desert_dawn_sunrise.jpg")
    img_oasis = os.path.abspath("app/assets/scenes/desert_oasis_palms.jpg")
    img_shield = os.path.abspath("app/assets/scenes/divine_sanctuary_shield.jpg")
    img_calligraphy = os.path.abspath("app/assets/scenes/glowing_calligraphy.jpg")
    img_arches = os.path.abspath("app/assets/scenes/moorish_palace_arches.jpg")
    img_ocean_sunset = os.path.abspath("app/assets/scenes/ocean_waves_sunset.jpg")
    img_quran_closeup = os.path.abspath("app/assets/scenes/quran_rehal_closeup.jpg")
    img_quran_sanctuary = os.path.abspath("app/assets/scenes/quran_rehal_sanctuary.jpg")
    img_fountain = os.path.abspath("app/assets/scenes/tranquil_courtyard_fountain.jpg")
    img_quran_master = os.path.abspath("app/assets/quran_rehal_master.jpg")

    pillar_sequences = {
        "islamic_stories": [
            {"type": "image", "file": img_fortress, "motion": "zoom_in"},
            {"type": "broll", "file": broll_desert},
            {"type": "image", "file": img_oasis, "motion": "pan_up"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_port, "motion": "zoom_out"},
            {"type": "image", "file": img_sunrise, "motion": "zoom_in"},
            {"type": "image", "file": img_library, "motion": "zoom_out"},
            {"type": "broll", "file": broll_ocean},
        ],
        "akhirah_unseen": [
            {"type": "image", "file": img_night, "motion": "zoom_in"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_ocean_sunset, "motion": "zoom_out"},
            {"type": "broll", "file": broll_ocean},
            {"type": "image", "file": img_shield, "motion": "pan_up"},
            {"type": "image", "file": img_sunrise, "motion": "zoom_in"},
            {"type": "image", "file": img_calligraphy, "motion": "zoom_out"},
        ],
        "seerah": [
            {"type": "image", "file": img_oasis, "motion": "zoom_in"},
            {"type": "broll", "file": broll_desert},
            {"type": "image", "file": img_fortress, "motion": "zoom_out"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_night, "motion": "pan_up"},
            {"type": "image", "file": img_library, "motion": "zoom_out"},
            {"type": "image", "file": img_quran_closeup, "motion": "zoom_in"},
        ],
        "misconceptions": [
            {"type": "image", "file": img_library, "motion": "zoom_in"},
            {"type": "image", "file": img_calligraphy, "motion": "pan_up"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_arches, "motion": "zoom_out"},
            {"type": "image", "file": img_quran_sanctuary, "motion": "zoom_in"},
            {"type": "broll", "file": broll_desert},
            {"type": "image", "file": img_port, "motion": "zoom_out"},
        ],
        "character_dealings": [
            {"type": "image", "file": img_fountain, "motion": "zoom_in"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_oasis, "motion": "pan_up"},
            {"type": "image", "file": img_arches, "motion": "zoom_out"},
            {"type": "broll", "file": broll_ocean},
            {"type": "image", "file": img_library, "motion": "zoom_in"},
        ],
        "crises_debt_turnaround": [
            {"type": "image", "file": img_ocean_sunset, "motion": "zoom_in"},
            {"type": "broll", "file": broll_ocean},
            {"type": "image", "file": img_shield, "motion": "pan_up"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_night, "motion": "zoom_out"},
            {"type": "image", "file": img_calligraphy, "motion": "zoom_in"},
        ],
        "daily_sunnah": [
            {"type": "image", "file": img_fountain, "motion": "zoom_in"},
            {"type": "image", "file": img_calligraphy, "motion": "pan_up"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_arches, "motion": "zoom_out"},
            {"type": "broll", "file": broll_desert},
            {"type": "image", "file": img_oasis, "motion": "zoom_in"},
        ],
        "family_marriage_sunnah": [
            {"type": "image", "file": img_fountain, "motion": "zoom_in"},
            {"type": "broll", "file": broll_clouds},
            {"type": "image", "file": img_arches, "motion": "pan_up"},
            {"type": "broll", "file": broll_ocean},
            {"type": "image", "file": img_oasis, "motion": "zoom_out"},
            {"type": "image", "file": img_night, "motion": "zoom_in"},
        ],
    }

    fallback_sequence = [
        {"type": "image", "file": img_library, "motion": "zoom_in"},
        {"type": "broll", "file": broll_clouds},
        {"type": "image", "file": img_fountain, "motion": "zoom_out"},
        {"type": "broll", "file": broll_ocean},
        {"type": "image", "file": img_calligraphy, "motion": "pan_up"},
        {"type": "broll", "file": broll_desert},
        {"type": "image", "file": img_arches, "motion": "zoom_in"},
    ]

    seq_pool = pillar_sequences.get(pillar_category, fallback_sequence)
    
    # If primary_image is provided and exists, prepend it as Scene 0
    pool_with_primary = []
    if primary_image and os.path.exists(primary_image):
        pool_with_primary.append({"type": "image", "file": os.path.abspath(primary_image), "motion": "zoom_in"})
    
    pool_with_primary.extend(seq_pool)

    scene_clips = []
    current_time = 0.0

    for i in range(num_scenes):
        scene_cfg = pool_with_primary[i % len(pool_with_primary)]
        if i == num_scenes - 1:
            scene_dur = total_dur - current_time
        else:
            scene_dur = round(base_scene_dur, 2)
        current_time += scene_dur

        clip_out = os.path.join(temp_dir, f"general_clip_{i:02d}.mp4")
        asset_file = scene_cfg["file"]
        if not os.path.exists(asset_file):
            asset_file = img_quran_master

        if scene_cfg["type"] == "broll" and os.path.exists(asset_file) and asset_file.endswith(".mp4"):
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", asset_file,
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-t", f"{scene_dur:.2f}",
                "-an",
                "-pix_fmt", "yuv420p",
                clip_out
            ]
        else:
            motion = scene_cfg.get("motion", "zoom_in")
            frames = max(30, int(scene_dur * 30))
            if motion == "zoom_in":
                zp = f"zoompan=z='min(zoom+0.0012,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30"
            elif motion == "zoom_out":
                zp = f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.0,zoom-0.0012))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30"
            elif motion == "pan_up":
                zp = f"zoompan=z=1.10:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-on/{frames})':d={frames}:s=1080x1920:fps=30"
            else:
                zp = f"zoompan=z='min(zoom+0.0010,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30"

            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", asset_file,
                "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{zp}",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-t", f"{scene_dur:.2f}",
                "-an",
                "-pix_fmt", "yuv420p",
                clip_out
            ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            scene_clips.append(clip_out)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to generate scene clip {i}: {e.stderr.decode('utf-8', errors='ignore')}")

    if not scene_clips:
        logger.error("No dynamic scene clips could be rendered; falling back to single image loop.")
        return None

    concat_list_file = os.path.join(temp_dir, "general_scenes_concat.txt")
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
    logger.info(f"Dynamic Master Visual Track rendered successfully: {master_visual_path}")
    return master_visual_path

def render_final_video(scenes: list, topic_id: int, video_format: str = "short", pillar_category: str = "daily_life") -> str:
    """
    Renders 9:16 vertical Islamic Short video with dynamic 4-7s scene cuts, B-rolls, and Kalpurush Bengali subtitles.
    """
    output_dir = "data/output"
    temp_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    final_output = os.path.join(output_dir, f"video_{topic_id}_{video_format}.mp4")
    
    if not scenes:
        logger.error("No scenes provided to editor.")
        return None
        
    master_audio_path = scenes[0].get("audio_path")
    vtt_path = scenes[0].get("vtt_path")
    image_path = scenes[0].get("image_path")
    
    if not master_audio_path or not os.path.exists(master_audio_path):
        logger.error(f"Master audio not found: {master_audio_path}")
        return None
        
    try:
        probe = ffmpeg.probe(master_audio_path)
        duration = float(probe['format']['duration'])
        logger.info(f"Audio duration: {duration:.2f}s")
        
        # 1. Build Dynamic Multi-Scene Visual Track (4-7s cuts, B-rolls, 8K thematic visuals)
        master_visual_path = build_dynamic_general_visual_track(
            total_dur=duration,
            temp_dir=temp_dir,
            pillar_category=pillar_category,
            primary_image=image_path
        )

        # Collect any custom highlight phrases from scenes
        custom_phrases = [sc.get("highlight_phrase") for sc in scenes if sc.get("highlight_phrase")]
        
        # 2. Convert VTT to ASS
        ass_path = os.path.join(temp_dir, "bengali_subtitles.ass")
        subprocess.run(["ffmpeg", "-y", "-i", vtt_path, ass_path], check=True, capture_output=True)
        
        # 3. Format ASS file with Kalpurush font and Center Alignment (Strict 2-Line Subtitles)
        with open(ass_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            
        def parse_ass_time(t_str):
            parts = t_str.strip().split(':')
            return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
            
        def format_ass_time(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = sec % 60
            return f"{h}:{m:02d}:{s:05.2f}"
            
        header_lines = []
        dialogues = []
        
        for line in lines:
            if line.startswith("Dialogue:"):
                parts = line.split(",", 9)
                if len(parts) == 10:
                    dialogues.append({
                        'prefix_fields': parts[0:3],
                        'start': parse_ass_time(parts[1]),
                        'end': parse_ass_time(parts[2]),
                        'start_str': parts[1],
                        'end_str': parts[2],
                        'middle_fields': parts[3:9],
                        'text': parts[9]
                    })
            else:
                if line.startswith("PlayResX:"):
                    header_lines.append(f"PlayResX: {VIDEO_WIDTH}")
                elif line.startswith("PlayResY:"):
                    header_lines.append(f"PlayResY: {VIDEO_HEIGHT}")
                elif line.startswith("Style: Default,"):
                    header_lines.append("Style: Default,Kalpurush,58,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3.2,1.8,5,70,70,0,1")
                else:
                    header_lines.append(line)
                    
        # De-overlap timestamps
        for i in range(len(dialogues) - 1):
            if dialogues[i]['end'] > dialogues[i+1]['start']:
                new_end = max(dialogues[i]['start'] + 0.1, dialogues[i+1]['start'] - 0.01)
                dialogues[i]['end'] = new_end
                dialogues[i]['end_str'] = format_ass_time(new_end)
                
        out_lines = list(header_lines)
        for d in dialogues:
            clean_text = d['text'].replace('{\\an5}', '')
            clean_text = re.sub(r'</?[a-zA-Z0-9_-]+>', '', clean_text)
            clean_text = re.sub(r'^\s*(arabic|bangla|english)\s*:\s*', '', clean_text, flags=re.IGNORECASE).strip()
            
            clean_text = clean_text.replace('\n', '\\N')
            sub_lines = [l.strip() for l in clean_text.split('\\N') if l.strip()]
            
            has_arabic = any(re.search(r'[\u0600-\u06FF]', l) for l in sub_lines)
            
            # Strict 2-Line Subtitle Mandate: clamp any multi-line paragraph to max 2 balanced lines
            if len(sub_lines) > 2:
                if has_arabic:
                    ar_lines = [l for l in sub_lines if re.search(r'[\u0600-\u06FF]', l)]
                    bn_lines = [l for l in sub_lines if not re.search(r'[\u0600-\u06FF]', l)]
                    sub_lines = [" ".join(ar_lines)]
                    if bn_lines:
                        sub_lines.append(" ".join(bn_lines))
                else:
                    all_text = " ".join(sub_lines).strip()
                    words = all_text.split()
                    mid = len(words) // 2
                    sub_lines = [" ".join(words[:mid]), " ".join(words[mid:])]
                    
            formatted_sub_lines = []
            bangla_idx = 0
            
            for sl in sub_lines:
                sl = sl.strip()
                if not sl:
                    continue
                if re.search(r'[\u0600-\u06FF]', sl):
                    # Arabic text with Amiri font and warm gold accent
                    formatted_sub_lines.append(f"{{\\fnAmiri\\fs80\\b1\\c&HEBAF41&}}{sl}")
                elif has_arabic:
                    # Inside an Arabic Ayah/Dua block
                    if bangla_idx == 0 and len(sub_lines) >= 3:
                        # Pronunciation line: Regular weight, subtle contrast
                        formatted_sub_lines.append(f"{{\\fnKalpurush\\fs52\\b0\\c&HE0E4E8&}}{sl}")
                        bangla_idx += 1
                    else:
                        # Translation line: Warm amber highlight
                        formatted_sub_lines.append(f"{{\\fnKalpurush\\fs58\\b1\\c&H3DBFF2&}}{sl}")
                        bangla_idx += 1
                else:
                    # Standard narration Bangla line: crisp white with dynamic trigger phrase highlight
                    highlighted_sl = apply_selective_narration_highlight(sl, custom_phrases)
                    formatted_sub_lines.append(f"{{\\fnKalpurush\\fs58\\b0\\c&HFFFFFF&}}{highlighted_sl}")
                    
            final_dialogue_text = "\\N".join(formatted_sub_lines) if formatted_sub_lines else f"{{\\fnKalpurush\\fs58\\b0}}{clean_text}"
            mid_str = ",".join(d['middle_fields'])
            out_lines.append(f"{d['prefix_fields'][0]},{d['start_str']},{d['end_str']},{mid_str},{{\\an5}}{final_dialogue_text}")
            
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")
            
        rel_ass = os.path.relpath(ass_path).replace('\\', '/')
        rel_fonts = os.path.relpath("app/assets/fonts").replace('\\', '/')
        
        # 4. Burn ASS Subtitles with Kalpurush Font & Subtle Cinematic Grade
        final_video_vf = f"colorlevels=rimin=0.03:gimin=0.03:bimin=0.03:rimax=0.92:gimax=0.92:bimax=0.92,subtitles='{rel_ass}':fontsdir='{rel_fonts}'"
        
        if master_visual_path and os.path.exists(master_visual_path):
            cmd = [
                "ffmpeg", "-y",
                "-i", master_visual_path,
                "-i", master_audio_path,
                "-vf", final_video_vf,
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "veryfast",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", f"{duration:.2f}",
                final_output
            ]
        else:
            # Fallback single image if multi-scene failed
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-t", str(duration),
                "-i", image_path,
                "-i", master_audio_path,
                "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},{final_video_vf}",
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "ultrafast",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                final_output
            ]
        
        logger.info(f"Running video render command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"🎉 Final 9:16 Bengali Video successfully rendered: {final_output}")
        return final_output
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg Error in final video render:\n{e.stderr.decode('utf8', errors='ignore')}")
        return None
    except Exception as e:
        logger.error(f"Error in final video render: {e}")
        return None
