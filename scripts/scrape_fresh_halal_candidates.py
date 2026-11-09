import urllib.request
import re
import json
import os
import sys

POOL_PATH = "data/scraped_pure_nature_pool.json"
with open(POOL_PATH, "r", encoding="utf-8") as f:
    pool = json.load(f)

# List of pristine Halal search tags on Mixkit
TAGS = [
    ("aurora", "stars"),
    ("galaxy", "space"),
    ("glacier", "mountains"),
    ("iceberg", "sea"),
    ("sand-dunes", "desert"),
    ("waterfall", "waterfall"),
    ("night-sky", "night_sky"),
    ("clouds", "clouds"),
    ("deep-space", "space"),
    ("timelapse-sky", "sky"),
    ("ocean-waves", "ocean"),
    ("misty-mountains", "mountains"),
    ("canyon", "canyon"),
    ("river-water", "river"),
]

total_found = 0
for tag, cat in TAGS:
    if cat not in pool:
        pool[cat] = []
    for page in range(1, 6):
        url = f"https://mixkit.co/free-stock-video/{tag}/?page={page}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                matches = re.findall(r'assets\.mixkit\.co/videos/(\d+)/', html)
                for cid in matches:
                    if cid not in pool[cat]:
                        pool[cat].append(cid)
                        total_found += 1
        except Exception:
            pass

with open(POOL_PATH, "w", encoding="utf-8") as f:
    json.dump(pool, f, indent=2)

print(f"Scraped and added {total_found} fresh candidates into pool.")
