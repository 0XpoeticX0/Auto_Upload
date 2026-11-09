import subprocess
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor

with open('data/stock_video_catalog.json', 'r', encoding='utf-8') as f:
    cat = json.load(f)

meta = cat.get('clip_metadata', {})
sample_urls = list(meta.keys())[:10]

os.makedirs('data/temp/timeline_test', exist_ok=True)

def extract_timeline(url):
    cid = url.split('/')[4]
    frames = []
    for ss in ['00:00:02.00', '00:00:07.00', '00:00:12.00']:
        ss_clean = ss.replace(":", "_")
        out = f'data/temp/timeline_test/{cid}_{ss_clean}.jpg'
        cmd = ['ffmpeg', '-y', '-ss', ss, '-i', url, '-vframes', '1', '-q:v', '2', out]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(out):
            frames.append(out)
    return cid, len(frames)

t0 = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(extract_timeline, sample_urls))

print('Done in', round(time.time() - t0, 2), 'seconds')
print('Results:', results)
