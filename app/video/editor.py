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
            # Alignment=5 is ASS code for absolute Middle-Center. 
            # With MarginV=0, the text block pivots exactly around the vertical center.
            # This guarantees the text NEVER jumps around when changing from 1 to 3 lines.
            style = "Alignment=5,Fontsize=14,Bold=1,MarginL=40,MarginR=40,MarginV=0,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2"
            video = video.filter('subtitles', safe_vtt, force_style=style)
            
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
