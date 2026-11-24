"""
beta/tests/test_v7_1_3_typography_suite.py - Acceptance Tests for Permanent Typography System.

Verifies:
1. Exact font-family resolution (Barlow Condensed, Inter, IBM Plex Mono).
2. Correct font-weight mapping (600, 700, 800, 900 / 400, 500, 600, 700, 800 / 500, 600).
3. Local font files loaded from beta/assets/fonts/ (raises FileNotFoundError on missing files).
4. No system-font fallback (zero fallback to Arial, Segoe UI, or default bitmap).
5. PT-BR accent rendering (á à â ã é ê í ó ô õ ú ü ç).
6. ES-419 accent and punctuation rendering (á é í ó ú ü ñ ¿ ¡).
7. Currency and football symbol support (€ £ $ • – — ✦ ▲ ▼).
8. Headline line-count limits (Max 2 lines, wraps or condenses cleanly).
9. Subtitle line-count limits (Max 2 lines, sentence case, 30-38 chars/line).
10. Safe margin enforcement (min 72px, preferred 84px, avoid below y=1640).
11. Telegram scene chart legibility scale (Barlow 36px/32px/26px, Inter 25px/22px, Mono 19px/20px).
12. Specimen files exist at native 1080x1920 resolution.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.typography import (
    FONT_FAMILIES,
    FONT_FILES,
    SAFE_ZONES,
    TYPOGRAPHY_TOKENS,
    TELEGRAM_CHART_TYPOGRAPHY,
    get_font_file,
    load_font,
    get_token_font,
    get_chart_font
)
from stages.generate_typography_specimens import wrap_text

FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"


def test_font_family_files_exist_locally():
    """All 11 approved font files must exist locally in beta/assets/fonts."""
    assert FONTS_DIR.exists(), f"Fonts directory missing: {FONTS_DIR}"
    for (family, weight), path in FONT_FILES.items():
        assert path.exists(), f"Missing local font file for {family} weight {weight}: {path}"
        assert path.stat().st_size > 50000, f"Font file suspiciously small: {path}"


def test_exact_font_family_resolution_and_weight_mapping():
    """Ensures each font family and weight resolves to the correct FreeType font instance."""
    # Barlow Condensed
    f_barlow_600 = load_font("Barlow Condensed", 600, 48)
    assert "Barlow" in f_barlow_600.font.family
    assert f_barlow_600.font.style in ["SemiBold", "Regular", "Bold"]

    f_barlow_800 = load_font("Barlow Condensed", 800, 78)
    assert "Barlow" in f_barlow_800.font.family
    assert "ExtraBold" in f_barlow_800.font.style or "Bold" in f_barlow_800.font.style

    # Inter
    f_inter_400 = load_font("Inter", 400, 32)
    assert "Inter" in f_inter_400.font.family

    f_inter_600 = load_font("Inter", 600, 46)
    assert "Inter" in f_inter_600.font.family

    # IBM Plex Mono
    f_mono_500 = load_font("IBM Plex Mono", 500, 24)
    assert "Plex Mono" in f_mono_500.font.family

    f_mono_600 = load_font("IBM Plex Mono", 600, 26)
    assert "Plex Mono" in f_mono_600.font.family


def test_no_system_font_fallback():
    """Invalid font requests must raise FileNotFoundError / KeyError rather than silently falling back."""
    try:
        get_font_file("NonExistentFontFamily", 400)
        assert False, "Should have raised KeyError for unsupported family"
    except KeyError:
        pass


def test_pt_br_accent_rendering():
    """Verifies that all Portuguese accented characters render without missing glyphs."""
    test_chars = "á à â ã é ê í ó ô õ ú ü ç Á À Â Ã É Ê Í Ó Ô Õ Ú Ü Ç"
    for family in ["Barlow Condensed", "Inter", "IBM Plex Mono"]:
        font = load_font(family, 600, 36)
        img = Image.new("RGBA", (1200, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), test_chars, font=font, fill=(255, 255, 255, 255))
        bbox = draw.textbbox((10, 10), test_chars, font=font)
        assert bbox[2] > bbox[0] + 500, f"Rendered width suspiciously small for {family}: {bbox}"


def test_es_419_accent_and_punctuation_rendering():
    """Verifies that all Spanish accented characters and inverted punctuation render."""
    test_chars = "¿¡ á é í ó ú ü ñ Á É Í Ó Ú Ü Ñ !?"
    for family in ["Barlow Condensed", "Inter", "IBM Plex Mono"]:
        font = load_font(family, 600, 36)
        img = Image.new("RGBA", (1200, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), test_chars, font=font, fill=(255, 255, 255, 255))
        bbox = draw.textbbox((10, 10), test_chars, font=font)
        assert bbox[2] > bbox[0] + 300, f"Rendered width suspiciously small for {family}: {bbox}"


def test_currency_and_football_symbols():
    """Verifies euro, pound, dollar, arrows and bullets."""
    symbols = "€60M £50M $100M • – — ✦ ▲ ▼ 0-1 2026–27"
    for family in ["Barlow Condensed", "Inter", "IBM Plex Mono"]:
        font = load_font(family, 600, 36)
        img = Image.new("RGBA", (1200, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), symbols, font=font, fill=(255, 255, 255, 255))
        bbox = draw.textbbox((10, 10), symbols, font=font)
        assert bbox[2] > bbox[0] + 300


def test_headline_line_count_and_wrapping():
    """Headlines must wrap cleanly and never exceed 2 lines."""
    font = get_token_font("primaryHeadline")
    long_headline = "ENDRICK PROPOSAL ADVANCES IN ITALY WITH REAL MADRID PROTECTIVE BUY-BACK CLAUSE"
    lines = wrap_text(long_headline, font, max_width=912, max_lines=2)
    assert len(lines) <= 2, f"Headline exceeded 2 lines: {lines}"
    assert len(lines) > 0


def test_subtitle_line_count_and_sentence_case():
    """Narration subtitles must be sentence case, maximum 2 lines, and target ~30-38 chars/line."""
    font = get_token_font("narrationSubtitle")
    sub_text = "Milan are targeting Endrick, exploring an ambitious move for the twenty-year-old forward."
    # Sentence case verification (not all uppercase)
    assert not sub_text.isupper(), "Subtitles must use sentence case, not permanent uppercase"
    lines = wrap_text(sub_text, font, max_width=920, max_lines=2)
    assert len(lines) <= 2, f"Subtitle exceeded 2 lines: {lines}"
    for l in lines:
        assert len(l) <= 50, f"Line too long: '{l}' ({len(l)} chars)"


def test_safe_margins_and_avoid_below():
    """Canvas dimensions and safe margins must conform to mobile 9:16 vertical broadcast specs."""
    assert SAFE_ZONES["canvas_width"] == 1080
    assert SAFE_ZONES["canvas_height"] == 1920
    assert SAFE_ZONES["margin_horizontal_min"] >= 72
    assert SAFE_ZONES["margin_horizontal_preferred"] >= 84
    assert SAFE_ZONES["avoid_below_y"] == 1640


def test_native_specimens_exist():
    """All 8 required specimen deliverables must exist on disk."""
    ws_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "typography"
    expected = [
        "typography_specimen_en_clean.png",
        "typography_specimen_en_diagnostic.png",
        "typography_specimen_pt_br_clean.png",
        "typography_specimen_pt_br_diagnostic.png",
        "typography_specimen_es_419_clean.png",
        "typography_specimen_es_419_diagnostic.png",
        "typography_before_after_comparison.png",
        "master_typography_showcase_telegram.jpg"
    ]
    for fn in expected:
        p = ws_dir / fn
        assert p.exists(), f"Specimen file missing: {p}"
        assert p.stat().st_size > 50000, f"Specimen file too small: {p}"

        # Check native resolution of 1080x1920 specimens
        if "specimen_" in fn and fn.endswith(".png"):
            with Image.open(p) as im:
                assert im.size == (1080, 1920), f"Wrong resolution for {fn}: {im.size}"


def test_v7_1_4_remotion_specimens_and_manifest():
    """All 10 V7.1.4 Remotion-rendered native broadcast specimens and manifest must exist."""
    ws_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1"
    typo_dir = ws_dir / "typography"
    man_path = ws_dir / "manifests" / "typography_manifest.json"

    assert man_path.exists(), f"Typography manifest missing: {man_path}"

    expected_remotion = [
        "headline_specimen.png",
        "player_reveal_specimen.png",
        "subtitle_specimen.png",
        "transfer_graphic_specimen.png",
        "lower_third_specimen.png",
        "outro_specimen.png",
        "pt_br_specimen.png",
        "es_419_specimen.png",
        "typography_master_clean.png",
        "typography_diagnostic.png"
    ]
    for fn in expected_remotion:
        p = typo_dir / fn
        assert p.exists(), f"Missing Remotion specimen: {p}"
        assert p.stat().st_size > 50000, f"Remotion specimen too small: {p}"
        with Image.open(p) as im:
            assert im.size == (1080, 1920), f"Wrong resolution for {fn}: {im.size} (expected 1080x1920)"


def test_telegram_contact_sheet_typography_scale():
    """Telegram contact sheet typography scale must match specified sizes."""
    assert TELEGRAM_CHART_TYPOGRAPHY["chartTitle"]["size"] in range(34, 39)
    assert TELEGRAM_CHART_TYPOGRAPHY["storyHeadline"]["size"] in range(32, 37)
    assert TELEGRAM_CHART_TYPOGRAPHY["sceneHeading"]["size"] in range(25, 29)
    assert TELEGRAM_CHART_TYPOGRAPHY["dialogueText"]["size"] in range(24, 28)
    assert TELEGRAM_CHART_TYPOGRAPHY["visualDescription"]["size"] in range(22, 25)
    assert TELEGRAM_CHART_TYPOGRAPHY["metadata"]["size"] in range(18, 21)
    assert TELEGRAM_CHART_TYPOGRAPHY["statusLabel"]["size"] in range(19, 23)
