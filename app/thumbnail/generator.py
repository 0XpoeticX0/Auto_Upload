import os
import re
import math
import subprocess
from PIL import Image, ImageDraw, ImageEnhance
from app.logger import logger

PILLAR_BADGES = {
    "islamic_stories": "[ সাহাবী ও নবীদের ঘটনা ]",
    "akhirah_unseen": "[ পরকাল ও কিয়ামতের আলামত ]",
    "seerah": "[ সীরাত ও নবীর পবিত্র জীবন ]",
    "misconceptions": "[ সহীহ হাদিস বনাম ভুল ধারণা ]",
    "character_dealings": "[ মুমিনের উত্তম চরিত্র ও আখলাক ]",
    "crises_debt_turnaround": "[ সংকট ও ঋণমুক্তির আমল ]",
    "daily_sunnah": "[ প্রতিদিনের ফজিলতপূর্ণ সুন্নাহ ]",
    "family_marriage_sunnah": "[ পরিবার ও দাম্পত্যের সুন্নাহ ]",
}

BOTTOM_TAGS = {
    "islamic_stories": "সত্য ঘটনা • কুরআন ও সহীহ হাদিস",
    "akhirah_unseen": "সতর্কবার্তা • সহীহ হাদিসের আলো",
    "seerah": "রাসূলুল্লাহ ﷺ-এর জীবন • সহীহ হাদিস",
    "misconceptions": "কুসংস্কার বর্জন • সহীহ হাদিসের আলো",
    "character_dealings": "উত্তম চরিত্র • সহীহ হাদিস",
    "crises_debt_turnaround": "সহীহ দোয়া ও তাওয়াক্কুল",
    "daily_sunnah": "রাসূলুল্লাহ ﷺ-এর সুন্নাহ",
    "family_marriage_sunnah": "ইসলামিক পরিবার • সুন্নাহ",
}

GOLD_KEYWORDS = [
    "কুসংস্কার", "ভুল ধারণা", "আমল", "দোয়া", "দোয়া", "ঋণ", "বরকত", 
    "গুনাহ", "আজাব", "জান্নাত", "জাহান্নাম", "তওবা", "ক্ষমা", "রিজিক",
    "বদনজর", "শান্তি", "তাওয়াক্কুল", "আল্লাহ", "রাসূলুল্লাহ"
]

def format_hook_lines(raw_text: str) -> tuple[str, str]:
    """Cleans title and formats into max 2 balanced, punchy lines with gold accents."""
    text = re.sub(r'[।\?!,\-–—\|]', ' ', raw_text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    
    if len(words) <= 4:
        line1 = " ".join(words)
        line2 = ""
    elif len(words) <= 8:
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
    else:
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:8])
        
    highlighted = False
    for kw in GOLD_KEYWORDS:
        if line2 and kw in line2 and not highlighted:
            line2 = line2.replace(kw, f"{{\\c&H0015CCFA&}}{kw}{{\\c&H00FFFFFF&}}", 1)
            highlighted = True
            break
            
    if not highlighted and line1:
        for kw in GOLD_KEYWORDS:
            if kw in line1:
                line1 = line1.replace(kw, f"{{\\c&H0015CCFA&}}{kw}{{\\c&H00FFFFFF&}}", 1)
                break
                
    return line1, line2

def generate_thumbnail(title: str, topic_id: int, base_image_path: str, category: str = "daily_life") -> str:
    """
    Generates a 1080x1920 vertical high-CTR thumbnail for Shorts/Reels:
    - 8K photorealistic human-free thematic background.
    - Soft dark vignette overlay behind middle title zone for 100% contrast.
    - Top golden category badge (e.g. [ সহীহ হাদিস বনাম ভুল ধারণা ]).
    - Punchy 2-line Bengali hook rendered via libass with Kalpurush font.
    - Bottom authentic reference tag.
    """
    logger.info(f"Generating 1080x1920 thumbnail for topic #{topic_id} ({category}): {title}")
    output_dir = "data/output"
    temp_dir = os.path.join("data", "temp", f"thumb_{topic_id}")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    final_path = os.path.join(output_dir, f"thumbnail_{topic_id}.jpg")
    
    if not base_image_path or not os.path.exists(base_image_path):
        from app.quality.vision_guardian import get_certified_safe_fallback
        fallback_bg = os.path.join(temp_dir, "fallback_base.jpg")
        if get_certified_safe_fallback(fallback_bg, category=category):
            base_image_path = fallback_bg
        else:
            base_image_path = "app/assets/scenes/ancient_islamic_library.jpg"
            
    try:
        # 1. Resize and crop base image to 1080x1920
        img = Image.open(base_image_path).convert("RGBA")
        w, h = img.size
        scale = max(1080 / w, 1920 / h)
        nw = int(math.ceil(w * scale))
        nh = int(math.ceil(h * scale))
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        x0 = (nw - 1080) // 2
        y0 = (nh - 1920) // 2
        cropped = resized.crop((x0, y0, x0 + 1080, y0 + 1920))
        
        # 2. Apply gentle contrast & color enhancement
        enhancer_contrast = ImageEnhance.Contrast(cropped)
        enhanced = enhancer_contrast.enhance(1.15)
        enhancer_color = ImageEnhance.Color(enhanced)
        enhanced = enhancer_color.enhance(1.15)
        
        # 3. Create dark vignette overlay to guarantee readability
        vig = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(vig)
        for y in range(480, 1380):
            dist = 1.0 - abs(y - 880) / 450.0
            alpha = int(165 * max(0.0, dist))
            draw.line([(0, y), (1080, y)], fill=(4, 7, 14, alpha))
            
        for y in range(1600, 1920):
            alpha = int(210 * ((y - 1600) / 320.0))
            draw.line([(0, y), (1080, y)], fill=(4, 7, 14, alpha))
            
        composite = Image.alpha_composite(enhanced, vig).convert("RGB")
        vig_path = os.path.join(temp_dir, "vignette_bg.jpg")
        composite.save(vig_path, quality=95)
        
        # 4. Prepare text elements
        badge = PILLAR_BADGES.get(category, "[ সহীহ হাদিসের বার্তা ]")
        bottom = BOTTOM_TAGS.get(category, "কুরআন ও সহীহ সুন্নাহর সঠিক বার্তা")
        line1, line2 = format_hook_lines(title)
        
        hook_text = f"{line1}\\N{line2}" if line2 else line1
        
        # 5. Build ASS subtitle script
        ass_path = os.path.join(temp_dir, "thumb.ass")
        ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Badge,Kalpurush,46,&H0015CCFA,&H000000FF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,1,5.0,2.5,5,50,50,0,1
Style: MainHook,Kalpurush,82,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,1,6.5,3.5,5,60,60,0,1
Style: BottomTag,Kalpurush,44,&H0015CCFA,&H000000FF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,3.5,2.0,5,50,50,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Badge,,0,0,0,,{{\\pos(540,730)}}{badge}
Dialogue: 0,0:00:00.00,0:00:05.00,MainHook,,0,0,0,,{{\\pos(540,890)}}{hook_text}
Dialogue: 0,0:00:00.00,0:00:05.00,BottomTag,,0,0,0,,{{\\pos(540,1750)}}{bottom}
"""
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
            
        rel_vig = os.path.relpath(vig_path).replace("\\", "/")
        rel_ass = os.path.relpath(ass_path).replace("\\", "/")
        rel_fonts = os.path.relpath("app/assets/fonts").replace("\\", "/")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", rel_vig,
            "-vf", f"subtitles='{rel_ass}':fontsdir='{rel_fonts}'",
            "-vframes", "1",
            "-q:v", "2",
            final_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"✅ Dynamic 1080x1920 thumbnail created: {final_path}")
        return final_path
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None
