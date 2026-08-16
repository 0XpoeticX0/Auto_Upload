import os
import shutil
import argparse
from app.logger import logger
from app.database import init_db
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

def main():
    parser = argparse.ArgumentParser(description="YouTube Automation Pipeline (Islamic Shorts Edition)")
    parser.add_argument("--duration", type=int, help="Target duration in seconds for the short video (max 90)")
    args = parser.parse_args()
    
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
    
    logger.info(f"--- Generating Master Visuals (16:9) ---")
    scenes = generate_all_images(scenes, topic_id, "master")
    
    logger.info(f"--- Generating Master Audio & Subtitles ---")
    scenes = generate_all_audio(scenes, topic_id, "master", topic_category)
    
    logger.info(f"--- Generating Metadata ---")
    base_metadata = generate_viral_metadata(topic_id, script_data)
    if base_metadata:
        base_metadata["category"] = topic_category
        
    import copy

    for v_format in ["short", "long"]:
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
        
        if metadata and v_format == "long":
            # Remove the #Shorts tag for the horizontal video
            metadata["description"] = metadata["description"].replace("#Shorts", "#IslamicVideo").replace("#shorts", "#IslamicVideo")
        
        logger.info(f"--- Running QC ({v_format}) ---")
        passed_qc = check_quality(final_video_path, thumbnail_path, metadata, topic_id)
        
        if passed_qc and metadata:
            logger.info(f"--- Uploading ({v_format}) ---")
            # The VTT file is located in the temp directory
            vtt_path = os.path.join("data", "temp", f"{topic_id}_{v_format}", "master_audio.vtt")
            upload_to_youtube(final_video_path, metadata, thumbnail_path, vtt_path)
            
            # Only upload the vertical format to Facebook to prevent duplicate Reels
            if v_format == "short":
                upload_to_facebook(final_video_path, metadata)

    logger.info("Islamic Shorts Pipeline finished.")
    
    # --- Aggressive Disk Space Cleanup ---
    logger.info("Performing aggressive cleanup to save disk space...")
    try:
        import shutil
        temp_dir = os.path.join("data", "temp")
        output_dir = os.path.join("data", "output")
        
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
            logger.info("Wiped temp directory.")
            
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            logger.info("Wiped output directory (videos & thumbnails).")
    except Exception as e:
        logger.error(f"Error during final cleanup: {e}")
        
    logger.info("Cleanup complete. Shutting down.")

if __name__ == "__main__":
    main()
