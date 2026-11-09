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

unreviewed = []
def load_candidates(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, ids in data.items():
            for cid in ids:
                cid_str = str(cid)
                if cid_str not in existing_ids and cid_str not in unreviewed:
                    unreviewed.append(cid_str)

load_candidates('data/scraped_pure_nature_pool.json')
load_candidates('data/scraped_candidates_pool.json')

print(f"Total unreviewed candidates available: {len(unreviewed)}")

offset = 0
for sheet_num in [29, 30, 31, 32]:
    chunk = unreviewed[offset:offset+80]
    out = build_sheet(chunk, sheet_num, grid_size=6)
    offset += 80
    if not out:
        break

print("Finished generating sheets 29-32!")
