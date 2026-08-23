import os
import sys
import subprocess
import shutil

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

audio_src = "e:/Project/youtube_video/1974.mp4"
video_src = "e:/Project/youtube_video/2038.mp4"
out_dir = "e:/Project/youtube_video/data/output/ahzab_merge"
fonts_dir = "e:/Project/youtube_video/app/assets/fonts"
os.makedirs(out_dir, exist_ok=True)

ass_path = os.path.join(out_dir, "exact_subtitles.ass").replace("\\", "/")

def to_ass_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        cs = 0
        s += 1
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

subtitles = [
    # 0.000 to 0.850: Reciter breath/silence (no text)
    (0.85, 2.25, "إِنَّ الْمُسْلِمِينَ", "নিশ্চয়ই আত্মসমর্পণকারী পুরুষ"),
    (2.25, 4.08, "وَالْمُسْلِمَاتِ", "এবং আত্মসমর্পণকারী নারী,"),
    (4.08, 5.76, "وَالْمُؤْمِنِينَ", "এবং মুমিন পুরুষ"),
    (5.76, 6.98, "وَالْمُؤْمِنَاتِ", "এবং মুমিন নারী,"),
    (6.98, 8.38, "وَالْقَانِتِينَ", "এবং অনুগত পুরুষ"),
    (8.38, 9.76, "وَالْقَانِتَاتِ", "এবং অনুগত নারী,"),
    (9.76, 11.18, "وَالصَّادِقِينَ", "এবং সত্যবাদী পুরুষ"),
    (11.18, 12.58, "وَالصَّادِقَاتِ", "এবং সত্যবাদী নারী,"),
    (12.58, 13.98, "وَالصَّابِرِينَ", "এবং ধৈর্যশীল পুরুষ"),
    (13.98, 15.58, "وَالصَّابِرَاتِ", "এবং ধৈর্যশীল নারী,"),
    (15.58, 17.95, "وَالْخَاشِعِينَ", "এবং বিনীত পুরুষ"),
    (17.95, 20.95, "وَالْخَاشِعَاتِ", "এবং বিনীত নারী,"),
    (20.95, 22.95, "وَالْمُتَصَدِّقِينَ", "এবং দানশীল পুরুষ"),
    (22.95, 25.18, "وَالْمُتَصَدِّقَاتِ", "এবং দানশীল নারী,"),
    (25.18, 28.78, "وَالصَّائِمِينَ", "এবং সিয়াম পালনকারী পুরুষ"),
    (28.78, 31.18, "وَالصَّائِمَاتِ", "এবং সিয়াম পালনকারী নারী,"),
    (31.18, 34.98, "وَالْحَافِظِينَ فُرُوجَهُمْ وَالْحَافِظَاتِ", "নিজেদের শালীনতা ও যৌনাঙ্গ হেফাজতকারী পুরুষ ও নারী"),
    (34.98, 42.58, "وَالذَّاكِرِينَ اللَّهَ كَثِيرًا وَالذَّاكِرَاتِ", "এবং আল্লাহকে অধিক স্মরণকারী পুরুষ ও নারী—"),
    (42.58, 45.58, "أَعَدَّ اللَّهُ لَهُم مَّغْفِرَةً", "আল্লাহ তাদের জন্য প্রস্তুত রেখেছেন ক্ষমা"),
    (45.58, 48.40, "وَأَجْرًا عَظِيمًا", "এবং মহাপুরস্কার।")
]

# Top Username Handle (@dailydos_islam matching @bo1truth)
# Arabic: Noto Sans Arabic Bold (White)
# Bengali: Noto Sans Bengali Bold (Golden Yellow highlight)
# Lower-Third: Large Orange "Al-Ahzab Surah" + White "35. Ayah" + Follow CTA
ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TopUsername,Arial,36,&H50FFFFFF,&H000000FF,&H00000000,&H60000000,1,0,0,0,100,100,0,0,1,1.5,1.0,5,40,40,0,1
Style: ArabicText,Noto Sans Arabic,68,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,1,3.8,2.5,5,40,40,0,1
Style: BengaliText,Noto Sans Bengali,52,&H002BD5FF,&H000000FF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,1,3.8,2.4,5,40,40,0,1
Style: SurahTitleOrange,Arial,72,&H002082F5,&H000000FF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,1,4.0,2.5,5,40,40,0,1
Style: AyahTitleWhite,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,1,0,0,0,100,100,0,0,1,3.5,2.0,5,40,40,0,1
Style: FollowCTA,Noto Sans Bengali,34,&H00E2E8F0,&H000000FF,&H00000000,&HB0000000,1,0,0,0,100,100,0,0,1,2.8,1.8,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

events = [
    # Top Username Handle matching 1974.mp4 (@bo1truth -> @dailydos_islam)
    "Dialogue: 0,0:00:00.00,0:00:48.44,TopUsername,,0,0,0,,{\\pos(540,160)}@dailydos_islam",
    # Permanent Lower-Third matching 1974.mp4
    "Dialogue: 0,0:00:00.00,0:00:48.44,SurahTitleOrange,,0,0,0,,{\\b1\\pos(540,1380)}Al-Ahzab Surah",
    "Dialogue: 0,0:00:00.00,0:00:48.44,AyahTitleWhite,,0,0,0,,{\\b1\\pos(540,1460)}35. Ayah",
    # Follow for more CTA
    "Dialogue: 0,0:00:00.00,0:00:48.44,FollowCTA,,0,0,0,,{\\pos(540,1540)}✦ Follow for more Quran Recitations: @dailydos_islam ✦",
]

for t_start, t_end, ar, bn in subtitles:
    s_ass = to_ass_time(t_start)
    e_ass = to_ass_time(t_end)
    events.append(f"Dialogue: 1,{s_ass},{e_ass},ArabicText,,0,0,0,,{{\\pos(540,850)}}{ar}")
    events.append(f"Dialogue: 1,{s_ass},{e_ass},BengaliText,,0,0,0,,{{\\pos(540,945)}}{bn}")

with open(ass_path, "w", encoding="utf-8") as f:
    f.write(ass_header + "\n".join(events) + "\n")

print(f"Generated Golden Highlighted ASS Subtitles: {ass_path}")

final_output = os.path.join(out_dir, "surah_al_ahzab_35_vertical.mp4").replace("\\", "/")
ass_escaped = ass_path.replace(":", "\\:").replace("/", "/")
fonts_escaped = fonts_dir.replace(":", "\\:").replace("/", "/")

filter_complex = (
    f"[1:v]scale=-1:1920,crop=1080:1920:(in_w-1080)/2:0,setpts=PTS/0.6,fps=30,eq=brightness=-0.08:contrast=1.08:saturation=0.95,vignette=angle=PI/3.8:x0=w/2:y0=h/2,split=4[a][b][c][d];"
    f"[a][b]xfade=transition=fade:duration=0.8:offset=15.875[x1];"
    f"[x1][c]xfade=transition=fade:duration=0.8:offset=31.750[x2];"
    f"[x2][d]xfade=transition=fade:duration=0.8:offset=47.625[x3];"
    f"[x3]trim=duration=48.44,setpts=PTS-STARTPTS,subtitles='{ass_escaped}':fontsdir='{fonts_escaped}'[vfinal]"
)

cmd = [
    "ffmpeg", "-y",
    "-i", audio_src,    # Master Audio from Video 1
    "-i", video_src,    # Background corridor from Video 2
    "-filter_complex", filter_complex,
    "-map", "[vfinal]",
    "-map", "0:a:0",
    "-c:v", "libx264",
    "-crf", "17",
    "-preset", "fast",
    "-c:a", "aac",
    "-b:a", "192k",
    "-t", "48.44",
    final_output
]

print("Rendering Master Video with @dailydos_islam Handle, Golden Bengali Highlight & Follow CTA...")
subprocess.run(cmd, check=True)

# Copy to workspace root
ws_root_path = "e:/Project/youtube_video/surah_al_ahzab_35_vertical.mp4"
shutil.copyfile(final_output, ws_root_path)

# Copy to artifacts
artifact_vid = "C:/Users/MaHir0/.gemini/antigravity/brain/41684ca8-cc27-429d-a9d6-52cb58c4498f/surah_al_ahzab_35_vertical.mp4"
shutil.copyfile(final_output, artifact_vid)

# Generate comparison preview frames
os.makedirs("scratch/gen_frames", exist_ok=True)
for t in [0.5, 1.5, 44.0]:
    subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", final_output, "-vframes", "1", "-q:v", "2", f"scratch/gen_frames/frame_{t:.1f}.jpg"], capture_output=True)
    shutil.copyfile(f"scratch/gen_frames/frame_{t:.1f}.jpg", f"C:/Users/MaHir0/.gemini/antigravity/brain/41684ca8-cc27-429d-a9d6-52cb58c4498f/gen_frame_{t:.1f}.jpg")

print("\n🎉 Master Render Complete! Saved to:", ws_root_path)
