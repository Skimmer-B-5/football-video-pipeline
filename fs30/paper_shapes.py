"""
Procedural Paper Shapes Generator for FS 30 Pipeline.
Generates hand-cut paper elements with irregular edges and drop shadows:
- torn_strip, circle, arrow, burst, banner, scribble_underline, ticket, jersey_silhouette.
"""

import math
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

def hex_to_rgba(hex_code: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    h = hex_code.lstrip('#')
    if len(h) == 3:
        h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)

def apply_paper_grain_and_tear(img: Image.Image, roughness: int = 6) -> Image.Image:
    """Applies hand-cut rough edge perturbation to an RGBA shape."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    alpha = img.split()[-1]
    mask_np = np.array(alpha, dtype=np.uint8)
    if roughness > 0:
        noise = np.random.randint(-roughness, roughness, mask_np.shape, dtype=np.int16)
        rough = np.clip(mask_np.astype(np.int16) + (noise * (mask_np > 10).astype(np.int16)), 0, 255).astype(np.uint8)
        rough_alpha = Image.fromarray(rough).filter(ImageFilter.GaussianBlur(0.6))
        img.putalpha(rough_alpha)
    return img

def create_drop_shadow(img: Image.Image, offset: Tuple[int, int] = (0, 16), blur: int = 20, alpha_factor: float = 0.5) -> Image.Image:
    """Generates an RGBA layer with the soft offset drop shadow of the image."""
    w, h = img.size
    shadow_pad = blur * 2 + max(abs(offset[0]), abs(offset[1]))
    canvas = Image.new("RGBA", (w + shadow_pad * 2, h + shadow_pad * 2), (0, 0, 0, 0))

    alpha = img.split()[-1]
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(blur / 2.0))
    s_np = (np.array(shadow_mask, dtype=np.float32) * alpha_factor).clip(0, 255).astype(np.uint8)
    shadow_layer = Image.new("RGBA", img.size, (10, 12, 16, 255))
    shadow_layer.putalpha(Image.fromarray(s_np))

    canvas.paste(shadow_layer, (shadow_pad + offset[0], shadow_pad + offset[1]), shadow_layer)
    return canvas, shadow_pad

def draw_torn_strip(color: str, width: int = 900, height: int = 140) -> Image.Image:
    """Horizontal paper strip with torn, fibrous edges."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = hex_to_rgba(color)

    # Build jagged top and bottom edge points
    points = []
    # Top edge left to right
    for x in range(0, width, 15):
        y = np.random.randint(6, 18)
        points.append((x, y))
    points.append((width, 10))
    # Right edge
    points.append((width, height - 10))
    # Bottom edge right to left
    for x in range(width, 0, -15):
        y = height - np.random.randint(6, 18)
        points.append((x, y))
    points.append((0, height - 10))

    draw.polygon(points, fill=rgba)
    return apply_paper_grain_and_tear(img, roughness=4)

def draw_circle(color: str, diameter: int = 400) -> Image.Image:
    """Hand-cut paper circle with imperfect radius."""
    img = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = hex_to_rgba(color)

    center = diameter / 2.0
    r_base = diameter * 0.46
    points = []
    for angle_deg in range(0, 360, 6):
        rad = math.radians(angle_deg)
        r = r_base + np.random.uniform(-4, 4)
        x = center + r * math.cos(rad)
        y = center + r * math.sin(rad)
        points.append((x, y))

    draw.polygon(points, fill=rgba)
    return apply_paper_grain_and_tear(img, roughness=4)

def draw_arrow(color: str, width: int = 500, height: int = 240) -> Image.Image:
    """Hand-cut bold arrow shape."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = hex_to_rgba(color)

    hw = height / 2.0
    points = [
        (20, hw - 35),
        (width - 160, hw - 35),
        (width - 160, 20),
        (width - 20, hw),
        (width - 160, height - 20),
        (width - 160, hw + 35),
        (20, hw + 35)
    ]
    draw.polygon(points, fill=rgba)
    return apply_paper_grain_and_tear(img, roughness=4)

def draw_burst(color: str, size: int = 500) -> Image.Image:
    """Multi-point paper sticker starburst."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = hex_to_rgba(color)

    center = size / 2.0
    num_points = 14
    points = []
    for i in range(num_points * 2):
        angle = i * (math.pi / num_points)
        r = (size * 0.46) if (i % 2 == 0) else (size * 0.32)
        r += np.random.uniform(-4, 4)
        points.append((center + r * math.cos(angle), center + r * math.sin(angle)))

    draw.polygon(points, fill=rgba)
    return apply_paper_grain_and_tear(img, roughness=5)

def draw_banner(color: str, width: int = 850, height: int = 180) -> Image.Image:
    """Ribbon banner with notched paper swallow-tail ends."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = hex_to_rgba(color)

    points = [
        (40, 20),
        (width - 40, 20),
        (width - 10, height / 2.0),
        (width - 40, height - 20),
        (40, height - 20),
        (10, height / 2.0)
    ]
    draw.polygon(points, fill=rgba)
    return apply_paper_grain_and_tear(img, roughness=4)

def draw_scribble_underline(color: str, width: int = 600, height: int = 70) -> Image.Image:
    """Hand-drawn marker scribble underline."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = hex_to_rgba(color)

    for seg in range(3):
        pts = []
        for x in range(20, width - 20, 25):
            y = 35 + math.sin(x * 0.05 + seg) * 12 + np.random.uniform(-3, 3)
            pts.append((x, y))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=rgba, width=9)

    return apply_paper_grain_and_tear(img, roughness=3)

def draw_ticket(color: str, width: int = 700, height: int = 240) -> Image.Image:
    """Vintage admission ticket card with circular side notches."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgba = hex_to_rgba(color)

    draw.rounded_rectangle([20, 20, width - 20, height - 20], radius=16, fill=rgba)
    # Side notches
    notch_r = 28
    draw.ellipse([-notch_r, height/2 - notch_r, notch_r, height/2 + notch_r], fill=(0, 0, 0, 0))
    draw.ellipse([width - notch_r, height/2 - notch_r, width + notch_r, height/2 + notch_r], fill=(0, 0, 0, 0))

    return apply_paper_grain_and_tear(img, roughness=4)

def generate_shape_image(shape_type: str, color_hex: str, size_hint: Optional[Tuple[int, int]] = None) -> Image.Image:
    """Factory creating any allowed paper shape."""
    if shape_type == "torn_strip":
        return draw_torn_strip(color_hex)
    elif shape_type == "circle":
        return draw_circle(color_hex)
    elif shape_type == "arrow":
        return draw_arrow(color_hex)
    elif shape_type == "burst":
        return draw_burst(color_hex)
    elif shape_type == "banner":
        return draw_banner(color_hex)
    elif shape_type == "scribble_underline":
        return draw_scribble_underline(color_hex)
    elif shape_type == "ticket":
        return draw_ticket(color_hex)
    elif shape_type == "jersey_silhouette":
        from fs30.stage4_fetch_assets import generate_jersey_silhouette
        return generate_jersey_silhouette(color=color_hex)
    else:
        return draw_torn_strip(color_hex)

def generate_text_card(
    text: str,
    bg_color: str = "#F4EFE6",
    text_color: str = "#0A0C10",
    max_w: int = 860
) -> Image.Image:
    """Creates a paper text card with max 6 words uppercase."""
    # Split text into lines
    words = text.upper().split()
    if len(words) > 3:
        mid = (len(words) + 1) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [" ".join(words)]

    font_size = 52 if len(words) <= 4 else 44
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    # Measure lines
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    line_bboxes = [dummy.textbbox((0, 0), l, font=font) for l in lines]
    max_lw = max(b[2] - b[0] for b in line_bboxes)
    total_lh = sum(b[3] - b[1] + 12 for b in line_bboxes)

    card_w = min(max_w, max_lw + 120)
    card_h = total_lh + 70

    img = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Paper card background
    draw.rounded_rectangle([10, 10, card_w - 10, card_h - 10], radius=12, fill=hex_to_rgba(bg_color))
    # Border
    draw.rounded_rectangle([10, 10, card_w - 10, card_h - 10], radius=12, outline=hex_to_rgba(text_color, 40), width=2)

    # Draw text lines
    y_curr = 35
    for l, b in zip(lines, line_bboxes):
        lw = b[2] - b[0]
        x = (card_w - lw) // 2
        draw.text((x, y_curr), l, font=font, fill=hex_to_rgba(text_color))
        y_curr += (b[3] - b[1] + 12)

    return apply_paper_grain_and_tear(img, roughness=4)
