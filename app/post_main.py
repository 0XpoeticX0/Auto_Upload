import os
import sys
import time
import argparse
from datetime import datetime, timezone
from app.logger import logger
from app.database import init_db, get_connection, purge_old_facebook_posts
from app.post.generator import generate_post_content
from app.post.card_builder import create_carousel_image_cards, create_carousel_video_slides
from app.post.uploader import upload_post_to_facebook

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def determine_target_language(cli_lang: str = None) -> str:
    """
    Determines post language. Defaults strictly to Bangla (বাংলা) for all automated runs.
    """
    if cli_lang and cli_lang.lower() in ["english", "en"]:
        return "english"
    return "bangla"

def run_facebook_post_pipeline(lang: str = None, no_upload: bool = False):
    init_db()
    purge_old_facebook_posts(days=20)  # Delete posts older than 20 days so topics can repeat
    
    target_lang = determine_target_language(lang)
    logger.info("==================================================")
    logger.info(f"--- Starting Daily 4-Slide Carousel Post Pipeline [{target_lang.upper()}] ---")
    logger.info("==================================================")
    
    # 1. Generate authentic 4-Slide Carousel content & caption with anti-repetition check
    post_data = generate_post_content(language=target_lang)
    if not post_data:
        logger.error("Pipeline aborted: Failed to generate carousel content.")
        return False
        
    post_title = post_data.get("title", "Islamic Reflection Carousel")
    first_slide = post_data.get("slides", [{}])[0] if post_data.get("slides") else {}
    quote = first_slide.get("main_text", first_slide.get("quote", ""))
    reference = first_slide.get("reference", "")
    caption = post_data.get("caption", "")
    
    # 2. Build 4 matching 1080x1350 aesthetic image cards
    output_dir = os.path.join("data", "output")
    logger.info("Rendering 4 matching 1080x1350 Carousel Image Cards...")
    carousel_cards = create_carousel_image_cards(post_data, output_dir)
    
    if not carousel_cards or len(carousel_cards) < 2:
        logger.error("Pipeline aborted: Carousel image cards creation failed.")
        return False
        
    logger.info(f"4 Carousel Image Cards created successfully: {carousel_cards}")
    
    # 3. Render 4 matching 6s 1080x1350 Micro-Video Slides with Quran audio
    logger.info("Rendering 4 Micro-Video Slides with authentic Quran recitation audio...")
    try:
        carousel_videos = create_carousel_video_slides(carousel_cards, output_dir)
        logger.info(f"4 Micro-Video Slides rendered: {carousel_videos}")
    except Exception as e:
        logger.warning(f"Micro-video rendering encountered an issue (continuing with images): {e}")
        carousel_videos = []

    # 4. Save to persistent history file & database
    from app.history import record_post_history
    record_post_history(post_title, category, quote, reference)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO facebook_posts (category, title, quote, reference, caption, image_path, status)
            VALUES (?, ?, ?, ?, ?, ?, 'GENERATED')
        ''', (category, post_title, quote, reference, caption, carousel_cards[0]))
        conn.commit()
        conn.close()
        logger.info("Saved carousel record to database and persistent history file.")
    except Exception as e:
        logger.error(f"Failed to record post in database: {e}")
        
    # 5. Upload to Facebook Page (Multi-Card Album) & Instagram Carousel
    if no_upload:
        logger.info("--- TEST MODE (NO UPLOAD): Skipping Facebook & Instagram upload ---")
        logger.info(f"Carousel slides preserved at: {carousel_cards}")
        return True
    else:
        logger.info("--- Publishing 4-Slide Carousel to Facebook & Instagram ---")
        upload_success = upload_post_to_facebook(carousel_cards, caption)
        
        if upload_success:
            logger.info(f"🎉 Daily {target_lang.capitalize()} Islamic Carousel Post Pipeline finished successfully!")
            return True
        else:
            logger.error("Daily Islamic Carousel Post Pipeline failed during upload.")
            return False

def run_facebook_post_pipeline_wrapper():
    parser = argparse.ArgumentParser(description="Run Facebook & Instagram Post Pipeline")
    parser.add_argument("--lang", choices=["english", "bangla", "auto"], default="auto", help="Post language")
    parser.add_argument("--no-upload", action="store_true", help="Generate post card without uploading to social media")
    args = parser.parse_args()
    
    cli_choice = None if args.lang == "auto" else args.lang
    success = run_facebook_post_pipeline(cli_choice, no_upload=args.no_upload)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    run_facebook_post_pipeline_wrapper()
