"""
Stage: Broadcast Explainer Graphics Generator.
Produces authentic 90s TV broadcast graphics for complex editorial concepts:
1. Transfer Flow & Contract / Buy-Back Clause Flowcharts
2. Stat Cards (Appearances, Minutes, Bench Ratio)
3. Quote Cards (Sourced quotes with speaker attribution)
4. Tactical Formation & Position Fit Overlays
Designed in vertical 1080x1920 with navy, gold, and crimson 90s broadcast identity.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "data" / "fonts"
IMAGES_DIR = PROJECT_ROOT / "data" / "images"
FONT_BOLD = FONTS_DIR / "BarlowCondensed-Bold.ttf"
FONT_EXTRABOLD = FONTS_DIR / "BarlowCondensed-ExtraBold.ttf"

def get_font(font_path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Load TTF font or fallback to default."""
    try:
        return ImageFont.truetype(str(font_path), size)
    except Exception:
        return ImageFont.load_default()

def create_contract_clause_graphic(
    title: str = "PROPOSED TRANSFER FRAMEWORK",
    parent_club: str = "REAL MADRID",
    target_club: str = "AC MILAN",
    bid_amount: str = "€60M BID",
    add_ons: str = "+ €10M ADD-ONS",
    clause_title: str = "LOS BLANCOS BUYBACK OPTION",
    clause_amount: str = "€80M CLAUSE",
    status_source: str = "REPORTED: CORRIERE DELLO SPORT",
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate an authentic 90s broadcast flowchart graphic explaining a transfer clause.
    Returns path to the generated 1080x1920 PNG image.
    """
    width, height = 1080, 1920
    im = Image.new("RGBA", (width, height), (10, 16, 32, 255)) # Dark navy background
    draw = ImageDraw.Draw(im)

    # 1. Subtle radial gradient & grid
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(16, 26, 48, 255), width=1)
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(16, 26, 48, 255), width=1)

    f_title = get_font(FONT_EXTRABOLD, 44)
    f_badge = get_font(FONT_BOLD, 26)
    f_club = get_font(FONT_EXTRABOLD, 38)
    f_amount = get_font(FONT_EXTRABOLD, 52)
    f_sub = get_font(FONT_BOLD, 28)
    f_source = get_font(FONT_BOLD, 24)

    # Top Header Card
    card_top = 380
    draw.rectangle([70, card_top, width - 70, card_top + 80], fill=(218, 37, 28, 255)) # Crimson red banner
    draw.text((width // 2, card_top + 40), title, font=f_title, fill=(255, 255, 255, 255), anchor="mm")

    # Source / Status pill
    draw.rectangle([140, card_top + 95, width - 140, card_top + 140], fill=(212, 175, 55, 255)) # Gold
    draw.text((width // 2, card_top + 117), status_source.upper(), font=f_badge, fill=(10, 16, 32, 255), anchor="mm")

    # Box 1: Parent Club (Real Madrid)
    b1_y = 600
    draw.rectangle([100, b1_y, 480, b1_y + 160], fill=(18, 30, 58, 255), outline=(212, 175, 55, 255), width=3)
    draw.text((290, b1_y + 40), "SELLER / PARENT CLUB", font=f_badge, fill=(180, 195, 220, 255), anchor="mm")
    draw.text((290, b1_y + 95), parent_club, font=f_club, fill=(255, 255, 255, 255), anchor="mm")

    # Arrow Down/Right -> AC Milan
    draw.line([(480, b1_y + 80), (600, b1_y + 80)], fill=(212, 175, 55, 255), width=6)
    draw.polygon([(595, b1_y + 70), (615, b1_y + 80), (595, b1_y + 90)], fill=(212, 175, 55, 255))

    # Box 2: Target Club (AC Milan)
    draw.rectangle([600, b1_y, 980, b1_y + 160], fill=(18, 30, 58, 255), outline=(212, 175, 55, 255), width=3)
    draw.text((790, b1_y + 40), "PROSPECTIVE BUYER", font=f_badge, fill=(180, 195, 220, 255), anchor="mm")
    draw.text((790, b1_y + 95), target_club, font=f_club, fill=(255, 255, 255, 255), anchor="mm")

    # Flow 1: Outgoing Bid & Add-ons
    flow1_y = 810
    draw.rectangle([100, flow1_y, width - 100, flow1_y + 180], fill=(14, 24, 46, 255), outline=(0, 200, 120, 255), width=2)
    draw.text((width // 2, flow1_y + 45), f"PROSPECTIVE OUTGOING FEE: {bid_amount}", font=f_amount, fill=(0, 240, 140, 255), anchor="mm")
    draw.text((width // 2, flow1_y + 115), f"PERFORMANCE INCENTIVES: {add_ons}", font=f_sub, fill=(220, 230, 245, 255), anchor="mm")

    # Flow 2: Return Buyback Clause Arrow
    flow2_y = 1040
    draw.rectangle([100, flow2_y, width - 100, flow2_y + 220], fill=(28, 20, 40, 255), outline=(255, 180, 0, 255), width=3)
    draw.text((width // 2, flow2_y + 45), f"↺ {clause_title}", font=f_title, fill=(255, 200, 50, 255), anchor="mm")
    draw.text((width // 2, flow2_y + 115), clause_amount, font=f_amount, fill=(255, 255, 255, 255), anchor="mm")
    draw.text((width // 2, flow2_y + 175), "STRUCTURED IDENTICAL TO NICO PAZ MODEL", font=f_badge, fill=(200, 210, 230, 255), anchor="mm")

    # Bottom analysis note
    draw.rectangle([100, 1310, width - 100, 1400], fill=(18, 30, 58, 255))
    draw.text((width // 2, 1355), "NOTE: REAL MADRID WOULD RETAIN FUTURE SPORTING CONTROL", font=f_source, fill=(212, 175, 55, 255), anchor="mm")

    if output_path is None:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        output_path = IMAGES_DIR / "graphic_contract_clause.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(str(output_path), "PNG")
    return output_path

def create_stat_card_graphic(
    player_name: str = "ENDRICK",
    club_name: str = "REAL MADRID",
    stat_items: Optional[list] = None,
    context_note: str = "COMPETITIVE MINUTES RESTRICTION",
    output_path: Optional[Path] = None
) -> Path:
    """Generate broadcast player statistic card."""
    width, height = 1080, 1920
    im = Image.new("RGBA", (width, height), (10, 16, 32, 255))
    draw = ImageDraw.Draw(im)

    stat_items = stat_items or [
        ("TOTAL LALIGA STARTS", "1 START"),
        ("COMPETITIVE MINUTES", "107 MINS"),
        ("ATTACKING HIERARCHY", "4TH CHOICE")
    ]

    f_title = get_font(FONT_EXTRABOLD, 48)
    f_badge = get_font(FONT_BOLD, 28)
    f_val = get_font(FONT_EXTRABOLD, 54)
    f_lbl = get_font(FONT_BOLD, 30)

    # Header
    y = 420
    draw.rectangle([80, y, width - 80, y + 120], fill=(218, 37, 28, 255))
    draw.text((width // 2, y + 45), player_name, font=f_title, fill=(255, 255, 255, 255), anchor="mm")
    draw.text((width // 2, y + 90), f"{club_name} • {context_note}", font=f_badge, fill=(255, 230, 100, 255), anchor="mm")

    # Stat blocks
    box_y = y + 170
    for label, val in stat_items:
        draw.rectangle([100, box_y, width - 100, box_y + 140], fill=(18, 30, 58, 255), outline=(212, 175, 55, 255), width=2)
        draw.text((140, box_y + 70), label, font=f_lbl, fill=(190, 205, 230, 255), anchor="lm")
        draw.text((width - 140, box_y + 70), val, font=f_val, fill=(255, 255, 255, 255), anchor="rm")
        box_y += 170

    if output_path is None:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        output_path = IMAGES_DIR / "graphic_stat_card.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(str(output_path), "PNG")
    return output_path

def create_explainer_graphic_for_scene(scene: Dict[str, Any], output_path: Path) -> Path:
    """
    Select and render the appropriate explainer graphic for a scene based on visual.kind.
    """
    visual = scene.get("visual", {})
    kind = visual.get("kind", "")
    on_screen = scene.get("on_screen", {})

    if kind in ("contract_or_clause_graphic", "transfer_flow_graphic"):
        return create_contract_clause_graphic(
            title=on_screen.get("headline", "PROPOSED TRANSFER FRAMEWORK"),
            parent_club="REAL MADRID",
            target_club="AC MILAN",
            bid_amount="€60M BID",
            add_ons="+ €10M ADD-ONS",
            clause_title="REAL MADRID BUYBACK CLAUSE",
            clause_amount="€80M CLAUSE (NICO PAZ MODEL)",
            status_source=f"REPORTED: {on_screen.get('status_badge', 'CORRIERE DELLO SPORT')}",
            output_path=output_path
        )
    elif kind == "stat_card":
        return create_stat_card_graphic(
            player_name=visual.get("primary_subject", "ENDRICK"),
            club_name="REAL MADRID",
            context_note="PLAYING TIME REALITY",
            output_path=output_path
        )
    else:
        # Default clause flowchart
        return create_contract_clause_graphic(output_path=output_path)
