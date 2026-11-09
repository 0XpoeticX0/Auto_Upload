# -*- coding: utf-8 -*-
import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

CATALOG_PATH = "data/stock_video_catalog.json"
REJECTED_PATH = "data/catalog_rejected_clips.json"
SHEETS_DIR = "data/temp/contact_sheets"

def approve_sheet(sheet_num: int, rejected_ids: list[str], default_category: str = "nature"):
    meta_path = os.path.join(SHEETS_DIR, f"sheet_{sheet_num}_meta.json")
    if not os.path.exists(meta_path):
        print(f"Meta file for sheet {sheet_num} not found!")
        return

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_list = json.load(f)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    meta_map = catalog.get("clip_metadata", {})
    by_cat = catalog.get("catalog_by_50_categories", {})

    rejected_dict = {}
    if os.path.exists(REJECTED_PATH):
        try:
            with open(REJECTED_PATH, "r", encoding="utf-8") as f:
                rejected_dict = json.load(f)
        except Exception:
            pass

    rej_set = set(str(r).strip() for r in rejected_ids)
    added_count = 0
    rejected_count = 0

    for item in meta_list:
        cid = str(item["id"])
        url = item["url"]
        if cid in rej_set:
            rejected_dict[url] = {"id": cid, "reason": "Manually rejected during visual inspection"}
            rejected_count += 1
        else:
            # Approved!
            if default_category not in by_cat:
                by_cat[default_category] = []
            if url not in by_cat[default_category]:
                by_cat[default_category].append(url)
            meta_map[url] = {
                "category": default_category,
                "title": f"Verified Halal {default_category} clip {cid}",
                "duration": 15.0,
                "id": cid,
                "url": url
            }
            added_count += 1

    total = sum(len(v) for v in by_cat.values())
    catalog["total_unique"] = total
    catalog["clip_metadata"] = meta_map
    catalog["catalog_by_50_categories"] = by_cat

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    with open(REJECTED_PATH, "w", encoding="utf-8") as f:
        json.dump(rejected_dict, f, indent=2, ensure_ascii=False)

    print(f"Sheet {sheet_num} processed: ✅ {added_count} Halal clips approved, ❌ {rejected_count} rejected. Total catalog now: {total}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python approve_sheet_clips.py <sheet_num> <cat> <comma_separated_rejected_ids>")
        sys.exit(1)
    sheet_num = int(sys.argv[1])
    cat = sys.argv[2] if len(sys.argv) > 2 else "nature"
    rej_str = sys.argv[3] if len(sys.argv) > 3 else ""
    rejections = [r.strip() for r in rej_str.split(",") if r.strip()]
    approve_sheet(sheet_num, rejections, cat)
