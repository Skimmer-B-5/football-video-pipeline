"""
beta/stages/generate_transfer_structure_graphic.py - Simplified Broadcast Transfer Structure Graphic Generator for Scene S03.

Fulfills V7.1.2 Mandate:
- Simplify existing card.
- Large readable figures:
  * €60M reported base proposal.
  * €80M–€85M reported buy-back range.
- NOT AGREED status (prominent).
- Minimal text, one clear visual relationship.
- No complicated multi-row dashboard.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.typography import load_font, get_token_font


def generate_s03_transfer_structure_graphic(out_path: Path) -> Path:
    w, h = 1080, 1920
    # Clean, dark slate studio canvas
    img = Image.new("RGB", (w, h), color=(14, 18, 28))
    draw = ImageDraw.Draw(img)

    # 1. Subtle, elegant background framing
    # Outer margin border
    draw.rectangle([(40, 60), (w - 40, h - 80)], outline=(30, 40, 60), width=2)
    # Subtle radial/linear accent bars
    draw.rectangle([(40, 60), (w - 40, 72)], fill=(56, 189, 248))

    # Fonts from central permanent typography design system
    font_kicker = load_font("IBM Plex Mono", 600, 24)
    font_title = load_font("Barlow Condensed", 800, 58)
    font_label = load_font("IBM Plex Mono", 500, 26)
    font_hero = load_font("Barlow Condensed", 800, 124)
    font_arrow = load_font("Barlow Condensed", 700, 32)
    font_status_badge = load_font("IBM Plex Mono", 600, 38)
    font_status_sub = load_font("Inter", 500, 26)
    font_footer = load_font("IBM Plex Mono", 500, 22)

    # 2. Header Area (Centered, clean)
    # Kicker Pill
    pill_w = 460
    pill_x0 = (w - pill_w) // 2
    draw.rounded_rectangle([(pill_x0, 200), (pill_x0 + pill_w, 255)], radius=12, fill=(24, 34, 54), outline=(56, 189, 248), width=2)
    draw.text((pill_x0 + 40, 212), "● REPORTED DEAL STRUCTURE", font=font_kicker, fill=(125, 211, 252))

    # Main Headline
    title_text = "ENDRICK TRANSFER PROPOSAL"
    title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((w - title_w) // 2, 290), title_text, font=font_title, fill=(255, 255, 255))

    # 3. Block 1: AC MILAN PROPOSED BASE + BONUSES
    b1_y0 = 420
    b1_h = 300
    draw.rounded_rectangle([(70, b1_y0), (w - 70, b1_y0 + b1_h)], radius=20, fill=(20, 26, 42), outline=(45, 60, 95), width=3)
    # Block 1 Header Tag
    draw.rounded_rectangle([(100, b1_y0 + 25), (600, b1_y0 + 70)], radius=8, fill=(30, 42, 68))
    draw.text((120, b1_y0 + 33), "AC MILAN • PREVIOUSLY EXPLORED PROPOSAL", font=font_label, fill=(186, 230, 253))

    # Hero Figure 1: €60M FIXED
    hero_1 = "€60M FIXED"
    draw.text((120, b1_y0 + 85), hero_1, font=font_hero, fill=(56, 189, 248))
    # Sub-component: + €10M in potential bonuses
    font_sub_bonus = load_font("Inter", 600, 28)
    draw.text((125, b1_y0 + 235), "+ €10M IN POTENTIAL BONUSES (UNCONFIRMED)", font=font_sub_bonus, fill=(125, 211, 252))

    # 4. Central Visual Relationship Indicator (One clear vertical transfer relationship)
    arrow_y = b1_y0 + b1_h + 25
    arrow_h = 90
    # Center connector line
    draw.line([(w // 2, b1_y0 + b1_h), (w // 2, arrow_y + 10)], fill=(70, 90, 130), width=4)
    draw.line([(w // 2, arrow_y + arrow_h - 10), (w // 2, arrow_y + arrow_h + 25)], fill=(70, 90, 130), width=4)

    # Connector Pill
    con_w = 540
    con_x0 = (w - con_w) // 2
    draw.rounded_rectangle([(con_x0, arrow_y), (con_x0 + con_w, arrow_y + arrow_h)], radius=16, fill=(25, 36, 56), outline=(96, 165, 250), width=2)
    arrow_label = "▲  REPURCHASE MECHANISM  ▼"
    al_bbox = draw.textbbox((0, 0), arrow_label, font=font_arrow)
    al_w = al_bbox[2] - al_bbox[0]
    draw.text(((w - al_w) // 2, arrow_y + 28), arrow_label, font=font_arrow, fill=(255, 255, 255))

    # 5. Block 2: REAL MADRID BUY-BACK CLAUSE
    b2_y0 = arrow_y + arrow_h + 25
    b2_h = 300
    draw.rounded_rectangle([(70, b2_y0), (w - 70, b2_y0 + b2_h)], radius=20, fill=(20, 26, 42), outline=(45, 60, 95), width=3)
    # Block 2 Header Tag
    draw.rounded_rectangle([(100, b2_y0 + 25), (640, b2_y0 + 70)], radius=8, fill=(48, 40, 20))
    draw.text((120, b2_y0 + 33), "REAL MADRID • REPORTED BUY-BACK PROTECTION", font=font_label, fill=(253, 224, 71))

    # Hero Figure 2: €80M–€85M
    hero_2 = "€80M – €85M"
    draw.text((120, b2_y0 + 85), hero_2, font=font_hero, fill=(250, 204, 21))
    draw.text((125, b2_y0 + 235), "ATTRIBUTED RANGE • NEVER FINALIZED OR AGREED", font=font_sub_bonus, fill=(253, 230, 138))

    # 6. Prominent NOT AGREED Status Banner
    st_y0 = b2_y0 + b2_h + 50
    st_h = 200
    draw.rounded_rectangle([(70, st_y0), (w - 70, st_y0 + st_h)], radius=20, fill=(50, 16, 20), outline=(239, 68, 68), width=3)

    # Status Hero Text
    st_text = "● STATUS: NOT AGREED"
    st_bbox = draw.textbbox((0, 0), st_text, font=font_status_badge)
    st_w = st_bbox[2] - st_bbox[0]
    draw.text(((w - st_w) // 2, st_y0 + 38), st_text, font=font_status_badge, fill=(254, 202, 202))

    # Status Subtitle
    st_sub = "Historical inquiry prior to Nov 23 medical update • Terms unformalized"
    sub_bbox = draw.textbbox((0, 0), st_sub, font=font_status_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    draw.text(((w - sub_w) // 2, st_y0 + 118), st_sub, font=font_status_sub, fill=(252, 165, 165))

    # 7. Lower Studio Branding Footer
    footer_text = "30 FOOTBALL PLUS • BROADCAST TRANSFER INTELLIGENCE"
    fb_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    fb_w = fb_bbox[2] - fb_bbox[0]
    draw.text(((w - fb_w) // 2, 1780), footer_text, font=font_footer, fill=(100, 116, 139))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), quality=95)
    return out_path


if __name__ == "__main__":
    out_f = PROJECT_ROOT / "temp" / "endrick_buyback_deal_structure_card.png"
    generate_s03_transfer_structure_graphic(out_f)
    print("Generated graphic at:", out_f)
