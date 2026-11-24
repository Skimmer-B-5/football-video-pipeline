"""
beta/stages/generate_typography_specimens.py

30 Football Plus — Typography Specimen Generator Engine (V7.1.3)
Generates full native-resolution 1080x1920 typography specimen sheets:
1. English Diagnostic & Clean Specimens
2. Brazilian Portuguese (PT-BR) Diagnostic & Clean Specimens
3. Latin American Spanish (ES-419) Diagnostic & Clean Specimens
4. Before-and-After Typography Comparison Sheet
5. Multi-panel Master Showcase Sheet for Telegram review

Includes the 8 mandatory elements:
- Breaking-news headline
- Player-name reveal
- Transfer-fee graphic
- Two-line narration subtitle
- Compact statistic
- Lower-third
- Category label
- 30 Football Plus outro
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.typography import (
    TYPOGRAPHY_TOKENS,
    SAFE_ZONES,
    load_font,
    get_token_font,
    FONT_FAMILIES
)

W, H = 1080, 1920

# Colors (1990s/2000s Restrained Broadcast Palette)
BG_BASE = (10, 15, 26)              # Deep broadcast slate navy
CARD_BG = (16, 24, 42)              # Midnight blue panel
CARD_BORDER = (40, 56, 86)          # Structural divider
ACCENT_CYAN = (56, 189, 248)        # Tech / Transfer cyan (#38bdf8)
ACCENT_GOLD = (250, 204, 21)        # Subject / Reveal gold (#facc15)
ACCENT_RED = (239, 68, 68)          # Breaking news crimson (#ef4444)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (148, 163, 184)        # Slate 400
TEXT_DIM = (100, 116, 139)          # Slate 500

SPECIMEN_DATA = {
    "en": {
        "lang_name": "English (EN)",
        "category": "TRANSFER WATCH",
        "kicker": "BREAKING NEWS",
        "headline": "ENDRICK PROPOSAL ADVANCES WITH MADRID BUY-BACK CLAUSE",
        "headline_compact": "ENDRICK BID ADVANCES",
        "player_reveal": "ENDRICK",
        "stat_hero": "€60M",
        "stat_label": "REPORTED BASE PROPOSAL",
        "stat_secondary": "€80M – €85M",
        "stat_secondary_label": "BUY-BACK RANGE",
        "stat_compact": "155 MINS • 2 GOALS",
        "stat_compact_label": "2026–27 MADRID RECORD",
        "subtitle": "Milan are targeting Endrick, exploring an ambitious move for the twenty-year-old forward.",
        "lower_third_kicker": "SERIE A INQUIRIES",
        "lower_third_body": "Real Madrid demand protective buy-back clause before January talks begin.",
        "source": "REUTERS / THE ATHLETIC • VERIFIED",
        "outro_headline": "30 FOOTBALL PLUS",
        "outro_sub": "BROADCAST FOOTBALL INTELLIGENCE • FOLLOW FOR DAILY REPORTS"
    },
    "pt_br": {
        "lang_name": "Brazilian Portuguese (PT-BR)",
        "category": "MERCADO DA BOLA",
        "kicker": "ÚLTIMA HORA",
        "headline": "PROPOSTA POR ENDRICK AVANÇA COM PROTEÇÃO DO REAL MADRID",
        "headline_compact": "OFERTA POR ENDRICK AVANÇA",
        "player_reveal": "ENDRICK",
        "stat_hero": "€60M",
        "stat_label": "PROPOSTA BASE NOTICIADA",
        "stat_secondary": "€80M – €85M",
        "stat_secondary_label": "CLÁUSULA DE RECOMPRA",
        "stat_compact": "155 MINS • 2 GOLS",
        "stat_compact_label": "TEMPORADA 2026–27",
        "subtitle": "O Milan estuda investida ambiciosa pelo atacante de vinte anos, mas espanhóis exigem recompra.",
        "lower_third_kicker": "NEGOCIAÇÃO EM CURSO",
        "lower_third_body": "Lesão no músculo da coxa direita não encerra o interesse italiano para janeiro.",
        "source": "APURAÇÃO / REUTERS • CHECADO",
        "outro_headline": "30 FOOTBALL PLUS",
        "outro_sub": "INTELIGÊNCIA DO FUTEBOL MUNDIAL • SIGA PARA ANÁLISES DIÁRIAS"
    },
    "es_419": {
        "lang_name": "Latin American Spanish (ES-419)",
        "category": "FICHAJES AL DÍA",
        "kicker": "ÚLTIMO MOMENTO",
        "headline": "EL MILAN PREPARA OFERTA POR ENDRICK CON CLÁUSULA BLINDADA",
        "headline_compact": "OFERTA POR ENDRICK",
        "player_reveal": "ENDRICK",
        "stat_hero": "€60M",
        "stat_label": "OFERTA BASE REPORTADA",
        "stat_secondary": "€80M – €85M",
        "stat_secondary_label": "OPCIÓN DE RECOMPRA",
        "stat_compact": "155 MINS • 2 GOLES",
        "stat_compact_label": "CAMPAÑA 2026–27",
        "subtitle": "El Milan analiza la llegada del delantero de veinte años, pero Madrid exige cláusula de retorno.",
        "lower_third_kicker": "MERCADO SERIE A",
        "lower_third_body": "Parte médico confirma lesión en el muslo derecho pendiente de evolución clínica.",
        "source": "REUTERS / THE ATHLETIC • VERIFICADO",
        "outro_headline": "30 FOOTBALL PLUS",
        "outro_sub": "INTELIGENCIA DEL FÚTBOL MUNDIAL • SÍGUENOS PARA REPORTES DIARIOS"
    }
}


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, max_lines: int = 2) -> List[str]:
    """Wraps text cleanly without breaking words."""
    words = text.split()
    lines = []
    curr = []
    for w in words:
        test = " ".join(curr + [w])
        bbox = font.getbbox(test)
        w_px = bbox[2] - bbox[0]
        if w_px <= max_width:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
                curr = [w]
            else:
                lines.append(w)
                curr = []
            if len(lines) >= max_lines:
                break
    if curr and len(lines) < max_lines:
        lines.append(" ".join(curr))
    return lines


def draw_tag_pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.FreeTypeFont,
                  bg: Tuple[int, int, int], fg: Tuple[int, int, int], border: Optional[Tuple[int, int, int]] = None,
                  pad_x: int = 14, pad_y: int = 6, radius: int = 6) -> int:
    """Draws a compact metadata tag pill and returns its total width."""
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius, fill=bg, outline=border, width=1 if border else 0)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, font=font, fill=fg)
    return w


def draw_specimen_frame(lang_key: str, diagnostic: bool = True) -> Image.Image:
    data = SPECIMEN_DATA[lang_key]
    img = Image.new("RGBA", (W, H), (*BG_BASE, 255))
    draw = ImageDraw.Draw(img)

    margin_x = SAFE_ZONES["margin_horizontal_preferred"]  # 84px
    content_w = W - 2 * margin_x  # 912px

    # Background architectural lines (subtle dark grid)
    for gy in range(0, H, 160):
        draw.line([(0, gy), (W, gy)], fill=(18, 25, 40), width=1)
    for gx in range(margin_x, W, 228):
        draw.line([(gx, 0), (gx, H)], fill=(18, 25, 40), width=1)

    # 1. BRAND IDENTIFIER REGION (y: 100 - 180)
    brand_font = get_token_font("brandMark")
    kicker_font = get_token_font("breakingKicker")
    cat_font = get_token_font("categoryLabel")
    diag_font = load_font("IBM Plex Mono", 500, 16)

    y_cur = 100
    draw.text((margin_x, y_cur), data["outro_headline"], font=brand_font, fill=TEXT_WHITE)
    
    # Right-aligned Category & Kicker Pills
    pill_text_kicker = f"● {data['kicker']}"
    pill_text_cat = data['category']
    pill_w_kicker = draw_tag_pill(draw, W - margin_x - 220, y_cur + 8, pill_text_kicker, kicker_font, bg=(60, 20, 24), fg=ACCENT_RED, border=ACCENT_RED)
    draw_tag_pill(draw, W - margin_x - 220 - 240, y_cur + 8, pill_text_cat, cat_font, bg=(20, 36, 56), fg=ACCENT_CYAN, border=ACCENT_CYAN)

    if diagnostic:
        draw.text((margin_x, y_cur - 26), "Brand: Barlow Condensed Bold 62px | Kicker/Cat: IBM Plex Mono SemiBold 24px", font=diag_font, fill=TEXT_MUTED)

    # Horizontal divider
    draw.line([(margin_x, 185), (W - margin_x, 185)], fill=CARD_BORDER, width=2)

    # 2. PRIMARY HEADLINE REGION (y: 220 - 410)
    hl_font = get_token_font("primaryHeadline")
    lines_hl = wrap_text(data["headline"], hl_font, content_w, max_lines=2)
    
    y_hl = 220
    if diagnostic:
        draw.text((margin_x, y_hl - 24), f"Headline: Barlow Condensed ExtraBold 78px (LH 0.98, Max 2 lines)", font=diag_font, fill=TEXT_MUTED)

    for line in lines_hl:
        draw.text((margin_x, y_hl), line, font=hl_font, fill=TEXT_WHITE)
        y_hl += 76

    # 3. PLAYER NAME REVEAL REGION (y: 410 - 540)
    p_font = get_token_font("playerReveal")
    y_p = 410
    draw.rounded_rectangle([(margin_x, y_p), (W - margin_x, y_p + 110)], radius=16, fill=CARD_BG, outline=CARD_BORDER, width=2)
    # Gold left accent bar
    draw.rounded_rectangle([(margin_x, y_p), (margin_x + 12, y_p + 110)], radius=4, fill=ACCENT_GOLD)
    
    p_tag_font = load_font("IBM Plex Mono", 600, 20)
    draw.text((margin_x + 36, y_p + 16), "● FOCAL SUBJECT REVEAL", font=p_tag_font, fill=ACCENT_GOLD)
    draw.text((margin_x + 36, y_p + 42), data["player_reveal"], font=p_font, fill=TEXT_WHITE)

    # Secondary metadata tag on right
    draw.text((W - margin_x - 240, y_p + 58), "AGE 20 • REAL MADRID", font=p_tag_font, fill=TEXT_MUTED)

    if diagnostic:
        draw.text((margin_x, y_p - 24), "Subject Reveal: Barlow Condensed ExtraBold 92px / Yellow Gold Accent", font=diag_font, fill=TEXT_MUTED)

    # 4. DATA GRAPHIC / TRANSFER VALUE & STATS REGION (y: 560 - 980)
    y_dg = 560
    draw.rounded_rectangle([(margin_x, y_dg), (W - margin_x, y_dg + 410)], radius=20, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Header tag inside data card
    d_label_font = get_token_font("statisticLabel")
    draw_tag_pill(draw, margin_x + 30, y_dg + 24, "REPORTED TRANSFER STRUCTURE", d_label_font, bg=(26, 36, 56), fg=ACCENT_CYAN, border=ACCENT_CYAN)

    # Hero Value: €60M
    stat_hero_font = get_token_font("statisticHero")
    draw.text((margin_x + 30, y_dg + 80), data["stat_hero"], font=stat_hero_font, fill=ACCENT_CYAN)
    
    hero_label_font = load_font("IBM Plex Mono", 500, 26)
    draw.text((margin_x + 400, y_dg + 115), data["stat_label"], font=hero_label_font, fill=TEXT_MUTED)

    # Divider inside card
    draw.line([(margin_x + 30, y_dg + 225), (W - margin_x - 30, y_dg + 225)], fill=CARD_BORDER, width=2)

    # Buyback Range & Secondary Stat
    stat_sec_font = load_font("Barlow Condensed", 800, 72)
    draw.text((margin_x + 30, y_dg + 250), data["stat_secondary"], font=stat_sec_font, fill=ACCENT_GOLD)
    draw.text((margin_x + 30, y_dg + 335), data["stat_secondary_label"], font=hero_label_font, fill=TEXT_MUTED)

    # Right side compact stat
    draw.text((W - margin_x - 380, y_dg + 265), data["stat_compact"], font=load_font("Barlow Condensed", 700, 48), fill=TEXT_WHITE)
    draw.text((W - margin_x - 380, y_dg + 335), data["stat_compact_label"], font=hero_label_font, fill=TEXT_MUTED)

    # Prominent NOT AGREED Banner at bottom of card
    not_agreed_font = load_font("IBM Plex Mono", 600, 22)
    draw_tag_pill(draw, W - margin_x - 260, y_dg + 24, "● STATUS: NOT AGREED", not_agreed_font, bg=(60, 20, 24), fg=ACCENT_RED, border=ACCENT_RED)

    if diagnostic:
        draw.text((margin_x, y_dg - 24), "Data Hero: Barlow Condensed ExtraBold 124px | Labels: IBM Plex Mono 26px", font=diag_font, fill=TEXT_MUTED)

    # 5. SUPPORTING LOWER-THIRD REGION (y: 1010 - 1240)
    y_lt = 1010
    draw.rounded_rectangle([(margin_x, y_lt), (W - margin_x, y_lt + 210)], radius=16, fill=(14, 20, 36), outline=CARD_BORDER, width=2)
    # Left accent band
    draw.rounded_rectangle([(margin_x, y_lt), (margin_x + 10, y_lt + 210)], radius=3, fill=ACCENT_CYAN)

    lt_kicker_font = load_font("IBM Plex Mono", 600, 22)
    draw.text((margin_x + 32, y_lt + 20), f"● {data['lower_third_kicker']}", font=lt_kicker_font, fill=ACCENT_CYAN)

    lt_body_font = get_token_font("lowerThird")
    lt_lines = wrap_text(data["lower_third_body"], lt_body_font, content_w - 70, max_lines=2)
    lt_y_text = y_lt + 62
    for l in lt_lines:
        draw.text((margin_x + 32, lt_y_text), l, font=lt_body_font, fill=TEXT_WHITE)
        lt_y_text += 44

    source_font = get_token_font("sourceMetadata")
    draw.text((margin_x + 32, y_lt + 168), data["source"], font=source_font, fill=TEXT_DIM)

    if diagnostic:
        draw.text((margin_x, y_lt - 24), "Lower Third: Inter SemiBold 36px | Source: IBM Plex Mono Medium 20px", font=diag_font, fill=TEXT_MUTED)

    # 6. NARRATION SUBTITLES REGION (y: 1280 - 1490)
    y_sub = 1280
    sub_font = get_token_font("narrationSubtitle")
    sub_lines = wrap_text(data["subtitle"], sub_font, content_w - 60, max_lines=2)

    # Restrained bottom gradient band (simulated subtle plate)
    draw.rounded_rectangle([(margin_x - 10, y_sub), (W - margin_x + 10, y_sub + 170)], radius=14, fill=(12, 17, 30, 210), outline=(32, 44, 70), width=1)
    
    sub_tag_font = load_font("IBM Plex Mono", 600, 18)
    draw.text((margin_x + 20, y_sub + 16), "CC • NARRATION SUBTITLES (SENTENCE CASE)", font=sub_tag_font, fill=TEXT_MUTED)

    y_sub_text = y_sub + 52
    for sl in sub_lines:
        # Subtle drop shadow for subtitle contrast
        draw.text((margin_x + 22, y_sub_text + 2), sl, font=sub_font, fill=(0, 0, 0, 200))
        draw.text((margin_x + 20, y_sub_text), sl, font=sub_font, fill=TEXT_WHITE)
        y_sub_text += 54

    if diagnostic:
        draw.text((margin_x, y_sub - 24), "Subtitles: Inter SemiBold 46px (LH 1.16, Max 36 chars/line, Sentence Case)", font=diag_font, fill=TEXT_MUTED)

    # 7. OUTRO BRANDING REGION (y: 1530 - 1760)
    y_outro = 1530
    draw.rounded_rectangle([(margin_x, y_outro), (W - margin_x, y_outro + 180)], radius=16, fill=CARD_BG, outline=CARD_BORDER, width=2)
    # Red top accent strip
    draw.rounded_rectangle([(margin_x, y_outro), (W - margin_x, y_outro + 8)], radius=4, fill=ACCENT_RED)

    outro_hl_font = get_token_font("outroHeadline")
    outro_cta_font = get_token_font("outroCTA")
    
    draw.text((margin_x + 36, y_outro + 38), data["outro_headline"], font=outro_hl_font, fill=TEXT_WHITE)
    draw.text((margin_x + 36, y_outro + 115), data["outro_sub"], font=outro_cta_font, fill=TEXT_MUTED)

    if diagnostic:
        draw.text((margin_x, y_outro - 24), "Outro: Barlow Condensed Bold 64px | CTA: Inter SemiBold 26px", font=diag_font, fill=TEXT_MUTED)

    # 8. PLATFORM BOTTOM SAFE ZONE INDICATOR (y: 1780 - 1920)
    if diagnostic:
        draw.line([(0, 1640), (W, 1640)], fill=(239, 68, 68, 120), width=2)
        draw.text((margin_x, 1645), "▲ CRITICAL SAFE ZONE LIMIT (Avoid primary text below y=1640 for mobile platform UI) ▲", font=diag_font, fill=ACCENT_RED)
        
        # Left and Right Safe Margins
        draw.line([(margin_x, 0), (margin_x, H)], fill=(56, 189, 248, 80), width=1)
        draw.line([(W - margin_x, 0), (W - margin_x, H)], fill=(56, 189, 248, 80), width=1)
        draw.text((margin_x + 8, H - 45), f"Horizontal Safe Margin: {margin_x}px | Language: {data['lang_name']}", font=diag_font, fill=ACCENT_CYAN)
    else:
        # Clean subtle studio footer
        clean_footer_font = load_font("IBM Plex Mono", 500, 18)
        draw.text((margin_x, H - 60), f"30 FOOTBALL PLUS • PERMANENT BROADCAST DESIGN SYSTEM (V7.1.3) • {data['lang_name'].upper()}", font=clean_footer_font, fill=TEXT_DIM)

    return img


def draw_before_after_comparison() -> Image.Image:
    """Renders a side-by-side 1920x1080 comparison between V7 Old Typography and V7.1.3 New Design System."""
    cw, ch = 960, 1080
    comp = Image.new("RGBA", (1920, 1080), (*BG_BASE, 255))
    draw = ImageDraw.Draw(comp)

    # Fonts
    title_font = load_font("Barlow Condensed", 700, 48)
    sub_title_font = load_font("Inter", 600, 24)
    mono_font = load_font("IBM Plex Mono", 600, 20)
    body_font = load_font("Inter", 400, 22)

    # 1. Left Half: BEFORE (V7 / Legacy Inconsistent Typography)
    draw.rectangle([(0, 0), (cw, 1080)], fill=(12, 16, 26))
    draw.rectangle([(30, 30), (cw - 30, 1050)], outline=(80, 30, 30), width=2)
    draw_tag_pill(draw, 50, 50, "BEFORE: V7 LEGACY TYPOGRAPHY", mono_font, bg=(60, 20, 20), fg=ACCENT_RED, border=ACCENT_RED)
    
    # Legacy problems list
    draw.text((50, 110), "INCONSISTENT SYSTEM FONT STACK", font=title_font, fill=(240, 140, 140))
    draw.text((50, 175), "• Arial / Fallback System Fonts with arbitrary weights", font=sub_title_font, fill=TEXT_MUTED)
    draw.text((50, 215), "• Headline size uncontrolled (overflow and uneven wrapping)", font=sub_title_font, fill=TEXT_MUTED)
    draw.text((50, 255), "• All-caps narration subtitles inside cartoonish boxes", font=sub_title_font, fill=TEXT_MUTED)
    draw.text((50, 295), "• Multi-font clash (no distinction between data & headlines)", font=sub_title_font, fill=TEXT_MUTED)
    draw.text((50, 335), "• Accent rendering risks across PT-BR and ES-419", font=sub_title_font, fill=TEXT_MUTED)

    # Legacy mock
    draw.rectangle([(50, 400), (cw - 50, 980)], fill=(20, 22, 30), outline=(60, 60, 60), width=2)
    # Simulate old Arial headline
    try:
        old_font_hl = ImageFont.truetype("arialbd.ttf", size=54)
        old_font_sub = ImageFont.truetype("arial.ttf", size=32)
    except:
        old_font_hl = load_font("Barlow Condensed", 600, 54)
        old_font_sub = load_font("Inter", 400, 32)
    draw.text((70, 430), "ENDRICK MILAN TRANSFER BID", font=old_font_hl, fill=(255, 255, 255))
    draw.text((70, 510), "€60M / BUYBACK €85M (STATUS UNKNOWN)", font=old_font_sub, fill=(200, 200, 200))
    draw.rectangle([(70, 600), (cw - 70, 720)], fill=(0, 0, 0), outline=(255, 255, 0), width=2)
    draw.text((85, 630), "MILAN ARE TARGETING ENDRICK FOR JANUARY MOVE", font=old_font_sub, fill=(255, 255, 0))
    draw.text((70, 800), "⚠️ Result: Generic AI template look, weak editorial hierarchy", font=body_font, fill=(248, 113, 113))

    # Center vertical divider
    draw.line([(cw, 0), (cw, 1080)], fill=ACCENT_CYAN, width=3)

    # 2. Right Half: AFTER (V7.1.3 Permanent Design System)
    draw.rectangle([(cw, 0), (1920, 1080)], fill=(10, 15, 26))
    draw.rectangle([(cw + 30, 30), (1920 - 30, 1050)], outline=(30, 70, 90), width=2)
    draw_tag_pill(draw, cw + 50, 50, "AFTER: V7.1.3 PERMANENT DESIGN SYSTEM", mono_font, bg=(20, 40, 60), fg=ACCENT_CYAN, border=ACCENT_CYAN)

    draw.text((cw + 50, 110), "THREE FONT FAMILIES • ONE CLEAR HIERARCHY", font=title_font, fill=ACCENT_CYAN)
    draw.text((cw + 50, 175), "1. Barlow Condensed (600–900): Headlines, player reveals, transfer hero", font=sub_title_font, fill=TEXT_WHITE)
    draw.text((cw + 50, 215), "2. Inter (400–800): Sentence-case subtitles, lower-thirds, CTA", font=sub_title_font, fill=TEXT_WHITE)
    draw.text((cw + 50, 255), "3. IBM Plex Mono (500–600): Structured kickers, categories, status labels", font=sub_title_font, fill=TEXT_WHITE)
    draw.text((cw + 50, 295), "• 100% Bundled local TTF files (zero system font fallback)", font=sub_title_font, fill=ACCENT_GOLD)
    draw.text((cw + 50, 335), "• Full native support for PT-BR / ES-419 accented typography", font=sub_title_font, fill=ACCENT_GOLD)

    # Modern mock
    draw.rectangle([(cw + 50, 400), (1920 - 50, 980)], fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw_tag_pill(draw, cw + 70, 425, "● TRANSFER WATCH", get_token_font("categoryLabel"), bg=(20, 36, 56), fg=ACCENT_CYAN, border=ACCENT_CYAN)
    draw_tag_pill(draw, cw + 320, 425, "● STATUS: NOT AGREED", mono_font, bg=(60, 20, 24), fg=ACCENT_RED, border=ACCENT_RED)
    
    draw.text((cw + 70, 480), "ENDRICK TRANSFER BID DEVELOPING", font=get_token_font("primaryHeadlineCompact"), fill=TEXT_WHITE)
    draw.text((cw + 70, 560), "€60M", font=load_font("Barlow Condensed", 800, 84), fill=ACCENT_CYAN)
    draw.text((cw + 260, 595), "REPORTED BASE PROPOSAL", font=load_font("IBM Plex Mono", 500, 22), fill=TEXT_MUTED)
    
    # Modern subtitle card
    draw.rounded_rectangle([(cw + 70, 680), (1920 - 70, 800)], radius=12, fill=(14, 20, 36), outline=(40, 55, 85), width=1)
    draw.text((cw + 90, 705), "Milan are targeting Endrick, exploring an ambitious move.", font=load_font("Inter", 600, 32), fill=TEXT_WHITE)
    draw.text((cw + 90, 745), "for the twenty-year-old forward.", font=load_font("Inter", 600, 32), fill=TEXT_WHITE)

    draw.text((cw + 70, 850), "30 FOOTBALL PLUS • BROADCAST FOOTBALL INTELLIGENCE", font=load_font("Barlow Condensed", 700, 36), fill=TEXT_WHITE)
    draw.text((cw + 70, 910), "✅ Result: Authoritative 1990s/2000s Sky/BBC broadcast DNA for mobile vertical format", font=body_font, fill=ACCENT_CYAN)

    return comp


def generate_all_specimens(out_dir: Path) -> Dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    generated = {}

    print(f"Generating V7.1.3 Typography Specimens in {out_dir}...")

    # 1. English Specimens
    en_clean = draw_specimen_frame("en", diagnostic=False)
    p_en_clean = out_dir / "typography_specimen_en_clean.png"
    en_clean.save(str(p_en_clean), quality=95)
    generated["en_clean"] = p_en_clean
    print(f"  [OK] {p_en_clean.name}")

    en_diag = draw_specimen_frame("en", diagnostic=True)
    p_en_diag = out_dir / "typography_specimen_en_diagnostic.png"
    en_diag.save(str(p_en_diag), quality=95)
    generated["en_diagnostic"] = p_en_diag
    print(f"  [OK] {p_en_diag.name}")

    # 2. PT-BR Specimens
    pt_clean = draw_specimen_frame("pt_br", diagnostic=False)
    p_pt_clean = out_dir / "typography_specimen_pt_br_clean.png"
    pt_clean.save(str(p_pt_clean), quality=95)
    generated["pt_br_clean"] = p_pt_clean
    print(f"  [OK] {p_pt_clean.name}")

    pt_diag = draw_specimen_frame("pt_br", diagnostic=True)
    p_pt_diag = out_dir / "typography_specimen_pt_br_diagnostic.png"
    pt_diag.save(str(p_pt_diag), quality=95)
    generated["pt_br_diagnostic"] = p_pt_diag
    print(f"  [OK] {p_pt_diag.name}")

    # 3. ES-419 Specimens
    es_clean = draw_specimen_frame("es_419", diagnostic=False)
    p_es_clean = out_dir / "typography_specimen_es_419_clean.png"
    es_clean.save(str(p_es_clean), quality=95)
    generated["es_419_clean"] = p_es_clean
    print(f"  [OK] {p_es_clean.name}")

    es_diag = draw_specimen_frame("es_419", diagnostic=True)
    p_es_diag = out_dir / "typography_specimen_es_419_diagnostic.png"
    es_diag.save(str(p_es_diag), quality=95)
    generated["es_419_diagnostic"] = p_es_diag
    print(f"  [OK] {p_es_diag.name}")

    # 4. Before-and-After Comparison Sheet
    comp = draw_before_after_comparison()
    p_comp = out_dir / "typography_before_after_comparison.png"
    comp.save(str(p_comp), quality=95)
    generated["before_after_comparison"] = p_comp
    print(f"  [OK] {p_comp.name}")

    # 5. Multi-panel Master Showcase Sheet for Telegram
    # Compose 3 side-by-side sheets: [EN Clean] [EN Diagnostic] [PT-BR Clean] at 3240x1920 scaled to 2160x1280
    showcase = Image.new("RGBA", (1080 * 3, 1920), (*BG_BASE, 255))
    showcase.paste(en_clean, (0, 0))
    showcase.paste(en_diag, (1080, 0))
    showcase.paste(pt_clean, (2160, 0))
    # Downscale for crisp mobile delivery on Telegram
    showcase_tg = showcase.resize((2160, 1280), Image.Resampling.LANCZOS)
    p_showcase = out_dir / "master_typography_showcase_telegram.jpg"
    showcase_tg.convert("RGB").save(str(p_showcase), quality=92)
    generated["showcase_telegram"] = p_showcase
    print(f"  [OK] {p_showcase.name}")

    return generated


if __name__ == "__main__":
    out_directory = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "typography"
    generate_all_specimens(out_directory)
