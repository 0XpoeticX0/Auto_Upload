import os
import re
import subprocess
import ffmpeg
from app.logger import logger

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

def render_final_video(scenes: list, topic_id: int, video_format: str = "short") -> str:
    """
    Renders 9:16 vertical Islamic Short video with Noto Sans Bengali & Arabic font subtitles.
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
        
        # 2. Format ASS file with Noto Sans Bengali & Center Alignment
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
                    s_parts = line.split(",")
                    if len(s_parts) >= 19:
                        s_parts[1] = "Noto Sans Bengali"
                        s_parts[18] = "5"  # Center alignment
                        header_lines.append(",".join(s_parts))
                    else:
                        header_lines.append(line)
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
            # Strip any stray tags
            clean_text = re.sub(r'</?[a-zA-Z0-9_-]+>', '', clean_text)
            clean_text = re.sub(r'^\s*(arabic|bangla)\s*:\s*', '', clean_text, flags=re.IGNORECASE).strip()
            mid_str = ",".join(d['middle_fields'])
            out_lines.append(f"{d['prefix_fields'][0]},{d['start_str']},{d['end_str']},{mid_str},{{\\an5}}{clean_text}")
            
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")
            
        safe_ass = ass_path.replace('\\', '/')
        fonts_dir = os.path.abspath("app/assets/fonts").replace('\\', '/')
        
        # 3. Build FFmpeg graph
        in_image = ffmpeg.input(image_path, loop=1, t=duration)
        in_audio = ffmpeg.input(master_audio_path)
        
        # Scale to 9:16 vertical (1080x1920)
        video = in_image.filter('scale', VIDEO_WIDTH, VIDEO_HEIGHT)
        
        # Subtitle styling: Noto Sans Bengali, large font size 68, bold, white with black outline
        style = "Fontname=Noto Sans Bengali,Fontsize=68,Bold=1,MarginL=60,MarginR=60,MarginV=0,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=5"
        
        if os.path.exists(fonts_dir):
            video = video.filter('subtitles', safe_ass, fontsdir=fonts_dir, force_style=style)
        else:
            video = video.filter('subtitles', safe_ass, force_style=style)
            
        # Background ambient audio if present
        bg_audio_path = "app/assets/background_audio.mp3"
        if os.path.exists(bg_audio_path):
            in_bg = ffmpeg.input(bg_audio_path, stream_loop=-1, t=duration).filter('volume', 0.12)
            final_audio = ffmpeg.filter([in_audio, in_bg], 'amix', inputs=2, duration='first')
        else:
            final_audio = in_audio
            
        out = ffmpeg.output(
            video,
            final_audio,
            final_output,
            vcodec='libx264',
            crf=18,
            preset='ultrafast',
            acodec='aac',
            audio_bitrate='192k',
            pix_fmt='yuv420p',
            shortest=None
        )
        out.run(overwrite_output=True, capture_stderr=True, quiet=True)
        logger.info(f"Final 9:16 Bengali Video successfully rendered: {final_output}")
        return final_output
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg Error in final video render:\n{e.stderr.decode('utf8', errors='ignore')}")
        return None
    except Exception as e:
        logger.error(f"Error in final video render: {e}")
        return None
