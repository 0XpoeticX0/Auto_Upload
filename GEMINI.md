# Video Production & Typography Mandates (Permanent Rules)

## 1. Multi-Part Series Header & Subtitles Standards
- **Multi-Part Badge (Top Area)**: In multi-part series, ALWAYS include the Part Indicator badge at the top (`\pos(540,240)`), e.g., `[ সহীহ বুখারী • পর্ব ১ ]`, `[ সহীহ বুখারী • পর্ব ২ ]`, etc., in gold font (`&H0015CCFA&`), size 44, so viewers immediately know which part they are watching.
- **Strict 2-Line Subtitles**: Subtitles MUST ALWAYS be **1 or 2 lines maximum** in the center (`\pos(540,960)`). Never 3, 4, 5, 6, or 7-line paragraphs.
- **Clause Chunking**: Each subtitle card must contain 5 to 9 words (~2.5s - 4.5s duration). Split long sentences into natural spoken clauses.
- **Line Break (`\N`)**: When word count >= 5, split exactly in the middle so Line 1 and Line 2 have balanced lengths (~3-5 words each).
- **Font Specifications**:
  - Font: `Kalpurush`
  - Weight: Regular (`Bold: 0`) — never heavy bold
  - Size: `56` (range 54–60)
  - Outline: `3.2`, Shadow: `1.8`
  - Colors: Crisp White (`&H00FFFFFF&`) with Royal Gold highlights (`{\c&H0041AFEB&}`) on sacred/key words (`আল্লাহ`, `রব`, `তাওয়াক্কুল`, `স্বর্ণমুদ্রা`, `দিনার`, etc.).
  - Alignment: `5` (Center-locked)
  - Margins: Left 70, Right 70 (guaranteeing >150px safe margins, ZERO text clipping).

## 2. Visual Standards & Generation Rules
- **Zero Watermarks & High-Definition**: Never use low-quality or watermarked AI endpoints (`pollinations.ai`). Use 8K photorealistic cinematic generation (`generate_image`) and authentic video B-rolls (`ocean_720.mp4`, `desert_720.mp4`, etc.).
- **Strict Shariah Compliance**: Strictly 0 humans, 0 faces, 0 silhouettes, 0 statues, 0 animals. Pure atmospheric architecture, landscapes, celestial skies, and symbolic objects.
- **Dynamic Pacing**: Fast-paced 4 to 8-second scene cuts (7–10 scenes per ~75s part)—never holding static images for 20+ seconds.

## 3. Multi-Part Pacing & Silent Outro
- **Tempo**: 1.08x speed for clear, engaging Bengali narration.
- **Duration**: Each part MUST be strictly under 90 seconds (target 65s - 82s).
- **TBC Silent Outro**:
  - The voiceover speech MUST finish completely and fade out before the "To Be Continued" badge appears.
  - Append a dedicated **3.0-second digital silence** (`apad=whole_dur=...`) at the end of each part.
  - The TBC badge (`বাকি অংশ দেখুন পর্ব ২-তে ➔` / `To Be Continued`) appears ONLY during this 3.0s silence. Audio and TBC text must NEVER overlap.

## 4. Quran Recitation Video Visual Mandates (100% Real Live-Motion Video Only)
- **STRICT PERMANENT BAN ON STILL IMAGES**: STRICTLY NEVER use static/still photos, still AI-generated images, or camera zoom/pan motion over JPG/PNG images (e.g. quran_rehal_master.jpg) in Quran videos. Still images with camera motion look cheap, static, and artificial.
- **100% Authentic Live-Motion Video Footage**: For ALL Quran recitation videos, the visual MUST ALWAYS be composed of real, high-definition (1080p/720p 60 FPS) cinematic motion video footage (moving ocean waves, flowing mountain waterfalls, real moving clouds/skies, starry celestial time-lapses, authentic mosque architecture).
- **Strict Shariah Visual Compliance**: Strictly 0 humans, 0 faces, 0 silhouettes, 0 statues, 0 animals. Pure atmospheric nature, celestial majesty, and classical sacred Islamic architecture.
- **50-Category Zero-Overlap Triplet Sequencing**: Each video must select 3 clips from 3 completely different categories out of the 50 Halal categories (Category(Clip 1) != Category(Clip 2) != Category(Clip 3)).
- **Serene Scene Pacing**: Fast-paced yet tranquil 15s to 20s scene cuts cycling round-robin in series (1 -> 2 -> 3 -> 1 -> 2 -> 3) locked to Ayah boundaries—never holding a single scene or looping 1 clip on itself.

## 5. Reciter & Audio Enhancement Mandate (Permanent Standard)
- **Strictly 2 Approved Reciters**: ONLY use **Sheikh Yasser Ad-Dossari** (`dossari`) and **Sheikh Mishary Rashid Alafasy** (`alafasy`). Strictly NO other reciters.
- **Thematic Emotion-to-Voice Matching**: Intelligently match the passage's emotional frequency to the ideal reciter: assign **Sheikh Mishary Rashid Alafasy** to comfort, solace, mercy, hope, repentance, Dua, family, and Jannah (soothing warm baritone); assign **Sheikh Yasser Ad-Dossari** to divine majesty, sovereignty, Day of Judgment (Qiyamah), absolute Tawakkul, and cosmic oaths (commanding thunderous delivery).
- **100% Pure Authentic EveryAyah Recitation**: For all Quran recitation videos, use 100% pure, authentic EveryAyah audio directly WITHOUT AI de-reverb or destructive filtering. Preserves the full natural sacred acoustic resonance, soulful warmth, and spiritual emotion of Sheikh Mishary Rashid Alafasy and Sheikh Yasser Ad-Dossari. Apply ONLY standard broadcast loudness normalization (`-18.0 LUFS`) at 256kbps for comfortable, consistent playback volume across all platforms.
- **Ear-Pleasing Auditory & Melodic Selection**: Selected passages MUST sound exceptionally sweet, soothing, and captivating to human ears. Prioritize Ayahs with rhythmic, flowing end-rhymes (Fawāṣil al-Āyāt: -ūn, -īn, -ā, -hā) and passages globally celebrated for auditory bliss (Jannah descriptions, divine affection, Prophet Duas, and dawn/night serenity). Strictly avoid dry administrative, legalistic, or transactional verses.


## 6. Zero-Duplication, Hadith Number Tracking & Series Count Mandate (Last 50 Videos)
- **Continuous Episode Progression from 51 (No Count Cap)**: Series episode counter for 'দৈনন্দিন সহীহ আমল' starts strictly from Episode 51 (`পর্ব ৫১`) and continuously increments (51 -> 52 -> 53 -> ...) without any upper bound/cap.
- **Strict 50-Video Topic Cooldown**: Programmatically block and reject any topic, semantic theme, Quranic Surah, Ayah range, or passage that has been published within the **last 50 videos** (tracked across Supabase cloud memory, local registries, and history).
- **Strict Hadith Number Deduplication (NO SAME HADITH)**: Deduplication checks the **exact Hadith number** (e.g. Bukhari 6474, Muslim 1893, Tirmidhi 3563, Abu Dawood 5095, etc.) and book citation, NOT just keywords. If a candidate Hadith number matches any Hadith used in the last 50 videos, it is strictly forbidden and rejected immediately.
- **Zero Duplicate Visuals**: Visual tracks must cycle through independent video buckets (`data/video_registry.json`) ensuring 0 identical clip sequences across consecutive productions.

## 7. Bengali Grammar, Pure Curiosity Hook & Anti-Broken-Bangla Mandate
- **Zero Broken Bengali (বিশুদ্ধ ও প্রাঞ্জল বাংলা)**: Sentences must be 100% grammatically correct, natural everyday spoken Bengali. Strictly 0 repeated words/clauses (`রাসূল ... রাসূল`, `জান্নাতের জিম্মাদার ... জান্নাতের জিম্মাদার`), zero ungrammatical run-ons.
- **Pure Curiosity Hooks (Open Loop)**: The on-screen text must NEVER lecture or preach (`সামলে চলুন`, `হেফাজত করুন`, `আমলটি করুন`). Must pose an irresistible open-loop inquiry or dramatic contrast ending with the bridge arrow `➔` (e.g., `মাত্র ২টি অঙ্গ হেফাজত করলে নবীজি (ﷺ) / জান্নাতের জিম্মাদার হওয়ার ঘোষণা দিয়েছিলেন ➔`).
- **Zero Tofu Boxes & Missing Glyphs**: Exclusively burn subtitles using `Kalpurush` font with `fontsdir='app/assets/fonts'`, guaranteeing 0 broken rectangle/tofu boxes (`🗹`).
- **Automated Gemini Verification & Auto-Edit Pass**: Every video hook must be verified by Gemini via `app/quality/bengali_hook_guardian.py`. If any broken Bengali, repetition, or preachy language is detected, Gemini automatically edits and rewrites the lines in-place before video rendering.

## 8. 300 Halal Video Catalog & Zero-Category-Overlap Mandate
- **Strict 15s–20s Duration**: Never use clips under 15 seconds (`duration >= 15.0s`). Clips longer than 20 seconds are automatically cut to 20.0s during scene production.
- **50 Distinct Categories (6 Clips Each)**: The central 300-clip catalog (`data/stock_video_catalog.json`) is partitioned into 50 canonical Halal categories (0 humans, 0 animals, 0 statues).
- **Strict Zero-Category-Overlap Within Every Video**: In every video triplet, all 3 clips MUST be selected from **3 completely different categories**:
  $$\text{Category}(\text{Clip 1}) \neq \text{Category}(\text{Clip 2}) \neq \text{Category}(\text{Clip 3})$$
  Zero videos ever use more than 1 clip from the same category.
- **Full Round-Robin Rotation**: The visual track cycles round-robin across the 3 clips in series (`1 ➔ 2 ➔ 3 ➔ 1 ➔ 2 ➔ 3`) instead of looping a single clip on itself.
- **100-Video Cycle Management & Permutations**: Partitioned into 100 videos per cycle with randomized internal permutations (`1 3 2`, `2 3 1`, `2 1 3`, `3 2 1`). Automatically shifts offsets and shuffles on rollover from Cycle 1 to Cycle 2.

## 9. 3-Pass Gemini API Re-Verification Mandate
Every production video must pass all 3 verification gates before release (`app/quality/triple_gemini_verifier.py`):
- **Pass 1: Religious & Contextual Truth**: Validates Uthmani Arabic scripture, Dr. Abu Bakr Zakaria Bengali translation (modernized heart/chest, zero "স্তন"), self-contained context, and zero unverified engagement bait.
- **Pass 2: Shariah Visual Compliance**: AI Vision frame audit (3–5 keyframes) via Gemini Multimodal Vision API enforcing strictly 0 living beings, 0 silhouettes, and 0 statues.
- **Pass 3: Typography, Pacing & Audio Mastering**: Validates Kalpurush Bengali typography, card duration $\ge 2.5\text{s}$, max 1–2 lines center-aligned, and -18.0 LUFS audio broadcast normalization.

## 10. Islamic Quiz Direct-Start & Human Pacing Mandate
- **Direct Inquiry Start (Zero Announcements)**: Quiz videos MUST start immediately at 0.0s with the spoken inquiry itself. STRICTLY NEVER speak or render "প্রশ্ন ১", "প্রশ্ন ২", "Question 1", or "Question 2".
- **Natural Human Speech Rate**: Spoken TTS narration rate is strictly set to natural conversational speed (`rate="+0%"` / 1.00x) with a dedicated `+0.25s` human breathing pause before the 3-second countdown clock begins.


