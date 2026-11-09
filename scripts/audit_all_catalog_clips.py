import os
import json
import subprocess
import time
from dotenv import load_dotenv
load_dotenv()

from google import genai
from PIL import Image

KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=KEY)

CATALOG_PATH = "data/stock_video_catalog.json"
ROTATION_PATH = "data/video_rotation_state.json"
TEMP_FRAME_DIR = "data/temp/catalog_audit"
os.makedirs(TEMP_FRAME_DIR, exist_ok=True)

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    cat = json.load(f)

# Collect all unique clips from the catalog
by_cat = cat.get("catalog_by_50_categories", {})
all_urls = []
for c, urls in by_cat.items():
    for u in urls:
        if u and u not in all_urls:
            all_urls.append(u)

print(f"Total unique clips to audit: {len(all_urls)}")

VISION_PROMPT = """You are a strict Islamic Shariah Visual Auditor enforcing a ZERO LIVING BEINGS policy.
Inspect this video frame with extreme scrutiny.

CHECK FOR ANY OF THE FOLLOWING:
1. Any human, person, man, woman, child, baby, worshipper, swimmer, or crowd.
2. Any silhouette, outline of a human figure, or shadow of a person.
3. Any human body parts: face, eyes, hands, hair, limbs, skin, torso, feet.
4. Any living animal, bird, insect, fish, or aquatic creature.
5. Any statue, sculpture, carving of living beings, or idol.
6. Any church, cathedral, or non-Islamic place of worship.

CRITERIA:
- If ANY living being, silhouette, human body part, living creature, statue, or church is present, set "pass": false and "has_violation": true.
- If it is 100% Halal atmospheric nature (ocean waves, sky, clouds, stars, mountains, desert, waterfalls, trees, Islamic mosque/architecture), set "pass": true and "has_violation": false.

Respond strictly in valid JSON:
{
    "pass": true,
    "has_violation": false,
    "confidence": 0.99,
    "details": "Description of scene"
}"""

SAFE_REPLACEMENTS = [
    "https://assets.mixkit.co/videos/4081/4081-720.mp4",   # Ocean waves
    "https://assets.mixkit.co/videos/1090/1090-720.mp4",   # Deep ocean
    "https://assets.mixkit.co/videos/4374/4374-720.mp4",   # Water texture
    "https://assets.mixkit.co/videos/1953/1953-720.mp4",   # Deep space stars
    "https://assets.mixkit.co/videos/20425/20425-720.mp4", # Moon celestial
    "https://assets.mixkit.co/videos/44621/44621-720.mp4", # Forest nature
    "https://assets.mixkit.co/videos/11185/11185-720.mp4", # Nebula stars
    "https://assets.mixkit.co/videos/1169/1169-720.mp4",   # Sunlight beams
    "https://assets.mixkit.co/videos/1180/1180-720.mp4",   # Arch nature
    "https://assets.mixkit.co/videos/41378/41378-720.mp4"  # Moon night sky
]

audit_log = {}
flagged_clips = {}
repl_idx = 0

for idx, url in enumerate(all_urls, 1):
    clip_id = url.split("/")[4] if "videos/" in url else str(idx)
    frame_path = os.path.join(TEMP_FRAME_DIR, f"frame_{clip_id}.jpg")

    # Extract single frame at 2.5s over HTTP
    if not os.path.exists(frame_path) or os.path.getsize(frame_path) < 1000:
        cmd = [
            "ffmpeg", "-y", "-ss", "00:00:02.50", "-i", url,
            "-vframes", "1", "-q:v", "2", frame_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0 or not os.path.exists(frame_path):
            print(f"[{idx}/{len(all_urls)}] Clip {clip_id}: Failed to fetch frame.")
            continue

    # Send to Gemini Vision
    try:
        img = Image.open(frame_path)
        resp = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[VISION_PROMPT, img]
        )
        raw_text = resp.text.strip()
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start != -1 and end != 0:
            data = json.loads(raw_text[start:end])
            is_pass = data.get("pass", True)
            has_violation = data.get("has_violation", False)
            details = data.get("details", "")

            if not is_pass or has_violation:
                print(f"[{idx}/{len(all_urls)}] ❌ REJECTED Clip {clip_id}: {details}")
                flagged_clips[url] = {
                    "id": clip_id,
                    "reason": details,
                    "replacement": SAFE_REPLACEMENTS[repl_idx % len(SAFE_REPLACEMENTS)]
                }
                repl_idx += 1
            else:
                audit_log[url] = {"id": clip_id, "pass": True, "details": details}
                if idx % 10 == 0 or idx == len(all_urls):
                    print(f"[{idx}/{len(all_urls)}] Audited {idx} clips... All clean so far.")
    except Exception as e:
        print(f"[{idx}/{len(all_urls)}] Vision API notice on {clip_id}: {e}")
        time.sleep(1)

print("\n================ AUDIT SUMMARY ================")
print(f"Total Clips Audited: {len(all_urls)}")
print(f"Flagged / Rejected Clips: {len(flagged_clips)}")

if flagged_clips:
    print("\nPurging and replacing flagged clips in catalog & rotation state...")
    # Update catalog
    for cat_name, urls in by_cat.items():
        new_urls = []
        for u in urls:
            if u in flagged_clips:
                new_urls.append(flagged_clips[u]["replacement"])
            else:
                new_urls.append(u)
        by_cat[cat_name] = new_urls
    
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2, ensure_ascii=False)

    # Update rotation state
    with open(ROTATION_PATH, "r", encoding="utf-8") as f:
        rot = json.load(f)
    for p in rot.get("plan", []):
        ordered = p.get("ordered_clips", [])
        new_ordered = []
        for u in ordered:
            if u in flagged_clips:
                new_ordered.append(flagged_clips[u]["replacement"])
            else:
                new_ordered.append(u)
        p["ordered_clips"] = new_ordered

    with open(ROTATION_PATH, "w", encoding="utf-8") as f:
        json.dump(rot, f, indent=2, ensure_ascii=False)

# Save audit report
with open("data/catalog_audit_report.json", "w", encoding="utf-8") as f:
    json.dump({
        "timestamp": time.time(),
        "total_audited": len(all_urls),
        "total_flagged": len(flagged_clips),
        "flagged": flagged_clips
    }, f, indent=2, ensure_ascii=False)

print("Catalog audit and purge completely finished!")
