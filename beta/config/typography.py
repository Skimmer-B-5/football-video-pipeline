"""
beta/config/typography.py

30 Football Plus — Permanent Central Typography Design System (Python Implementation)
Single source of truth for Pillow image generation, transfer cards, contact sheets,
and subtitle layout. Enforces strict resolution to local TTF files in beta/assets/fonts.

Font Families:
1. Barlow Condensed (600, 700, 800, 900)
2. Inter (400, 500, 600, 700, 800)
3. IBM Plex Mono (500, 600)
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from PIL import ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

FONT_FAMILIES = {
    "DISPLAY": "Barlow Condensed",
    "READING": "Inter",
    "MONO": "IBM Plex Mono",
}

# Exact local TTF mappings
FONT_FILES: Dict[Tuple[str, int], Path] = {
    # Barlow Condensed
    ("Barlow Condensed", 600): FONTS_DIR / "barlow_condensed" / "BarlowCondensed-SemiBold.ttf",
    ("Barlow Condensed", 700): FONTS_DIR / "barlow_condensed" / "BarlowCondensed-Bold.ttf",
    ("Barlow Condensed", 800): FONTS_DIR / "barlow_condensed" / "BarlowCondensed-ExtraBold.ttf",
    ("Barlow Condensed", 900): FONTS_DIR / "barlow_condensed" / "BarlowCondensed-Black.ttf",

    # Inter
    ("Inter", 400): FONTS_DIR / "inter" / "Inter-Regular.ttf",
    ("Inter", 500): FONTS_DIR / "inter" / "Inter-Medium.ttf",
    ("Inter", 600): FONTS_DIR / "inter" / "Inter-SemiBold.ttf",
    ("Inter", 700): FONTS_DIR / "inter" / "Inter-Bold.ttf",
    ("Inter", 800): FONTS_DIR / "inter" / "Inter-ExtraBold.ttf",

    # IBM Plex Mono
    ("IBM Plex Mono", 500): FONTS_DIR / "ibm_plex_mono" / "IBMPlexMono-Medium.ttf",
    ("IBM Plex Mono", 600): FONTS_DIR / "ibm_plex_mono" / "IBMPlexMono-SemiBold.ttf",
}

# Safe zone boundaries in 1080x1920 space
SAFE_ZONES = {
    "canvas_width": 1080,
    "canvas_height": 1920,
    "margin_horizontal_min": 72,
    "margin_horizontal_preferred": 84,
    "brand_identifier_y": (100, 180),
    "primary_headline_y": (240, 580),
    "supporting_info_y": (1080, 1320),
    "subtitle_y": (1390, 1600),
    "avoid_below_y": 1640,
}

# Semantic typography tokens
TYPOGRAPHY_TOKENS: Dict[str, Dict[str, Any]] = {
    "brandMark": {
        "family": "Barlow Condensed",
        "weight": 700,
        "size": 62,
        "line_height": 1.0,
        "text_transform": "uppercase",
        "color": (255, 255, 255, 255),
        "description": "30 Football Plus primary broadcast wordmark"
    },
    "breakingKicker": {
        "family": "IBM Plex Mono",
        "weight": 600,
        "size": 24,
        "line_height": 1.15,
        "letter_spacing": 1.4,
        "text_transform": "uppercase",
        "color": (250, 204, 21, 255),  # Yellow
        "description": "Breaking news status kicker capsule"
    },
    "categoryLabel": {
        "family": "IBM Plex Mono",
        "weight": 600,
        "size": 24,
        "line_height": 1.15,
        "letter_spacing": 1.2,
        "text_transform": "uppercase",
        "color": (56, 189, 248, 255),  # Cyan
        "description": "Story category pill"
    },
    "primaryHeadline": {
        "family": "Barlow Condensed",
        "weight": 800,
        "size": 78,
        "line_height": 0.98,
        "max_lines": 2,
        "text_transform": "uppercase",
        "color": (255, 255, 255, 255),
        "description": "Main news headline for vertical 9:16 canvas"
    },
    "primaryHeadlineCompact": {
        "family": "Barlow Condensed",
        "weight": 800,
        "size": 66,
        "line_height": 0.98,
        "max_lines": 2,
        "text_transform": "uppercase",
        "color": (255, 255, 255, 255),
        "description": "Condensed headline for longer phrases (>35 characters)"
    },
    "playerReveal": {
        "family": "Barlow Condensed",
        "weight": 800,
        "size": 92,
        "line_height": 0.95,
        "max_lines": 1,
        "text_transform": "uppercase",
        "color": (250, 204, 21, 255),  # Yellow
        "description": "Subject name reveal when focal player appears"
    },
    "supportingHeadline": {
        "family": "Inter",
        "weight": 600,
        "size": 36,
        "line_height": 1.12,
        "max_lines": 2,
        "text_transform": "none",
        "color": (226, 232, 240, 255),
        "description": "Contextual subheadline beneath main headline"
    },
    "narrationSubtitle": {
        "family": "Inter",
        "weight": 600,
        "size": 46,
        "line_height": 1.16,
        "max_lines": 2,
        "max_chars_per_line": 36,
        "text_transform": "none",
        "color": (255, 255, 255, 255),
        "description": "Sentence-case narration subtitles aligned to speech"
    },
    "statisticHero": {
        "family": "Barlow Condensed",
        "weight": 800,
        "size": 124,
        "line_height": 0.92,
        "max_lines": 1,
        "text_transform": "uppercase",
        "color": (56, 189, 248, 255),  # Cyan
        "description": "Large hero statistic or transfer value (e.g. €60M)"
    },
    "statisticLabel": {
        "family": "IBM Plex Mono",
        "weight": 500,
        "size": 26,
        "line_height": 1.15,
        "text_transform": "uppercase",
        "color": (148, 163, 184, 255),
        "description": "Technical label accompanying hero statistic"
    },
    "lowerThird": {
        "family": "Inter",
        "weight": 600,
        "size": 36,
        "line_height": 1.15,
        "max_lines": 2,
        "text_transform": "none",
        "color": (255, 255, 255, 255),
        "description": "Two-tier broadcast lower-third headline"
    },
    "tickerText": {
        "family": "Inter",
        "weight": 600,
        "size": 30,
        "line_height": 1.1,
        "text_transform": "uppercase",
        "color": (255, 255, 255, 255),
        "description": "Continuous rolling news ticker channel"
    },
    "sourceMetadata": {
        "family": "IBM Plex Mono",
        "weight": 500,
        "size": 20,
        "line_height": 1.15,
        "text_transform": "uppercase",
        "color": (100, 116, 139, 255),
        "description": "Source attribution, wire provenance & timecodes"
    },
    "outroHeadline": {
        "family": "Barlow Condensed",
        "weight": 700,
        "size": 64,
        "line_height": 1.0,
        "text_transform": "uppercase",
        "color": (255, 255, 255, 255),
        "description": "Outro closing plate headline"
    },
    "outroCTA": {
        "family": "Inter",
        "weight": 600,
        "size": 26,
        "line_height": 1.2,
        "text_transform": "none",
        "color": (148, 163, 184, 255),
        "description": "Outro call to action and social handles"
    }
}

# Telegram Contact Sheet Scale (1920-wide canvas)
TELEGRAM_CHART_TYPOGRAPHY = {
    "chartTitle": {"family": "Barlow Condensed", "weight": 700, "size": 36},
    "storyHeadline": {"family": "Barlow Condensed", "weight": 700, "size": 34},
    "sceneHeading": {"family": "Barlow Condensed", "weight": 700, "size": 26},
    "dialogueText": {"family": "Inter", "weight": 600, "size": 25},
    "visualDescription": {"family": "Inter", "weight": 400, "size": 22},
    "metadata": {"family": "IBM Plex Mono", "weight": 500, "size": 19},
    "statusLabel": {"family": "IBM Plex Mono", "weight": 600, "size": 20},
}


def get_font_file(family: str, weight: int) -> Path:
    """Resolves local font file path. Raises FileNotFoundError if missing."""
    key = (family, weight)
    if key not in FONT_FILES:
        # Fallback to closest weight within family
        weights = [w for (f, w) in FONT_FILES.keys() if f == family]
        if not weights:
            raise KeyError(f"Unsupported font family: '{family}'")
        closest_w = min(weights, key=lambda w: abs(w - weight))
        key = (family, closest_w)

    path = FONT_FILES[key]
    if not path.exists():
        raise FileNotFoundError(
            f"Mandatory font file missing: {path}. "
            f"Run 'beta/stages/setup_official_font_collection.py' to download official fonts."
        )
    return path


def load_font(family: str, weight: int, size: int) -> ImageFont.FreeTypeFont:
    """Loads a FreeType font object directly from local TTF assets."""
    font_path = get_font_file(family, weight)
    return ImageFont.truetype(str(font_path), size=size)


def get_token_font(token_name: str, size_override: Optional[int] = None) -> ImageFont.FreeTypeFont:
    """Loads font configured for a semantic token."""
    if token_name not in TYPOGRAPHY_TOKENS:
        raise KeyError(f"Unknown typography token: '{token_name}'")
    cfg = TYPOGRAPHY_TOKENS[token_name]
    size = size_override if size_override is not None else cfg["size"]
    return load_font(cfg["family"], cfg["weight"], size)


def get_chart_font(element_name: str, size_override: Optional[int] = None) -> ImageFont.FreeTypeFont:
    """Loads font configured for Telegram Scene Chart elements."""
    if element_name not in TELEGRAM_CHART_TYPOGRAPHY:
        raise KeyError(f"Unknown chart typography element: '{element_name}'")
    cfg = TELEGRAM_CHART_TYPOGRAPHY[element_name]
    size = size_override if size_override is not None else cfg["size"]
    return load_font(cfg["family"], cfg["weight"], size)
