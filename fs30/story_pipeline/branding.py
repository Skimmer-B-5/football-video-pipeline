"""
FS30 TV Branding Engine (Experimental Component).
Provides:
1. Persistent top-left broadcast bug: [OFFICIAL FS30 BADGE] [TV] (Enlarged to 150px, commanding broadcast presence).
2. Dedicated broadcast outro end card with authentic torn paper headline and official FS30 branding.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

MODULE_DIR = Path(__file__).resolve().parent
BADGES_DIR = MODULE_DIR / "assets" / "badges"
FONTS_DIR = MODULE_DIR / "assets" / "fonts"
PAPER_DIR = MODULE_DIR / "assets" / "paper_widgets"

def get_brand_font(size: int = 36, role: str = "headline") -> ImageFont.ImageFont:
    font_map = {
        "headline": FONTS_DIR / "BarlowCondensed-ExtraBold.ttf",
        "sub": FONTS_DIR / "BarlowCondensed-Bold.ttf",
        "serif": FONTS_DIR / "SourceSerif4-Bold.ttf",
        "meta": FONTS_DIR / "IBMPlexSans.ttf"
    }
    p = font_map.get(role, font_map["headline"])
    try:
        return ImageFont.truetype(str(p), size)
    except Exception:
        return ImageFont.load_default()

_BADGE_CACHE = {}

def get_official_badge() -> Image.Image:
    if "badge" not in _BADGE_CACHE:
        p = BADGES_DIR / "fs30_official_badge.png"
        with Image.open(p) as im:
            _BADGE_CACHE["badge"] = im.convert("RGBA")
    return _BADGE_CACHE["badge"]

def create_fs30_tv_watermark(badge_size: int = 150) -> Image.Image:
    """
    Creates the persistent broadcast watermark:
    [OFFICIAL FS30 BADGE] [TV]
    - Substantially enlarged: badge_size 150px, TV font size 78pt.
    - Thick bold athletic 'TV' lettering in deep vibrant red (#D90429).
    - Retro offset shadow for high legibility against any background.
    - Pure transparent red lettering with drop shadow.
    """
    badge_raw = get_official_badge()
    badge = badge_raw.resize((badge_size, badge_size), Image.Resampling.LANCZOS)

    f_tv = get_brand_font(78, role="headline")
    bbox = f_tv.getbbox("TV")
    tv_w = bbox[2] - bbox[0]
    tv_h = bbox[3] - bbox[1]

    total_w = badge_size + 20 + tv_w + 30
    total_h = max(badge_size, tv_h + 20) + 16

    watermark = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))

    # Badge drop shadow
    b_alpha = badge.split()[-1]
    b_sh_mask = b_alpha.filter(ImageFilter.GaussianBlur(8))
    sh_layer = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 180))
    watermark.paste(sh_layer, (4, 8), mask=b_sh_mask)
    # Paste badge
    watermark.paste(badge, (0, 0), mask=b_alpha)

    # TV text position
    tv_x = badge_size + 18
    tv_y = (badge_size - tv_h) // 2 - 4

    # Draw offset shadow for TV
    w_draw = ImageDraw.Draw(watermark)
    w_draw.text((tv_x + 3, tv_y + 4), "TV", fill=(10, 12, 16, 240), font=f_tv) # Drop Shadow
    w_draw.text((tv_x, tv_y), "TV", fill=(217, 4, 41, 255), font=f_tv)  # Vibrant Crimson Red

    return watermark

def render_fs30_outro(t: float, f_idx: int) -> Image.Image:
    """
    Dedicated ~2.0s broadcast outro card:
    [OFFICIAL FS30 LOGO (580px)]
    [AUTHENTIC TORN PAPER BANNER: THIS IS FOOTBALL IN 30s.]
    NEW STORIES EVERY WEEK.
    FOLLOW FOR MORE.
    """
    canvas = Image.new("RGBA", (1080, 1920), (14, 16, 22, 255))

    # Radial ambient spotlight glow behind badge
    center_glow = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(center_glow)
    g_draw.ellipse([(120, 420), (960, 1320)], fill=(34, 42, 58, 160))
    center_glow = center_glow.filter(ImageFilter.GaussianBlur(130))
    canvas.paste(center_glow, (0, 0), center_glow)

    # 1. Official FS 30 Badge with deliberate slam entrance (1.30x -> 1.0x)
    p_slam = min(1.0, t / 0.35)
    scale = 1.0 + (1.0 - p_slam) * 0.30
    bw = int(580 * scale)
    bh = int(580 * scale)

    badge_raw = get_official_badge()
    badge_scaled = badge_raw.resize((bw, bh), Image.Resampling.LANCZOS)

    # Deep drop shadow
    b_alpha = badge_scaled.split()[-1]
    sh_mask = b_alpha.filter(ImageFilter.GaussianBlur(22))
    sh_np = np.array(sh_mask, dtype=np.float32) * (180 / 255.0)
    sh_mask = Image.fromarray(sh_np.astype(np.uint8))

    bx = (1080 - bw) // 2
    by = 480 - int((1.0 - p_slam) * 45)

    canvas.paste(Image.new("RGBA", (bw, bh), (0, 0, 0, 255)), (bx, by + 22), mask=sh_mask)
    canvas.paste(badge_scaled, (bx, by), mask=b_alpha)

    # 2. Authentic Torn Paper Headline Banner: "THIS IS FOOTBALL IN 30s."
    banner_raw_p = PAPER_DIR / "real_torn_paper_banner.png"
    if banner_raw_p.exists():
        with Image.open(banner_raw_p) as b_im:
            pw, ph = 960, 160
            banner_scaled = b_im.resize((pw, ph), Image.Resampling.LANCZOS).convert("RGBA")
            b_draw = ImageDraw.Draw(banner_scaled)
            b_draw.rectangle([(28, 22), (36, ph - 22)], fill=(217, 4, 41, 255))
            f_h1 = get_brand_font(64, role="headline")
            b_draw.text((pw // 2, ph // 2), "THIS IS FOOTBALL IN 30s.", fill=(18, 20, 26, 255), font=f_h1, anchor="mm")

            b_sh_mask = banner_scaled.split()[-1].filter(ImageFilter.GaussianBlur(14))
            total_bw, total_bh = pw + 30, ph + 30
            b_res = Image.new("RGBA", (total_bw, total_bh), (0, 0, 0, 0))
            b_res.paste(Image.new("RGBA", (pw, ph), (0, 0, 0, 180)), (15, 20), mask=b_sh_mask)
            b_res.paste(banner_scaled, (15, 15), mask=banner_scaled.split()[-1])

            cx = (1080 - total_bw) // 2
            cy = by + bh + 75
            canvas.paste(b_res, (cx, cy), b_res)
    else:
        # Fallback
        cy = by + bh + 75

    draw = ImageDraw.Draw(canvas)

    # 3. Sub-tagline: "NEW STORIES EVERY WEEK." (Barlow Condensed Bold, 46pt in Mustard Gold)
    f_h2 = get_brand_font(46, role="sub")
    draw.text((540, cy + 195), "NEW STORIES EVERY WEEK.", fill=(229, 184, 36, 255), font=f_h2, anchor="mm")

    # Vibrant red accent underline
    draw.rectangle([(320, cy + 228), (760, cy + 233)], fill=(217, 4, 41, 255))

    # 4. CTA: "FOLLOW FOR MORE." (IBM Plex Sans Bold, 34pt in Warm Ivory)
    f_h3 = get_brand_font(34, role="meta")
    draw.text((540, cy + 275), "FOLLOW FOR MORE", fill=(240, 242, 245, 230), font=f_h3, anchor="mm")

    return canvas.convert("RGB")
