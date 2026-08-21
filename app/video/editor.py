# -*- coding: utf-8 -*-
import os
import re
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
    "কবরের আজাব", "ঋণের বোঝা", "সহীহ সুন্নাহ", "ভিত্তিহীন কুসংস্কার", "কুসংস্কার",
    "সদকা", "গুনাহ", "বরকত", "রিজিক", "বদনজর", "অশান্তি", 
    "ক্ষমা", "তওবা", "আজাব", "অভিশাপ", "হারাম", "হালাল", 
    "সওয়াব", "সওয়াব", "প্রতিদান", "রহমত", "জান্নাত", "জাহান্নাম", "ঈমান"
]

HIGHLIGHT_KEYWORDS_CYAN = [
    "সুন্নাহটি", "সুন্নাহ", "আমলটি", "আমলগুলো", "আমল", "দোয়াটি", "দোয়াটি", "দোয়া", "দোয়া", "হেফাজত"
]

def apply_selective_narration_highlight(text: str) -> str:
    """Highlights max 1 punchy keyword (1-2 words) per line in Gold or Cyan, keeping base text crisp white."""
    for kw in HIGHLIGHT_KEYWORDS_GOLD:
        pattern = r'(?<![a-zA-Z0-9\u0980-\u09FF])(' + re.escape(kw) + r')(?![a-zA-Z0-9\u0980-\u09FF])'
        if re.search(pattern, text):
            return re.sub(pattern, f"{COLOR_GOLD_ASS}\\1{COLOR_RESET_ASS}", text, count=1)
            
    for kw in HIGHLIGHT_KEYWORDS_CYAN:
        pattern = r'(?<![a-zA-Z0-9\u0980-\u09FF])(' + re.escape(kw) + r')(?![a-zA-Z0-9\u0980-\u09FF])'
        if re.search(pattern, text):
            return re.sub(pattern, f"{COLOR_CYAN_ASS}\\1{COLOR_RESET_ASS}", text, count=1)
            
    return text

def render_final_video(scenes: list, topic_id: int, video_format: str = "short") -> str:
    """
    Renders 9:16 vertical Islamic Short video with Hind Siliguri authentic Bengali font subtitles.
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
        
    if not image_path or not os.path.exists(image_path):
        logger.error(f"Master visual not found: {image_path}")
        return None
        
    try:
        probe = ffmpeg.probe(master_audio_path)
        duration = float(probe['format']['duration'])
        logger.info(f"Audio duration: {duration:.2f}s")
        
        # 1. Convert VTT to ASS
        ass_path = os.path.join(temp_dir, "bengali_subtitles.ass")
        subprocess.run(["ffmpeg", "-y", "-i", vtt_path, ass_path], check=True, capture_output=True)
        
        # 2. Format ASS file with Hind Siliguri font and Center Alignment
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
                    header_lines.append("Style: Default,Noto Sans Bengali,74,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,5,60,60,0,1")
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
            # Clean any stray tags or prefixes
            clean_text = re.sub(r'</?[a-zA-Z0-9_-]+>', '', clean_text)
            clean_text = re.sub(r'^\s*(arabic|bangla|english)\s*:\s*', '', clean_text, flags=re.IGNORECASE).strip()
            
            clean_text = clean_text.replace('\n', '\\N')
            sub_lines = clean_text.split('\\N')
            formatted_sub_lines = []
            
            has_arabic = any(re.search(r'[\u0600-\u06FF]', l) for l in sub_lines)
            bangla_idx = 0
            
            for sl in sub_lines:
                sl = sl.strip()
                if not sl:
                    continue
                if re.search(r'[\u0600-\u06FF]', sl):
                    # Style Arabic text with Amiri font and gold accent (UNTOUCHED)
                    formatted_sub_lines.append(f"{{\\fnAmiri\\fs82\\b1\\c&HEBAF41&}}{sl}")
                elif has_arabic:
                    # Inside an Arabic Ayah/Dua block (UNTOUCHED)
                    if bangla_idx == 0 and len(sub_lines) >= 3:
                        # Pronunciation line: NOT bold, smaller font
                        formatted_sub_lines.append(f"{{\\fnNoto Sans Bengali\\fs62\\b0\\c&HE0E4E8&}}{sl}")
                        bangla_idx += 1
                    else:
                        # Translation line: Warm yellowish / amber highlight
                        formatted_sub_lines.append(f"{{\\fnNoto Sans Bengali\\fs70\\b1\\c&H3DBFF2&}}{sl}")
                        bangla_idx += 1
                else:
                    # Standard narration Bangla line: crisp white with selective 1-2 word highlight
                    highlighted_sl = apply_selective_narration_highlight(sl)
                    formatted_sub_lines.append(f"{{\\fnNoto Sans Bengali\\fs74\\b1\\c&HFFFFFF&}}{highlighted_sl}")
                    
            final_dialogue_text = "\\N".join(formatted_sub_lines) if formatted_sub_lines else f"{{\\fnNoto Sans Bengali\\fs74\\b1}}{clean_text}"
            mid_str = ",".join(d['middle_fields'])
            out_lines.append(f"{d['prefix_fields'][0]},{d['start_str']},{d['end_str']},{mid_str},{{\\an5}}{final_dialogue_text}")
            
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")
            
        # Use relative paths for FFmpeg to prevent Windows drive letter colon issues
        rel_ass = os.path.relpath(ass_path).replace('\\', '/')
        
        # 3. Build FFmpeg rendering command
        final_video_vf = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},subtitles='{rel_ass}'"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", str(duration),
            "-i", image_path,
            "-i", master_audio_path,
            "-vf", final_video_vf,
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
        logger.info(f"Final 9:16 Bengali Video successfully rendered: {final_output}")
        return final_output
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg Error in final video render:\n{e.stderr.decode('utf8', errors='ignore')}")
        return None
    except Exception as e:
        logger.error(f"Error in final video render: {e}")
        return None
