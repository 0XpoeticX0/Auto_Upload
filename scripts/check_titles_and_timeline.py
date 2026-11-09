import json

with open('data/stock_video_catalog.json', 'r', encoding='utf-8') as f:
    cat = json.load(f)

meta = cat.get('clip_metadata', {})
suspicious_keywords = [
    'woman', 'man', 'girl', 'boy', 'person', 'people', 'human', 'hand', 'face', 'walk', 
    'run', 'swim', 'couple', 'dancer', 'model', 'dog', 'cat', 'bird', 'animal', 'horse', 
    'cross', 'church', 'statue', 'bikini', 'beach crowd', 'tourist', 'child', 'kid',
    'surfer', 'hiker', 'feet', 'yoga', 'athlete', 'worship', 'portrait', 'posing'
]

flagged = []
for u, d in meta.items():
    title = (d.get('title') or '').lower()
    for kw in suspicious_keywords:
        # Check whole word match or plural
        if kw in title:
            flagged.append((d.get('id'), kw, title, u))
            break

print(f"Total flagged by suspicious keywords in title: {len(flagged)}")
for cid, kw, title, u in flagged:
    print(f"ID {cid} (matched '{kw}'): '{title}' -> {u}")
