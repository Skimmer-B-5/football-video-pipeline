"""
beta/stages/explainer_graphics.py - Broadcast-Grade Vertical Explainer Graphics Engine.

Generates 1080x1920 editorial infographics matching the 90s Sky Sports / BBC Sport visual DNA:
1. Transfer & Contract Clause Breakdown (Fees, Add-ons, Buy-back clauses).
2. Tactical Fit & Playing-Time Minutes Comparison Card.
3. VAR & Controversial Decision Breakdown.

Replaces generic training photos or static stadiums with genuine visual explanations.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BRANDING_DIR = DATA_DIR / "branding"
FONT_DIR = DATA_DIR / "fonts"

FONT_HEADLINE_PATH = FONT_DIR / "BarlowCondensed-ExtraBold.ttf"
FONT_BOLD_PATH = FONT_DIR / "BarlowCondensed-Bold.ttf"
FONT_REGULAR_PATH = FONT_DIR / "BarlowCondensed-Regular.ttf"

def _get_fonts():
    try:
        f_title = ImageFont.truetype(str(FONT_HEADLINE_PATH), 52)
        f_sub = ImageFont.truetype(str(FONT_BOLD_PATH), 32)
        f_card_title = ImageFont.truetype(str(FONT_HEADLINE_PATH), 38)
        f_card_val = ImageFont.truetype(str(FONT_HEADLINE_PATH), 58)
        f_body = ImageFont.truetype(str(FONT_REGULAR_PATH), 28)
        f_badge = ImageFont.truetype(str(FONT_HEADLINE_PATH), 24)
        return f_title, f_sub, f_card_title, f_card_val, f_body, f_badge
    except Exception:
        f = ImageFont.load_default()
        return f, f, f, f, f, f

def render_contract_clause_card(
    player_name: str = "ENDRICK",
    source_club: str = "REAL MADRID",
    target_club: str = "AC MILAN",
    base_fee: str = "€60M",
    add_ons: str = "€10M",
    buyback_clause: str = "€80M",
    out_path: Optional[Path] = None,
    width: int = 1080,
    height: int = 1920
) -> Image.Image:
    """
    Renders an editorial transfer formula infographic explaining deal structure,
    fees, and buyback clauses clearly on a mobile vertical canvas.
    """
    img = Image.new("RGBA", (width, height), (4, 12, 32, 255))
    draw = ImageDraw.Draw(img)
    f_title, f_sub, f_card_title, f_card_val, f_body, f_badge = _get_fonts()

    # 1. Subtle Radial Spotlight & Pitch Turf Grid
    for r in range(700, 0, -12):
        factor = 1.0 - (r / 700.0)
        alpha = int(factor * factor * 90)
        draw.ellipse([width // 2 - r, 750 - r, width // 2 + r, 750 + r], fill=(12, 38, 95, alpha))

    # 2. Main Explainer Header Card (y: 220 to 390)
    draw.rounded_rectangle([60, 220, 1020, 380], radius=12, fill=(6, 22, 60, 240))
    draw.rounded_rectangle([60, 220, 1020, 380], radius=12, outline=(255, 215, 0, 200), width=2)
    # Red category tab
    draw.rounded_rectangle([80, 235, 340, 280], radius=6, fill=(217, 4, 41, 255))
    draw.text((100, 242), "TRANSFER FORMULA", fill=(255, 255, 255), font=f_badge)
    
    draw.text((80, 290), f"{player_name.upper()} CONTRACT CLAUSE", fill=(255, 255, 255), font=f_title)
    draw.text((80, 345), f"{source_club.upper()}  ➔  {target_club.upper()}", fill=(255, 215, 0), font=f_sub)

    # 3. Block 1: Base Valuation / Loan Bid (y: 410 to 600)
    draw.rounded_rectangle([60, 410, 1020, 590], radius=12, fill=(10, 28, 70, 230))
    draw.rounded_rectangle([60, 410, 1020, 590], radius=12, outline=(50, 100, 180, 180), width=1)
    draw.rectangle([60, 410, 74, 590], fill=(255, 215, 0, 255)) # Left gold bar
    draw.text((100, 435), "PROPOSED BASE BID / LOAN VALUATION", fill=(160, 195, 240), font=f_card_title)
    draw.text((100, 485), base_fee, fill=(255, 255, 255), font=f_card_val)
    draw.text((100, 550), f"Primary upfront capital committed by {target_club}.", fill=(210, 225, 245), font=f_body)

    # 4. Block 2: Performance Add-ons (y: 620 to 800)
    draw.rounded_rectangle([60, 620, 1020, 800], radius=12, fill=(10, 28, 70, 230))
    draw.rounded_rectangle([60, 620, 1020, 800], radius=12, outline=(50, 100, 180, 180), width=1)
    draw.rectangle([60, 620, 74, 800], fill=(120, 190, 255, 255)) # Left blue bar
    draw.text((100, 645), "PERFORMANCE & TROPHY ADD-ONS", fill=(160, 195, 240), font=f_card_title)
    draw.text((100, 695), add_ons, fill=(255, 215, 0), font=f_card_val)
    draw.text((100, 760), "Tied to Champions League qualification & match appearances.", fill=(210, 225, 245), font=f_body)

    # 5. Block 3: The Critical Twist - Buy-Back Clause (y: 830 to 1030)
    # High-tension crimson red accents to emphasize the core tension!
    draw.rounded_rectangle([60, 830, 1020, 1030], radius=12, fill=(25, 12, 35, 245))
    draw.rounded_rectangle([60, 830, 1020, 1030], radius=12, outline=(217, 4, 41, 230), width=2)
    draw.rectangle([60, 830, 74, 1030], fill=(217, 4, 41, 255)) # Left red bar
    
    # "THE KEY CLAUSE" badge
    draw.rounded_rectangle([100, 850, 310, 888], radius=6, fill=(217, 4, 41, 255))
    draw.text((115, 855), "CRUCIAL CONDITION", fill=(255, 255, 255), font=f_badge)
    
    draw.text((100, 905), f"MADRID BUY-BACK REPURCHASE CLAUSE", fill=(255, 180, 190), font=f_card_title)
    draw.text((100, 950), buyback_clause, fill=(255, 215, 0), font=f_card_val)

    # 6. Precedent Note Card (y: 1060 to 1180)
    draw.rounded_rectangle([60, 1060, 1020, 1180], radius=10, fill=(8, 20, 50, 220))
    draw.text((90, 1080), "STRATEGIC PRECEDENT:", fill=(255, 215, 0), font=f_sub)
    draw.text((90, 1125), "Mirrors the exact loan & buyback structure Madrid used for Nico Paz.", fill=(220, 235, 255), font=f_body)

    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, format="PNG")
        print(f"[ExplainerGraphics] ✓ Rendered Contract Clause Card -> {out_path.name}")

    return img

def render_tactical_minutes_card(
    player_name: str = "ENDRICK",
    source_club: str = "REAL MADRID",
    target_club: str = "AC MILAN",
    current_minutes: str = "182 MINS",
    projected_minutes: str = "1,450+ MINS",
    tactical_role: str = "CENTRAL STARTING STRIKER",
    out_path: Optional[Path] = None,
    width: int = 1080,
    height: int = 1920
) -> Image.Image:
    """
    Renders an editorial playing-time and tactical fit comparison card.
    """
    img = Image.new("RGBA", (width, height), (4, 12, 32, 255))
    draw = ImageDraw.Draw(img)
    f_title, f_sub, f_card_title, f_card_val, f_body, f_badge = _get_fonts()

    # Spotlight
    for r in range(650, 0, -12):
        factor = 1.0 - (r / 650.0)
        alpha = int(factor * factor * 85)
        draw.ellipse([width // 2 - r, 750 - r, width // 2 + r, 750 + r], fill=(15, 45, 110, alpha))

    # Header Card
    draw.rounded_rectangle([60, 220, 1020, 380], radius=12, fill=(6, 22, 60, 240))
    draw.rounded_rectangle([60, 220, 1020, 380], radius=12, outline=(255, 215, 0, 200), width=2)
    draw.rounded_rectangle([80, 235, 340, 280], radius=6, fill=(10, 120, 220, 255))
    draw.text((100, 242), "TACTICAL ANALYSIS", fill=(255, 255, 255), font=f_badge)
    
    draw.text((80, 290), f"{player_name.upper()} PLAYING TIME DILEMMA", fill=(255, 255, 255), font=f_title)
    draw.text((80, 345), "BENCH ROTATION  VS  GUARANTEED STARTER", fill=(255, 215, 0), font=f_sub)

    # Comparison Block 1: Madrid Reality (y: 410 to 600)
    draw.rounded_rectangle([60, 410, 1020, 590], radius=12, fill=(10, 25, 60, 230))
    draw.rectangle([60, 410, 74, 590], fill=(120, 140, 170, 255))
    draw.text((100, 435), f"CURRENT ROLE: {source_club.upper()}", fill=(160, 180, 210), font=f_card_title)
    draw.text((100, 485), current_minutes, fill=(240, 100, 100), font=f_card_val)
    # Visual Progress bar (12% filled)
    draw.rounded_rectangle([100, 555, 960, 575], radius=6, fill=(20, 40, 80, 255))
    draw.rounded_rectangle([100, 555, 200, 575], radius=6, fill=(240, 90, 90, 255))

    # Comparison Block 2: Milan Projected (y: 620 to 810)
    draw.rounded_rectangle([60, 620, 1020, 800], radius=12, fill=(10, 28, 70, 230))
    draw.rectangle([60, 620, 74, 800], fill=(255, 215, 0, 255))
    draw.text((100, 645), f"PROJECTED ROLE: {target_club.upper()}", fill=(160, 220, 255), font=f_card_title)
    draw.text((100, 695), projected_minutes, fill=(255, 215, 0), font=f_card_val)
    # Visual Progress bar (80% filled)
    draw.rounded_rectangle([100, 765, 960, 785], radius=6, fill=(20, 40, 80, 255))
    draw.rounded_rectangle([100, 765, 780, 785], radius=6, fill=(255, 215, 0, 255))

    # Block 3: Tactical System Requirements (y: 830 to 1030)
    draw.rounded_rectangle([60, 830, 1020, 1030], radius=12, fill=(12, 32, 80, 240))
    draw.rounded_rectangle([60, 830, 1020, 1030], radius=12, outline=(100, 180, 255, 180), width=1)
    draw.text((100, 855), "TACTICAL ROLE AT SAN SIRO:", fill=(255, 215, 0), font=f_card_title)
    draw.text((100, 905), tactical_role, fill=(255, 255, 255), font=f_sub)
    draw.text((100, 955), "• Milan require clinical box presence and high-line pressing.", fill=(210, 230, 255), font=f_body)
    draw.text((100, 990), "• Madrid insist development must include regular European starts.", fill=(210, 230, 255), font=f_body)

    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path, format="PNG")
        print(f"[ExplainerGraphics] ✓ Rendered Tactical Minutes Card -> {out_path.name}")

    return img

if __name__ == "__main__":
    t_dir = DATA_DIR / "temp_assembly"
    t_dir.mkdir(parents=True, exist_ok=True)
    render_contract_clause_card(out_path=t_dir / "test_clause_card.png")
    render_tactical_minutes_card(out_path=t_dir / "test_tactical_card.png")
    print("✓ Explainer graphics test completed.")
