# -*- coding: utf-8 -*-
"""
app/quiz/card_builder.py
========================
High-Converting 60-30-10 Islamic Quiz Glassmorphic Overlay & Subtitle Generator.
Strictly adheres to:
1. 60-30-10 Rule:
   - 60% Dominant: Live-motion background footage + deep midnight frosted glass (#08100C).
   - 30% Secondary: Pure white (#FFFFFF) Kalpurush typography + slate glass borders (#2D5F4B).
   - 10% Accent: Radiant Islamic Gold (#FFD52B) and Luminous Emerald (#10B981).
2. docs/VIRAL_HOOK_RULES.md (4 Core Psychology Rules + Golden Highlight Framework).
3. docs/QUIZ_CONTENT_RULES.md (3-Question Rapid-Fire Interaction).
4. GEMINI.md (100% Halal live-motion footage, Kalpurush font, zero static photos).
"""

import os
import re
from PIL import Image, ImageDraw

WIDTH = 1080
HEIGHT = 1920

# ── 60-30-10 Color Palette ──────────────────────────────────────────────────
COLOR_BG_DARK_GLASS = (8, 16, 12, 230)       # 60% Dominant: Deep midnight frosted glass
COLOR_CARD_BORDER = (45, 95, 75, 255)        # 30% Secondary: Clean emerald glass border
COLOR_GOLD_ACCENT = (255, 213, 43, 255)      # 10% Accent: #FFD52B Vibrant Golden Yellow
COLOR_GOLD_BORDER = (235, 175, 65, 255)      # Royal Gold border
COLOR_GOLD_CONTAINER = (45, 34, 10, 235)     # Warm gold-tinted pill container
COLOR_CORRECT_FILL = (16, 185, 129, 255)     # 10% Accent: #10B981 Luminous Emerald Green
COLOR_CORRECT_BORDER = (255, 255, 255, 255)  # Pure White glow outline
COLOR_WRONG_DIM_FILL = (6, 14, 11, 120)      # Muted 30% opacity for incorrect options
COLOR_WRONG_DIM_BORDER = (22, 40, 32, 90)    # Subdued border

# ASS BGR Colors
ASS_COLOR_WHITE = "&H00FFFFFF&"
ASS_COLOR_GOLD = "&H002BD5FF&"               # BGR for #FFD52B (Vibrant Golden Yellow)
ASS_COLOR_EMERALD = "&H0081B910&"            # BGR for #10B981
ASS_COLOR_MUTED = "&H007A8F83&"              # Dimmed option text
ASS_COLOR_DARK = "&H000B1711&"               # Dark contrast text for badges

def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    box: tuple,
    radius: int,
    fill: tuple,
    outline: tuple = None,
    width: int = 1
):
    """Draws a smooth anti-aliased rounded rectangle with RGBA support."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def create_viral_overlay(
    q_data: dict,
    state: str = "question",
    out_png_path: str = "data/temp/overlay.png"
) -> str:
    """
    Renders 60-30-10 glassmorphic UI overlay as a transparent PNG:
    - Top Psychology Challenge Hook Pill
    - Category & Question Tracker Badge
    - Main Question Glassmorphic Card
    - 3 Tactile Option cards with circular letter badges
    - Dynamic animated progress timer / Sahih Hadith proof card
    """
    os.makedirs(os.path.dirname(out_png_path), exist_ok=True)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    q_num = q_data.get("number", 1)
    total_q = q_data.get("total_questions", 3)
    category = q_data.get("category", "কুরআন ও হাদিস")
    options = q_data.get("options", ["ক) ...", "খ) ...", "গ) ..."])
    correct_opt = q_data.get("correct_option", "ক").strip()
    correct_letter = correct_opt[0] if correct_opt else "ক"
    is_revealed = (state == "reveal")

    # ── 1. Top Viral Hook Banner (Y: 130 to 235) ──────────────────────────────
    hook_box = (65, 130, WIDTH - 65, 235)
    draw_rounded_rect(draw, (63, 128, WIDTH - 63, 237), radius=28, fill=(0, 0, 0, 70), outline=(255, 213, 43, 90), width=2)
    draw_rounded_rect(draw, hook_box, radius=26, fill=COLOR_GOLD_CONTAINER, outline=COLOR_GOLD_ACCENT, width=3)

    # ── 2. Category & Tracker Pill (Y: 255 to 310) ────────────────────────────
    tracker_box = (270, 255, WIDTH - 270, 310)
    draw_rounded_rect(draw, tracker_box, radius=18, fill=(12, 30, 22, 220), outline=(50, 110, 85, 220), width=1)

    # ── 3. Main Question Glassmorphic Card (Y: 335 to 680) ───────────────────
    q_box = (65, 335, WIDTH - 65, 680)
    draw_rounded_rect(draw, (62, 332, WIDTH - 62, 683), radius=34, fill=(0, 0, 0, 80), outline=(45, 95, 75, 100), width=2)
    draw_rounded_rect(draw, q_box, radius=32, fill=COLOR_BG_DARK_GLASS, outline=COLOR_CARD_BORDER, width=2)

    # ── 4. Tactile Option Cards (3 Options) ───────────────────────────────────
    opt_start_y = 715
    opt_height = 145
    opt_gap = 28

    for idx, opt in enumerate(options):
        opt_str = opt.strip()
        opt_letter = opt_str[0] if opt_str else ["ক", "খ", "গ"][idx]
        is_this_correct = (opt_letter == correct_letter) or (correct_opt in opt_str)
        y1 = opt_start_y + idx * (opt_height + opt_gap)
        y2 = y1 + opt_height
        opt_box = (75, y1, WIDTH - 75, y2)

        if is_revealed:
            if is_this_correct:
                # 10% Accent Luminous Emerald
                draw_rounded_rect(draw, (71, y1 - 4, WIDTH - 71, y2 + 4), radius=26, fill=(16, 185, 129, 60), outline=(16, 185, 129, 120), width=3)
                draw_rounded_rect(draw, opt_box, radius=24, fill=COLOR_CORRECT_FILL, outline=COLOR_CORRECT_BORDER, width=3)
                # White checkmark circle
                draw.ellipse((105, y1 + 35, 180, y1 + 110), fill=(255, 255, 255, 255), outline=None)
            else:
                # Dimmed
                draw_rounded_rect(draw, opt_box, radius=24, fill=COLOR_WRONG_DIM_FILL, outline=COLOR_WRONG_DIM_BORDER, width=1)
                draw.ellipse((105, y1 + 35, 180, y1 + 110), fill=(14, 25, 20, 150), outline=(40, 70, 55, 100), width=1)
        else:
            # 30% Secondary structure
            draw_rounded_rect(draw, (73, y1 - 2, WIDTH - 73, y2 + 2), radius=26, fill=(0, 0, 0, 60), outline=(45, 95, 75, 80), width=1)
            draw_rounded_rect(draw, opt_box, radius=24, fill=COLOR_BG_DARK_GLASS, outline=COLOR_CARD_BORDER, width=2)
            # 10% Gold circular letter badge
            draw.ellipse((105, y1 + 35, 180, y1 + 110), fill=(45, 34, 10, 240), outline=COLOR_GOLD_ACCENT, width=2)

    # ── 5. Dynamic Footer (Countdown vs. Sahih Proof) ──────────────────────────
    if not is_revealed:
        # Progress Bar & Ticking Indicator
        bar_bg = (120, 1245, WIDTH - 120, 1262)
        draw_rounded_rect(draw, bar_bg, radius=8, fill=(15, 30, 24, 200), outline=(40, 80, 60, 150), width=1)

        pct_map = {
            "question": 1.0,
            "countdown_3": 0.66,
            "countdown_2": 0.33,
            "countdown_1": 0.08
        }
        fill_pct = pct_map.get(state, 1.0)
        bar_w = int((WIDTH - 240) * fill_pct)
        if bar_w > 12:
            fill_box = (120, 1245, 120 + bar_w, 1262)
            draw_rounded_rect(draw, fill_box, radius=8, fill=COLOR_GOLD_ACCENT, outline=None)
    else:
        # Sahih Proof Card
        proof_box = (75, 1235, WIDTH - 75, 1375)
        draw_rounded_rect(draw, (72, 1232, WIDTH - 72, 1378), radius=24, fill=(0, 0, 0, 80), outline=(16, 185, 129, 90), width=2)
        draw_rounded_rect(draw, proof_box, radius=22, fill=(12, 34, 24, 245), outline=(16, 185, 129, 240), width=2)

    # ── 6. Bottom Progress Tracker Dots & CTA (Y: 1720 to 1840) ───────────────
    total_dots = total_q
    dot_radius = 12
    start_dot_x = int(WIDTH / 2 - ((total_dots - 1) * 36) / 2)
    for d in range(total_dots):
        cx = start_dot_x + d * 36
        cy = 1750
        if d < q_num:
            draw.ellipse((cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius), fill=COLOR_GOLD_ACCENT, outline=(255, 255, 255, 255), width=2)
        else:
            draw.ellipse((cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius), fill=(30, 55, 45, 180), outline=(60, 100, 80, 150), width=1)

    img.save(out_png_path, "PNG")
    return out_png_path

def format_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int((sec - int(sec)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def build_timed_ass(q_data: dict, t_countdown: float, t_reveal: float, total_dur: float, out_ass_path: str):
    """
    Builds timed ASS subtitle file using Kalpurush font and 60-30-10 styling.
    """
    ts_start = format_ts(0.0)
    ts_c3 = format_ts(t_countdown)
    ts_c2 = format_ts(t_countdown + 1.0)
    ts_c1 = format_ts(t_countdown + 2.0)
    ts_rev = format_ts(t_reveal)
    ts_end = format_ts(total_dur)

    raw_question = q_data.get("question", "")
    question = re.sub(r'^(?:প্রশ্ন\s*[০-৯\d]+[:।\-]?\s*|Question\s*\d+[:.\-]?\s*|Q\d+[:.\-]?\s*)', '', raw_question, flags=re.IGNORECASE).strip()
    options = q_data.get("options", [])
    correct_opt = q_data.get("correct_option", "ক").strip()
    correct_letter = correct_opt[0] if correct_opt else "ক"
    explanation = q_data.get("explanation", "").strip()
    q_num = q_data.get("number", 1)
    total_q = q_data.get("total_questions", 3)
    category = q_data.get("category", "আল-কুরআন")

    hook_text = "🏆 ৩টি সহজ ইসলামিক প্রশ্ন—৩-এ ৩ পাওয়ার চ্যালেঞ্জ নিচ্ছেন? ➔"

    # Golden Highlights on sacred question terms (10% Accent)
    styled_q = question
    for term in ["বিসমিল্লাহ", "সূরা", "ফরজ", "হারাম", "হালাল", "নবীজি", "রাসূলুল্লাহ", "সালাত", "যোহর", "আসর", "দেনমোহর", "গীবত"]:
        if term in styled_q:
            styled_q = styled_q.replace(term, f"{{\\c{ASS_COLOR_GOLD}}}{term}{{\\c{ASS_COLOR_WHITE}}}")
            break

    words = styled_q.split()
    mid = len(words) // 2
    if len(words) > 5:
        line_1 = " ".join(words[:mid])
        line_2 = " ".join(words[mid:])
        lines = [line_1, line_2]
    else:
        lines = [" ".join(words)]

    dialogues = []
    # 1. Top Hook
    dialogues.append(f"Dialogue: 0,{ts_start},{ts_end},HookStyle,,0,0,0,,{{\\pos(540,182)}}{hook_text}")
    # 2. Tracker
    dialogues.append(f"Dialogue: 0,{ts_start},{ts_end},TrackerStyle,,0,0,0,,{{\\pos(540,282)}}📖 {category} • প্রশ্ন {q_num}/{total_q}")

    # 3. Question Text (30% Secondary White)
    start_q_y = 480 - (len(lines) - 1) * 38
    for line in lines:
        dialogues.append(f"Dialogue: 0,{ts_start},{ts_end},QuestionStyle,,0,0,0,,{{\\pos(540,{start_q_y})}}{line}")
        start_q_y += 82

    # 4. Options
    opt_y = 787
    for idx, opt in enumerate(options):
        opt_str = opt.strip()
        opt_letter = opt_str[0] if opt_str else ["ক", "খ", "গ"][idx]
        is_this_correct = (opt_letter == correct_letter) or (correct_opt in opt_str)
        opt_text = opt_str[2:].strip() if len(opt_str) > 2 and opt_str[1] in [')', ':', '-'] else opt_str

        # Before reveal: 30% secondary white
        dialogues.append(f"Dialogue: 0,{ts_start},{ts_rev},OptionStyle,,0,0,0,,{{\\pos(540,{opt_y})}}{opt_text}")

        # After reveal:
        if is_this_correct:
            # 10% Accent Luminous Emerald
            dialogues.append(f"Dialogue: 0,{ts_rev},{ts_end},OptionCorrectStyle,,0,0,0,,{{\\pos(540,{opt_y})}}{opt_text}")
        else:
            # Dimmed out
            dialogues.append(f"Dialogue: 0,{ts_rev},{ts_end},OptionDimStyle,,0,0,0,,{{\\pos(540,{opt_y})}}{opt_text}")
        opt_y += 173

    # 5. Countdown text (10% Gold)
    dialogues.append(f"Dialogue: 0,{ts_c3},{ts_c2},TimerNumStyle,,0,0,0,,{{\\pos(540,1315)}}⏱️ আর ৩ সেকেন্ড...")
    dialogues.append(f"Dialogue: 0,{ts_c2},{ts_c1},TimerNumStyle,,0,0,0,,{{\\pos(540,1315)}}⏱️ আর ২ সেকেন্ড...")
    dialogues.append(f"Dialogue: 0,{ts_c1},{ts_rev},TimerNumStyle,,0,0,0,,{{\\pos(540,1315)}}⏱️ আর ১ সেকেন্ড...")

    # 6. Reveal Badge & Sahih Proof
    dialogues.append(f"Dialogue: 0,{ts_rev},{ts_end},RevealBadgeStyle,,0,0,0,,{{\\pos(540,1268)}}✅ সঠিক উত্তর: [{correct_letter}]")
    if explanation:
        dialogues.append(f"Dialogue: 0,{ts_rev},{ts_end},ProofStyle,,0,0,0,,{{\\pos(540,1322)}}{explanation}")

    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HookStyle,Kalpurush,38,{ASS_COLOR_WHITE},&H000000FF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,0,0,5,30,30,10,1
Style: TrackerStyle,Kalpurush,34,{ASS_COLOR_GOLD},&H000000FF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,0,0,5,30,30,10,1
Style: QuestionStyle,Kalpurush,54,{ASS_COLOR_WHITE},&H000000FF&,&H00050D09&,&H70000000&,0,0,0,0,100,100,0,0,1,3.5,1.5,5,80,80,10,1
Style: OptionStyle,Kalpurush,48,{ASS_COLOR_WHITE},&H000000FF&,&H0008120D&,&H50000000&,0,0,0,0,100,100,0,0,1,2.8,1.2,5,100,100,10,1
Style: OptionCorrectStyle,Kalpurush,50,{ASS_COLOR_DARK},&H000000FF&,&H00FFFFFF&,&H00000000&,1,0,0,0,100,100,0,0,1,1.5,0,5,100,100,10,1
Style: OptionDimStyle,Kalpurush,44,{ASS_COLOR_MUTED},&H000000FF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,0,0,5,100,100,10,1
Style: TimerNumStyle,Kalpurush,42,{ASS_COLOR_GOLD},&H000000FF&,&H000A1812&,&H60000000&,0,0,0,0,100,100,0,0,1,3.0,1.2,5,30,30,10,1
Style: RevealBadgeStyle,Kalpurush,46,{ASS_COLOR_GOLD},&H000000FF&,&H00091710&,&H70000000&,1,0,0,0,100,100,0,0,1,3.2,1.5,5,30,30,10,1
Style: ProofStyle,Kalpurush,32,{ASS_COLOR_WHITE},&H000000FF&,&H0007130E&,&H50000000&,0,0,0,0,100,100,0,0,1,2.2,1.0,5,80,80,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(dialogues)

    os.makedirs(os.path.dirname(out_ass_path), exist_ok=True)
    with open(out_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
