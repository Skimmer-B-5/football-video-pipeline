"""
beta/stages/generate_v7_1_6_4_visual_assets.py
Generates the revised visual assets for Beta V7.1.6.4:
1. S02: Repaired 9:16 crop from source image cand_S02_e3c35c4a37.jpg preserving entire face, ears, hairline, and kit.
2. S03: Simplified, restrained transfer graphic overlay on dominant football photography (no missing glyphs, no visual clutter).
3. S04: Clean 9:16 crop from cand_S04_11fe2a9773.jpg, accurately documented as an archival training session file photo.
"""

import sys
import hashlib
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.typography import load_font

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def repair_s02_portrait(cand_path: Path, out_path: Path):
    img = cv2.imread(str(cand_path))
    h, w = img.shape[:2]
    target_w = int(h * 9 / 16) # 427
    
    # Endrick face center in source is x=411, y=187
    x1 = max(0, 411 - target_w // 2)
    x2 = x1 + target_w
    if x2 > w:
        x2 = w
        x1 = w - target_w

    cropped = img[:, x1:x2]
    # Resize to exact 1080x1920
    crop_1080 = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(out_path), crop_1080)
    print(f"Repaired S02 portrait: {out_path.name} ({out_path.stat().st_size} bytes)")

def create_simplified_s03(base_photo_path: Path, out_path: Path):
    w, h = 1080, 1920
    photo = Image.open(base_photo_path).convert("RGBA")
    pw, ph = photo.size
    target_ratio = w / h
    current_ratio = pw / ph
    if current_ratio > target_ratio:
        new_w = int(ph * target_ratio)
        left = (pw - new_w) // 2
        photo = photo.crop((left, 0, left + new_w, ph))
    else:
        new_h = int(pw / target_ratio)
        top = (ph - new_h) // 2
        photo = photo.crop((0, top, pw, top + new_h))
    photo = photo.resize((w, h), Image.Resampling.LANCZOS)

    # Scrim overlay (subtle so photography dominates)
    scrim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    scrim_draw = ImageDraw.Draw(scrim)
    for y in range(h):
        if 420 <= y <= 1180:
            alpha = int(140 + 40 * (1.0 - abs(y - 800) / 380))
            scrim_draw.line([(0, y), (w, y)], fill=(8, 14, 28, alpha))
        elif y > 1180:
            scrim_draw.line([(0, y), (w, y)], fill=(8, 14, 28, 150))

    canvas = Image.alpha_composite(photo, scrim)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    font_kicker = load_font("IBM Plex Mono", 600, 24)
    font_title = load_font("Barlow Condensed", 800, 60)
    font_label = load_font("IBM Plex Mono", 600, 24)
    font_hero = load_font("Barlow Condensed", 800, 108)
    font_hero_sub = load_font("Inter", 600, 26)
    font_divider_label = load_font("Barlow Condensed", 700, 26)
    font_secondary = load_font("Barlow Condensed", 800, 76)
    font_badge = load_font("IBM Plex Mono", 700, 28)
    font_badge_sub = load_font("Inter", 600, 22)

    # Kicker
    draw.text((70, 460), "● PROPOSED TERMS", font=font_kicker, fill=(56, 189, 248))
    # Headline
    draw.text((70, 500), "ENDRICK TRANSFER PROPOSAL", font=font_title, fill=(255, 255, 255))
    draw.line([(70, 575), (w - 70, 575)], fill=(56, 189, 248, 180), width=2)

    # Section 1: €60M fixed + €10M bonuses
    draw.text((70, 600), "AC MILAN • REPORTED BASE PROPOSAL", font=font_label, fill=(186, 230, 253))
    draw.text((70, 635), "€60M FIXED", font=font_hero, fill=(255, 255, 255))
    draw.text((70, 760), "+ €10M IN POTENTIAL BONUSES (UNCONFIRMED)", font=font_hero_sub, fill=(56, 189, 248))

    # Divider (clean text, NO unsupported Unicode arrows/glyphs)
    draw.line([(70, 815), (w - 70, 815)], fill=(70, 90, 130, 140), width=1)
    draw.text((70, 830), "SEPARATE REPORTED REPURCHASE CLAUSE", font=font_divider_label, fill=(203, 213, 225))
    draw.line([(70, 875), (w - 70, 875)], fill=(70, 90, 130, 140), width=1)

    # Section 2: €80M - €85M Buy-back range
    draw.text((70, 895), "REAL MADRID • REPORTED BUY-BACK RANGE", font=font_label, fill=(253, 224, 71))
    draw.text((70, 930), "€80M – €85M", font=font_secondary, fill=(250, 204, 21))
    draw.text((70, 1025), "CORRIERE DELLO SPORT (€80M) • TNT SPORTS BRAZIL (€85M)", font=font_hero_sub, fill=(254, 240, 138))

    # Clear status badge: NOT AGREED
    badge_y = 1090
    draw.rounded_rectangle([(70, badge_y), (360, badge_y + 55)], radius=8, fill=(220, 38, 38), outline=(254, 202, 202), width=1)
    draw.text((88, badge_y + 11), "NOT AGREED", font=font_badge, fill=(255, 255, 255))
    draw.text((380, badge_y + 16), "NO FORMAL CLAUSE ACCEPTED BY CLUBS", font=font_badge_sub, fill=(226, 232, 240))

    final_img = canvas.convert("RGB")
    final_img.save(str(out_path), "PNG", quality=95)
    print(f"Generated simplified S03 graphic: {out_path.name} ({out_path.stat().st_size} bytes)")

def repair_s04_training_crop(cand_path: Path, out_path: Path):
    img = cv2.imread(str(cand_path))
    h, w = img.shape[:2]
    target_w = int(h * 9 / 16) # 488
    
    # Endrick center in S04 candidate is x=959, y=205
    x1 = max(0, 959 - target_w // 2)
    x2 = x1 + target_w
    if x2 > w:
        x2 = w
        x1 = w - target_w

    cropped = img[:, x1:x2]
    crop_1080 = cv2.resize(cropped, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(str(out_path), crop_1080)
    print(f"Repaired S04 archival training crop: {out_path.name} ({out_path.stat().st_size} bytes)")

def main():
    approved_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "assets" / "approved"
    cand_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "assets" / "candidates"

    # 1. S02 Repair
    repair_s02_portrait(cand_dir / "cand_S02_e3c35c4a37.jpg", approved_dir / "S02_approved_repaired.png")

    # 2. S03 Simplified Graphic
    create_simplified_s03(cand_dir / "cand_S01_012908f010.jpg", approved_dir / "S03_approved_repaired.png")

    # 3. S04 Archival Training Repair
    repair_s04_training_crop(cand_dir / "cand_S04_11fe2a9773.jpg", approved_dir / "S04_approved_repaired.png")

if __name__ == "__main__":
    main()
