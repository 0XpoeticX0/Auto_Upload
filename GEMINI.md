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

## 2. Typography & Subtitle Standards
- **Font & Rendering**: Exclusively use `Kalpurush` font with `fontsdir='app/assets/fonts'`, regular weight (`Bold: 0`), size 54–60, outline 3.2, shadow 1.8. Zero missing glyphs or tofu boxes (`🗹`).
- **Strict 1–2 Line Subtitles**: Subtitles MUST ALWAYS be **1 or 2 lines maximum** in the center (`\pos(540,960)`). Never 3+ line paragraphs.
- **Clause Chunking & Balance**: Each subtitle card contains 5 to 9 words (~2.5s - 4.5s duration). Split evenly in the middle (`\N`) so both lines have balanced length (~3-5 words each).
- **Safe Margins**: Safe margin > 150px (Left/Right margins 70), center-locked alignment (`5`), zero text clipping.
- **Highlights**: Crisp white (`&H00FFFFFF&`) with Royal Gold highlights (`{\c&H0041AFEB&}`) on sacred/key words (`আল্লাহ`, `রব`, `তাওয়াক্কুল`, etc.).

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
