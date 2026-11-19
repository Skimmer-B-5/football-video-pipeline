"""
Stage: Frosted-Glass Tactical HUD Generator.
Uses Python Pillow to auto-render dark-mode stat cards, transfer fees,
and tactical metrics whenever a script cites hard numbers.
Composited over Scene 3 to break visual fatigue of AI faces.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HUD_WIDTH = 920
HUD_HEIGHT = 440

def get_font(size: int, bold: bool = False):
    """Load system font or fallback gracefully."""
    font_names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "Arial"
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()

def render_frosted_tactical_hud(
    title: str,
    stats: List[Dict[str, str]],
    badge_label: str = "TACTICAL INTEL",
    badge_color: str = "#38bdf8",  # Sky blue neon
    output_path: Optional[Path] = None,
    canvas_w: int = 1080,
    canvas_h: int = 1920
) -> Path:
    """
    Renders a 1080x1920 transparent PNG containing a centered, high-contrast
    frosted-glass dark-mode tactical HUD card.
    """
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # Center placement in lower-center
    card_x = (canvas_w - HUD_WIDTH) // 2
    card_y = 650  # Above subtitle area (subtitles are around y=1400-1600)

    # 1. Dark frosted glass background card
    card = Image.new("RGBA", (HUD_WIDTH, HUD_HEIGHT), (0, 0, 0, 0))
    draw_card = ImageDraw.Draw(card)

    # Glass container: semi-transparent deep navy slate
    glass_color = (13, 19, 33, 225)
    border_color = (56, 189, 248, 180)  # Neon border accent

    draw_card.rounded_rectangle(
        [(0, 0), (HUD_WIDTH, HUD_HEIGHT)],
        radius=28,
        fill=glass_color,
        outline=border_color,
        width=3
    )

    # 2. Header Category Badge
    badge_bg = (30, 41, 59, 240)
    draw_card.rounded_rectangle(
        [(36, 32), (36 + 210, 32 + 38)],
        radius=10,
        fill=badge_bg,
        outline=(56, 189, 248, 220),
        width=2
    )
    font_badge = get_font(18, bold=True)
    draw_card.text((48, 41), f"⚡ {badge_label}", font=font_badge, fill="#38bdf8")

    # 3. Main Subject Title
    font_title = get_font(34, bold=True)
    clean_title = title.upper()[:32]
    draw_card.text((36, 88), clean_title, font=font_title, fill="#ffffff")

    # Thin separator line
    draw_card.line([(36, 138), (HUD_WIDTH - 36, 138)], fill=(255, 255, 255, 45), width=2)

    # 4. Render Stat Cards (Up to 3 metric pills)
    num_stats = min(len(stats), 3)
    if num_stats > 0:
        pill_w = (HUD_WIDTH - 72 - ((num_stats - 1) * 20)) // num_stats
        pill_h = 145
        pill_y = 158

        font_val = get_font(28, bold=True)
        font_lbl = get_font(16, bold=False)

        for i, st in enumerate(stats[:num_stats]):
            px = 36 + i * (pill_w + 20)
            # Stat pill background
            draw_card.rounded_rectangle(
                [(px, pill_y), (px + pill_w, pill_y + pill_h)],
                radius=18,
                fill=(23, 32, 51, 230),
                outline=(71, 85, 105, 160),
                width=2
            )

            val = str(st.get("value", "N/A"))[:12]
            lbl = str(st.get("label", "METRIC")).upper()[:16]

            # Text inside pill
            draw_card.text((px + 20, pill_y + 24), val, font=font_val, fill="#fbbf24")  # Gold accent
            draw_card.text((px + 20, pill_y + 82), lbl, font=font_lbl, fill="#94a3b8")

    # 5. Tactical Pitch Footnote / Radar Watermark
    font_foot = get_font(15, bold=False)
    draw_card.text(
        (36, HUD_HEIGHT - 48),
        "TACTICAL TELEMETRY // FOOTBALL IN 30 SECONDS",
        font=font_foot,
        fill=(148, 163, 184, 160)
    )

    # Composite card onto 1080x1920 canvas
    canvas.alpha_composite(card, (card_x, card_y))

    if not output_path:
        output_path = Path("evidence/tactical_hud_sample.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG")
    print(f"[TacticalHUD] Frosted HUD rendered successfully to: {output_path}")
    return output_path

def composite_hud_onto_image(image_path: Path, hud_path: Path, output_path: Optional[Path] = None) -> Path:
    """Burn HUD directly onto scene visual."""
    base = Image.open(image_path).convert("RGBA")
    if base.size != (1080, 1920):
        base = base.resize((1080, 1920), Image.Resampling.LANCZOS)
    hud = Image.open(hud_path).convert("RGBA")
    combined = Image.alpha_composite(base, hud)
    final_rgb = combined.convert("RGB")
    out_p = output_path or image_path
    final_rgb.save(out_p, "JPEG", quality=95)
    return out_p

if __name__ == "__main__":
    test_out = Path("evidence/test_hud.png")
    render_frosted_tactical_hud(
        title="Mauricio Pochettino",
        stats=[
            {"label": "CONTRACT", "value": "2.5 YRS"},
            {"label": "COMPENSATION", "value": "£14.2M"},
            {"label": "SQUAD AGE", "value": "24.1"}
        ],
        badge_label="FINANCIAL INTEL",
        output_path=test_out
    )
