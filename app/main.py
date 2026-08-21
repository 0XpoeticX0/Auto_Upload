import os
import shutil
import argparse
from app.logger import logger
from app.database import init_db, purge_old_topics
from app.research.discover import run_discovery
from app.scripts.generator import generate_script
from app.tts.edge_provider import generate_all_audio
from app.visuals.generator import generate_all_images
from app.video.editor import render_final_video
from app.thumbnail.generator import generate_thumbnail
from app.metadata.generator import generate_viral_metadata
from app.quality.checker import check_quality
from app.upload.youtube import upload_to_youtube
from app.upload.facebook import upload_to_facebook

def cleanup_temp_folder():
    temp_dir = os.path.join("data", "temp")
    if os.path.exists(temp_dir):
        logger.info("Cleaning up old temp files...")
        try:
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean temp folder: {e}")

def main(no_upload: bool = False):
    parser = argparse.ArgumentParser(description="YouTube Automation Pipeline (Islamic Shorts Edition)")
    parser.add_argument("--duration", type=int, help="Target duration in seconds for the short video (max 90)")
    parser.add_argument("--no-upload", action="store_true", help="Render video without uploading to social media")
    args, unknown = parser.parse_known_args()
    
    if args.no_upload:
        no_upload = True
        
    target_short_duration = args.duration
    if not target_short_duration:
        target_short_duration = 90
    else:
        target_short_duration = min(target_short_duration, 90)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    logger.info("--- Starting Youtube Automation Pipeline (Islamic Shorts) ---")
    
    cleanup_temp_folder()
    init_db()
    purge_old_topics(days=40)  # Delete topics older than 40 days so they can repeat
    
    topic = run_discovery()
    if not topic:
        logger.error("No topic available.")
        return
        
    topic_id = topic["id"]
    topic_title = topic["title"]
    topic_category = topic.get("category", "islamic_knowledge")
    logger.info(f"Content category this run: {topic_category.upper().replace('_', ' ')}")
    
    script_data = generate_script(topic_id, topic_title, "short", target_short_duration, topic_category, series_info=topic)
    if not script_data:
        logger.error(f"Failed to generate script. Exiting.")
        return
        
    scenes = script_data.get("scenes", [])
    
    logger.info(f"--- Generating Visuals (9:16 Vertical) ---")
    scenes = generate_all_images(scenes, topic_id, "short", pillar_category=topic_category)
    
    logger.info(f"--- Generating Audio & Subtitles ---")
    scenes = generate_all_audio(scenes, topic_id, "short", topic_category)
    
    logger.info(f"--- Generating Metadata ---")
    base_metadata = generate_viral_metadata(topic_id, script_data)
    if base_metadata:
        base_metadata["category"] = topic_category
        
    import copy

    for v_format in ["short"]:
        logger.info(f"--- Rendering Video ({v_format}) ---")
        final_video_path = render_final_video(scenes, topic_id, v_format)
        
        if not final_video_path:
            logger.error(f"Video rendering failed for {v_format}")
            continue
            
        logger.info(f"--- Generating Thumbnail ({v_format}) ---")
        base_image = scenes[0].get("image_path") if scenes else None
        thumbnail_path = generate_thumbnail(script_data.get("title", topic_title), topic_id, base_image)
        
        # Deepcopy metadata so we can safely modify it per format
        metadata = copy.deepcopy(base_metadata) if base_metadata else None
        
        # Fallback metadata if AI generation failed
        if not metadata:
            logger.warning("Metadata generation failed. Using fallback metadata for upload.")
            metadata = {
                "youtube_title": topic_title[:60],
                "facebook_title": topic_title,
                "description": f"{topic_title}\n\n📚 Authentic Sources:\n- Quran & Authentic Sunnah\n\n🔔 Subscribe on YouTube: https://www.youtube.com/@dailydos-no1\n👍 Follow on Facebook: https://www.facebook.com/DailyDosNo1\n\n#Islam #Islamic #Quran #Shorts",
                "thumbnail_hook": topic_title[:20],
                "tags": ["Islam", "Islamic", "Quran", "Hadith", "Muslim", "Shorts"],
            }
        
        logger.info(f"--- Running QC ({v_format}) ---")
        passed_qc = check_quality(final_video_path, thumbnail_path, metadata, topic_id)
        
        if passed_qc:
            if no_upload:
                logger.info("--- TEST MODE (NO UPLOAD): Skipping YouTube & Facebook uploads ---")
                import subprocess
                subprocess.run(["ffmpeg", "-y", "-ss", "00:00:03", "-i", final_video_path, "-vframes", "1", "data/output/preview_frame_1.jpg"], check=False)
                subprocess.run(["ffmpeg", "-y", "-ss", "00:00:08", "-i", final_video_path, "-vframes", "1", "data/output/preview_frame_2.jpg"], check=False)
                subprocess.run(["ffmpeg", "-y", "-ss", "00:00:14", "-i", final_video_path, "-vframes", "1", "data/output/preview_frame_3.jpg"], check=False)
                logger.info(f"Verification frames and video preserved in data/output/ for inspection.")
            else:
                logger.info(f"--- Uploading ({v_format}) ---")
                vtt_path = scenes[0].get("vtt_path")
                upload_to_youtube(final_video_path, metadata, thumbnail_path, vtt_path)
                upload_to_facebook(final_video_path, metadata)

    logger.info("Islamic Shorts Pipeline finished.")
    
    # --- Aggressive Disk Space Cleanup ---
    if not no_upload:
        logger.info("Performing aggressive cleanup to save disk space...")
        try:
            import shutil
            temp_dir = os.path.join("data", "temp")
            output_dir = os.path.join("data", "output")
            
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info("Wiped temp directory.")
                
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
                logger.info("Wiped output directory (videos & thumbnails).")
                
        except Exception as e:
            logger.error(f"Failed during cleanup: {e}")
            
    logger.info("Pipeline run complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Islamic Shorts Pipeline")
    parser.add_argument("--no-upload", action="store_true", help="Run full pipeline and render video without uploading to social media")
    args = parser.parse_args()
    main(no_upload=args.no_upload)
