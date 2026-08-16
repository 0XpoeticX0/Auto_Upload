import os
import ffmpeg
from app.logger import logger

def create_silent_scene(image_path: str, duration: float, output_path: str, video_format: str):
    logger.info(f"Rendering silent scene clip: {output_path} ({duration:.2f}s)")
    try:
        # Instead of using the memory-heavy 'zoompan' filter, we use a static image.
        # This renders instantly and looks cleaner with the dynamic subtitles overlaid.
        in_image = ffmpeg.input(image_path, loop=1, t=duration)
        
        # Ensure correct dimensions
        if video_format == "short":
            # Crop the center 9:16 portion from the 16:9 master image to prevent stretching
            video = in_image.filter('crop', 'ih*9/16', 'ih').filter('scale', 1080, 1920)
        else:
            video = in_image.filter('scale', 1920, 1080)
        
        # Render silent video (no audio, no subtitles yet)
        out = ffmpeg.output(video, output_path, vcodec='libx264', crf=18, preset='ultrafast', pix_fmt='yuv420p', shortest=None)
        out.run(overwrite_output=True, quiet=True)
        return True
    except Exception as e:
        logger.error(f"Error creating silent scene video: {e}")
        return False

def render_final_video(scenes: list, topic_id: int, video_format: str = "short"):
    base_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    output_dir = "data/output"
    
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    final_output = os.path.join(output_dir, f"video_{topic_id}_{video_format}.mp4")
    
    if not scenes:
        logger.error("No scenes provided to editor.")
        return None
        
    master_audio_path = scenes[0].get("audio_path")
    if not master_audio_path or not os.path.exists(master_audio_path):
        logger.error(f"Master audio track not found: {master_audio_path}")
        return None
        
    # Get total audio duration
    try:
        probe = ffmpeg.probe(master_audio_path)
        total_duration = float(probe['format']['duration'])
    except Exception as e:
        logger.error(f"Failed to probe master audio duration: {e}")
        return None
        
    logger.info(f"Total audio duration: {total_duration:.2f}s.")
    
    # 1. Render the SINGLE master visual track
    image_path = scenes[0].get("image_path")
    if not image_path:
        logger.error("No master image provided. Cannot render video.")
        return None
        
    master_visual_path = os.path.join(base_dir, "master_visual.mp4")
    
    logger.info("Rendering Master Visual track (Single Scene Mode)...")
    if not create_silent_scene(image_path, total_duration, master_visual_path, video_format):
        logger.error("Failed to render master visual track.")
        return None
        
    # 2. Multiplex Master Audio, Master Visual, and burn Master Subtitles
    logger.info("Multiplexing master audio and burning subtitles...")
    try:
        vtt_path = master_audio_path.replace('.mp3', '.vtt')
        # Use relative path to avoid FFmpeg colon-escaping issues with Windows absolute paths (e.g. C:/)
        safe_vtt = vtt_path.replace('\\', '/')
        
        in_visual = ffmpeg.input(master_visual_path)
        in_audio = ffmpeg.input(master_audio_path)
        
        video = in_visual
        if os.path.exists(vtt_path):
            import re
            import subprocess
            ass_path = vtt_path.replace(".vtt", ".ass")
            
            # 1. Convert VTT to ASS
            subprocess.run(["ffmpeg", "-y", "-i", vtt_path, ass_path], check=True, capture_output=True)
            
            # 2. Process ASS to strictly de-overlap timestamps, update canvas, and inject {\an5}
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
            is_vertical = (video_format == "short")
            target_width = 1080 if is_vertical else 1920
            target_height = 1920 if is_vertical else 1080
            
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
                        header_lines.append(f"PlayResX: {target_width}")
                    elif line.startswith("PlayResY:"):
                        header_lines.append(f"PlayResY: {target_height}")
                    elif line.startswith("Style: Default,"):
                        s_parts = line.split(",")
                        if len(s_parts) >= 19:
                            s_parts[18] = "5" # Set Alignment to Mid-Center
                            header_lines.append(",".join(s_parts))
                        else:
                            header_lines.append(line)
                    else:
                        header_lines.append(line)
                    
            # Strictly eliminate any overlapping timestamps between consecutive cues
            for i in range(len(dialogues) - 1):
                if dialogues[i]['end'] > dialogues[i+1]['start']:
                    new_end = max(dialogues[i]['start'] + 0.1, dialogues[i+1]['start'] - 0.01)
                    dialogues[i]['end'] = new_end
                    dialogues[i]['end_str'] = format_ass_time(new_end)
                    
            # Reconstruct ASS file with absolute center anchor {\an5} directly in the Text field
            out_lines = list(header_lines)
            for d in dialogues:
                clean_text = d['text'].replace('{\\an5}', '')
                mid_str = ",".join(d['middle_fields'])
                out_lines.append(f"{d['prefix_fields'][0]},{d['start_str']},{d['end_str']},{mid_str},{{\\an5}}{clean_text}")
                
            with open(ass_path, "w", encoding="utf-8") as f:
                f.write("\n".join(out_lines) + "\n")
                
            safe_ass = ass_path.replace('\\', '/')
            # Font size scaled for large, bold, punchy mobile/desktop reading
            font_size = 60 if is_vertical else 65
            style = f"Fontsize={font_size},Bold=1,MarginL=60,MarginR=60,MarginV=0,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=5"
            video = video.filter('subtitles', safe_ass, force_style=style)
            
        out = ffmpeg.output(
            video, 
            in_audio, 
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
        logger.info(f"Final video successfully rendered: {final_output}")
        return final_output
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg Error in final multiplexing step:\n{e.stderr.decode('utf8', errors='ignore')}")
        return None
    except Exception as e:
        logger.error(f"Error in final multiplexing step: {e}")
        return None
