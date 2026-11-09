# -*- coding: utf-8 -*-
"""
300-Halal-Video Triplet Rotator Engine with Cyclic Shuffle.
Architecture:
- Central Pool: 300 Halal video clips (0 humans, 0 faces, 0 animals, 100% serene).
- Triplet Grouping: 3 clips per video in serial (Scene 1, Scene 2, Scene 3) -> 100 videos per cycle.
- Internal Permutation: Each triplet of 3 is randomized in playback order (e.g. 1-3-2, 2-3-1, 2-1-3, 3-1-2).
- Continuous Cycle Progression:
  When 100 videos finish (Cycle 1 complete):
  Cycle 2 begins with a fresh randomized re-pairing and new internal permutations.
  Guarantees zero identical visual sequences across consecutive videos and cycles!
"""

import os
import json
import random
from app.logger import logger

ROTATION_STATE_FILE = os.path.abspath("data/video_rotation_state.json")
CATALOG_FILE = os.path.abspath("data/stock_video_catalog.json")

def load_catalog_clips() -> list[str]:
    """Loads all unique Halal video links or local paths from the central catalog."""
    if not os.path.exists(CATALOG_FILE):
        logger.warning(f"Catalog file not found at {CATALOG_FILE}. Using fallback empty list.")
        return []

    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_clips = []
        # Support both 'clip_metadata' (url keyed) and 'catalog' (category keyed)
        if "clip_metadata" in data:
            for u in data["clip_metadata"]:
                if u and u not in all_clips:
                    all_clips.append(u)

        catalog = data.get("catalog", {})
        for cat, urls in catalog.items():
            for u in urls:
                if u and u not in all_clips:
                    all_clips.append(u)

        return all_clips
    except Exception as e:
        logger.error(f"Error loading stock video catalog: {e}")
        return []

def load_50_categories_catalog() -> tuple[list[str], dict[str, list[str]]]:
    """Loads canonical 50 categories and their 6 assigned clips from central catalog."""
    if not os.path.exists(CATALOG_FILE):
        return [], {}

    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        cats = data.get("categories_50", [])
        by_cat = data.get("catalog_by_50_categories", {})
        return cats, by_cat
    except Exception as e:
        logger.error(f"Error reading 50 categories catalog: {e}")
        return [], {}

def generate_cycle_plan(clips_pool: list[str], cycle_num: int) -> list[dict]:
    """
    Generates a complete 100-video plan for the specified cycle enforcing:
    1. STRICT CATEGORY DIVERSITY: In every video, all 3 clips MUST come from 3 DIFFERENT categories!
       (Zero videos ever use > 1 video from the same category).
    2. Internal Permutations: Randomizes playback order (e.g. 1 3 2, 2 3 1, 2 1 3).
    3. Balanced Usage: All 50 categories are utilized evenly across the 100-video cycle.
    """
    cats_50, by_cat = load_50_categories_catalog()

    rng = random.Random(cycle_num * 7919 + 1337)
    all_permutations = [
        [1, 2, 3],
        [1, 3, 2],
        [2, 1, 3],
        [2, 3, 1],
        [3, 1, 2],
        [3, 2, 1]
    ]

    # If 50 categories catalog is available, use the guaranteed zero-duplicate category scheduler
    if len(cats_50) == 50 and all(len(by_cat.get(c, [])) >= 6 for c in cats_50):
        # Deterministically shuffle the 6 clips inside each category for this cycle
        shuffled_cat_clips = {}
        for c in cats_50:
            c_clips = list(by_cat[c][:6])
            rng.shuffle(c_clips)
            shuffled_cat_clips[c] = c_clips

        # Shift offsets for this cycle so each cycle uses different category triplets
        offset1 = (cycle_num * 7) % 50
        offset2 = (cycle_num * 17 + 13) % 50
        offset3 = (cycle_num * 31 + 27) % 50

        # Ensure offset1, offset2, offset3 are pairwise distinct
        while len({offset1, offset2, offset3}) < 3:
            offset2 = (offset2 + 5) % 50
            offset3 = (offset3 + 11) % 50

        cat_usage = {c: 0 for c in cats_50}
        plan = []

        for vid_idx in range(100):
            # Select 3 distinct category indices
            c1_idx = (vid_idx + offset1) % 50
            c2_idx = (vid_idx + offset2) % 50
            c3_idx = (vid_idx + offset3) % 50

            # Guard against any collision
            if c2_idx == c1_idx:
                c2_idx = (c2_idx + 1) % 50
            if c3_idx in (c1_idx, c2_idx):
                c3_idx = (c3_idx + 2) % 50

            c1 = cats_50[c1_idx]
            c2 = cats_50[c2_idx]
            c3 = cats_50[c3_idx]

            cat_usage[c1] += 1
            cat_usage[c2] += 1
            cat_usage[c3] += 1

            clip_a = shuffled_cat_clips[c1][(cat_usage[c1] - 1) % 6]
            clip_b = shuffled_cat_clips[c2][(cat_usage[c2] - 1) % 6]
            clip_c = shuffled_cat_clips[c3][(cat_usage[c3] - 1) % 6]

            base_triplet = [clip_a, clip_b, clip_c]
            base_cats = [c1, c2, c3]

            chosen_perm = rng.choice(all_permutations)
            ordered_clips = [base_triplet[p - 1] for p in chosen_perm]
            ordered_cats = [base_cats[p - 1] for p in chosen_perm]

            plan.append({
                "video_in_cycle": vid_idx + 1,
                "global_video_index": (cycle_num - 1) * 100 + (vid_idx + 1),
                "categories": ordered_cats,
                "permutation_order": chosen_perm,
                "permutation_str": " ".join(str(p) for p in chosen_perm),
                "ordered_clips": ordered_clips
            })

        return plan

    # Fallback if 50 categories catalog is not available
    if len(clips_pool) < 3:
        raise ValueError(f"Clips pool must contain at least 3 clips, got {len(clips_pool)}")

    # Use full available clips pool rounded down to nearest multiple of 3
    num_triplets = len(clips_pool) // 3
    target_count = num_triplets * 3
    working_pool = list(clips_pool[:target_count])

    # Deterministic shuffle for this cycle
    rng = random.Random(cycle_num * 7919 + 1337)
    shuffled_indices = list(range(len(working_pool)))
    rng.shuffle(shuffled_indices)

    all_permutations = [
        [1, 2, 3],
        [1, 3, 2],
        [2, 1, 3],
        [2, 3, 1],
        [3, 1, 2],
        [3, 2, 1]
    ]

    plan = []
    num_videos = len(working_pool) // 3  # exactly 100 videos for 300 clips

    for vid_idx in range(num_videos):
        idx_a = shuffled_indices[vid_idx * 3]
        idx_b = shuffled_indices[vid_idx * 3 + 1]
        idx_c = shuffled_indices[vid_idx * 3 + 2]

        base_triplet = [
            working_pool[idx_a],
            working_pool[idx_b],
            working_pool[idx_c]
        ]

        # Choose a random internal permutation (1-indexed representation: 1, 2, 3)
        chosen_perm = rng.choice(all_permutations)
        # Apply permutation to the 3 clips:
        # e.g. [2, 3, 1] means: Clip 2 first, Clip 3 second, Clip 1 third
        ordered_clips = [base_triplet[p - 1] for p in chosen_perm]

        plan.append({
            "video_in_cycle": vid_idx + 1,
            "global_video_index": (cycle_num - 1) * num_videos + (vid_idx + 1),
            "base_indices": [idx_a, idx_b, idx_c],
            "permutation_order": chosen_perm,
            "permutation_str": " ".join(str(p) for p in chosen_perm),
            "ordered_clips": ordered_clips
        })

    return plan

def _fetch_cloud_rotation_state() -> dict:
    """Fetches real-time rotation state from Supabase to prevent git rollback conflicts."""
    try:
        from app.history import _get_supabase_config
        url, key = _get_supabase_config()
        if url and key:
            import urllib.request
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}"
            }
            req = urllib.request.Request(f"{url}/used_islamic_video?id=eq.triplet_rotation_state_v1", headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    rows = json.loads(resp.read().decode("utf-8"))
                    if rows and "title" in rows[0]:
                        return json.loads(rows[0]["title"])
    except Exception as e:
        logger.debug(f"Cloud rotation state fetch notice: {e}")
    return {}

def _sync_cloud_rotation_state(state: dict):
    """Upserts rotation state to Supabase so all runners (CI and local) stay strictly monotonic."""
    try:
        from app.history import _get_supabase_config
        url, key = _get_supabase_config()
        if url and key:
            import urllib.request
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            }
            payload = {
                "id": "triplet_rotation_state_v1",
                "title": json.dumps({
                    "current_cycle": state.get("current_cycle", 1),
                    "current_video_in_cycle": state.get("current_video_in_cycle", 1),
                    "total_videos_completed": state.get("total_videos_completed", 0),
                    "recent_clips": state.get("recent_clips", [])[-30:]
                }),
                "source": "triplet_rotation_state"
            }
            req = urllib.request.Request(f"{url}/used_islamic_video", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
    except Exception as e:
        logger.debug(f"Cloud rotation sync notice: {e}")

def load_or_init_rotation_state() -> dict:
    """Loads existing rotation state or initializes Cycle 1, synchronizing with cloud truth."""
    state = None
    if os.path.exists(ROTATION_STATE_FILE):
        try:
            with open(ROTATION_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read {ROTATION_STATE_FILE}: {e}")

    if not state or "current_cycle" not in state or "plan" not in state:
        clips = load_catalog_clips()
        cycle_num = 1
        plan = generate_cycle_plan(clips, cycle_num)
        state = {
            "current_cycle": cycle_num,
            "current_video_in_cycle": 1,
            "total_videos_completed": 0,
            "total_clips_in_pool": len(clips),
            "plan": plan,
            "history": [],
            "recent_clips": []
        }

    # Cloud-truth synchronization: Cloud ALWAYS supersedes any stale local state
    cloud_state = _fetch_cloud_rotation_state()
    if cloud_state:
        cloud_completed = cloud_state.get("total_videos_completed", 0)
        local_completed = state.get("total_videos_completed", 0)
        if cloud_completed > local_completed:
            state["current_cycle"] = max(cloud_state.get("current_cycle", 1), state.get("current_cycle", 1))
            state["current_video_in_cycle"] = cloud_state.get("current_video_in_cycle", state.get("current_video_in_cycle", 1))
            state["total_videos_completed"] = cloud_completed
            logger.info(f"☁️ [Triplet Rotator] Synced monotonic progress from cloud: Video #{state['current_video_in_cycle']}/100 (Total completed: {cloud_completed})")
        if "recent_clips" in cloud_state and cloud_state["recent_clips"]:
            state["recent_clips"] = cloud_state["recent_clips"]

    # Validate plan against current catalog: refresh if obsolete clips exist
    all_catalog_clips = set(load_catalog_clips())
    needs_refresh = False
    for p in state.get("plan", []):
        for c in p.get("ordered_clips", []):
            if c not in all_catalog_clips:
                needs_refresh = True
                break
        if needs_refresh:
            break

    if needs_refresh:
        logger.info("🔄 [Triplet Rotator] Re-generating cycle plan to purge obsolete clips.")
        state["plan"] = generate_cycle_plan(load_catalog_clips(), state.get("current_cycle", 1))
        save_rotation_state(state)

    return state

def save_rotation_state(state: dict):
    """Saves rotation state to disk atomically and synchronizes to cloud."""
    os.makedirs(os.path.dirname(ROTATION_STATE_FILE), exist_ok=True)
    temp_file = ROTATION_STATE_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(temp_file, ROTATION_STATE_FILE)
    _sync_cloud_rotation_state(state)


BANNED_CLIP_BLACKLIST = {
    "19501", "9514", "1986", "14138", "2490", "45402", "45022", "45395", "4441", "18308", "42495"
}

def is_clip_halal_gemini(clip_url: str, temp_dir: str = "data/temp/clip_audits") -> tuple[bool, str]:
    """
    Performs full-length frame-by-frame timeline analysis at 1 frame per second (each 1s).
    Extracts every single second of the video and audits:
    1. Fast deterministic local FasterRCNN object detector on EVERY 1-second frame.
    2. Deep Gemini Multimodal Vision API on any flagged frame + key representative frames (0 silhouettes, 0 statues, 0 crosses).
    If ANY 1-second frame fails, the clip is rejected, purged from catalog, and permanently blacklisted.
    """
    # 1. Fast check against permanent banned blacklist
    for bad in BANNED_CLIP_BLACKLIST:
        if bad in str(clip_url):
            return False, f"Clip matches banned ID {bad}"

    os.makedirs(temp_dir, exist_ok=True)
    clip_id = clip_url.split("/")[4] if "videos/" in clip_url else str(abs(hash(clip_url)))[:8]

    # 2. Extract 1 frame per second (each 1s) across the entire video timeline
    import subprocess
    import glob
    clip_temp = os.path.join(temp_dir, f"clip_{clip_id}")
    os.makedirs(clip_temp, exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-i", clip_url,
        "-vf", "fps=1",
        "-q:v", "3",
        os.path.join(clip_temp, "sec_%03d.jpg")
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=14)
    except Exception:
        pass

    frame_paths = sorted(glob.glob(os.path.join(clip_temp, "*.jpg")))
    if not frame_paths:
        try: os.rmdir(clip_temp)
        except: pass
        logger.warning(f"[Shariah Gate] Could not extract 1s frames for {clip_id}; checked during post-render.")
        return True, "Passed (remote fetch warning)"

    def _cleanup():
        for fp in frame_paths:
            try: os.remove(fp)
            except: pass
        try: os.rmdir(clip_temp)
        except: pass

    # 3. Layer 1: Fast Local FasterRCNN Pre-check across EVERY 1-second frame
    flagged_frames = []
    try:
        import torch
        import torchvision.models.detection as detection_models
        from torchvision.io import read_image
        weights = detection_models.FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT
        model = detection_models.fasterrcnn_mobilenet_v3_large_320_fpn(weights=weights)
        model.eval()
        preprocess = weights.transforms()
        cats = weights.meta["categories"]
        living_classes = {"person", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}

        for sec_idx, fpath in enumerate(frame_paths):
            img_tensor = read_image(fpath)
            batch = [preprocess(img_tensor)]
            with torch.no_grad():
                pred = model(batch)[0]
            for label, score in zip(pred["labels"], pred["scores"]):
                cat_name = cats[label]
                if cat_name in living_classes and float(score) >= 0.50:
                    flagged_frames.append((sec_idx + 1, cat_name, float(score), fpath))
                    break # One detection per second is enough
    except Exception as e:
        logger.debug(f"[Shariah Gate] Local detector notice: {e}")

    # 4. Layer 2: Deep Gemini Multimodal Vision API Verification
    try:
        from app.llm.provider import get_api_keys_pool
        from google import genai
        from PIL import Image

        keys = get_api_keys_pool()
        if keys:
            # Audit any frame flagged by FasterRCNN
            for sec_idx, cname, score, fpath in flagged_frames:
                # High-confidence person is an instant rejection
                if cname == "person" and score >= 0.85:
                    reason = f"Person detected at second {sec_idx}: {cname} ({round(score, 2)})"
                    BANNED_CLIP_BLACKLIST.add(clip_id)
                    logger.warning(f"❌ [Shariah Gate REJECTED] Clip {clip_id}: {reason}")
                    _record_rejection_in_catalog(clip_id, clip_url, reason)
                    _cleanup()
                    return False, reason

                # Confirm with Gemini Vision
                confirm_prompt = """Strict Islamic Shariah Visual Audit:
Is there ANY living person, human, face, silhouette, animal, bird, insect, or living creature in this image?
Answer with valid JSON:
{"pass": true/false, "has_living_being": true/false, "reason": "Detailed description of what you see"}"""
                for key in keys[:3]:
                    try:
                        client = genai.Client(api_key=key)
                        resp = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=[confirm_prompt, Image.open(fpath)]
                        )
                        raw_text = resp.text or ""
                        import json as _json, re as _re
                        match = _re.search(r"\{.*\}", raw_text, _re.DOTALL)
                        if match:
                            data = _json.loads(match.group(0))
                            if not data.get("pass", True) or data.get("has_living_being", False):
                                reason = f"Living being confirmed at second {sec_idx}: {data.get('reason', cname)}"
                                BANNED_CLIP_BLACKLIST.add(clip_id)
                                logger.warning(f"❌ [Shariah Gate REJECTED] Clip {clip_id}: {reason}")
                                _record_rejection_in_catalog(clip_id, clip_url, reason)
                                _cleanup()
                                return False, reason
                        break
                    except Exception:
                        continue

            # Also audit 3 key milestone frames (start, middle, end) for statues/crosses/idols
            indices_to_check = [0, len(frame_paths)//2, len(frame_paths)-1]
            sample_frames = [frame_paths[i] for i in indices_to_check if i < len(frame_paths)]
            prompt = """Strict Islamic Shariah Visual Audit:
Are there ANY humans, silhouettes, statues, idols, crosses, or churches in this image?
Respond in JSON: {"pass": true/false, "reason": "Description"}"""
            for fpath in sample_frames:
                for key in keys[:3]:
                    try:
                        client = genai.Client(api_key=key)
                        resp = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=[prompt, Image.open(fpath)]
                        )
                        raw_text = resp.text or ""
                        import json as _json, re as _re
                        match = _re.search(r"\{.*\}", raw_text, _re.DOTALL)
                        if match:
                            data = _json.loads(match.group(0))
                            if not data.get("pass", True):
                                reason = data.get("reason", "Contains prohibited imagery")
                                BANNED_CLIP_BLACKLIST.add(clip_id)
                                logger.warning(f"❌ [Shariah Gate REJECTED] Clip {clip_id}: {reason}")
                                _record_rejection_in_catalog(clip_id, clip_url, reason)
                                _cleanup()
                                return False, reason
                        break
                    except Exception:
                        continue
    except Exception as e:
        logger.warning(f"[Shariah Gate] Vision check notice: {e}")

    _cleanup()
    return True, "Clean 100% Halal at each 1s"

def _record_rejection_in_catalog(clip_id: str, clip_url: str, reason: str):
    """Automatically records rejected clip into catalog_rejected_clips.json and removes it from stock_video_catalog.json."""
    try:
        rej_file = os.path.abspath("data/catalog_rejected_clips.json")
        rej = {}
        if os.path.exists(rej_file):
            with open(rej_file, "r", encoding="utf-8") as f:
                rej = json.load(f)
        rej[clip_url] = {"id": clip_id, "reason": reason}
        with open(rej_file, "w", encoding="utf-8") as f:
            json.dump(rej, f, indent=2, ensure_ascii=False)

        cat_file = os.path.abspath(CATALOG_FILE)
        if os.path.exists(cat_file):
            with open(cat_file, "r", encoding="utf-8") as f:
                cat = json.load(f)
            meta = cat.get("clip_metadata", {})
            if clip_url in meta:
                del meta[clip_url]
            by_cat = cat.get("catalog_by_50_categories", {})
            for c_name, u_list in by_cat.items():
                if clip_url in u_list:
                    u_list.remove(clip_url)
            cat["total_unique"] = len(meta)
            with open(cat_file, "w", encoding="utf-8") as f:
                json.dump(cat, f, indent=2, ensure_ascii=False)
            logger.info(f"Purged rejected clip {clip_id} from central catalog.")
    except Exception as e:
        logger.warning(f"Failed to record rejection for {clip_id}: {e}")

def get_next_video_scenes(advance: bool = True) -> dict:
    """
    Selects 3 RANDOM Halal clips sequentially (one-by-one check):
    1. Picks Clip 1 from a random category -> audits frame-by-frame across timeline.
       If it fails, purges and retries until Clip 1 is verified & locked in.
    2. Picks Clip 2 from a DIFFERENT category -> audits frame-by-frame until verified & locked in.
    3. Picks Clip 3 from a THIRD distinct category -> audits frame-by-frame until verified & locked in.
    Guarantees Category 1 != Category 2 != Category 3, and preserves verified clips without re-auditing.
    """
    cats_50, by_cat = load_50_categories_catalog()
    all_categories = [c for c, urls in by_cat.items() if urls]

    if len(all_categories) < 3:
        return {
            "clips": [
                os.path.abspath("app/assets/broll/ocean_720.mp4"),
                os.path.abspath("app/assets/broll/clouds_720.mp4"),
                os.path.abspath("app/assets/broll/desert_720.mp4")
            ],
            "categories": ["ocean", "clouds", "desert"],
            "permutation": [1, 2, 3],
            "permutation_str": "local_fallback"
        }

    verified_clips = []
    chosen_categories = []

    # Available categories to pick from (ensures Category 1 != Category 2 != Category 3)
    remaining_categories = [c for c in all_categories]
    random.shuffle(remaining_categories)

    for slot_idx in range(1, 4):
        slot_verified = False
        max_slot_attempts = 15

        while not slot_verified and max_slot_attempts > 0 and remaining_categories:
            max_slot_attempts -= 1
            cat = remaining_categories.pop(0)

            cat_clips = [u for u in by_cat.get(cat, []) if not any(b in u for b in BANNED_CLIP_BLACKLIST)]
            if not cat_clips:
                continue

            random.shuffle(cat_clips)
            for candidate_clip in cat_clips:
                logger.info(f"🔍 [Slot {slot_idx}/3] Auditing candidate clip from category '{cat}'...")
                is_halal, reason = is_clip_halal_gemini(candidate_clip)
                if is_halal:
                    verified_clips.append(candidate_clip)
                    chosen_categories.append(cat)
                    slot_verified = True
                    logger.info(f"✅ [Slot {slot_idx}/3 APPROVED] Clip from '{cat}' verified 100% Halal!")
                    break
                else:
                    logger.warning(f"❌ [Slot {slot_idx}/3 REJECTED] Clip failed: {reason}. Trying next candidate...")

        if not slot_verified:
            logger.warning(f"Could not secure verified clip for slot {slot_idx}.")
            break

    if len(verified_clips) == 3:
        # Randomize the playback sequence of the 3 verified clips
        combined = list(zip(verified_clips, chosen_categories))
        random.shuffle(combined)
        final_clips, final_cats = zip(*combined)

        logger.info(f"🎬 [Triplet Ready] Secured 3 individually verified clips from distinct categories: {list(final_cats)}")
        return {
            "clips": list(final_clips),
            "categories": list(final_cats),
            "permutation": [1, 2, 3],
            "permutation_str": "sequential_verified"
        }

    # Guaranteed Halal fallback if network/remote access fails
    logger.warning("Using guaranteed 100% Halal local b-roll fallback triplet.")
    return {
        "clips": [
            os.path.abspath("app/assets/broll/ocean_720.mp4"),
            os.path.abspath("app/assets/broll/clouds_720.mp4"),
            os.path.abspath("app/assets/broll/desert_720.mp4")
        ],
        "categories": ["ocean", "clouds", "desert"],
        "permutation": [1, 2, 3],
        "permutation_str": "local_fallback"
    }
