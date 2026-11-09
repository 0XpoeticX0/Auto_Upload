# -*- coding: utf-8 -*-
import os
import sys
import json
import urllib.request
import subprocess
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

CATALOG_PATH = "data/stock_video_catalog.json"
REJECTED_PATH = "data/catalog_rejected_clips.json"
SHEETS_DIR = "data/temp/contact_sheets"
FRAMES_DIR = "data/temp/contact_sheet_frames"
os.makedirs(SHEETS_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    catalog = json.load(f)

meta = catalog.get("clip_metadata", {})
existing_ids = set()
for u in meta.keys():
    if "videos/" in u:
        cid = u.split("/")[4]
        existing_ids.add(cid)

rejected_ids = set()
if os.path.exists(REJECTED_PATH):
    try:
        with open(REJECTED_PATH, "r", encoding="utf-8") as f:
            rej = json.load(f)
            for u in rej.keys():
                if "videos/" in u:
                    rejected_ids.add(u.split("/")[4])
    except Exception:
        pass

# Add permanent blacklisted IDs
for b in ["19501", "9514", "1986", "14138", "2490", "45402", "45022", "45395", "4441", "18308", "42495", "35472"]:
    rejected_ids.add(b)

def is_valid_url(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return int(resp.headers.get('Content-Length', 0)) > 1200000
    except Exception:
        pass
    return False

def extract_frame(url: str, clip_id: str) -> str | None:
    out_frame = os.path.join(FRAMES_DIR, f"frame_{clip_id}.jpg")
    if os.path.exists(out_frame) and os.path.getsize(out_frame) > 1000:
        return out_frame
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:02.50", "-i", url,
        "-vframes", "1", "-q:v", "2", out_frame
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(out_frame) and os.path.getsize(out_frame) > 1000:
        return out_frame
    return None

from concurrent.futures import ThreadPoolExecutor

def process_candidate(cid):
    if cid in existing_ids or cid in rejected_ids:
        return None
    url = f"https://assets.mixkit.co/videos/{cid}/{cid}-720.mp4"
    if not is_valid_url(url):
        return None
    frame = extract_frame(url, cid)
    if frame:
        return (cid, url, frame)
    return None

def build_sheet(candidate_ids: list[str], sheet_num: int, grid_size: int = 5) -> str | None:
    total_slots = grid_size * grid_size
    valid_clips = []
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        results = executor.map(process_candidate, candidate_ids)
        for res in results:
            if res:
                valid_clips.append(res)
                if len(valid_clips) >= total_slots:
                    break

    if not valid_clips:
        print(f"No valid clips found for sheet {sheet_num}")
        return None

    tile_w, tile_h = 384, 216
    grid_img = Image.new("RGB", (grid_size * tile_w, grid_size * tile_h), (15, 15, 15))
    draw = ImageDraw.Draw(grid_img)

    sheet_meta = []
    for idx, (cid, url, frame_path) in enumerate(valid_clips):
        row = idx // grid_size
        col = idx % grid_size
        x = col * tile_w
        y = row * tile_h
        try:
            im = Image.open(frame_path).resize((tile_w, tile_h))
            grid_img.paste(im, (x, y))
            # Draw badge with clip ID
            draw.rectangle([x, y, x + 85, y + 26], fill=(0, 0, 0))
            draw.text((x + 6, y + 5), cid, fill=(255, 255, 255))
            sheet_meta.append({"id": cid, "url": url, "slot": idx + 1})
        except Exception:
            pass

    out_sheet = os.path.join(SHEETS_DIR, f"sheet_{sheet_num}.jpg")
    grid_img.save(out_sheet, quality=90)
    
    meta_path = os.path.join(SHEETS_DIR, f"sheet_{sheet_num}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(sheet_meta, f, indent=2)
        
    print(f"Generated sheet {sheet_num} with {len(sheet_meta)} clips at {out_sheet}", flush=True)
    return out_sheet

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cat":
        cat_name = sys.argv[2]
        sheet_idx = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        with open("data/scraped_candidates_pool.json", "r", encoding="utf-8") as f:
            pool = json.load(f)
        cands = pool.get(cat_name, [])
        print(f"Loaded {len(cands)} candidates for category '{cat_name}'")
        build_sheet(cands, sheet_idx, grid_size=5)
    else:
        sheet_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        start_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        end_id = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
        cands = [str(i) for i in range(start_id, end_id)]
        build_sheet(cands, sheet_idx, grid_size=5)
