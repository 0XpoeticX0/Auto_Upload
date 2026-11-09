import os
import sys
import json
import argparse
import time
from app.logger import logger
from app.quiz.generator import generate_quiz_script
from app.quiz.renderer import render_quiz_video
from app.quiz.history import fetch_used_quiz_questions, record_used_quiz_questions, format_quiz_metadata

def run_quiz_pipeline(language: str = "bn", output_path: str = "data/output/quiz_sample_video.mp4", upload: bool = False) -> str | None:
    logger.info(f"=== Starting 5-Question Interactive Islamic Quiz Pipeline (language={language}, upload={upload}) ===")
    
    # 1. Fetch recent questions from Supabase for zero repetition (last 300 questions)
    recent_questions = fetch_used_quiz_questions(limit=300)
    logger.info(f"Loaded {len(recent_questions)} previous questions to avoid overlap (300-question window).")
    
    # 2. Generate Script
    quiz_script = generate_quiz_script(recent_questions=recent_questions, language=language)
    if not quiz_script:
        logger.error("Failed to generate quiz script.")
        return None
        
    logger.info(f"Quiz Title: {quiz_script.get('title')}")
    for q in quiz_script.get("questions", []):
        logger.info(f"Q{q.get('number')}: {q.get('question')} -> Correct: {q.get('correct_option')}")
        
    # Save script JSON for reference
    json_path = "data/output/quiz_sample_script.json"
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(quiz_script, f, indent=2, ensure_ascii=False)
    logger.info(f"Script saved to {json_path}")
    
    # 3. Render Full Video
    video_path = render_quiz_video(quiz_script, output_path=output_path, language=language)
    if not video_path or not os.path.exists(video_path):
        logger.error("Quiz video rendering failed.")
        return None
        
    logger.info(f"✅ Quiz video successfully generated: {video_path}")
    
    # 4. Upload if requested
    if upload:
        metadata = format_quiz_metadata(quiz_script)
        logger.info(f"Uploading Quiz Video: '{metadata.get('youtube_title')}'...")
        
        # Extract clean Question 1 thumbnail at t=2.0s
        thumbnail_path = None
        try:
            import subprocess
            thumb_path = os.path.splitext(video_path)[0] + "_thumb.jpg"
            subprocess.run([
                "ffmpeg", "-y",
                "-ss", "2.0",
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                thumb_path
            ], check=True, capture_output=True)
            if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                thumbnail_path = thumb_path
                logger.info(f"✅ Quiz Question 1 thumbnail extracted at t=2.0s: {thumbnail_path}")
        except Exception as e:
            logger.warning(f"Quiz thumbnail extraction notice: {e}")

        # Upload to YouTube Shorts
        yt_success = False
        try:
            from app.upload.youtube import upload_to_youtube
            yt_success = upload_to_youtube(video_path, metadata, thumbnail_path=thumbnail_path)
        except Exception as e:
            logger.warning(f"YouTube upload error: {e}")
            
        # Upload to Facebook & Instagram Reels
        fb_success = False
        try:
            from app.upload.facebook import upload_to_facebook
            fb_success = upload_to_facebook(video_path, metadata, video_type="reel", thumbnail_path=thumbnail_path)
        except Exception as e:
            logger.warning(f"Facebook upload error: {e}")
            
        logger.info(f"Upload results: YouTube={yt_success}, Facebook/Instagram={fb_success}")
        
        # Record questions to Supabase so they are NEVER repeated
        record_used_quiz_questions(quiz_script)
        
    return video_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 5-Question Islamic Quiz Reel")
    parser.add_argument("--lang", default="bn", choices=["en", "bn"], help="Language of quiz (en/bn)")
    parser.add_argument("--out", default="data/output/quiz_sample_video.mp4", help="Output MP4 path")
    parser.add_argument("--upload", action="store_true", help="Upload video to YouTube and Facebook/Instagram")
    args = parser.parse_args()
    
    run_quiz_pipeline(language=args.lang, output_path=args.out, upload=args.upload)
