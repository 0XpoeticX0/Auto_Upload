# -*- coding: utf-8 -*-
"""
Quran Verse Video Pipeline (< 90s)
Automated selection, recitation download, centered Bengali translation subtitles, and rendering.
"""
from app.quran_verse.generator import run_quran_verse_pipeline, generate_quran_verse_video

__all__ = ["run_quran_verse_pipeline", "generate_quran_verse_video"]
