import os
import re
import subprocess
from app.logger import logger
from app.quiz.sfx import ensure_sfx_assets
from app.quiz.card_builder import render_hook_card, render_question_card, render_outro_card, clean_text_ass

BANGLA_VOICE = "bn-BD-PradeepNeural"
ENGLISH_VOICE = "en-US-ChristopherNeural"

def enhance_islamic_pronunciation(text: str) -> str:
    """Pre-processes Arabic/Islamic terms to phonetic Bengali spellings that Edge-TTS pronounces with natural accuracy."""
    if not text:
        return ""
    phonetic_map = {
        r'\bসুমাইয়্যাহ\b': 'সুমাইয়া',
        r'\bসুমাইয়্যা\b': 'সুমাইয়া',
        r'\bসুমাইয়া\b': 'সুমাইয়া',
        r'\bতাওবাহ\b': 'তাওবা',
        r'\bআত-তাওবাহ\b': 'আত-তাওবা',
        r'\bহযরত\b': 'হজরত',
        r'\bসূরা\b': 'সুরা',
        r'\bসূরার\b': 'সুরার',
        r'\bসালাত\b': 'সালাত',
        r'\bসালাতের\b': 'সালাতের',
        r'\bমিরাজ\b': 'মেরাজ',
        r'\bজিবরাঈল\b': 'জিবরাইল',
        r'\bমিকাইল\b': 'মিকায়িল',
        r'\bইসরাফিল\b': 'ইসরাফিল',
        r'\bআজরাইল\b': 'আজরাইল',
        r'\bআয়িশা\b': 'আয়েশা',
        r'\bখাদিজাহ\b': 'খাদিজা',
        r'\bফাতিমাহ\b': 'ফাতেমা',
    }
    res = text
    for pattern, replacement in phonetic_map.items():
        res = re.sub(pattern, replacement, res)
    return res

def synthesize_voice(text: str, out_mp3: str, voice: str = BANGLA_VOICE, rate: str = "+5%") -> bool:
    """Synthesizes natural, calm voiceover narration using Edge TTS at +5% (1.05x) speed."""
    clean_t = enhance_islamic_pronunciation(clean_text_ass(text))
    cmd = [
        "edge-tts",
        f"--voice={voice}",
        f"--text={clean_t}",
        f"--rate={rate}",
        "--pitch=+0Hz",
        f"--write-media={out_mp3}"
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100
    except Exception as e:
        logger.warning(f"Voice synthesis error for '{clean_t[:30]}': {e}")
        return False

def get_audio_duration(file_path: str) -> float:
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 3.0

def expand_honorifics_spoken(text: str) -> str:
    """Expands short honorific formulas to their full, respectful spoken pronunciation."""
    if not text:
        return ""
    female_names = ["আয়েশা", "খাদিজা", "ফাতেমা", "ফাতিমা", "সুমাইয়া", "হাফসা", "মরিয়ম", "মারিয়াম", "যয়নব", "যায়নব", "উম্মে কুলসুম", "রুকাইয়্যাহ", "সাওদা", "জুওয়াইরিয়া", "সফিয়্যাহ", "মাইমুনা"]
    
    # Expand (সা.) and (ﷺ)
    res = re.sub(r'\(\s*(?:সা\.|সা|ﷺ)\s*\)', 'সাল্লাল্লাহু আলাইহি ওয়া সাল্লাম', text)
    # Expand (আ.)
    res = re.sub(r'\(\s*(?:আ\.|আ)\s*\)', 'আলাইহিস সালাম', res)
    # Expand (রহ.)
    res = re.sub(r'\(\s*(?:রহ\.|রহ)\s*\)', 'রাহিমাহুল্লাহ', res)
    
    # Expand (রা.) based on gender
    def repl_ra(match):
        start = match.start()
        preceding = res[max(0, start - 35):start]
        for f in female_names:
            if f in preceding:
                return 'রাদিয়াল্লাহু আনহা'
        return 'রাদিয়াল্লাহু আনহু'
        
    res = re.sub(r'\(\s*(?:রা\.|রা)\s*\)', repl_ra, res)
    return res

def format_spoken_question(q_num: int, q_text: str, options: list[str], language: str = "bn") -> str:
    """
    Formats spoken question:
    - Fast, natural conversational delivery without artificial awkward pauses
    - No literal 'অপশন' / 'Option'
    - Strips 'ক)', 'খ)', 'গ)' (does NOT speak them)
    - Inserts 'নাকি' (or 'or') before the last option
    - Fully expands (সা.), (রা.), (আ.) honorifics
    """
    q_clean = enhance_islamic_pronunciation(expand_honorifics_spoken(clean_text_ass(q_text))).rstrip("।? ")
    
    opts_clean = []
    for opt in options:
        # Strip prefixes like "ক) ", "খ) ", "গ) ", "A) ", "B) ", "C) "
        opt_t = re.sub(r'^[কখগঘABCDEFabcdef\d]+[\)\.\:\-]\s*', '', opt.strip())
        # Strip parenthetical synonyms/duplicates
        opt_t = re.sub(r'\s*[\(\[\{][^\)\]\}]*[\)\]\}]', '', opt_t).strip()
        opt_t = enhance_islamic_pronunciation(expand_honorifics_spoken(clean_text_ass(opt_t))).strip()
        opt_t = re.sub(r'\s+', ' ', opt_t)
        opts_clean.append(opt_t)
        
    bn_nums = {1: "১", 2: "২", 3: "৩", 4: "৪", 5: "৫"}
    num_str = bn_nums.get(q_num, str(q_num))
    
    if language == "bn":
        if len(opts_clean) >= 3:
            spoken_opts = f"{opts_clean[0]}, {opts_clean[1]}, নাকি {opts_clean[2]}?"
        elif len(opts_clean) == 2:
            spoken_opts = f"{opts_clean[0]}, নাকি {opts_clean[1]}?"
        else:
            spoken_opts = ", ".join(opts_clean)
        return f"প্রশ্ন {num_str}। {q_clean}? {spoken_opts}"
    else:
        if len(opts_clean) >= 3:
            spoken_opts = f"{opts_clean[0]}, {opts_clean[1]}, or {opts_clean[2]}?"
        elif len(opts_clean) == 2:
            spoken_opts = f"{opts_clean[0]}, or {opts_clean[1]}?"
        else:
            spoken_opts = ", ".join(opts_clean)
        return f"Question {q_num}. {q_clean}? {spoken_opts}"

def render_quiz_video(quiz_data: dict, output_path: str = "data/output/quiz_sample_video.mp4", language: str = "bn") -> str | None:
    """
    Renders the complete 5-question interactive Quiz video (9:16) with fast-paced audio & visual sync (~45s).
    """
    temp_dir = "data/temp/quiz_render"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    sfx = ensure_sfx_assets()
    voice = BANGLA_VOICE if language == "bn" else ENGLISH_VOICE
    all_scene_mp4s = []
    
    # ── 1. SCENE 1: HOOK (0 - 3s) ─────────────────────────────────────────────
    logger.info("Rendering Scene 1: Hook...")
    hook = quiz_data.get("hook", {})
    hook_img = os.path.join(temp_dir, "scene_1_hook.jpg")
    render_hook_card(hook, hook_img)
    
    if language == "bn":
        hook_voice_text = f"{hook.get('headline', 'ইসলামিক জ্ঞান যাচাই করুন!')} {hook.get('sub_text', 'সময় বেশি লাগলে ভিডিওটি পজ করুন!')}"
    else:
        hook_voice_text = f"{hook.get('headline', 'Test your Islamic knowledge!')} {hook.get('sub_text', 'Pause the video if you need more time!')}"
        
    hook_voice_mp3 = os.path.join(temp_dir, "hook_voice.mp3")
    synthesize_voice(hook_voice_text, hook_voice_mp3, voice=voice, rate="+5%")
    
    hook_dur = max(2.0, get_audio_duration(hook_voice_mp3) + 0.15)
    
    # Balanced comfortable audio volume for hook
    hook_audio = os.path.join(temp_dir, "hook_audio.mp3")
    cmd_hook_audio = [
        "ffmpeg", "-y",
        "-i", hook_voice_mp3,
        "-i", sfx["whoosh"],
        "-filter_complex", "[0:a]volume=1.0[voice];[1:a]volume=0.30[sfx];[voice][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]",
        "-map", "[a]",
        "-b:a", "192k",
        hook_audio
    ]
    subprocess.run(cmd_hook_audio, capture_output=True)
    if not os.path.exists(hook_audio):
        hook_audio = hook_voice_mp3
        
    scene_1_mp4 = os.path.join(temp_dir, "scene_1_full.mp4")
    cmd_s1 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{hook_dur:.3f}",
        "-i", hook_img,
        "-i", hook_audio,
        "-c:v", "libx264", "-crf", "18", "-preset", "ultrafast", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-pix_fmt", "yuv420p",
        "-shortest",
        scene_1_mp4
    ]
    subprocess.run(cmd_s1, check=True, capture_output=True)
    all_scene_mp4s.append(scene_1_mp4)
    
    # ── 2. SCENES 2 to 4: 3 QUESTIONS (with 1.5s Timer + 1.4s Reveal) ─────────
    questions = quiz_data.get("questions", [])
    for q_idx, q in enumerate(questions, 1):
        q_num = q.get("number", q_idx)
        logger.info(f"Rendering Question {q_num}/3...")
        
        q_text = q.get("question", "")
        options = q.get("options", [])
        
        # 1. Voice for question and options WITHOUT saying 'option/অপশন'
        q_voice_text = format_spoken_question(q_num, q_text, options, language=language)
        q_voice_mp3 = os.path.join(temp_dir, f"q_{q_num}_voice.mp3")
        synthesize_voice(q_voice_text, q_voice_mp3, voice=voice, rate="+5%")
        
        voice_dur = get_audio_duration(q_voice_mp3)
        base_dur = voice_dur + 0.05  # Snappy transition to countdown
        countdown_dur = 1.5          # 1.5s thinking timer
        reveal_dur = 1.4             # 1.4s clear reveal
        total_q_dur = base_dur + countdown_dur + reveal_dur
        
        # Generate images for question states
        q_base_img = os.path.join(temp_dir, f"q_{q_num}_base.jpg")
        render_question_card(q, countdown_val=None, is_revealed=False, out_path=q_base_img)
        
        q_c2_img = os.path.join(temp_dir, f"q_{q_num}_c2.jpg")
        render_question_card(q, countdown_val=2, is_revealed=False, out_path=q_c2_img)
        
        q_c1_img = os.path.join(temp_dir, f"q_{q_num}_c1.jpg")
        render_question_card(q, countdown_val=1, is_revealed=False, out_path=q_c1_img)
        
        q_rev_img = os.path.join(temp_dir, f"q_{q_num}_rev.jpg")
        render_question_card(q, countdown_val=None, is_revealed=True, out_path=q_rev_img)
        
        # 2. Build exact timeline ffconcat file for frame-accurate video
        q_timeline_txt = os.path.join(temp_dir, f"q_{q_num}_timeline.txt")
        with open(q_timeline_txt, "w", encoding="utf-8") as f:
            f.write("ffconcat version 1.0\n")
            f.write(f"file '{os.path.abspath(q_base_img).replace(chr(92), '/')}'\n")
            f.write(f"duration {base_dur:.3f}\n")
            f.write(f"file '{os.path.abspath(q_c2_img).replace(chr(92), '/')}'\n")
            f.write("duration 1.000\n")
            f.write(f"file '{os.path.abspath(q_c1_img).replace(chr(92), '/')}'\n")
            f.write("duration 1.000\n")
            f.write(f"file '{os.path.abspath(q_rev_img).replace(chr(92), '/')}'\n")
            f.write(f"duration {reveal_dur:.3f}\n")
            f.write(f"file '{os.path.abspath(q_rev_img).replace(chr(92), '/')}'\n")
            
        # 3. Build composite audio track with 2 clock ticks + reveal bell chime
        t1 = base_dur
        t2 = base_dur + 1.0
        t_bell = base_dur + 2.0
        
        q_composite_audio = os.path.join(temp_dir, f"q_{q_num}_composite_audio.mp3")
        cmd_q_audio = [
            "ffmpeg", "-y",
            "-i", q_voice_mp3,
            "-i", sfx["clock_tick"],
            "-i", sfx["clock_tick"],
            "-i", sfx["correct_bell"],
            "-filter_complex",
            f"[1:a]adelay={int(t1*1000)}|{int(t1*1000)},volume=0.80[tick1];"
            f"[2:a]adelay={int(t2*1000)}|{int(t2*1000)},volume=0.90[tick2];"
            f"[3:a]adelay={int(t_bell*1000)}|{int(t_bell*1000)},volume=0.85[bell];"
            f"[0:a]volume=1.0[voice];"
            f"[voice][tick1][tick2][bell]amix=inputs=4:duration=longest:dropout_transition=0:normalize=0[outa]",
            "-map", "[outa]",
            "-t", f"{total_q_dur:.3f}",
            "-b:a", "192k",
            q_composite_audio
        ]
        subprocess.run(cmd_q_audio, capture_output=True)
        if not os.path.exists(q_composite_audio):
            q_composite_audio = q_voice_mp3
            
        # 4. Render entire question scene in a single clean FFmpeg invocation
        q_scene_full = os.path.join(temp_dir, f"q_{q_num}_full_scene.mp4")
        cmd_render_q = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", q_timeline_txt,
            "-i", q_composite_audio,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "ultrafast",
            "-r", "25",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-pix_fmt", "yuv420p",
            "-t", f"{total_q_dur:.3f}",
            q_scene_full
        ]
        subprocess.run(cmd_render_q, check=True, capture_output=True)
        all_scene_mp4s.append(q_scene_full)
        
    # ── 3. SCENE 7: OUTRO & SCORE EVALUATION (2 - 3s) ─────────────────────────
    logger.info("Rendering Scene 7: Outro & Score CTA...")
    outro = quiz_data.get("outro", {})
    outro_img = os.path.join(temp_dir, "scene_7_outro.jpg")
    render_outro_card(outro, outro_img)
    
    if language == "bn":
        outro_voice_text = f"{outro.get('score_prompt', '৩টিতে আপনার স্কোর কত হলো? কমেন্টে জানান!')} {outro.get('follow_cta', 'দ্বীনি জ্ঞান বৃদ্ধি করতে আমাদের ফলো করুন!')}"
    else:
        outro_voice_text = f"{outro.get('score_prompt', 'What was your score out of 3? Drop it below!')} {outro.get('follow_cta', 'Follow for weekly evaluation quizzes!')}"
        
    outro_voice_mp3 = os.path.join(temp_dir, "outro_voice.mp3")
    synthesize_voice(outro_voice_text, outro_voice_mp3, voice=voice, rate="+5%")
    
    outro_dur = max(2.0, get_audio_duration(outro_voice_mp3) + 0.15)
    
    outro_audio = os.path.join(temp_dir, "outro_audio.mp3")
    cmd_mix_outro = [
        "ffmpeg", "-y",
        "-i", outro_voice_mp3,
        "-i", sfx["outro_riser"],
        "-filter_complex", "[0:a]volume=1.0[voice];[1:a]volume=0.30[sfx];[voice][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]",
        "-map", "[a]",
        "-b:a", "192k",
        outro_audio
    ]
    subprocess.run(cmd_mix_outro, capture_output=True)
    if not os.path.exists(outro_audio):
        outro_audio = outro_voice_mp3
        
    scene_7_mp4 = os.path.join(temp_dir, "scene_7_full.mp4")
    cmd_s7 = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{outro_dur:.3f}",
        "-i", outro_img,
        "-i", outro_audio,
        "-c:v", "libx264", "-crf", "18", "-preset", "ultrafast", "-r", "25",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-pix_fmt", "yuv420p",
        "-shortest",
        scene_7_mp4
    ]
    subprocess.run(cmd_s7, check=True, capture_output=True)
    all_scene_mp4s.append(scene_7_mp4)
    
    # ── 4. CONCATENATE ALL 7 SCENE VIDEOS (With Loudness Normalization) ───────
    logger.info("Concatenating all quiz scenes into final seamless video with uniform loudness...")
    
    filter_inputs = "".join(f"[{i}:v][{i}:a]" for i in range(len(all_scene_mp4s)))
    filter_complex = f"{filter_inputs}concat=n={len(all_scene_mp4s)}:v=1:a=1[vraw][araw];[araw]loudnorm=I=-14:LRA=7:TP=-1.5[a]"
    
    cmd_concat = ["ffmpeg", "-y"]
    for v in all_scene_mp4s:
        cmd_concat.extend(["-i", v])
    cmd_concat.extend([
        "-filter_complex", filter_complex,
        "-map", "[vraw]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-r", "25",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        output_path
    ])
    subprocess.run(cmd_concat, check=True, capture_output=True)
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        total_dur = get_audio_duration(output_path)
        logger.info(f"🎉 5-Question Islamic Quiz Reel rendered successfully: {output_path} ({total_dur:.1f}s)")
        return output_path
    else:
        logger.error("Failed to concatenate final quiz video.")
        return None
