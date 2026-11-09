import sys
import os
sys.path.insert(0, ".")
import json
from scripts.generate_contact_sheet import build_sheet

with open('data/scraped_pure_nature_pool.json', 'r', encoding='utf-8') as f:
    pool = json.load(f)

# Sheet 13: Mist & Fog
cands_13 = []
for k in ['mist', 'fog']:
    cands_13.extend(pool.get(k, []))
print('Sheet 13 candidates:', len(cands_13))
build_sheet(cands_13, 13, grid_size=6)

# Sheet 14: Rain, Water Droplets, Ripples
cands_14 = []
for k in ['water-droplets', 'rain', 'ripples', 'water-texture']:
    cands_14.extend(pool.get(k, []))
print('Sheet 14 candidates:', len(cands_14))
build_sheet(cands_14, 14, grid_size=6)

# Sheet 15: Waves & Ocean Water
cands_15 = pool.get('waves', [])
print('Sheet 15 candidates:', len(cands_15))
build_sheet(cands_15, 15, grid_size=6)

# Sheet 16: Space & Night Sky
cands_16 = []
for k in ['space', 'universe', 'night-sky', 'stars']:
    cands_16.extend(pool.get(k, []))
print('Sheet 16 candidates:', len(cands_16))
build_sheet(cands_16, 16, grid_size=6)

print("Batch generation of Sheets 13-16 complete!")
