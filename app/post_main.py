import os
import sys
import time
import argparse
from datetime import datetime, timezone
from app.logger import logger
from app.database import init_db, get_connection
from app.post.generator import generate_post_content
from app.post.card_builder import create_post_image_card
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
    
    target_lang = determine_target_language(lang)
    logger.info("==================================================")
    logger.info(f"--- Starting Daily Post Pipeline [{target_lang.upper()}] ---")
    logger.info("==================================================")
    
    # 1. Generate authentic post content & caption with anti-repetition check
    post_data = generate_post_content(language=target_lang)
    if not post_data:
        logger.error("Pipeline aborted: Failed to generate post content.")
        return False
        
    post_title = post_data.get("title", "Islamic Reflection")
    category = post_data.get("category", "islamic_knowledge")
    quote = post_data.get("quote", "")
    reference = post_data.get("reference", "")
    caption = post_data.get("caption", "")
    
    # 2. Build 1080x1350 aesthetic image reflection card
    timestamp = int(time.time())
    output_image_path = os.path.join("data", "output", f"fb_post_{target_lang}_{timestamp}.jpg")
    
    logger.info(f"Generating aesthetic photo card: {output_image_path}")
    created_image = create_post_image_card(post_data, output_image_path)
    
    if not os.path.exists(created_image) or os.path.getsize(created_image) < 10000:
        logger.error("Pipeline aborted: Image card creation failed.")
        return False
        
    logger.info(f"Image card successfully created: {created_image}")
    
    # 3. Save to database to enforce 30-day anti-repetition tracking
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO facebook_posts (category, title, quote, reference, caption, image_path, status)
            VALUES (?, ?, ?, ?, ?, ?, 'GENERATED')
        ''', (category, post_title, quote, reference, caption, created_image))
        conn.commit()
        conn.close()
        logger.info("Saved post record to database for 30-day anti-repetition history.")
    except Exception as e:
        logger.error(f"Failed to record post in database: {e}")
        
    # 4. Upload to Facebook Page & Instagram
    if no_upload:
        logger.info("--- TEST MODE (NO UPLOAD): Skipping Facebook & Instagram upload ---")
        logger.info(f"Photo post card preserved at: {created_image}")
        return True
    else:
        logger.info("--- Publishing Photo Post to Facebook & Instagram ---")
        upload_success = upload_post_to_facebook(created_image, caption)
        
        if upload_success:
            logger.info(f"Daily {target_lang.capitalize()} Islamic Post Pipeline finished successfully!")
            return True
        else:
            logger.error("Daily Islamic Post Pipeline failed during upload.")
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
