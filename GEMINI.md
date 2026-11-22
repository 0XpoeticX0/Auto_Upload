# Production Standards & Quality Mandates

## 1. Visual Standards (100% Halal Live-Motion Video Only)
- **100% Real Live-Motion Footage**: All videos must use real, high-definition (1080p/720p 60 FPS) cinematic video footage (ocean waves, mountain waterfalls, moving skies/clouds, celestial time-lapses, serene Islamic architecture).
- **Strict Ban on Still Images**: STRICTLY ZERO static photos, still AI images, or camera zoom/pan over JPG/PNG graphics in Quran videos. No artificial motion over still pictures.
- **Strict Shariah Compliance**: Strictly 0 humans, 0 faces, 0 silhouettes, 0 statues, 0 animals. Pure atmospheric nature, celestial majesty, and classical sacred architecture.
- **Zero Watermarks**: Strictly no watermarked or low-quality AI endpoints.
- **3-Clip Triplet Selection (Zero Category Overlap)**:
  - Each video selects 3 clips from 3 completely different categories out of the 50 Halal categories (`Category(Clip 1) != Category(Clip 2) != Category(Clip 3)`).
- **Dynamic Round-Robin Rotation (No Forced Anchors)**:
  - Visuals cycle round-robin across the 3 clips in series (`1 ➔ 2 ➔ 3 ➔ 1 ➔ 2 ➔ 3`) with 15s–20s scenes.
  - **No video is ever forced to start with a specific clip, image, or fixed opening scene.** Visuals start dynamically and naturally from the selected rotation.
  - Never hold a single scene or loop 1 clip on itself.

## 2. Clean Video & Metadata Standards (Strict Mandate)
- **100% Clean Video (Zero On-Screen Text)**: For all Quran recitation videos, strictly zero on-screen text, zero subtitles (no Arabic, no English, no Bengali), zero gradient darkening overlays, and zero badges. Only pure, pristine 1080x1920 60 FPS live-motion nature footage.
- **Zero Reciter & Verse Names in Metadata**: STRICTLY ZERO reciter names (no "Alafasy", no "Dossari", etc.), ZERO Surah names (no "Surah ..."), and ZERO verse numbers in titles, descriptions, and tags across all videos.
  - *Title format*: `{Emotional Curiosity Hook} #Shorts #Quran`
  - *Description format*: Emotional curiosity hook, sacred Arabic verses and unfiltered English translation, authentic Hadith on sharing goodness, and universal tags.
  - *Tags*: Strictly universal high-ranking Islamic/Quran tags (zero reciter tags, zero Surah tags).
- **Zero Pinned Comments**: Strictly `pinned_comment = None` across all platforms (no automated first comments).

## 3. Audio & Recitation Standards
- **Approved Quran Reciters**: Strictly **Sheikh Yasser Ad-Dossari** (`dossari`) and **Sheikh Mishary Rashid Alafasy** (`alafasy`).
  - *Alafasy*: Mercy, comfort, hope, repentance, Dua, Jannah (warm baritone).
  - *Dossari*: Divine majesty, Day of Judgment, sovereignty, Tawakkul, cosmic oaths (thunderous delivery).
- **100% Authentic Audio & Normalization**: Pure EveryAyah recitation audio without destructive de-reverb filtering. Broadcast loudness normalization at **-18.0 LUFS** (256kbps).
- **Auditory Bliss**: Verses must be spiritually uplifting and melodic, with rhythmic end-rhymes (Fawāṣil al-Āyāt). Strictly avoid dry legalistic verses.
- **Islamic Quiz Pacing**:
  - Direct inquiry start at 0.0s. STRICTLY NEVER speak or display "প্রশ্ন ১", "Question 1", etc.
  - Conversational speech rate (1.00x / `rate="+0%"`) with a +0.25s human breath pause before countdown clock.

## 4. Bengali Language & Curiosity Hooks
- **Zero Broken Bengali (বিশুদ্ধ ও প্রাঞ্জল বাংলা)**: 100% grammatically correct, natural everyday spoken Bengali. Zero repeated words/clauses, zero awkward literal translations.
- **Pure Curiosity Hooks (Open Loop)**: Hooks must never lecture or preach. Must present an intriguing inquiry or dramatic contrast ending with the bridge arrow `➔`.
- **Automated Gemini Verification**: Hooks and translations pass automated review via `bengali_hook_guardian.py` to auto-edit any preachy or unnatural phrasing before rendering.

## 5. Series Progression & Zero-Duplication
- **Continuous Episode Counting**: Series episode counter for 'দৈনন্দিন সহীহ আমল' starts from Episode 51 (`পর্ব ৫১`) and continuously increments without cap. Top badge placed at `\pos(540,240)` in gold font (`&H0015CCFA&`), size 44.
- **Strict 50-Video Topic Cooldown**: Block and reject any theme, Surah, Ayah range, or topic published in the last 50 videos.
- **Strict Hadith Number Deduplication**: Deduplication checks exact Hadith citation (e.g. Bukhari 6474, Muslim 1893), never reusing the same Hadith within the last 50 videos.
- **Multi-Part Pacing & Silent Outro**:
  - Target duration 65s–82s (strictly under 90s) at 1.08x tempo.
  - 3.0-second digital silence at the end (`apad=whole_dur=...`). "To Be Continued" badge (`বাকি অংশ দেখুন পর্ব ২-তে ➔`) appears ONLY during this silence, never overlapping voiceover.

## 6. 3-Pass Verification Gate
Every production video must clear all 3 automated gates before upload (`triple_gemini_verifier.py`):
- **Pass 1 (Religious Truth)**: Validates Uthmani Arabic text and Islamic Foundation Bangladesh Bengali translation.
- **Pass 2 (Shariah Visual Audit)**: Frame audit enforcing strictly 0 living beings, faces, or silhouettes.
- **Pass 3 (Audio & Typography)**: Validates Kalpurush Bengali typography, card duration >= 2.5s, max 1–2 lines, and -18.0 LUFS audio normalization.
