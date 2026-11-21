"""
FS 30 Procedural Vector & Sticker Kit (In-Code, CC0).
Generates hand-cut paper stickers with irregular edges, palette coloring,
and white paper core strokes per Requirement B7.
"""

import math
import random
import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
STICKERS_DIR = ASSETS_DIR / "stickers"
STICKERS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = ASSETS_DIR / "index.sqlite"

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

def perturb_points(points, max_jitter=3.5, num_subdivs=2):
    """Subdivides and adds slight organic jitter to simulate hand-cut paper contours."""
    pts = list(points)
    for _ in range(num_subdivs):
        new_pts = []
        n = len(pts)
        for i in range(n):
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            mid_x = (p1[0] + p2[0]) / 2.0 + random.uniform(-max_jitter, max_jitter)
            mid_y = (p1[1] + p2[1]) / 2.0 + random.uniform(-max_jitter, max_jitter)
            new_pts.append(p1)
            new_pts.append((mid_x, mid_y))
        pts = new_pts
    return pts

def apply_paper_stroke_and_shadow(img_rgba: Image.Image, stroke_w: int = 8) -> Image.Image:
    """Applies a crisp white paper edge stroke and subtle paper drop shadow."""
    w, h = img_rgba.size
    pad = stroke_w + 14
    canvas_w, canvas_h = w + pad * 2, h + pad * 2

    alpha = img_rgba.split()[-1]
    # Dilate alpha for white stroke
    dilated_alpha = alpha.filter(ImageFilter.MaxFilter(stroke_w * 2 + 1))
    
    # White paper core
    white_core = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    white_shape = Image.new("RGBA", (w, h), (250, 248, 244, 255))
    white_shape.putalpha(dilated_alpha)
    
    # Soft drop shadow
    shadow_mask = dilated_alpha.filter(ImageFilter.GaussianBlur(radius=5))
    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    s_col = Image.new("RGBA", (w, h), (0, 0, 0, 110))
    s_col.putalpha(shadow_mask)
    shadow_layer.paste(s_col, (pad + 2, pad + 4), s_col)

    # Composite
    out = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    out.paste(shadow_layer, (0, 0), shadow_layer)
    out.paste(white_shape, (pad, pad), white_shape)
    out.paste(img_rgba, (pad, pad), img_rgba)

    return out

# ----------------- INDIVIDUAL PROCEDURAL BUILDERS -----------------

def make_starburst(size=(512, 512), fill=DEFAULT_PALETTE["red"]) -> Image.Image:
    w, h = size
    cx, cy = w // 2, h // 2
    points = []
    n_points = 20
    r_outer = min(cx, cy) - 40
    r_inner = r_outer * 0.62
    for i in range(n_points * 2):
        angle = i * math.pi / n_points
        r = r_outer if i % 2 == 0 else r_inner
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        points.append((px, py))
    pts = perturb_points(points, max_jitter=2.0)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(pts, fill=fill)
    return apply_paper_stroke_and_shadow(img)

def make_burst(size=(512, 512), fill=DEFAULT_PALETTE["yellow"]) -> Image.Image:
    w, h = size
    cx, cy = w // 2, h // 2
    points = []
    n_points = 14
    for i in range(n_points * 2):
        angle = i * math.pi / n_points
        r = (min(cx, cy) - 30) * random.uniform(0.85, 1.05) if i % 2 == 0 else (min(cx, cy) * 0.45 * random.uniform(0.8, 1.1))
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        points.append((px, py))
    pts = perturb_points(points, max_jitter=3.0)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(pts, fill=fill)
    return apply_paper_stroke_and_shadow(img)

def make_arrow(size=(512, 320), direction="right", fill=DEFAULT_PALETTE["yellow"]) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if direction == "right":
        pts = [(40, 110), (280, 110), (280, 40), (460, 160), (280, 280), (280, 210), (40, 210)]
    elif direction == "left":
        pts = [(472, 110), (232, 110), (232, 40), (52, 160), (232, 280), (232, 210), (472, 210)]
    else: # curved
        pts = [(40, 220), (160, 80), (320, 80), (320, 30), (460, 140), (320, 250), (320, 180), (160, 180), (60, 270)]
    pts = perturb_points(pts, max_jitter=2.5)
    draw.polygon(pts, fill=fill)
    return apply_paper_stroke_and_shadow(img)

def make_stamp(text: str, fill=DEFAULT_PALETTE["red"], size=(560, 220)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer rectangular frame with paper perturbation
    pts = [(20, 20), (w - 20, 20), (w - 20, h - 20), (20, h - 20)]
    pts = perturb_points(pts, max_jitter=2.0)
    draw.polygon(pts, fill=(248, 244, 236, 255), outline=fill, width=8)

    try:
        font = ImageFont.truetype("arialbd.ttf", 64)
    except Exception:
        font = ImageFont.load_default()

    # Draw centered stamp text
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx, ty = (w - tw) // 2, (h - th) // 2 - 8
    draw.text((tx, ty), text, font=font, fill=fill)

    # Rotate stamp slightly for editorial analog feel
    tilted = img.rotate(random.choice([-4.5, -3.0, 3.5, 5.0]), resample=Image.Resampling.BICUBIC, expand=True)
    return apply_paper_stroke_and_shadow(tilted, stroke_w=6)

def make_ticket(size=(620, 260)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Ticket shape with perforated side notches
    notch_r = 24
    pts = [
        (20, 20), (w - 20, 20),
        (w - 20, h // 2 - notch_r),
        (w - 20 - notch_r, h // 2),
        (w - 20, h // 2 + notch_r),
        (w - 20, h - 20), (20, h - 20),
        (20, h // 2 + notch_r),
        (20 + notch_r, h // 2),
        (20, h // 2 - notch_r)
    ]
    pts = perturb_points(pts, max_jitter=2.0)
    draw.polygon(pts, fill=DEFAULT_PALETTE["cream"], outline=DEFAULT_PALETTE["dark"], width=4)

    # Perforated dashed line
    sep_x = int(w * 0.72)
    for y in range(30, h - 30, 16):
        draw.line([(sep_x, y), (sep_x, y + 8)], fill=DEFAULT_PALETTE["dark"], width=3)

    try:
        font_b = ImageFont.truetype("arialbd.ttf", 26)
        font_s = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_b = ImageFont.load_default()
        font_s = ImageFont.load_default()

    draw.text((45, 45), "MATCHDAY ADMISSION", font=font_b, fill=DEFAULT_PALETTE["red"])
    draw.text((45, 90), "GATE 04 • SECTION B • ROW 12", font=font_s, fill=DEFAULT_PALETTE["dark"])
    draw.text((45, 140), "NO. 08291485", font=font_b, fill=DEFAULT_PALETTE["dark"])
    draw.text((sep_x + 20, 70), "STUB", font=font_b, fill=DEFAULT_PALETTE["dark"])
    draw.text((sep_x + 16, 110), "KEEP", font=font_s, fill=DEFAULT_PALETTE["red"])

    return apply_paper_stroke_and_shadow(img)

def make_torn_strip(size=(720, 160), fill=DEFAULT_PALETTE["cream"]) -> Image.Image:
    w, h = size
    pts = [(20, 20)]
    # Jagged top
    for x in range(30, w - 20, 25):
        pts.append((x, 20 + random.uniform(-4, 4)))
    pts.append((w - 20, 20))
    # Jagged right
    pts.append((w - 20, h - 20))
    # Jagged bottom
    for x in range(w - 30, 20, -25):
        pts.append((x, h - 20 + random.uniform(-6, 6)))
    pts.append((20, h - 20))
    
    pts = perturb_points(pts, max_jitter=2.5)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(pts, fill=fill)
    return apply_paper_stroke_and_shadow(img)

def make_card(color_name="yellow", size=(320, 440)) -> Image.Image:
    w, h = size
    col = DEFAULT_PALETTE["yellow"] if color_name == "yellow" else DEFAULT_PALETTE["red"]
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Rounded rectangular referee card
    draw.rounded_rectangle([20, 20, w - 20, h - 20], radius=28, fill=col, outline=(245, 245, 245), width=6)
    return apply_paper_stroke_and_shadow(img)

def make_football(size=(420, 420)) -> Image.Image:
    w, h = size
    cx, cy = w // 2, h // 2
    r = min(cx, cy) - 30
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer circle
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DEFAULT_PALETTE["cream"], outline=DEFAULT_PALETTE["dark"], width=6)
    
    # Center pentagon
    pent_pts = []
    for i in range(5):
        ang = i * 2 * math.pi / 5 - math.pi / 2
        pent_pts.append((cx + r * 0.35 * math.cos(ang), cy + r * 0.35 * math.sin(ang)))
    draw.polygon(pent_pts, fill=DEFAULT_PALETTE["dark"])
    
    # Radiating spokes to outer edges
    for i in range(5):
        ang = i * 2 * math.pi / 5 - math.pi / 2
        p1 = pent_pts[i]
        p2 = (cx + r * math.cos(ang), cy + r * math.sin(ang))
        draw.line([p1, p2], fill=DEFAULT_PALETTE["dark"], width=5)

    return apply_paper_stroke_and_shadow(img)

def make_trophy(size=(420, 480)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Cup silhouette in gold
    pts = [
        (130, 70), (290, 70), (280, 220), (240, 290), (240, 360),
        (310, 410), (110, 410), (180, 360), (180, 290), (140, 220)
    ]
    draw.polygon(pts, fill=DEFAULT_PALETTE["gold"], outline=DEFAULT_PALETTE["dark"], width=5)
    # Handles
    draw.arc([70, 90, 170, 230], 90, 270, fill=DEFAULT_PALETTE["gold"], width=16)
    draw.arc([250, 90, 350, 230], 270, 90, fill=DEFAULT_PALETTE["gold"], width=16)
    return apply_paper_stroke_and_shadow(img)

def make_crown(size=(460, 320)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pts = [
        (50, 250), (410, 250), (410, 110), (320, 180),
        (230, 60), (140, 180), (50, 110)
    ]
    pts = perturb_points(pts, max_jitter=2.5)
    draw.polygon(pts, fill=DEFAULT_PALETTE["gold"], outline=DEFAULT_PALETTE["dark"], width=5)
    return apply_paper_stroke_and_shadow(img)

def make_whistle(size=(440, 320)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Whistle chamber and mouthpiece
    draw.ellipse([80, 110, 260, 260], fill=DEFAULT_PALETTE["grey"], outline=DEFAULT_PALETTE["dark"], width=5)
    draw.polygon([(210, 110), (380, 110), (380, 180), (240, 180)], fill=DEFAULT_PALETTE["grey"], outline=DEFAULT_PALETTE["dark"])
    draw.line([(380, 110), (380, 180)], fill=DEFAULT_PALETTE["dark"], width=5)
    draw.ellipse([110, 70, 160, 120], fill=DEFAULT_PALETTE["cream"], outline=DEFAULT_PALETTE["dark"], width=4)
    return apply_paper_stroke_and_shadow(img)

def make_paperclip(size=(280, 480)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Paperclip wire loops
    draw.arc([70, 50, 210, 190], 180, 360, fill=(70, 75, 85), width=18)
    draw.line([(70, 120), (70, 370)], fill=(70, 75, 85), width=18)
    draw.arc([70, 300, 210, 440], 0, 180, fill=(70, 75, 85), width=18)
    draw.line([(210, 120), (210, 370)], fill=(70, 75, 85), width=18)
    draw.line([(110, 150), (110, 340)], fill=(70, 75, 85), width=18)
    draw.arc([110, 100, 170, 200], 180, 360, fill=(70, 75, 85), width=18)
    return apply_paper_stroke_and_shadow(img, stroke_w=6)

def make_push_pin(size=(320, 380)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Needle
    draw.polygon([(155, 230), (165, 230), (160, 360)], fill=(120, 125, 135))
    # Pin head in red
    draw.ellipse([100, 60, 220, 130], fill=DEFAULT_PALETTE["red"], outline=DEFAULT_PALETTE["dark"], width=4)
    draw.polygon([(120, 110), (200, 110), (180, 230), (140, 230)], fill=DEFAULT_PALETTE["red"], outline=DEFAULT_PALETTE["dark"], width=4)
    draw.ellipse([120, 210, 200, 245], fill=DEFAULT_PALETTE["red"], outline=DEFAULT_PALETTE["dark"], width=4)
    return apply_paper_stroke_and_shadow(img)

def make_scoreboard(size=(640, 320)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([20, 20, w - 20, h - 20], radius=16, fill=DEFAULT_PALETTE["dark"], outline=DEFAULT_PALETTE["cream"], width=6)
    
    try:
        font_big = ImageFont.truetype("arialbd.ttf", 92)
        font_team = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        font_big = ImageFont.load_default()
        font_team = ImageFont.load_default()
        
    draw.text((60, 45), "HOME", font=font_team, fill=DEFAULT_PALETTE["yellow"])
    draw.text((w - 180, 45), "AWAY", font=font_team, fill=DEFAULT_PALETTE["yellow"])
    draw.text((100, 120), "3", font=font_big, fill=DEFAULT_PALETTE["cream"])
    draw.text((w // 2 - 16, 120), "-", font=font_big, fill=DEFAULT_PALETTE["red"])
    draw.text((w - 150, 120), "1", font=font_big, fill=DEFAULT_PALETTE["cream"])

    return apply_paper_stroke_and_shadow(img)

# ----------------- MASTER GENERATOR & INDEXER -----------------

BUILDERS = [
    ("starburst_red", "starburst", lambda: make_starburst(fill=DEFAULT_PALETTE["red"]), ["starburst", "badge", "burst", "red"]),
    ("starburst_yellow", "starburst", lambda: make_starburst(fill=DEFAULT_PALETTE["yellow"]), ["starburst", "badge", "burst", "yellow"]),
    ("burst_dynamic", "burst", lambda: make_burst(fill=DEFAULT_PALETTE["yellow"]), ["burst", "pop", "action", "yellow"]),
    ("burst_red", "burst", lambda: make_burst(fill=DEFAULT_PALETTE["red"]), ["burst", "pop", "danger", "red"]),
    ("arrow_right", "arrow", lambda: make_arrow(direction="right", fill=DEFAULT_PALETTE["yellow"]), ["arrow", "pointer", "right", "yellow"]),
    ("arrow_left", "arrow", lambda: make_arrow(direction="left", fill=DEFAULT_PALETTE["yellow"]), ["arrow", "pointer", "left", "yellow"]),
    ("arrow_curved", "arrow", lambda: make_arrow(direction="curved", fill=DEFAULT_PALETTE["red"]), ["arrow", "curve", "direction", "red"]),
    ("stamp_rumour", "stamp", lambda: make_stamp("RUMOUR", fill=DEFAULT_PALETTE["red"]), ["stamp", "rumour", "transfer", "red"]),
    ("stamp_confirmed", "stamp", lambda: make_stamp("CONFIRMED", fill=(34, 139, 34)), ["stamp", "confirmed", "official", "green"]),
    ("stamp_official", "stamp", lambda: make_stamp("OFFICIAL", fill=DEFAULT_PALETTE["blue"]), ["stamp", "official", "announcement", "blue"]),
    ("stamp_breaking", "stamp", lambda: make_stamp("BREAKING", fill=DEFAULT_PALETTE["red"]), ["stamp", "breaking", "news", "urgent"]),
    ("match_ticket", "ticket", make_ticket, ["ticket", "admission", "matchday", "retro"]),
    ("torn_strip_cream", "torn_strip", lambda: make_torn_strip(fill=DEFAULT_PALETTE["cream"]), ["torn", "strip", "paper", "cream", "banner"]),
    ("torn_strip_red", "torn_strip", lambda: make_torn_strip(fill=DEFAULT_PALETTE["red"]), ["torn", "strip", "red", "banner"]),
    ("yellow_card", "card", lambda: make_card("yellow"), ["card", "yellow_card", "referee", "foul"]),
    ("red_card", "card", lambda: make_card("red"), ["card", "red_card", "referee", "sent_off"]),
    ("football_ball", "ball", make_football, ["ball", "football", "soccer", "match"]),
    ("trophy_cup", "trophy", make_trophy, ["trophy", "cup", "champion", "silverware"]),
    ("champions_crown", "crown", make_crown, ["crown", "king", "champion", "gold"]),
    ("referee_whistle", "whistle", make_whistle, ["whistle", "referee", "match", "kickoff"]),
    ("office_paperclip", "paperclip", make_paperclip, ["paperclip", "office", "dossier", "stationery"]),
    ("push_pin_red", "push_pin", make_push_pin, ["push_pin", "pin", "tack", "board", "red"]),
    ("stadium_scoreboard", "scoreboard", make_scoreboard, ["scoreboard", "result", "score", "match", "retro"])
]

def generate_all_stickers(log_func=print) -> List[Dict[str, Any]]:
    """Builds and indexes all procedural vector kit items into SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    generated_items = []
    log_func(f"[StickerKit] Generating {len(BUILDERS)} procedural hand-cut vector items...")

    for item_id, item_type, builder_fn, tags in BUILDERS:
        img = builder_fn()
        out_path = STICKERS_DIR / f"{item_id}.png"
        img.save(out_path, "PNG")

        w, h = img.size
        sz = out_path.stat().st_size
        ar = round(w / float(h), 3)

        # Alpha analysis
        a_arr = np.array(img.split()[-1])
        alpha_cov = round(float(np.count_nonzero(a_arr > 10)) / float(a_arr.size), 3)

        rec = {
            "id": f"sticker_{item_id}",
            "path": str(out_path.resolve()),
            "name": out_path.name,
            "pack": "Procedural Vector Kit",
            "type": "sticker",
            "tags": json.dumps(tags),
            "dominant_colours": "#f0ede6",
            "has_alpha": 1,
            "alpha_coverage": alpha_cov,
            "width": w,
            "height": h,
            "aspect_ratio": ar,
            "file_size_bytes": sz,
            "source_url": "code://fs30/assets/sticker_kit.py",
            "author": "FS 30 Vector Engine",
            "license": "Procedural Vector Kit (CC0)",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "date_added": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "attribution_required": 0
        }

        cursor.execute("""
            INSERT OR REPLACE INTO assets (
                id, path, pack, type, tags, dominant_colours, has_alpha,
                alpha_coverage, width, height, aspect_ratio, file_size_bytes,
                source_url, author, license, license_url, date_added, attribution_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec["id"], rec["path"], rec["pack"], rec["type"],
            rec["tags"], rec["dominant_colours"], rec["has_alpha"],
            rec["alpha_coverage"], rec["width"], rec["height"],
            rec["aspect_ratio"], rec["file_size_bytes"], rec["source_url"],
            rec["author"], rec["license"], rec["license_url"],
            rec["date_added"], rec["attribution_required"]
        ))
        generated_items.append(rec)

    conn.commit()
    conn.close()
    log_func(f"[StickerKit] ✓ All {len(generated_items)} stickers rendered to {STICKERS_DIR.name} and indexed.")
    return generated_items

if __name__ == "__main__":
    generate_all_stickers()
