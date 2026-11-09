import os
import json
from PIL import Image, ImageDraw

RESULTS_PATH = "data/temp/timeline_audit_results.json"
OUT_SHEET = "data/temp/flagged_timeline_sheet.jpg"

if not os.path.exists(RESULTS_PATH):
    print("Results file not found!")
    exit(0)

with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

flagged = data.get("flagged", [])
print(f"Total flagged clips to inspect: {len(flagged)}")

if not flagged:
    print("Zero flagged clips! All clips are 100% clean!")
    exit(0)

# Build a filmstrip sheet where each row is 1 clip with 3 frames (t1, t2, t3)
tile_w, tile_h = 320, 180
rows = len(flagged)
sheet_w = 3 * tile_w
sheet_h = rows * tile_h

sheet_img = Image.new("RGB", (sheet_w, sheet_h), (20, 20, 20))
draw = ImageDraw.Draw(sheet_img)

for r_idx, item in enumerate(flagged):
    cid = item["cid"]
    y = r_idx * tile_h
    for c_idx, t_name in enumerate(["t1", "t2", "t3"]):
        f_path = f"data/temp/catalog_timeline_frames/{cid}_{t_name}.jpg"
        x = c_idx * tile_w
        if os.path.exists(f_path):
            try:
                im = Image.open(f_path).resize((tile_w, tile_h))
                sheet_img.paste(im, (x, y))
            except Exception:
                pass
        # Draw label
        draw.rectangle([x, y, x + 110, y + 24], fill=(0, 0, 0))
        draw.text((x + 5, y + 5), f"{cid} ({t_name})", fill=(255, 255, 255))

sheet_img.save(OUT_SHEET, quality=90)
print(f"Saved flagged inspection sheet to {OUT_SHEET}")
