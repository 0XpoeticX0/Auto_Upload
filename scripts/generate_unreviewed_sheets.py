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

with open('data/scraped_pure_nature_pool.json', 'r', encoding='utf-8') as f:
    pool = json.load(f)

unreviewed = []
for k, ids in pool.items():
    for cid in ids:
        if cid not in existing_ids and cid not in unreviewed:
            unreviewed.append(cid)

print(f"Total unreviewed: {len(unreviewed)}")

# Sheet 17
build_sheet(unreviewed[0:60], 17, grid_size=6)
# Sheet 18
build_sheet(unreviewed[60:120], 18, grid_size=6)
# Sheet 19
build_sheet(unreviewed[120:180], 19, grid_size=6)
# Sheet 20
build_sheet(unreviewed[180:240], 20, grid_size=6)

print("Sheets 17, 18, 19, 20 generated successfully!")
