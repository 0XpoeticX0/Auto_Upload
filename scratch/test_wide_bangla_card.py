import os
import sys
import shutil
import time
import subprocess
from PIL import Image
import requests

CARD_WIDTH = 1080
CARD_HEIGHT = 1350

def split_text_wrap_ass(text: str, max_chars: int = 56) -> list[str]:
    if not text:
        return []
    lines = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        words = paragraph.split()
        cur_line = []
        cur_len = 0
        for w in words:
            clean_w = w.replace("{\\c&H003DBFF2&}", "").replace("{\\c&H00FFFFFF&}", "")
            if cur_len + len(clean_w) + (1 if cur_line else 0) <= max_chars:
                cur_line.append(w)
                cur_len += len(clean_w) + (1 if cur_line else 0)
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(clean_w)
        if cur_line:
            lines.append(" ".join(cur_line))
    return lines

def format_quote_with_highlights_ass(quote_text: str, highlight_phrases: list) -> str:
    styled = quote_text
    for hl in highlight_phrases:
        if hl and hl in styled and "{\\c" not in hl:
            styled = styled.replace(hl, f"{{\\c&H003DBFF2&}}{hl}{{\\c&H00FFFFFF&}}")
    return styled

def render_wide_bangla_card(post_data: dict, output_path: str):
    temp_dir = os.path.abspath("data/temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    timestamp = int(time.time() * 1000)
    temp_bg = os.path.join(temp_dir, f"bg_wide_{timestamp}.jpg")
    temp_canvas = os.path.join(temp_dir, f"canvas_wide_{timestamp}.jpg")
    temp_ass = os.path.join(temp_dir, f"card_wide_{timestamp}.ass")
    
    # 1. Background Visual (Top 35% height ~ 430px with smooth feather into pitch black)
    target_h = 430
    # Download visual
    image_prompt = post_data.get("image_prompt", "sunlight streaming through lush green forest path, majestic tall trees, cinematic atmospheric photography 8k, serene, empty, no humans")
    headers = {"User-Agent": "Mozilla/5.0"}
    encoded_prompt = requests.utils.quote(image_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1350&nologo=true&seed=42"
    r = requests.get(url, headers=headers, timeout=30)
    with open(temp_bg, "wb") as f:
        f.write(r.content)
        
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), (8, 9, 12))
    with Image.open(temp_bg).convert("RGBA") as bg_img:
        bg_w, bg_h = bg_img.size
        scale = max(CARD_WIDTH / bg_w, target_h / bg_h)
        new_w = int(bg_w * scale)
        new_h = int(bg_h * scale)
        bg_scaled = bg_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        crop_x = (new_w - CARD_WIDTH) // 2
        bg_cropped = bg_scaled.crop((crop_x, 0, crop_x + CARD_WIDTH, target_h))
        
        mask = Image.new("L", (CARD_WIDTH, target_h), 255)
        for y in range(target_h):
            if y < target_h * 0.35:
                alpha = 255
            else:
                progress = (y - target_h * 0.35) / (target_h * 0.65)
                alpha = int(255 * (1.0 - (progress ** 1.6)))
            for x in range(CARD_WIDTH):
                mask.putpixel((x, y), alpha)
                
        card.paste(bg_cropped.convert("RGB"), (0, 0), mask)
    card.save(temp_canvas, "JPEG", quality=95)
    
    # 2. Text layout utilizing full horizontal width (left-to-right ~88% of screen)
    header = post_data.get("header", "").strip()
    bangla_quote = post_data.get("quote", "").strip()
    highlight_phrases = post_data.get("highlight_phrases", [])
    explain_title = post_data.get("explain_title", "ব্যাখ্যা:").strip()
    explanation = post_data.get("explanation", "").strip()
    reference = post_data.get("reference", "").strip()
    
    # Ensure header splits cleanly: narrator line 1, Rasulullah line 2 if needed
    if "রাসূলুল্লাহ" in header and "\n" not in header and len(header) > 36:
        # Split cleanly right before Rasulullah
        for split_token in ["রাসূলুল্লাহ", "রাসূলুল্লাহ (সা.)", "মহান আল্লাহ"]:
            if split_token in header:
                idx = header.find(split_token)
                header = header[:idx].rstrip() + "\n" + header[idx:].lstrip()
                break
                
    styled_header = header
    if "রাসূলুল্লাহ" in styled_header and "{\\c" not in styled_header:
        for t in ["রাসূলুল্লাহ (সা.) বলেছেন, মহান আল্লাহ বলেন:", "রাসূলুল্লাহ (সা.) বলেছেন:", "রাসূলুল্লাহ (ﷺ) বলেছেন:"]:
            if t in styled_header:
                styled_header = styled_header.replace(t, f"{{\\c&H003DBFF2&}}{t}{{\\c&H00FFFFFF&}}")
                break
                
    styled_quote = format_quote_with_highlights_ass(bangla_quote, highlight_phrases) if bangla_quote else ""
    
    # Wide wrapping: max 52 chars for quote, max 56 chars for explanation (fills ~900px of 1080px)
    header_lines = split_text_wrap_ass(styled_header, max_chars=48)
    quote_lines = split_text_wrap_ass(styled_quote, max_chars=50)
    explain_lines = split_text_wrap_ass(explanation, max_chars=54)
    
    f_header = 46
    f_quote = 46
    f_explain_title = 34
    f_explain_body = 35
    f_ref = 42
    f_wm = 26
    
    h_step = 58
    q_step = 60
    e_step = 48
    
    # Text block centered in the lower 65% of the card
    current_y = 520
    dialogues = []
    
    # 1. Header
    for h_l in header_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Header,,0,0,0,,{{\\pos(540,{current_y})}}{h_l}")
        current_y += h_step
    current_y += 28
    
    # 2. Quote (Wide & spacious)
    for q_l in quote_lines:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Quote,,0,0,0,,{{\\pos(540,{current_y})}}{q_l}")
        current_y += q_step
    current_y += 36
    
    # 3. Explain Section (Wide & compact 2-3 lines)
    if explanation:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,ExplainTitle,,0,0,0,,{{\\pos(540,{current_y})}}{explain_title}")
        current_y += 48
        for e_l in explain_lines:
            dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Explain,,0,0,0,,{{\\pos(540,{current_y})}}{e_l}")
            current_y += e_step
            
    # 4. Reference & Watermark with comfortable bottom space
    ref_y = max(1170, current_y + 40)
    wm_y = min(1260, ref_y + 55)
    
    if reference:
        dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Reference,,0,0,0,,{{\\pos(540,{ref_y})}}{reference}")
    dialogues.append(f"Dialogue: 0,0:00:00.00,0:00:05.00,Watermark,,0,0,0,,{{\\pos(540,{wm_y})}}@DailyDosOfIslam")
    
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {CARD_WIDTH}
PlayResY: {CARD_HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Header,Noto Sans Bengali,{f_header},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,5,50,50,0,1
Style: Quote,Noto Sans Bengali,{f_quote},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,0,5,50,50,0,1
Style: ExplainTitle,Noto Sans Bengali,{f_explain_title},&H00A0A5B0,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,5,50,50,0,1
Style: Explain,Noto Sans Bengali,{f_explain_body},&H00D0D4DC,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,5,50,50,0,1
Style: Reference,Noto Sans Bengali,{f_ref},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,5,50,50,0,1
Style: Watermark,Noto Sans Bengali,{f_wm},&H00808590,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,5,50,50,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(dialogues)

    with open(temp_ass, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    safe_ass = os.path.relpath(temp_ass).replace('\\', '/')
    cmd = ["ffmpeg", "-y", "-i", temp_canvas, "-vf", f"subtitles='{safe_ass}'", "-frames:v", "1", "-update", "1", output_path]
    subprocess.run(cmd, check=True)
    print("Rendered wide card at:", output_path)

if __name__ == "__main__":
    post_data = {
        "header": "আবু হুরায়রা (রা.) থেকে বর্ণিত, রাসূলুল্লাহ (সা.) বলেছেন:",
        "quote": "‘এক ব্যক্তি পথ দিয়ে হেঁটে যাওয়ার সময় রাস্তায় একটি কাঁটার ডাল দেখতে পেয়ে তা সরিয়ে দিল। আল্লাহ তার এই কাজের কদর করলেন এবং তাকে ক্ষমা করে দিলেন।’",
        "highlight_phrases": ["কাঁটার ডাল", "তাকে ক্ষমা করে দিলেন"],
        "explain_title": "ব্যাখ্যা:",
        "explanation": "মানুষের পথ চলা সহজ করার মতো ছোট নিঃস্বার্থ উপকারও আল্লাহর কাছে অত্যন্ত প্রিয়। দৈনন্দিন জীবনের কোনো ছোট নেক আমলকেই অবহেলা করবেন না, হয়তো সেই সামান্য কাজটিই আপনার ক্ষমার কারণ হতে পারে।",
        "reference": "সহীহ বুখারী: ২৪৭২, সহীহ মুসলিম: ১৯১৪",
        "image_prompt": "sunlight streaming through lush green forest path, majestic tall trees, cinematic atmospheric photography 8k, serene, empty, no humans"
    }
    out = os.path.abspath("data/test_wide_bangla_card.jpg")
    render_wide_bangla_card(post_data, out)
