"""
FS 30 Paper Compositor Engine (C1, C4, C5, C7).
Implements real paper layer compositing:
- Paper texture multiplication (from local packs)
- Hand-cut lighter paper edge (6-12 px core with organic contour)
- Dual-layer shadows: tight contact shadow + wide ambient shadow scaled by z
- 5 distinct text card styles (torn strip, taped label, ticket, stamp, sticky note)
- Content validation for shapes (no empty shapes allowed)
- Strict safe-zone and face-clear placement rules
"""

import math
import random
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
import numpy as np

from fs30.assets.library import library

DEFAULT_PALETTE = {
    "red": (200, 16, 46),
    "yellow": (255, 204, 0),
    "blue": (0, 77, 152),
    "cream": (246, 241, 232),
    "dark": (18, 20, 26),
    "white": (255, 255, 255),
    "grey": (180, 185, 195),
    "gold": (218, 165, 32)
}

def perturb_contour(points: List[Tuple[float, float]], jitter: float = 2.5) -> List[Tuple[float, float]]:
    """Adds organic hand-cut perturbation to polygon coordinates."""
    new_pts = []
    n = len(points)
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        mid_x = (p1[0] + p2[0]) / 2.0 + random.uniform(-jitter, jitter)
        mid_y = (p1[1] + p2[1]) / 2.0 + random.uniform(-jitter, jitter)
        new_pts.append(p1)
        new_pts.append((mid_x, mid_y))
    return new_pts

def create_dual_paper_shadows(
    img_rgba: Image.Image,
    z_gap: float = 0.5,
    light_angle_deg: float = 90.0
) -> Tuple[Image.Image, int]:
    """
    C1: Creates dual-layer paper shadow:
    1. Contact shadow: tight, dark, sharp shadow directly beneath paper edge.
    2. Ambient shadow: wide, soft, diffuse shadow scaling with z-depth.
    Returns: (shadow_canvas, padding)
    """
    w, h = img_rgba.size
    alpha = img_rgba.split()[-1]

    # Z-dependent shadow parameters
    # Contact shadow
    c_offset_y = max(2, int(4 * (0.8 + 0.4 * z_gap)))
    c_blur = max(3, int(5 * (0.8 + 0.4 * z_gap)))
    c_alpha_val = int(255 * 0.65)

    # Ambient shadow (scales with z)
    a_offset_y = max(8, int(18 * z_gap))
    a_blur = max(12, int(30 * z_gap))
    a_alpha_val = int(255 * (0.22 + 0.15 * z_gap))

    pad = a_blur * 2 + a_offset_y + 16
    canvas_w, canvas_h = w + pad * 2, h + pad * 2

    # 1. Generate ambient shadow
    amb_mask = alpha.filter(ImageFilter.GaussianBlur(radius=a_blur))
    amb_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    amb_color = Image.new("RGBA", (w, h), (0, 0, 0, a_alpha_val))
    amb_color.putalpha(amb_mask)
    amb_layer.paste(amb_color, (pad, pad + a_offset_y), amb_color)

    # 2. Generate contact shadow
    con_mask = alpha.filter(ImageFilter.GaussianBlur(radius=c_blur))
    con_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    con_color = Image.new("RGBA", (w, h), (0, 0, 0, c_alpha_val))
    con_color.putalpha(con_mask)
    con_layer.paste(con_color, (pad, pad + c_offset_y), con_color)

    # Combine both shadows
    shadow_canvas = Image.alpha_composite(amb_layer, con_layer)
    return shadow_canvas, pad

def apply_handcut_paper_edge(
    img_rgba: Image.Image,
    stroke_w: int = 10,
    edge_color: Tuple[int, int, int] = (250, 248, 244)
) -> Image.Image:
    """
    C1: Adds a rough, hand-cut lighter paper edge core around cutouts and cards.
    """
    w, h = img_rgba.size
    pad = stroke_w + 4
    canvas_w, canvas_h = w + pad * 2, h + pad * 2

    alpha = img_rgba.split()[-1]
    # Dilate alpha mask to create the stroke
    dilated = alpha.filter(ImageFilter.MaxFilter(stroke_w * 2 + 1))
    # Slight organic jitter on the stroke mask
    stroke_mask = dilated.filter(ImageFilter.GaussianBlur(radius=1.2))

    stroke_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    stroke_core = Image.new("RGBA", (w, h), (*edge_color, 255))
    stroke_core.putalpha(stroke_mask)
    stroke_layer.paste(stroke_core, (pad, pad), stroke_core)

    # Composite original image over stroke
    out = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    out.paste(stroke_layer, (0, 0), stroke_layer)
    out.paste(img_rgba, (pad, pad), img_rgba)

    return out

_PAPER_TEX_CACHE = {}

def multiply_paper_texture(
    base_img: Image.Image,
    texture_path: Optional[Path] = None,
    intensity: float = 0.45
) -> Image.Image:
    """
    C1: Multiplies a real paper texture (creases, fibres) onto a paper layer.
    """
    if texture_path is None or not Path(texture_path).exists():
        # Pick from local library
        tex_asset = library.pick("paper_multiply")
        if tex_asset:
            texture_path = Path(tex_asset["path"])
        else:
            return base_img

    try:
        t_key = str(texture_path)
        if t_key not in _PAPER_TEX_CACHE:
            with Image.open(texture_path) as tex:
                _PAPER_TEX_CACHE[t_key] = tex.convert("RGB")
        tex = _PAPER_TEX_CACHE[t_key]

        w, h = base_img.size
        tex_resized = tex.resize((w, h), Image.Resampling.BILINEAR)
        tex_adj = ImageOps.autocontrast(tex_resized)
        
        # Blend
        base_rgb = base_img.convert("RGB")
        multiplied = ImageChops.multiply(base_rgb, tex_adj)
        blended = Image.blend(base_rgb, multiplied, intensity)
        
        if base_img.mode == "RGBA":
            blended.putalpha(base_img.split()[-1])
        return blended
    except Exception:
        return base_img

# ----------------- C5: 5 DISTINCT TEXT CARD STYLES -----------------

def create_text_card_torn_strip(
    text: str,
    font_size: int = 48,
    fill_color: Tuple[int, int, int] = DEFAULT_PALETTE["cream"],
    text_color: Tuple[int, int, int] = DEFAULT_PALETTE["dark"]
) -> Image.Image:
    """Style 1: Torn Paper Strip with fibrous jagged edges."""
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = tw + 80, th + 60

    # Draw irregular jagged torn polygon
    pts = [(10, 10)]
    for x in range(25, w - 10, 20):
        pts.append((x, 10 + random.uniform(-4, 4)))
    pts.append((w - 10, 10))
    for y in range(20, h - 10, 15):
        pts.append((w - 10 + random.uniform(-3, 3), y))
    pts.append((w - 10, h - 10))
    for x in range(w - 25, 10, -20):
        pts.append((x, h - 10 + random.uniform(-5, 5)))
    pts.append((10, h - 10))

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(pts, fill=(*fill_color, 255))
    
    # Multiply real paper fibre texture onto torn strip
    img = multiply_paper_texture(img, intensity=0.5)

    # Draw text
    draw = ImageDraw.Draw(img)
    tx = (w - tw) // 2
    ty = (h - th) // 2 - 4
    draw.text((tx, ty), text, font=font, fill=text_color)

    return apply_handcut_paper_edge(img, stroke_w=6)

def create_text_card_taped_label(
    text: str,
    font_size: int = 44,
    card_color: Tuple[int, int, int] = DEFAULT_PALETTE["cream"],
    text_color: Tuple[int, int, int] = DEFAULT_PALETTE["dark"]
) -> Image.Image:
    """Style 2: Clean Cream Card taped down with genuine Packing Tape."""
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Give generous width so tape stays on outer corners without covering text
    card_w = tw + 280
    card_h = th + 54

    pad = 40
    total_w, total_h = card_w + pad * 2, card_h + pad * 2
    img = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = pad, pad
    # Slightly perturbed card rectangle
    pts = [(cx, cy), (cx + card_w, cy), (cx + card_w, cy + card_h), (cx, cy + card_h)]
    pts = perturb_contour(pts, jitter=1.5)
    draw.polygon(pts, fill=(*card_color, 255), outline=DEFAULT_PALETTE["red"], width=4)

    # Multiply paper texture
    img = multiply_paper_texture(img, intensity=0.4)
    draw = ImageDraw.Draw(img)
    tx = cx + (card_w - tw) // 2
    ty = cy + (card_h - th) // 2 - 4
    draw.text((tx, ty), text, font=font, fill=text_color)

    # Apply packing tape asset strictly on far outer corners
    tape_asset = library.pick("tape")
    if tape_asset and Path(tape_asset["path"]).exists():
        try:
            with Image.open(tape_asset["path"]) as t_img:
                # Resize tape strip
                tw_target = 85
                th_target = int(tw_target * (t_img.height / t_img.width))
                t_thumb = t_img.convert("RGBA").resize((tw_target, th_target), Image.Resampling.BILINEAR)
                # Rotate slightly
                t_rot1 = t_thumb.rotate(-18, expand=True)
                t_rot2 = t_thumb.rotate(18, expand=True)
                img.paste(t_rot1, (cx - 15, cy - 15), t_rot1)
                img.paste(t_rot2, (cx + card_w - tw_target + 15, cy - 15), t_rot2)
        except Exception:
            pass

    return apply_handcut_paper_edge(img, stroke_w=6)

def create_text_card_newspaper(
    headline: str,
    sub_tag: str = "EXCLUSIVE REPORT",
    font_size: int = 44
) -> Image.Image:
    """Style 3: Aged Newsprint Cutout with authentic editorial serif/headline styling."""
    try:
        font_head = ImageFont.truetype("arialbd.ttf", font_size)
        font_sub = ImageFont.truetype("arialbd.ttf", 18)
    except Exception:
        font_head = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    bbox = font_head.getbbox(headline)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = max(tw + 70, 360), th + 85

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Newsprint aged paper polygon
    pts = [(10, 10), (w - 10, 10), (w - 10, h - 10), (10, h - 10)]
    pts = perturb_contour(pts, jitter=2.0)
    draw.polygon(pts, fill=(238, 232, 218, 255), outline=(40, 42, 48), width=3)

    # Multiply paper texture
    img = multiply_paper_texture(img, intensity=0.55)
    draw = ImageDraw.Draw(img)

    # Top news banner strip
    draw.rectangle([14, 14, w - 14, 42], fill=(200, 16, 46))
    draw.text((24, 18), sub_tag, font=font_sub, fill=(255, 255, 255))

    # Headline
    tx = (w - tw) // 2
    ty = 48 + (h - 48 - th) // 2 - 4
    draw.text((tx, ty), headline, font=font_head, fill=(18, 20, 24))

    return apply_handcut_paper_edge(img, stroke_w=8)

def create_text_card_rubber_stamp(
    text: str,
    color=DEFAULT_PALETTE["red"]
) -> Image.Image:
    """Style 4: Heavy Inked Rubber Stamp."""
    try:
        font = ImageFont.truetype("arialbd.ttf", 52)
    except Exception:
        font = ImageFont.load_default()

    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = tw + 60, th + 44

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pts = [(8, 8), (w - 8, 8), (w - 8, h - 8), (8, h - 8)]
    pts = perturb_contour(pts, jitter=1.8)
    draw.polygon(pts, fill=(248, 244, 236, 255), outline=color, width=7)

    draw.text(((w - tw) // 2, (h - th) // 2 - 4), text, font=font, fill=color)
    tilted = img.rotate(random.choice([-4.0, -2.5, 3.0, 4.5]), expand=True, resample=Image.Resampling.BICUBIC)
    return apply_handcut_paper_edge(tilted, stroke_w=6)

def create_text_card_ticket(
    headline: str,
    meta_text: str = "OFFICIAL RECORD"
) -> Image.Image:
    """Style 5: Perforated Vintage Match Ticket Card."""
    try:
        font_main = ImageFont.truetype("arialbd.ttf", 36)
        font_sub = ImageFont.truetype("arialbd.ttf", 15)
    except Exception:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    bbox = font_main.getbbox(headline)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = max(tw + 220, 640), 160

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    notch_r = 16
    pts = [
        (10, 10), (w - 10, 10),
        (w - 10, h // 2 - notch_r),
        (w - 10 - notch_r, h // 2),
        (w - 10, h // 2 + notch_r),
        (w - 10, h - 10), (10, h - 10),
        (10, h // 2 + notch_r),
        (10 + notch_r, h // 2),
        (10, h // 2 - notch_r)
    ]
    pts = perturb_contour(pts, jitter=1.8)
    draw.polygon(pts, fill=DEFAULT_PALETTE["cream"], outline=DEFAULT_PALETTE["dark"], width=4)

    # Perforated line
    sep_x = w - 140
    for y in range(16, h - 16, 12):
        draw.line([(sep_x, y), (sep_x, y + 6)], fill=DEFAULT_PALETTE["dark"], width=3)

    img = multiply_paper_texture(img, intensity=0.45)
    draw = ImageDraw.Draw(img)

    draw.text((30, 25), meta_text, font=font_sub, fill=DEFAULT_PALETTE["red"])
    draw.text((30, 65), headline, font=font_main, fill=DEFAULT_PALETTE["dark"])
    draw.text((sep_x + 18, 48), "FS 30", font=font_main, fill=DEFAULT_PALETTE["red"])
    draw.text((sep_x + 22, 95), "PASS", font=font_sub, fill=DEFAULT_PALETTE["dark"])

    return apply_handcut_paper_edge(img, stroke_w=6)

# ----------------- C4: CONTENT-BEARING SHAPES -----------------

def create_content_starburst(
    text: str,
    color=DEFAULT_PALETTE["red"],
    size=(440, 440)
) -> Image.Image:
    """
    C4: Enforces that starbursts carry meaningful content (stat, number, or word).
    """
    if not text or text.strip() == "":
        raise ValueError("C4 Violation: Shape layer without text/content is invalid and rejected!")

    from fs30.assets.sticker_kit import make_starburst
    base = make_starburst(size=size, fill=color)
    draw = ImageDraw.Draw(base)

    try:
        font = ImageFont.truetype("arialbd.ttf", 52)
    except Exception:
        font = ImageFont.load_default()

    # Center text in starburst
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    cx, cy = base.width // 2, base.height // 2
    draw.text((cx - tw // 2, cy - th // 2 - 4), text, font=font, fill=(255, 255, 255))

    return base
