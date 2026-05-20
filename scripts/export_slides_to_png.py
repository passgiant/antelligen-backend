"""Export every slide of PRESENTATION_SLIDES.pptx to PNG via PowerPoint COM."""
from __future__ import annotations

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

import win32com.client

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPTX = os.path.join(ROOT, "docs", "angelligen", "PRESENTATION_SLIDES.pptx")
OUT_DIR = os.path.join(ROOT, "docs", "angelligen", "_slides_preview")

os.makedirs(OUT_DIR, exist_ok=True)

ppt = win32com.client.Dispatch("PowerPoint.Application")
try:
    pres = ppt.Presentations.Open(PPTX, WithWindow=False)
    total = pres.Slides.Count
    print(f"Total slides: {total}", flush=True)
    for i in range(1, total + 1):
        out = os.path.join(OUT_DIR, f"slide_{i:02d}.png")
        pres.Slides(i).Export(out, "PNG", 1600, 900)
        print(f"  ✓ {out}", flush=True)
    pres.Close()
finally:
    ppt.Quit()

print("Done")
