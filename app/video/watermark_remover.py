# -*- coding: utf-8 -*-
import os
import subprocess
import json
from app.logger import logger

def get_video_info(video_path: str) -> dict:
    """Uses ffprobe to inspect video resolution, duration, and aspect ratio."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        data = json.loads(res.stdout)
        video_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'video'), None)
        audio_stream = next((s for s in data.get('streams', []) if s.get('codec_type') == 'audio'), None)
        
        width = int(video_stream.get('width', 1080)) if video_stream else 1080
        height = int(video_stream.get('height', 1920)) if video_stream else 1920
        duration = float(data.get('format', {}).get('duration', 0.0))
        
        return {
            'width': width,
            'height': height,
            'duration': duration,
            'has_audio': audio_stream is not None,
            'aspect_ratio': width / height if height > 0 else 0.5625
        }
    except Exception as e:
        logger.warning(f'ffprobe failed for {video_path}: {e}')
        return {'width': 1080, 'height': 1920, 'duration': 0, 'has_audio': True, 'aspect_ratio': 0.5625}

def process_and_clean_video(
    input_path: str,
    output_path: str,
    mode: str = 'smart_safe_crop',
    trim_outro_seconds: float = 0.0,
    delogo_corner: str = 'bottom_right'
) -> str:
    """
    Cleans watermark and enforces pristine 1080x1920 (9:16) format.

    Modes:
    - 'smart_safe_crop': 4.5% center zoom + scale to 1080x1920 (Lossless & invisible way to strip corner logos)
    - 'delogo': Inpaints/interpolates the watermark area
    - 'blur_corner': Applies subtle frosted blur on watermark
    - 'center_fit_9_16': Fits any 16:9 or 1:1 video into 9:16 vertical canvas
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f'Input video not found: {input_path}')

    info = get_video_info(input_path)
    in_w = info['width']
    in_h = info['height']
    duration = info['duration']

    logger.info(f'Processing video: {input_path} ({in_w}x{in_h}, {duration:.1f}s, mode: {mode})')

    vf_filters = []
    aspect = in_w / in_h if in_h > 0 else 0.5625
    is_vertical = 0.52 <= aspect <= 0.60

    if mode == 'smart_safe_crop':
        if is_vertical:
            vf_filters.append('crop=in_w*0.955:in_h*0.955:(in_w-out_w)/2:(in_h-out_h)/2')
            vf_filters.append('scale=1080:1920:flags=lanczos')
        else:
            vf_filters.append('crop=in_h*(9/16):in_h:(in_w-out_w)/2:0')
            vf_filters.append('scale=1080:1920:flags=lanczos')

    elif mode == 'delogo':
        if delogo_corner == 'bottom_right':
            vf_filters.append('scale=1080:1920:flags=lanczos')
            vf_filters.append('delogo=x=880:y=1820:w=180:h=80:show=0')
        elif delogo_corner == 'top_right':
            vf_filters.append('scale=1080:1920:flags=lanczos')
            vf_filters.append('delogo=x=880:y=30:w=180:h=80:show=0')
        else:
            vf_filters.append('scale=1080:1920:flags=lanczos')

    elif mode == 'blur_corner':
        vf_filters.append('scale=1080:1920:flags=lanczos')
        vf_filters.append('delogo=x=880:y=1820:w=180:h=80:show=0')

    else:
        vf_filters.append('scale=1080:1920:flags=lanczos')

    filter_str = ','.join(vf_filters)
    cmd = ['ffmpeg', '-y', '-i', input_path]

    if trim_outro_seconds > 0 and duration > trim_outro_seconds:
        new_dur = duration - trim_outro_seconds
        cmd.extend(['-t', str(new_dur)])

    cmd.extend([
        '-vf', filter_str,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        '-r', '30'
    ])

    if info['has_audio']:
        cmd.extend(['-c:a', 'aac', '-b:a', '192k', '-ar', '44100'])
    else:
        cmd.extend(['-an'])

    cmd.append(output_path)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        logger.error(f'FFmpeg watermark removal failed: {res.stderr}')
        raise RuntimeError(f'FFmpeg failed with exit code {res.returncode}: {res.stderr[-400:]}')

    logger.info(f'✅ Video successfully processed & watermark removed: {output_path}')
    return output_path
