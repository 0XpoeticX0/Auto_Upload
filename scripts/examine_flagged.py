import json

with open('data/temp/timeline_audit_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

flagged = data['flagged']
print(f"Total flagged clips: {len(flagged)}")

for item in flagged:
    cid = item['cid']
    det_list = [f"{v['detected']} (t{v['timestamp_idx']}: {v['confidence']})" for v in item['violations']]
    print(f"Clip {cid}: {', '.join(det_list)}")
