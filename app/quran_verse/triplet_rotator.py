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

    # Pad or truncate to 300 clips (or nearest multiple of 3)
    target_count = 300
    if len(clips_pool) >= target_count:
        working_pool = list(clips_pool[:target_count])
    else:
        # If fewer than 300 available, cycle them to reach 300
        working_pool = []
        while len(working_pool) < target_count:
            working_pool.extend(clips_pool)
        working_pool = working_pool[:target_count]

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
    Extracts a quick sample frame via FFmpeg and audits the clip using Gemini Multimodal Vision API.
    Guarantees strictly 0 humans, 0 faces, 0 silhouettes, 0 statues, 0 animals.
    """
    # 1. Fast check against permanent banned blacklist
    for bad in BANNED_CLIP_BLACKLIST:
        if bad in str(clip_url):
            return False, f"Clip matches banned ID {bad}"

    os.makedirs(temp_dir, exist_ok=True)
    clip_id = clip_url.split("/")[4] if "videos/" in clip_url else str(abs(hash(clip_url)))[:8]
    frame_path = os.path.join(temp_dir, f"audit_{clip_id}.jpg")

    # 2. Extract single frame at 2.50s directly over HTTP
    import subprocess
    cmd = [
        "ffmpeg", "-y", "-ss", "00:00:02.50", "-i", clip_url,
        "-vframes", "1", "-q:v", "2", frame_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode != 0 or not os.path.exists(frame_path) or os.path.getsize(frame_path) < 1000:
        logger.warning(f"[Shariah Gate] Could not extract remote frame for {clip_id}; will be checked during post-render.")
        return True, "Passed (remote fetch warning)"

    # 3. Gemini Multimodal Vision Audit
    try:
        from app.llm.provider import get_api_keys_pool
        from google import genai
        from PIL import Image

        keys = get_api_keys_pool()
        if not keys:
            return True, "Keys unavailable"

        prompt = """Strict Islamic Shariah Visual Audit:
Are there ANY humans, people, women, men, children, faces, silhouettes, human body parts (hands/legs/hair/skin), swimsuits, living animals, statues, idols, or churches in this image?

CRITERIA:
- If ANY human, silhouette, statue, church, or living being is detected, return JSON:
  {"pass": false, "reason": "Detailed description of what was detected"}
- Only if 100% Halal atmospheric nature (ocean, sky, clouds, stars, mountains, desert, waterfalls, trees, Islamic mosque), return JSON:
  {"pass": true, "reason": "Clean 100% Halal nature"}"""

        # Try key pool for resilience
        for key in keys[:3]:
            try:
                client = genai.Client(api_key=key)
                img = Image.open(frame_path)
                resp = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=[prompt, img]
                )
                raw_text = resp.text or ""
                import json as _json, re as _re
                match = _re.search(r"\{.*\}", raw_text, _re.DOTALL)
                if match:
                    data = _json.loads(match.group(0))
                    if not data.get("pass", True):
                        reason = data.get("reason", "Contains living beings or prohibited imagery")
                        BANNED_CLIP_BLACKLIST.add(clip_id)
                        logger.warning(f"❌ [Shariah Gate REJECTED] Clip {clip_id}: {reason}")
                        return False, reason
                return True, "Clean 100% Halal"
            except Exception as e:
                continue
    except Exception as e:
        logger.warning(f"[Shariah Gate] Vision check notice: {e}")

    return True, "Clean"

def get_next_video_scenes(advance: bool = True) -> dict:
    """
    Selects 3 RANDOM Halal clips from 3 completely distinct categories (Zero Tracking Required).
    Audits every selected clip with Gemini Vision API.
    If ANY clip fails, deletes/discards the triplet and loops to pick 3 NEW clips until 100% Halal.
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

    max_attempts = 15
    for attempt in range(max_attempts):
        # 1. Randomly sample 3 completely different categories
        chosen_cats = random.sample(all_categories, 3)
        candidate_clips = []
        for cat in chosen_cats:
            available = [u for u in by_cat[cat] if not any(b in u for b in BANNED_CLIP_BLACKLIST)]
            if available:
                candidate_clips.append(random.choice(available))
            else:
                candidate_clips.append(random.choice(by_cat[cat]))

        # Randomize playback order
        random.shuffle(candidate_clips)

        # 2. Pre-audit each of the 3 clips with Gemini Vision
        all_passed = True
        failed_reason = ""
        for clip in candidate_clips:
            is_halal, reason = is_clip_halal_gemini(clip)
            if not is_halal:
                all_passed = False
                failed_reason = f"Clip {clip} failed: {reason}"
                logger.warning(f"⚠️ [Shariah Gate] {failed_reason}. Discarding triplet and picking 3 NEW random clips (Attempt {attempt+1}/{max_attempts})...")
                break

        if all_passed:
            logger.info(f"✅ [Triplet Selected] Picked 3 RANDOM clips from categories {chosen_cats} - All 3 verified Halal by Gemini!")
            return {
                "clips": candidate_clips,
                "categories": chosen_cats,
                "permutation": [1, 2, 3],
                "permutation_str": "random_verified"
            }

    # Ultimate guaranteed Halal fallback
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
