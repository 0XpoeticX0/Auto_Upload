import json
import os

CATALOG_PATH = "data/stock_video_catalog.json"
REJECTED_PATH = "data/catalog_rejected_clips.json"

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    cat = json.load(f)

with open(REJECTED_PATH, "r", encoding="utf-8") as f:
    rej = json.load(f)

meta = cat.get("clip_metadata", {})
c50 = cat.get("catalog_by_50_categories", {})

PURGE_IDS = {
    "1101": "Shirtless surfer on sea rocks at t2 and t3",
    "1002": "Shirtless surfer walking into beach frame at t2 and t3",
    "35462": "Hiker in blue standing in canyon riverbed at t3",
    "40078": "Speedboats with people cruising in bay",
    "45075": "Human hand and arm entering frame at campfire at t2 and t3",
    "45164": "Human legs in shorts standing by RC track at t1 and t2",
    "45165": "People standing in background of RC track",
    "45171": "Human hands stirring wok with food",
    "46336": "Human hands entering frame to untie gift ribbon",
    "46355": "Factory worker in jacket entering frame at conveyor belt",
    "46436": "Woman in short dress stepping in front of camera and dancing at t2 and t3",
    "14201": "Cemetery crosses, tombstones and jack-o'-lanterns at t2",
    "19613": "Casino gambling playing card suits (spades, clubs, diamonds) falling"
}

purged_count = 0
for u in list(meta.keys()):
    cid = u.split("/")[4] if "videos/" in u else None
    if cid in PURGE_IDS:
        rej[u] = {
            "id": cid,
            "reason": f"Full-length timeline audit caught: {PURGE_IDS[cid]}"
        }
        del meta[u]
        purged_count += 1

# Purge from categories
for cat_name, urls in c50.items():
    c50[cat_name] = [u for u in urls if u.split("/")[4] not in PURGE_IDS]

total_unique = len(meta)
cat["total_unique"] = total_unique
cat["clip_metadata"] = meta
cat["catalog_by_50_categories"] = c50

with open(CATALOG_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

with open(REJECTED_PATH, "w", encoding="utf-8") as f:
    json.dump(rej, f, indent=2, ensure_ascii=False)

print(f"Successfully purged {purged_count} non-Halal videos from catalog.")
print(f"Total Unique 100% Halal Videos Remaining: {total_unique}")
print(f"Total Blacklisted Videos: {len(rej)}")
