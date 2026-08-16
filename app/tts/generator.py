import os
from app.logger import logger
import app.tts.edge_provider as edge_provider

def generate_all_audio(scenes: list, topic_id: int, video_format: str = "short"):
    updated_scenes = []
    base_dir = os.path.join("data", "temp", f"{topic_id}_{video_format}")
    os.makedirs(base_dir, exist_ok=True)
    
    for scene in scenes:
        scene_num = scene.get("scene_number")
        narration = scene.get("narration")
        
        if not narration:
            continue
            
        audio_path = os.path.join(base_dir, f"scene_{scene_num}.mp3")
        success = edge_provider.generate_tts(narration, audio_path)
        
        scene["audio_path"] = audio_path if success else None
        updated_scenes.append(scene)
        
    return updated_scenes
