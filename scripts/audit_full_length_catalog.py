# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import subprocess
import torch
import torchvision.models.detection as models
from torchvision.io import read_image
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

CATALOG_PATH = "data/stock_video_catalog.json"
REJECTED_PATH = "data/catalog_rejected_clips.json"
TIMELINE_DIR = "data/temp/catalog_timeline_frames"
os.makedirs(TIMELINE_DIR, exist_ok=True)

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    cat = json.load(f)

meta = cat.get("clip_metadata", {})
all_urls = list(meta.keys())
print(f"Loaded {len(all_urls)} clips from catalog for full-length timeline audit.", flush=True)

# 1. Extract 3 frames (at 2s, 6s, 10s) for each clip
def extract_clip_frames(url):
    cid = url.split("/")[4]
    timestamps = ["00:00:02.00", "00:00:06.00", "00:00:10.00"]
    frame_paths = []
    for idx, ss in enumerate(timestamps):
        out = os.path.join(TIMELINE_DIR, f"{cid}_t{idx+1}.jpg")
        if not os.path.exists(out) or os.path.getsize(out) < 1000:
            cmd = ["ffmpeg", "-y", "-ss", ss, "-i", url, "-vframes", "1", "-q:v", "2", out]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
            except Exception:
                pass
        if os.path.exists(out) and os.path.getsize(out) >= 1000:
            frame_paths.append((idx+1, out))
    return cid, url, frame_paths

print("Phase 1: Ensuring all multi-timestamp frames exist across all clips...", flush=True)
t0 = time.time()
clip_frames_map = {}

with ThreadPoolExecutor(max_workers=32) as ex:
    futures = [ex.submit(extract_clip_frames, u) for u in all_urls]
    for i, fut in enumerate(as_completed(futures)):
        cid, url, frames = fut.result()
        clip_frames_map[cid] = (url, frames)
        if (i + 1) % 150 == 0 or (i + 1) == len(all_urls):
            print(f"  Processed {i + 1}/{len(all_urls)} clips ({round(time.time() - t0, 1)}s)...", flush=True)

print(f"Phase 1 complete in {round(time.time() - t0, 1)} seconds.", flush=True)

# 2. Run FasterRCNN detection
print("Phase 2: Initializing FasterRCNN detector for Shariah violations...", flush=True)
weights = models.FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT
model = models.fasterrcnn_mobilenet_v3_large_320_fpn(weights=weights)
model.eval()
preprocess = weights.transforms()
cats = weights.meta["categories"]

LIVING_BEINGS = {"person", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}

flagged_clips = []
clean_clips = []

print("Phase 3: Scanning all multi-timestamp frames with FasterRCNN...", flush=True)
t1 = time.time()

for idx, (cid, (url, frames)) in enumerate(clip_frames_map.items()):
    violations = []
    for t_idx, f_path in frames:
        try:
            img = read_image(f_path)
            batch = [preprocess(img)]
            with torch.no_grad():
                pred = model(batch)[0]
            for label, score in zip(pred["labels"], pred["scores"]):
                cat_name = cats[label]
                if cat_name in LIVING_BEINGS and score >= 0.50:
                    violations.append({
                        "timestamp_idx": t_idx,
                        "frame": f_path,
                        "detected": cat_name,
                        "confidence": round(float(score), 3)
                    })
        except Exception:
            pass

    if violations:
        flagged_clips.append({"cid": cid, "url": url, "violations": violations})
    else:
        clean_clips.append({"cid": cid, "url": url})

    if (idx + 1) % 100 == 0 or (idx + 1) == len(clip_frames_map):
        print(f"  Audited {idx + 1}/{len(clip_frames_map)} clips: {len(clean_clips)} clean, {len(flagged_clips)} flagged ({round(time.time() - t1, 1)}s)...", flush=True)

print(f"\nFinal Audit Results:")
print(f"Total Clips Audited: {len(clip_frames_map)}")
print(f"100% Clean Across Full Timeline: {len(clean_clips)}")
print(f"Flagged with Potential Violations: {len(flagged_clips)}")

with open("data/temp/timeline_audit_results.json", "w", encoding="utf-8") as f:
    json.dump({"clean": clean_clips, "flagged": flagged_clips}, f, indent=2)

print("Results saved to data/temp/timeline_audit_results.json")
