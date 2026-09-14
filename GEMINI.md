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

## 4. Quran Recitation Video Mandates (Permanent Standard)
- **Dedicated Sacred Visual (Open Quran on Rehal)**: For ALL Quran recitation videos, the visual MUST ALWAYS feature the **Holy Quran open on an antique carved wooden Rehal (রেহাল)** placed on a traditional emerald prayer carpet inside a grand, serene mosque/sanctuary, illuminated by soft golden morning sunbeams/god rays and floating glowing dust particles (`app/assets/quran_rehal_master.jpg`).
- **Strictly No Empty Corridors**: NEVER use plain empty hallways, generic corridors, or abstract loops without the Holy Quran on the Rehal.
- **Zero Living Beings**: Strictly 0 humans, 0 faces, 0 silhouettes. The focal sacred object is the Holy Quran on the Rehal.
- **Dual Visual Styles (Selected at Random)**:
  - **Style A (100% Pure Quran on Rehal)**: Fast-paced 4 to 7-second scene cuts cycling purely between 5 distinct 8K angles and camera motions (`zoom_in`, `zoom_out`, `pan_up`) of the Holy Quran on the wooden Rehal.
  - **Style B (Balanced Hybrid)**: Holy Quran on the Rehal anchored every few seconds, interwoven with authentic nature video B-rolls (`ocean_720.mp4`, `clouds_720.mp4`, `desert_720.mp4`) and sacred calligraphy.

## 5. Reciter & Audio Enhancement Mandate (Permanent Standard)
- **Strictly 2 Approved Reciters**: ONLY use **Sheikh Yasser Ad-Dossari** (`dossari`) and **Sheikh Mishary Rashid Alafasy** (`alafasy`). Strictly NO other reciters.
- **Resemble Enhance Full Studio AI**: All recitation audio MUST be processed using **Resemble Enhance** (CFM ODE Midpoint solver, De-Reverb + high-frequency voice harmonic restoration) to deliver close-mic, intimate, crystal-clear studio acoustics. Fallback to DeepFilterNet3 only if cloud access is unavailable.

