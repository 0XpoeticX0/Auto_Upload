import sys
import os
sys.path.insert(0, ".")
import json
from concurrent.futures import ThreadPoolExecutor
from scripts.generate_contact_sheet import build_sheet, is_valid_url

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

# Permanent blacklist
for b in ["19501", "9514", "1986", "14138", "2490", "45402", "45022", "45395", "4441", "18308", "42495", "35472"]:
    existing_ids.add(b)

def check_cid(cid):
    s = str(cid)
    if s in existing_ids:
        return None
    url = f"https://assets.mixkit.co/videos/{s}/{s}-720.mp4"
    if is_valid_url(url):
        return s
    return None

# Focus on pristine nature and celestial ranges
nature_ranges = [
    range(10400, 10450), # galaxies & deep space
    range(14150, 14220), # cosmos & night sky
    range(19600, 19650), # vibrant cosmos
    range(30000, 30100), # star fields
    range(31500, 31650), # celestial
    range(32900, 33000), # nebula & cosmos
    range(48350, 48500), # landscapes
    range(49300, 49450), # landscapes & water
    range(50850, 51000), # forest & mountain
    range(51500, 51600), # nature hd
]

all_cids = []
for r in nature_ranges:
    all_cids.extend(list(r))

print(f"Scanning {len(all_cids)} nature candidate IDs...", flush=True)

valid_cids = []
with ThreadPoolExecutor(max_workers=32) as ex:
    results = ex.map(check_cid, all_cids)
    for res in results:
        if res:
            valid_cids.append(res)

print(f"Found {len(valid_cids)} valid fresh nature CDN video clips!", flush=True)

slot = 0
for sheet_num in [43, 44, 45, 46]:
    chunk = valid_cids[slot : slot + 36]
    if len(chunk) < 36:
        print(f"Not enough clips for sheet {sheet_num}: only {len(chunk)} left")
        if chunk:
            build_sheet(chunk, sheet_num, grid_size=6)
        break
    out = build_sheet(chunk, sheet_num, grid_size=6)
    slot += 36
    print(f"Built Sheet {sheet_num} successfully!", flush=True)

print("Sheets 43-46 ready for visual inspection!")
