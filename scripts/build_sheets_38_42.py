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

ranges_to_scan = [
    range(46300, 46550),
    range(47300, 47550),
    range(48300, 48550),
    range(49300, 49550),
    range(50300, 50550),
]

all_cids = []
for r in ranges_to_scan:
    all_cids.extend(list(r))

print(f"Scanning {len(all_cids)} CDN candidate IDs...", flush=True)

valid_cids = []
with ThreadPoolExecutor(max_workers=32) as ex:
    results = ex.map(check_cid, all_cids)
    for res in results:
        if res:
            valid_cids.append(res)

print(f"Found {len(valid_cids)} valid fresh CDN video clips!", flush=True)

slot = 0
for sheet_num in [38, 39, 40, 41, 42]:
    chunk = valid_cids[slot : slot + 36]
    if len(chunk) < 36:
        print(f"Not enough clips for sheet {sheet_num}: only {len(chunk)} left")
        if chunk:
            build_sheet(chunk, sheet_num, grid_size=6)
        break
    out = build_sheet(chunk, sheet_num, grid_size=6)
    slot += 36
    print(f"Built Sheet {sheet_num} successfully!", flush=True)

print("Sheets 38-42 ready for visual inspection!")
