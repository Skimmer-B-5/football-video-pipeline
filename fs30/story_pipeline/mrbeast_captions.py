"""
MrBeast-Style Animated Word-by-Word Caption Renderer for 9:16 Vertical Video.
Features:
- Dynamic phrase grouping (2-4 words per burst)
- Kinetic word-level highlighting in vibrant Neon Yellow (#FFE800)
- Tactile scale-pop bounce animation on active word (1.14x -> 1.06x)
- Heavy 12px pure black outline for 100% contrast over any background
- Deep 3D drop shadow
- Sub-pixel smooth compositing via PIL
"""

import math
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Font configuration
IMPACT_PATH = Path(r"C:\Windows\Fonts\impact.ttf")
FONT_SIZE = 64
if IMPACT_PATH.exists():
    CAPTION_FONT = ImageFont.truetype(str(IMPACT_PATH), FONT_SIZE)
else:
    LOCAL_FONT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\fs30\story_pipeline\assets\fonts\BarlowCondensed-ExtraBold.ttf")
    CAPTION_FONT = ImageFont.truetype(str(LOCAL_FONT), FONT_SIZE + 6)

# Palette
COLOR_WHITE = (255, 255, 255, 255)
COLOR_YELLOW = (255, 232, 0, 255)   # MrBeast signature electric yellow
COLOR_RED = (255, 45, 65, 255)      # Climax emphasis words
COLOR_BLACK = (0, 0, 0, 255)
COLOR_SHADOW = (0, 0, 0, 220)

# Emphasis words that pop in bright red
CLIMAX_WORDS = {"KICK", "SHATTERED", "THERMONUCLEAR", "BANNED", "KING", "RED", "PRISON", "HEADBUTT", "PANENKA", "ZIZOU", "AUDACITY", "108"}

_TIMELINE: List[dict] = []
_WORD_BBOX_CACHE: Dict[str, Tuple[int, int, int, int]] = {}

def init_captions(json_path: Path):
    global _TIMELINE
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            _TIMELINE = json.load(f)
    else:
        _TIMELINE = []

def get_word_bbox(word: str) -> Tuple[int, int, int, int]:
    if word not in _WORD_BBOX_CACHE:
        dummy_img = Image.new("RGBA", (1, 1))
        d = ImageDraw.Draw(dummy_img)
        _WORD_BBOX_CACHE[word] = d.textbbox((0, 0), word, font=CAPTION_FONT, stroke_width=12)
    return _WORD_BBOX_CACHE[word]

def draw_mrbeast_captions(canvas: Image.Image, t: float, center_y: int = 1710) -> Image.Image:
    """
    Renders the active MrBeast caption phrase for timestamp `t` onto `canvas`.
    """
    if not _TIMELINE:
        return canvas

    # Find active phrase for timestamp t
    active_phrase = None
    for p in _TIMELINE:
        if p["start"] <= t < p["end"]:
            active_phrase = p
            break

    if not active_phrase:
        return canvas

    words = active_phrase["words"]
    if not words:
        return canvas

    was_rgb = (canvas.mode == "RGB")
    if was_rgb:
        canvas = canvas.convert("RGBA")

    # 1. Measure words and calculate layout
    gap = 22
    word_metrics = []
    total_w = 0

    for w_obj in words:
        text = w_obj["word"].upper()
        bbox = get_word_bbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        word_metrics.append((text, w, h, bbox, w_obj["start"], w_obj["end"]))
        total_w += w

    total_w += gap * (len(words) - 1)
    start_x = (canvas.width - total_w) // 2

    # 2. Render phrase
    curr_x = start_x
    for text, w, h, bbox, t_start, t_end in word_metrics:
        is_active = (t_start <= t < t_end)
        
        # Color
        if is_active:
            fill_col = COLOR_RED if text in CLIMAX_WORDS else COLOR_YELLOW
        else:
            fill_col = COLOR_WHITE

        # Active word kinetic scale pop (1.14x bounce)
        scale = 1.0
        if is_active:
            p_pop = min(1.0, (t - t_start) / 0.12)
            # Fast bounce curve
            scale = 1.06 + 0.08 * math.sin(p_pop * math.pi)

        if scale > 1.01:
            pad = 30
            patch_w = w + pad * 2
            patch_h = h + pad * 2
            patch = Image.new("RGBA", (patch_w, patch_h), (0, 0, 0, 0))
            p_draw = ImageDraw.Draw(patch)

            # Deep shadow
            p_draw.text(
                (pad - bbox[0] + 6, pad - bbox[1] + 7),
                text,
                font=CAPTION_FONT,
                fill=COLOR_SHADOW,
                stroke_width=12,
                stroke_fill=COLOR_SHADOW
            )
            # Heavy black stroke + colored fill
            p_draw.text(
                (pad - bbox[0], pad - bbox[1]),
                text,
                font=CAPTION_FONT,
                fill=fill_col,
                stroke_width=12,
                stroke_fill=COLOR_BLACK
            )

            # Proportional scale
            sw = int(patch_w * scale)
            sh = int(patch_h * scale)
            scaled_patch = patch.resize((sw, sh), Image.Resampling.LANCZOS)

            px = curr_x - (sw - patch_w) // 2 - pad
            py = center_y - (sh - patch_h) // 2 - (h // 2) - pad
            canvas.paste(scaled_patch, (px, py), mask=scaled_patch.split()[-1])
        else:
            # Razor-sharp direct rendering
            dx = curr_x - bbox[0]
            dy = center_y - (h // 2) - bbox[1]

            d = ImageDraw.Draw(canvas)
            # Shadow
            d.text((dx + 6, dy + 7), text, font=CAPTION_FONT, fill=COLOR_SHADOW, stroke_width=12, stroke_fill=COLOR_SHADOW)
            # Stroke + Fill
            d.text((dx, dy), text, font=CAPTION_FONT, fill=fill_col, stroke_width=12, stroke_fill=COLOR_BLACK)

        curr_x += w + gap

    if was_rgb:
        return canvas.convert("RGB")
    return canvas
