import os
import json
from PIL import Image, ImageDraw, ImageFont

with open('data/temp/timeline_audit_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

flagged = data['flagged']

# Filter flagged clips that have living being detections
targeted_cids = []
for item in flagged:
    cid = item['cid']
    for v in item['violations']:
        if v['detected'] in ['person', 'cow', 'horse', 'dog', 'cat', 'sheep', 'bird', 'elephant']:
            if cid not in targeted_cids:
                targeted_cids.append(cid)
            break

print(f"Total targeted flagged clips: {len(targeted_cids)}")

tile_w, tile_h = 320, 180

def build_review_sheet(cids, sheet_idx):
    rows = len(cids)
    img = Image.new("RGB", (3 * tile_w, rows * tile_h), (25, 25, 25))
    draw = ImageDraw.Draw(img)

    for r_idx, cid in enumerate(cids):
        y = r_idx * tile_h
        for c_idx, t_name in enumerate(["t1", "t2", "t3"]):
            x = c_idx * tile_w
            f_path = f"data/temp/catalog_timeline_frames/{cid}_{t_name}.jpg"
            if os.path.exists(f_path):
                try:
                    tile = Image.open(f_path).resize((tile_w, tile_h))
                    img.paste(tile, (x, y))
                except Exception:
                    pass
            draw.rectangle([x, y, x + 100, y + 22], fill=(0, 0, 0))
            draw.text((x + 5, y + 4), f"{cid}_{t_name}", fill=(255, 255, 255))

    out_path = f"data/temp/flagged_review_sheet_{sheet_idx}.jpg"
    img.save(out_path, quality=88)
    print(f"Saved {out_path} with {len(cids)} clips.")

# Split into chunks of 15
for idx, i in enumerate(range(0, len(targeted_cids), 15)):
    chunk = targeted_cids[i:i+15]
    build_review_sheet(chunk, idx + 1)
