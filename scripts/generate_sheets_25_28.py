import sys
import os
sys.path.insert(0, ".")
import json
from scripts.generate_contact_sheet import build_sheet, existing_ids, rejected_ids

unreviewed = []
def load_candidates(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, ids in data.items():
            for cid in ids:
                cid_str = str(cid)
                if cid_str not in existing_ids and cid_str not in rejected_ids and cid_str not in unreviewed:
                    unreviewed.append(cid_str)

load_candidates('data/scraped_pure_nature_pool.json')
load_candidates('data/scraped_candidates_pool.json')

print(f"Total unreviewed candidates available: {len(unreviewed)}")

offset = 0
for sheet_num in [25, 26, 27, 28]:
    # take up to 80 candidates per sheet to guarantee 36 valid slots
    chunk = unreviewed[offset:offset+80]
    out = build_sheet(chunk, sheet_num, grid_size=6)
    offset += 80
    if not out:
        break

print("Finished generating sheets 25-28!")
