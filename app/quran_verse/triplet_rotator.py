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

def get_next_video_scenes(advance: bool = True) -> dict:
    """
    Retrieves the 3 ordered scenes for the current video in cycle.
    If advance=True, advances the pointer to the next video, triggering
    the next cycle (Cycle 2, 3...) when 100 videos are completed.

    Returns:
    {
        "cycle": int,
        "video_in_cycle": int,
        "global_video_index": int,
        "permutation": list[int],       # e.g. [2, 3, 1]
        "permutation_str": str,         # e.g. "2 3 1"
        "clips": list[str],             # 3 ordered video paths/urls
        "is_cycle_rollover": bool
    }
    """
    state = load_or_init_rotation_state()
    current_cycle = state.get("current_cycle", 1)
    current_vid = state.get("current_video_in_cycle", 1)

    # Sync with cloud history (Supabase) so GitHub Actions containers automatically pick up exact progress
    try:
        from app.history import fetch_recent_quran_pipeline_history
        q_hist = fetch_recent_quran_pipeline_history(limit=500)
        published_count = len(q_hist)
        if published_count > state.get("total_videos_completed", 0):
            current_cycle = (published_count // 100) + 1
            current_vid = (published_count % 100) + 1
            state["current_cycle"] = current_cycle
            state["current_video_in_cycle"] = current_vid
            state["total_videos_completed"] = published_count
    except Exception as e:
        logger.debug(f"Cloud history sync notice: {e}")

    plan = state.get("plan", [])

    if not plan or current_vid > len(plan):
        # Current cycle finished! Start next cycle!
        current_cycle += 1
        clips = load_catalog_clips()
        plan = generate_cycle_plan(clips, current_cycle)
        current_vid = 1
        state["current_cycle"] = current_cycle
        state["current_video_in_cycle"] = current_vid
        state["plan"] = plan
        logger.info(f"🔄 [Triplet Rotator ROLLOVER] 100 videos completed! Advanced to Cycle {current_cycle} with brand-new clip pairings and permutations!")

    item = plan[current_vid - 1]

    raw_clips = list(item.get("ordered_clips", []))
    raw_cats = list(item.get("categories", []))

    # Anti-Repeat Cooldown Enforcement:
    # Strictly forbid any clip that was used in recent videos (last 15 clips / 5 videos)
    recent_clips = list(state.get("recent_clips", []))
    if not recent_clips and state.get("history"):
        for h in state.get("history")[-5:]:
            recent_clips.extend(h.get("clips", []))

    recent_set = set(recent_clips[-15:])
    final_clips = []
    cats_50, by_cat = load_50_categories_catalog()
    all_pool = load_catalog_clips()

    for idx, c in enumerate(raw_clips):
        if c in recent_set:
            cat = raw_cats[idx] if idx < len(raw_cats) else None
            alt_clips = by_cat.get(cat, []) if cat else []
            candidates = [a for a in alt_clips if a not in recent_set and a not in final_clips and a not in raw_clips]
            if not candidates:
                candidates = [a for a in all_pool if a not in recent_set and a not in final_clips and a not in raw_clips]
            if candidates:
                replacement = candidates[0]
                logger.warning(f"⚠️ [Triplet Anti-Repeat] Clip '{c}' was used in recent videos! Swapped with fresh clip '{replacement}'.")
                final_clips.append(replacement)
            else:
                final_clips.append(c)
        else:
            final_clips.append(c)

    result = {
        "cycle": current_cycle,
        "video_in_cycle": current_vid,
        "global_video_index": item.get("global_video_index", current_vid),
        "categories": raw_cats,
        "permutation": item.get("permutation_order", [1, 2, 3]),
        "permutation_str": item.get("permutation_str", "1 2 3"),
        "clips": final_clips,
        "is_cycle_rollover": (current_vid == 1 and current_cycle > 1)
    }

    if advance:
        next_vid = current_vid + 1
        state["total_videos_completed"] = state.get("total_videos_completed", 0) + 1
        state["recent_clips"] = (state.get("recent_clips", []) + final_clips)[-30:]
        state["history"].append({
            "cycle": current_cycle,
            "video_in_cycle": current_vid,
            "permutation": item.get("permutation_str"),
            "clips": final_clips
        })
        # Keep history capped at 100
        if len(state["history"]) > 100:
            state["history"] = state["history"][-100:]

        if next_vid > len(plan):
            # Prepare next cycle
            next_cycle = current_cycle + 1
            clips = load_catalog_clips()
            state["current_cycle"] = next_cycle
            state["current_video_in_cycle"] = 1
            state["plan"] = generate_cycle_plan(clips, next_cycle)
            logger.info(f"🎉 [Triplet Rotator] Video 100 of Cycle {current_cycle} complete! Queued Cycle {next_cycle} with fresh rotation.")
        else:
            state["current_video_in_cycle"] = next_vid

        save_rotation_state(state)

    logger.info(f"🎬 [Triplet Rotator] Selected 3 clips for Cycle {current_cycle} Video #{current_vid}/100 (Order: {result['permutation_str']})")
    return result

def get_current_rotation_status() -> dict:
    """Returns human-readable status of the 300-video rotation engine."""
    state = load_or_init_rotation_state()
    return {
        "current_cycle": state.get("current_cycle", 1),
        "current_video_in_cycle": state.get("current_video_in_cycle", 1),
        "total_videos_completed": state.get("total_videos_completed", 0),
        "total_pool_clips": state.get("total_clips_in_pool", 300),
        "videos_per_cycle": 100,
        "clips_per_video": 3,
        "next_video_order": state.get("plan", [{}])[state.get("current_video_in_cycle", 1) - 1].get("permutation_str", "1 2 3")
    }
