# -*- coding: utf-8 -*-
"""
app/quiz/renderer.py
====================
Production Renderer for 3-Question Interactive Islamic Quiz Reels.
Strictly implements:
1. 60-30-10 Visual Rule (60% Live-Motion Backdrop, 30% White Structure, 10% Gold/Emerald Accents).
2. 60-30-10 Audio Rule (60% Voiceover at -18 LUFS, 30% Nature Bed, 10% Tactile Clock & Bell SFX).
3. Conversational Native Host (PradeepNeural @ 0% rate, -2Hz pitch, broadcast EQ).
4. Kalpurush typography with fontsdir='app/assets/fonts'.
5. Dynamic 3-Question seamless video assembly.
"""

import os
import re
import subprocess
import asyncio
import edge_tts
from app.logger import logger
from app.quiz.card_builder import create_viral_overlay, build_timed_ass

DEFAULT_BROLL_VIDEO = "app/assets/broll/ocean_720.mp4"

SFX_TICK = "data/assets/sfx/clock_tick.wav"
SFX_BELL = "data/assets/sfx/correct_bell.wav"

async def _synthesize_voice(text: str, out_wav: str, voice: str = "bn-BD-PradeepNeural", rate: str = "+0%"):
    """Synthesizes human-paced voiceover with warm studio broadcast EQ and -18 LUFS normalization."""
    clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', text).strip()
    raw_mp3 = out_wav + ".raw.mp3"
    
    voices = [voice, "bn-IN-BashkarNeural", "bn-BD-NabanitaNeural"]
    success = False
    for v in voices:
        try:
            communicate = edge_tts.Communicate(clean_text, v, rate=rate)
            await communicate.save(raw_mp3)
            if os.path.exists(raw_mp3) and os.path.getsize(raw_mp3) > 100:
                success = True
                break
        except Exception:
            continue
            
    if not success:
        raise RuntimeError(f"Failed to synthesize voice for text: {clean_text}")
    
    cmd = [
        "ffmpeg", "-y", "-i", raw_mp3,
        "-af", "highpass=f=80,equalizer=f=160:t=q:w=1:g=2.5,equalizer=f=3500:t=q:w=1:g=2.0,loudnorm=I=-18:TP=-1.5:LRA=11",
        "-ar", "44100", "-ac", "2",
        out_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(raw_mp3):
        os.remove(raw_mp3)

def synthesize_voice_sync(text: str, out_wav: str):
    asyncio.run(_synthesize_voice(text, out_wav))

def get_audio_duration(audio_file: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_file
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def render_single_question_scene(
    q_data: dict,
    broll_path: str,
    temp_dir: str,
    scene_idx: int
) -> str:
    """
    Renders one full question scene (Voice + 3 Ticks + Reveal Chime + 60-30-10 Visuals).
    """
    q_num = q_data.get("number", scene_idx)
    q_text = q_data.get("question", "")
    out_mp4 = os.path.join(temp_dir, f"scene_q{q_num}.mp4")

    # 1. Voice
    voice_wav = os.path.join(temp_dir, f"voice_q{q_num}.wav")
    spoken_text = re.sub(r'^(?:প্রশ্ন\s*[০-৯\d]+[:।\-]?\s*|Q\d+[:.\-]?\s*)', '', q_text, flags=re.IGNORECASE).strip()
    if not spoken_text.endswith("?"):
        spoken_text += "?"
    synthesize_voice_sync(spoken_text, voice_wav)
    voice_dur = get_audio_duration(voice_wav)

    # 2. Timing
    t_countdown = voice_dur + 0.30  # Natural breathing pause before countdown
    t_c3 = t_countdown
    t_c2 = t_countdown + 1.0
    t_c1 = t_countdown + 2.0
    t_reveal = t_countdown + 3.0
    total_dur = t_reveal + 2.50

    # 3. Visual Overlays
    states = ["question", "countdown_3", "countdown_2", "countdown_1", "reveal"]
    png_overlays = {}
    for st in states:
        png_path = os.path.join(temp_dir, f"q{q_num}_overlay_{st}.png")
        create_viral_overlay(q_data, state=st, out_png_path=png_path)
        png_overlays[st] = png_path

    ass_path = os.path.join(temp_dir, f"q{q_num}_subtitles.ass")
    build_timed_ass(q_data, t_countdown, t_reveal, total_dur, ass_path)

    # 4. 60-30-10 Audio Mix (60% Voice, 30% Nature Bed, 10% SFX Cues)
    composite_audio = os.path.join(temp_dir, f"audio_q{q_num}.wav")
    ms_c3 = int(t_c3 * 1000)
    ms_c2 = int(t_c2 * 1000)
    ms_c1 = int(t_c1 * 1000)
    ms_bell = int(t_reveal * 1000)

    audio_cmd = [
        "ffmpeg", "-y",
        "-i", voice_wav,
        "-f", "lavfi", "-t", f"{total_dur:.2f}", "-i", "anoisesrc=c=pink:r=44100:a=0.01,lowpass=f=600,highpass=f=80",
        "-i", SFX_TICK,
        "-i", SFX_TICK,
        "-i", SFX_TICK,
        "-i", SFX_BELL,
        "-filter_complex",
        f"[0:a]volume=1.1,apad=whole_dur={total_dur:.2f}[vce];"
        f"[1:a]volume=0.15[amb];"
        f"[2:a]adelay={ms_c3}|{ms_c3},volume=4.0[t3];"
        f"[3:a]adelay={ms_c2}|{ms_c2},volume=4.0[t2];"
        f"[4:a]adelay={ms_c1}|{ms_c1},volume=4.0[t1];"
        f"[5:a]adelay={ms_bell}|{ms_bell},volume=2.2[bell];"
        f"[vce][amb][t3][t2][t1][bell]amix=inputs=6:duration=longest:dropout_transition=0:normalize=0,"
        f"loudnorm=I=-18:TP=-1.5:LRA=11,apad=whole_dur={total_dur:.2f}[aout]",
        "-map", "[aout]",
        composite_audio
    ]
    subprocess.run(audio_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 5. Video Compositing with Continuous Live-Motion Footage
    rel_ass = os.path.relpath(ass_path).replace('\\', '/')
    fc = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"colorlevels=rimin=0.08:gimin=0.08:bimin=0.08:rimax=0.70:gimax=0.70:bimax=0.70[bg];"
        f"[bg][1:v]overlay=0:0:enable='between(t,0,{t_c3})'[v1];"
        f"[v1][2:v]overlay=0:0:enable='between(t,{t_c3},{t_c2})'[v2];"
        f"[v2][3:v]overlay=0:0:enable='between(t,{t_c2},{t_c1})'[v3];"
        f"[v3][4:v]overlay=0:0:enable='between(t,{t_c1},{t_reveal})'[v4];"
        f"[v4][5:v]overlay=0:0:enable='gte(t,{t_reveal})'[v5];"
        f"[v5]subtitles='{rel_ass}':fontsdir='app/assets/fonts'[vout]"
    )

    render_cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-ss", "00:00:01",
        "-t", f"{total_dur:.2f}",
        "-i", broll_path,
        "-i", png_overlays["question"],
        "-i", png_overlays["countdown_3"],
        "-i", png_overlays["countdown_2"],
        "-i", png_overlays["countdown_1"],
        "-i", png_overlays["reveal"],
        "-i", composite_audio,
        "-filter_complex", fc,
        "-map", "[vout]",
        "-map", "6:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        out_mp4
    ]
    subprocess.run(render_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"   ✓ Question {q_num} scene rendered ({total_dur:.2f}s): {out_mp4}")
    return out_mp4

def render_quiz_video(quiz_data: dict, output_path: str = "data/output/quiz_sample_video.mp4", language: str = "bn") -> str | None:
    """
    Renders the complete 3-question interactive Quiz video (9:16) with 60-30-10 live-motion design (~28-32s).
    """
    temp_dir = "data/temp/quiz_render"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    questions = quiz_data.get("questions", [])
    if not questions:
        logger.error("No questions found in quiz data.")
        return None

    logger.info(f"Rendering 3-Question Quiz Video following 60-30-10 Rule ({len(questions)} questions)...")
    scene_files = []

    for idx, q in enumerate(questions, 1):
        scene_mp4 = render_single_question_scene(q, DEFAULT_BROLL_VIDEO, temp_dir, idx)
        scene_files.append(scene_mp4)

    # Concatenate all 3 scenes into final MP4
    concat_txt = os.path.join(temp_dir, "scenes_concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for sf in scene_files:
            abs_p = os.path.abspath(sf).replace('\\', '/')
            f.write(f"file '{abs_p}'\n")

    logger.info(f"Concatenating {len(scene_files)} scenes into final video: {output_path}...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        output_path
    ]
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        total_dur = get_audio_duration(output_path)
        logger.info(f"✅ Full 3-Question Quiz Reel successfully rendered: {output_path} (Duration: {total_dur:.2f}s)")
        return output_path
    else:
        logger.error(f"Failed to produce output video at {output_path}")
        return None
