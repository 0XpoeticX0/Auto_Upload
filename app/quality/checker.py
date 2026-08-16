import os
from app.logger import logger
from app.database import get_connection

def check_quality(video_path: str, thumbnail_path: str, metadata: dict, topic_id: int):
    logger.info("Running Quality Control...")
    
    score = 100
    
    if not video_path or not os.path.exists(video_path):
        logger.error("QC Failed: Final video file does not exist.")
        score -= 50
        
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        logger.warning("QC Warning: Thumbnail missing.")
        score -= 20
        
    if not metadata or "youtube_title" not in metadata:
        logger.error("QC Failed: Metadata missing or incomplete.")
        score -= 30
        
    logger.info(f"Quality Score: {score}/100")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if score >= 80:
        cursor.execute("UPDATE topics SET status = 'READY' WHERE id = ?", (topic_id,))
        conn.commit()
        conn.close()
        return True
    else:
        cursor.execute("UPDATE topics SET status = 'FAILED' WHERE id = ?", (topic_id,))
        conn.commit()
        conn.close()
        logger.error("Video failed quality control check.")
        return False
