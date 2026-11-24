import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.typography import load_font

def create_s03_restrained_photo_overlay(out_path: Path):
    w, h = 1080, 1920
    
    # 1. Base authentic football photography: Santiago Bernabeu illuminated stadium
    base_photo_path = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "assets" / "candidates" / "cand_S01_012908f010.jpg"
    if base_photo_path.exists():
        photo = Image.open(base_photo_path).convert("RGBA")
        # Center-crop 9:16
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
    else:
        photo = Image.new("RGBA", (w, h), color=(15, 23, 42, 255))
        
    # 2. Apply restrained dark vignette scrim to ensure photography dominates while typography is readable
    scrim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    scrim_draw = ImageDraw.Draw(scrim)
    # Dark linear gradient over middle band [y: 350 to 1250]
    for y in range(h):
        if 350 <= y <= 1250:
            alpha = int(140 + 50 * (1.0 - abs(y - 800) / 450)) # 140-190 alpha
            scrim_draw.line([(0, y), (w, y)], fill=(10, 15, 28, alpha))
        elif y > 1250:
            # Slightly darker lower area for subtitles/ticker
            scrim_draw.line([(0, y), (w, y)], fill=(10, 15, 28, 160))
            
    canvas = Image.alpha_composite(photo, scrim)
    draw = ImageDraw.Draw(canvas)
    
    # Fonts
    font_kicker = load_font("IBM Plex Mono", 600, 24)
    font_title = load_font("Barlow Condensed", 800, 64)
    font_label = load_font("IBM Plex Mono", 600, 26)
    font_hero = load_font("Barlow Condensed", 800, 118)
    font_hero_sub = load_font("Inter", 600, 26)
    font_connector = load_font("Barlow Condensed", 700, 30)
    font_badge = load_font("IBM Plex Mono", 700, 36)
    font_badge_sub = load_font("Inter", 600, 24)
    
    # 3. Restrained Typographic Data Overlay (No solid card; floating text with subtle glow/scrim)
    # Kicker Pill
    pill_text = "● REPORTED DEAL STRUCTURE"
    draw.text((70, 420), pill_text, font=font_kicker, fill=(56, 189, 248))
    
    # Main Headline
    draw.text((70, 465), "ENDRICK TRANSFER PROPOSAL", font=font_title, fill=(255, 255, 255))
    
    # Thin divider rule
    draw.line([(70, 550), (w - 70, 550)], fill=(56, 189, 248, 180), width=2)
    
    # Block 1: Proposed Base
    draw.text((70, 580), "AC MILAN • REPORTED WINTER PROPOSAL", font=font_label, fill=(186, 230, 253))
    draw.text((70, 620), "€60M FIXED", font=font_hero, fill=(56, 189, 248))
    draw.text((70, 755), "+ €10M IN POTENTIAL BONUSES (UNCONFIRMED)", font=font_hero_sub, fill=(224, 242, 254))
    
    # Vertical connecting relationship
    draw.line([(70, 815), (w - 70, 815)], fill=(70, 90, 130, 140), width=1)
    draw.text((70, 835), "▲  REPORTED REPURCHASE FIGURES (NOT AGREED)  ▼", font=font_connector, fill=(255, 255, 255))
    draw.line([(70, 885), (w - 70, 885)], fill=(70, 90, 130, 140), width=1)
    
    # Block 2: Repurchase figures reported by separate outlets
    draw.text((70, 915), "REAL MADRID • REPORTED BUY-BACK RANGE", font=font_label, fill=(253, 224, 71))
    draw.text((70, 955), "€80M – €85M", font=font_hero, fill=(250, 204, 21))
    draw.text((70, 1090), "€80M (CORRIERE DELLO SPORT) • €85M (TNT SPORTS BRAZIL)", font=font_hero_sub, fill=(254, 240, 138))
    
    # 4. Status Indicator: NOT AGREED
    badge_y = 1150
    draw.rounded_rectangle([(70, badge_y), (480, badge_y + 65)], radius=10, fill=(239, 68, 68), outline=(254, 202, 202), width=2)
    draw.text((100, badge_y + 12), "STATUS: NOT AGREED", font=font_badge, fill=(255, 255, 255))
    draw.text((510, badge_y + 18), "NO CLAUSE COMPLETED BETWEEN CLUBS", font=font_badge_sub, fill=(226, 232, 240))
    
    # Convert to RGB and save
    final_img = canvas.convert("RGB")
    final_img.save(str(out_path), "PNG", quality=95)
    print(f"Created restrained S03 photo-overlay: {out_path} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    out_test = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "assets" / "approved" / "S03_approved_restrained_overlay.png"
    create_s03_restrained_photo_overlay(out_test)
