import sys
import os
sys.path.insert(0, ".")
import json
from scripts.generate_contact_sheet import build_sheet

with open('data/stock_video_catalog.json', 'r', encoding='utf-8') as f:
    cat = json.load(f)
existing_ids = set()
for u in cat.get('clip_metadata', {}).keys():
    if 'videos/' in u:
        existing_ids.add(u.split('/')[4])

with open('data/catalog_rejected_clips.json', 'r', encoding='utf-8') as f:
    rej = json.load(f)
for u in rej.keys():
    if 'videos/' in u:
        existing_ids.add(u.split('/')[4])

with open('data/scraped_pure_nature_pool.json', 'r', encoding='utf-8') as f:
    pool = json.load(f)

unreviewed = []
for k, ids in pool.items():
    for cid in ids:
        if cid not in existing_ids and cid not in unreviewed:
            unreviewed.append(cid)

print(f"Total unreviewed: {len(unreviewed)}")

# Sheet 21
build_sheet(unreviewed[0:60], 21, grid_size=6)
# Sheet 22
build_sheet(unreviewed[60:120], 22, grid_size=6)
# Sheet 23
build_sheet(unreviewed[120:180], 23, grid_size=6)
# Sheet 24
build_sheet(unreviewed[180:240], 24, grid_size=6)

print("Sheets 21, 22, 23, 24 generated successfully!")
