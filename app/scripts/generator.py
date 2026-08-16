from app.llm.provider import extract_json
from app.logger import logger
from app.database import get_connection
import json

CATEGORY_TONES = {
    "islamic_knowledge": "a wise, sincere, and knowledgeable Islamic scholar sharing powerful reminders from the Quran and Sunnah. Speak with absolute authenticity, compassion, and awe."
}

def generate_script(topic_id: int, topic_title: str, video_format: str = "short", duration_sec: int = 90, category: str = "islamic_knowledge", series_info: dict = None):
    logger.info(f"Generating {video_format} script for topic: {topic_title} ({duration_sec}s)")
    
    # 1 scene = ~5-6 seconds. We want roughly 5-6 scenes for a short, and ~24 for a 3 min video.
    num_scenes = max(5, round(duration_sec / 7.5))
    words_per_scene = 20
    total_words = num_scenes * words_per_scene
    
    tone = CATEGORY_TONES.get(category, CATEGORY_TONES["islamic_knowledge"])

    rules = []
    
    rules.append(f"""=============================================
RULE 1 — DURATION (NON-NEGOTIABLE)
=============================================
- You MUST write EXACTLY {num_scenes} scenes.
- Every single scene's narration MUST contain approximately {words_per_scene} words.
- DO NOT summarize or skip scenes to save space.""")

    rules.append("""=============================================
RULE 2 — ISLAMIC AUTHENTICITY & CITATIONS (STRICT & MANDATORY)
=============================================
- Every single fact, story, Ayah, and Hadith MUST be 100% AUTHENTIC from the Quran or Sahih/Hasan Sunnah (Sahih Bukhari, Sahih Muslim, Sunan Abi Dawud, Jami' at-Tirmidhi, Sunan an-Nasa'i, Sunan Ibn Majah, Musnad Ahmad).
- STRICTLY FORBIDDEN: NEVER use weak (da'eef) hadiths, fabricated claims, cultural myths, or made-up narratives.
- NEVER cut an Ayah or Hadith in half: The quoted Arabic text must be a complete, grammatically intact verse, Hadith statement, or self-contained Dua.
- You MUST provide the exact chapter/verse (e.g. 'Quran 2:153') or exact collection & number (e.g. 'Sahih Bukhari 5063', 'Sahih Muslim 1631') in the 'references' array of your JSON output.""")

    rules.append("""=============================================
RULE 3 — HOOK & VIRAL STORYTELLING
=============================================
- THE 3-SECOND CURIOSITY GAP: Scene 1 narration MUST start with a hook that creates a curiosity gap. Start with a bold claim or a relatable question that makes the viewer realize there is a secret they don't know. Never start with a dry fact.
- MAKE IT RELATABLE: Translate complex topics into things the viewer experiences every day. Speak directly to them ("Have you ever...", "Think about...").
- Final scene narration MUST end with exactly: "Follow for more authentic Islamic reminders... every single day!\"""")
    
    json_format = f"""{{
    "title": "Catchy viral title under 60 characters",
    "references": ["Reference 1", "Reference 2"],
    "scenes": [
        {{
            "scene_number": 1,
            "narration": "Exactly {words_per_scene} words...",
            "visuals": "Detailed visual prompt, photorealistic, 8k, cinematic"
        }}
    ]
}}"""

    rules.append(f"""=============================================
RULE 4 — WRITE FOR THE EAR (VOICE & TONE)
=============================================
- Write like {tone}
- USE SIMPLE, EVERYDAY VOCABULARY: Write at a 5th-grade reading level. Use words people use daily. Do not use complex, academic, or "hard to catch" words.
- AI READS EXACTLY WHAT YOU TYPE. If you write formally, it sounds like a robot.
- USE CONTRACTIONS: Always use "it's", "they're", "wouldn't", "you've". Never use "it is" or "they are".
- USE FILLER WORDS: Occasionally start sentences with "Now,", "Look,", or "Listen," to make it sound conversational.
- FORCE PUNCTUATION PAUSES: Use ellipses (...) for dramatic, trailing pauses. Use em-dashes (—) for a sudden interruption or shift in tone.
- SHORT, PUNCHY SENTENCES: Break up long sentences. If it has an "and", make it two sentences.""")

    rules.append("""=============================================
RULE 5 — THE "BUT / THEREFORE" FRAMEWORK
=============================================
- DO NOT use "and then" storytelling. 
- A gripping script says: "This happened, THEREFORE this happened, BUT then this went wrong."
- The narrative must escalate and constantly shift momentum.""")

    rules.append("""=============================================
RULE 6 — NO REPETITION (CRITICAL)
=============================================
- NEVER repeat the same sentence or phrase.
- Each scene must introduce NEW information, NEW story beats, or NEW concepts.
- The story must continuously move forward.""")

    rules.append("""=============================================
RULE 7 — VISUAL-SCRIPT MATCHING (CRITICAL)
=============================================
Every scene's 'visuals' field MUST literally show what the narration describes at that exact moment.
- NEVER describe a close-up face, portrait, or selfie. ALWAYS describe the full environment and scene.
- Describe the LOCATION and ACTION, not the person's face.
- Always end visual prompt with: ", wide angle, full scene, photorealistic, 8k, dramatic lighting, cinematic\"""")

    rules.append("""=============================================
RULE 8 — DUAL-VOICE ENGINE (COMPLETE ARABIC RECITATION & EXPLANATION)
=============================================
- When quoting an Ayah (Quranic verse), authentic Hadith, or Dua, you MUST write the FULL, complete Arabic script, followed by a newline (\\n), followed by the English pronunciation, followed by a newline (\\n), followed by the full English translation, ALL inside the `<ARABIC>` tags.
- DO NOT cut an Ayah or Hadith in half. The Arabic quotation must be a complete, self-contained statement.
- The English translation inside the `<ARABIC>` tags must be the full, accurate translation of the entire Arabic text.
- AFTER THE ARABIC BLOCK: The English narration that follows MUST be a standalone, complete sentence that clearly explains what the Ayah/Hadith means and connects its profound lesson to the viewer's life.
- NEVER split a sentence across Arabic and English (e.g., DO NOT do '<ARABIC>...</ARABIC> because grief overwhelmed them').
- Correct Example:
  "The Prophet said, <ARABIC>اصْنَعُوا لآلِ جَعْفَرٍ طَعَامًا فَإِنَّهُ قَدْ أَتَاهُمْ أَمْرٌ يَشْغَلُهُمْ\\nIsna'oo li-Aali Ja'farin ta'aman fa-innahu qad ataahum amrun yash-ghaluhum\\n(Prepare food for the family of Ja'far, for there has come upon them what overwhelms them with grief)</ARABIC>. Notice how the Prophet commanded the community to immediately step in and take care of grieving families."
- ONLY wrap the Arabic recitation/Dua block inside `<ARABIC>`. Do not wrap normal English narration.""")


    system_prompt = f"""You are an expert Islamic content writer and master storyteller.
Your job is to write a script for a {duration_sec}-second video (approx {num_scenes} scenes).
Content Category: {category.upper().replace('_', ' ')}

{chr(10).join(rules)}

=============================================
OUTPUT FORMAT
=============================================
Return ONLY valid JSON. No extra text before or after.
- CRITICAL: DO NOT use double quotes (") inside your JSON string values. If you need to quote dialogue, use single quotes ('). This prevents JSON parsing errors.

{json_format}
"""

    user_prompt = f"""Topic: {topic_title}

CHECKLIST BEFORE YOU RESPOND:
1. Did you write EXACTLY {num_scenes} scenes? ___
2. Does each scene have ~{words_per_scene} words? ___
3. Does every visual match its narration exactly? ___
4. Did you double check that you are NOT repeating sentences? ___
5. Did you use ellipses (...) and contractions (they're, it's) to force the TTS to sound human? ___
6. Did you provide authentic references (Quran/Sahih Sunnah)? ___

Only respond when all boxes are checked."""

    script_data = extract_json(system_prompt, user_prompt)
    
    if not script_data:
        logger.error("Failed to generate script.")
        return None
    
    scenes = script_data.get("scenes", [])
    actual_scenes = len(scenes)
    actual_words = sum(len(s.get("narration", "").split()) for s in scenes)
    estimated_duration = actual_words / 2.5
    logger.info(f"Script: {actual_scenes}/{num_scenes} scenes | ~{actual_words} words | ~{estimated_duration:.0f}s estimated duration (target: {duration_sec}s)")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO scripts (topic_id, raw_script, scenes_json)
        VALUES (?, ?, ?)
    ''', (topic_id, json.dumps(script_data), json.dumps(scenes)))
    
    cursor.execute("UPDATE topics SET status = 'SCRIPTING' WHERE id = ?", (topic_id,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Script ({video_format}) successfully generated and saved.")
    return script_data
