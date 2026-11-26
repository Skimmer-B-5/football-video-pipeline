"""
# PROVENANCE: Copied from stages/vox_visual_engine.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ - Safe experimental development environment.
"""

"""
Stage: Vox Visual Engine & Kinetic Editorial Motion Graphics
Implements signature Vox Media / Magnates Media documentary visual language:
1. 2.5D Parallax Subject Cutouts with White Paper Sticker Strokes & Soft Shadows
2. Authentic Editorial Newspaper / Magazine Clippings with Neon Highlighter Wipes
3. Kinetic Stat Cards & Financial Callout Badges
4. Multiplane FFmpeg Parallax Compositor (Background drift vs. Foreground float)
"""

import sys
import os
import math
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Cached rembg session using lightweight u2netp (4.5MB)
_REMBG_SESSION = None

def get_rembg_session():
    """Lazily load lightweight u2netp session once."""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        try:
            import rembg
            _REMBG_SESSION = rembg.new_session("u2netp")
            print("[VoxEngine] rembg u2netp session initialized.")
        except Exception as e:
            print(f"[VoxEngine] rembg initialization notice: {e}")
            _REMBG_SESSION = False
    return _REMBG_SESSION if _REMBG_SESSION is not False else None


def get_system_font(size: int = 32, bold: bool = False) -> ImageFont.ImageFont:
    """Find a clean, bold system font for editorial text."""
    font_candidates = [
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\seguisb.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf"
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_subject_cutout(
    input_image_path: Path,
    output_png_path: Path,
    stroke_width: int = 6,
    stroke_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    shadow_offset: Tuple[int, int] = (0, 16),
    shadow_blur: int = 18,
    shadow_alpha: int = 100
) -> Path:
    """
    Remove background from input image, apply signature Vox white paper sticker stroke,
    and cast a smooth directional drop shadow.
    """
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    input_img = Image.open(input_image_path).convert("RGBA")
    
    session = get_rembg_session()
    if session:
        import rembg
        cutout = rembg.remove(input_img, session=session)
    else:
        # Fallback: simple center crop if rembg unavailable
        cutout = input_img

    alpha = cutout.split()[-1]
    w, h = cutout.size

    # 1. White Paper Sticker Outline (Dilate alpha mask)
    stroke_mask = alpha.filter(ImageFilter.MaxFilter(stroke_width * 2 + 1))
    stroke_layer = Image.new("RGBA", (w, h), stroke_color)
    stroke_layer.putalpha(stroke_mask)

    # 2. Soft Drop Shadow (Further dilate + Gaussian blur)
    s_filter_size = shadow_blur if (shadow_blur % 2 == 1) else (shadow_blur + 1)
    shadow_mask = stroke_mask.filter(ImageFilter.MaxFilter(s_filter_size))
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(shadow_blur / 2.0))
    
    # Scale shadow alpha
    shadow_np = np.array(shadow_mask, dtype=np.float32) * (shadow_alpha / 255.0)
    shadow_mask = Image.fromarray(shadow_np.astype(np.uint8))

    # Canvas with padding for shadow offset
    pad_x = abs(shadow_offset[0]) + shadow_blur
    pad_y = abs(shadow_offset[1]) + shadow_blur
    total_w = w + pad_x * 2
    total_h = h + pad_y * 2

    canvas = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    
    # Paste shadow offset
    canvas.paste(
        Image.new("RGBA", (w, h), (10, 15, 25, 255)),
        (pad_x + shadow_offset[0], pad_y + shadow_offset[1]),
        mask=shadow_mask
    )
    # Paste stroke outline
    canvas.paste(stroke_layer, (pad_x, pad_y), mask=stroke_mask)
    # Paste subject
    canvas.paste(cutout, (pad_x, pad_y), mask=alpha)

    # Trim empty transparency margins
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)

    canvas.save(output_png_path, "PNG")
    print(f"[VoxEngine] Created subject cutout sticker: {output_png_path.name} ({canvas.size[0]}x{canvas.size[1]})")
    return output_png_path


def create_newspaper_clipping_card(
    headline: str,
    source_name: str,
    highlight_phrase: str,
    output_png_path: Path,
    date_str: str = "BREAKING INVESTIGATION",
    width: int = 960,
    height: int = 560
) -> Path:
    """
    Renders an authentic Vox editorial newspaper clipping card:
    - Parchment paper background with fine border
    - Source publication masthead with rule lines
    - Bold headline with animated / highlighted phrase
    - 3D drop shadow
    """
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)

    # Outer paper rectangle (with rounded corners)
    paper_box = [16, 16, width - 16, height - 16]
    # Parchment color
    paper_bg = (248, 246, 240, 255)
    border_color = (220, 216, 204, 255)
    draw.rounded_rectangle(paper_box, radius=12, fill=paper_bg, outline=border_color, width=2)

    # Source Masthead
    font_masthead = get_system_font(22, bold=True)
    font_date = get_system_font(16, bold=False)
    masthead_text = f"{source_name.upper()} • {date_str.upper()}"
    draw.text((45, 40), masthead_text, fill=(180, 20, 30, 255), font=font_masthead)

    # Horizontal dividing rule
    draw.line([(45, 78), (width - 45, 78)], fill=(190, 185, 175, 255), width=2)

    # Headline text wrapping
    font_headline = get_system_font(38, bold=True)
    words = headline.split()
    lines = []
    curr_line = []
    
    for w in words:
        curr_line.append(w)
        bbox = font_headline.getbbox(" ".join(curr_line))
        if bbox[2] - bbox[0] > (width - 100):
            curr_line.pop()
            lines.append(" ".join(curr_line))
            curr_line = [w]
    if curr_line:
        lines.append(" ".join(curr_line))

    # Render headline lines and find bounding box of highlight_phrase
    y_text = 105
    line_height = 54
    highlight_boxes = []

    for line in lines[:5]:
        line_bbox = font_headline.getbbox(line)
        draw.text((45, y_text), line, fill=(20, 24, 30, 255), font=font_headline)

        # Check if highlight phrase is in this line
        if highlight_phrase and highlight_phrase.lower() in line.lower():
            start_idx = line.lower().find(highlight_phrase.lower())
            pre_text = line[:start_idx]
            match_text = line[start_idx:start_idx + len(highlight_phrase)]
            
            pre_w = font_headline.getbbox(pre_text)[2] if pre_text else 0
            match_w = font_headline.getbbox(match_text)[2] - font_headline.getbbox(match_text)[0]
            
            hl_x1 = 45 + pre_w - 4
            hl_y1 = y_text + 4
            hl_x2 = hl_x1 + match_w + 8
            hl_y2 = y_text + line_height - 6
            highlight_boxes.append((hl_x1, hl_y1, hl_x2, hl_y2))

        y_text += line_height

    # Draw Vox Yellow Highlighter Stroke (with semi-transparency)
    if highlight_boxes:
        hl_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        hl_draw = ImageDraw.Draw(hl_layer)
        for h_box in highlight_boxes:
            # Vibrant neon yellow marker
            hl_draw.rounded_rectangle(h_box, radius=4, fill=(255, 235, 30, 160))
        # Re-composite headline on top of highlighter for clean readability
        card = Image.alpha_composite(card, hl_layer)
        # Re-draw text cleanly
        draw = ImageDraw.Draw(card)
        y_text = 105
        for line in lines[:5]:
            draw.text((45, y_text), line, fill=(15, 20, 25, 255), font=font_headline)
            y_text += line_height

    # Stamp / Verified Seal
    font_seal = get_system_font(18, bold=True)
    draw.rounded_rectangle([width - 240, height - 70, width - 45, height - 32], radius=6, fill=(240, 236, 226, 255), outline=(180, 175, 160, 255), width=1)
    draw.text((width - 225, height - 64), "OFFICIAL REPORT", fill=(90, 85, 80, 255), font=font_seal)

    # Cast 3D Drop Shadow on the entire card
    shadow_card = Image.new("RGBA", (width + 60, height + 60), (0, 0, 0, 0))
    card_alpha = card.split()[-1]
    shadow_mask = card_alpha.filter(ImageFilter.GaussianBlur(14))
    shadow_np = np.array(shadow_mask, dtype=np.float32) * (110 / 255.0)
    shadow_mask = Image.fromarray(shadow_np.astype(np.uint8))
    
    shadow_card.paste(Image.new("RGBA", (width, height), (15, 20, 30, 255)), (30, 42), mask=shadow_mask)
    shadow_card.paste(card, (30, 30), mask=card_alpha)

    shadow_card.save(output_png_path, "PNG")
    print(f"[VoxEngine] Created newspaper clipping card: {output_png_path.name}")
    return output_png_path


def create_stat_callout_badge(
    stat_value: str,
    stat_label: str,
    output_png_path: Path,
    accent_color: Tuple[int, int, int] = (235, 45, 55),
    width: int = 680,
    height: int = 240
) -> Path:
    """
    Renders a bold, high-contrast kinetic stat badge:
    E.g. [- €90M DEBT -] or [ 8-YEAR CONTRACT ]
    """
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    badge = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)

    box = [16, 16, width - 16, height - 16]
    # Dark slate card
    draw.rounded_rectangle(box, radius=16, fill=(18, 22, 28, 245), outline=accent_color, width=3)

    # Left accent indicator bar
    draw.rounded_rectangle([22, 28, 32, height - 28], radius=3, fill=accent_color)

    font_val = get_system_font(58, bold=True)
    font_lbl = get_system_font(24, bold=True)

    draw.text((50, 42), stat_value.upper(), fill=(255, 255, 255, 255), font=font_val)
    draw.text((52, 136), stat_label.upper(), fill=(accent_color[0], accent_color[1], accent_color[2], 255), font=font_lbl)

    # Drop shadow
    shadow_badge = Image.new("RGBA", (width + 40, height + 40), (0, 0, 0, 0))
    b_alpha = badge.split()[-1]
    s_mask = b_alpha.filter(ImageFilter.GaussianBlur(12))
    s_np = np.array(s_mask, dtype=np.float32) * (120 / 255.0)
    s_mask = Image.fromarray(s_np.astype(np.uint8))

    shadow_badge.paste(Image.new("RGBA", (width, height), (10, 15, 20, 255)), (20, 30), mask=s_mask)
    shadow_badge.paste(badge, (20, 20), mask=b_alpha)

    shadow_badge.save(output_png_path, "PNG")
    print(f"[VoxEngine] Created stat callout badge: {output_png_path.name} ('{stat_value}')")
    return output_png_path


def render_vox_parallax_slide(
    bg_image_path: Path,
    cutout_png_path: Path,
    output_mp4_path: Path,
    duration_sec: float,
    fps: int = 30
) -> Path:
    """
    Renders 2.5D multiplane parallax animation using FFmpeg:
    - Background: Blurred, darkened, with slow inward Ken Burns zoom (1.0 -> 1.05)
    - Foreground Cutout: Floats upward slightly and scales at different rate (1.0 -> 1.08)
    """
    output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
    dur_frames = int(duration_sec * fps)

    filter_complex = (
        f"[0:v]scale=1200:2133:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"boxblur=luma_radius=6:luma_power=2,colorchannelmixer=aa=0.85,"
        f"zoompan=z='min(zoom+0.0006,1.05)':d={dur_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}[bg];"
        f"[1:v]scale=980:-1[fg];"
        f"[bg][fg]overlay=x='(W-w)/2':y='H-h-(t*10)':shortest=1[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(bg_image_path),
        "-loop", "1", "-t", f"{duration_sec:.2f}", "-i", str(cutout_png_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-t", f"{duration_sec:.2f}",
        str(output_mp4_path)
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[VoxEngine] Rendered 2.5D Parallax Slide: {output_mp4_path.name} ({duration_sec:.2f}s)")
    return output_mp4_path


def render_vox_clipping_slide(
    bg_image_path: Path,
    clipping_png_path: Path,
    output_mp4_path: Path,
    duration_sec: float,
    fps: int = 30
) -> Path:
    """
    Renders newspaper clipping slide with camera push-in and tilt:
    - Background: Heavily blurred editorial photo
    - Clipping Card: Zooms forward smoothly as narrator speaks
    """
    output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
    dur_frames = int(duration_sec * fps)

    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"boxblur=luma_radius=12:luma_power=2,colorchannelmixer=aa=0.75,"
        f"zoompan=z='min(zoom+0.0005,1.04)':d={dur_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps}[bg];"
        f"[1:v]scale=1000:-1[card];"
        f"[bg][card]overlay=x='(W-w)/2':y='(H-h)/2':shortest=1[outv]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(bg_image_path),
        "-loop", "1", "-t", f"{duration_sec:.2f}", "-i", str(clipping_png_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-t", f"{duration_sec:.2f}",
        str(output_mp4_path)
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[VoxEngine] Rendered Newspaper Clipping Slide: {output_mp4_path.name} ({duration_sec:.2f}s)")
    return output_mp4_path
