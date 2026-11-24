"""
config/design_tokens.py - Single Source of Truth for Visual Design, Layout & Audio Tokens.

Coordinates, safe zones, color palette, typography, CRT effects, and audio mastering
used uniformly across the Python video assembler, Remotion renderer, and QA engine.
Defines the iconic late-1990s / early-2000s football television broadcast aesthetic
(Sky Sports / BBC Sport DNA) optimized for vertical 9:16 mobile formats.
"""

from typing import Dict, Any, Tuple

# 1. Canvas Dimensions & Timing
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
FPS = 30.0
ASPECT_RATIO = "9:16"

# 2. Platform Safe Margins (YouTube Shorts, TikTok, Instagram Reels)
SAFE_MARGIN_TOP = 80
SAFE_MARGIN_BOTTOM = 90
SAFE_MARGIN_LEFT = 55
SAFE_MARGIN_RIGHT = 55

# 3. Layout Coordinates (Strictly anchored in 1080x1920 space)
LAYOUT_TOKENS = {
    # Top-Left Channel Bug (User's Bezel Logo)
    "logo_bug": {
        "x": 55,
        "y": 80,
        "width": 115,
        "height": 105,
        "z_index": 60,
    },
    # Top-Right Truthful Status Kicker Capsule (e.g. ● TRANSFER WATCH or ● NEWS UPDATE)
    "status_kicker": {
        "x": 750,
        "y": 95,
        "width": 275,
        "height": 64,
        "z_index": 60,
    },
    # Central Photographic Stage (leaves 1130px height of unobstructed view)
    "stage": {
        "top": 210,
        "bottom": 1380,
        "left": 55,
        "right": 1025,
        "z_index": 20,
    },
    # Synchronized Subtitles / Captions (Positioned safely above lower third)
    "subtitles": {
        "y": 1300,
        "max_width": 940,
        "safe_bottom": 540,  # 1920 - 540 = 1380px
        "font_size": 38,
        "z_index": 45,
    },
    # Two-Tier Broadcast Lower-Third News Panel
    "lower_third": {
        "x": 60,
        "y": 1440,
        "width": 960,       # x: 60 to 1020
        "height": 200,      # y: 1440 to 1640
        "accent_bar_w": 14, # Left gold accent bar width
        "gold_bar_x": 60,
        "gold_bar_w": 14,
        "kicker_tag_y": 1380,
        "kicker_tag_h": 55,
        "z_index": 40,
    },
    # Rolling Factual News Ticker (LOWERED to bottom: 90px above mobile bottom interface)
    "ticker": {
        "x": 0,
        "y": 1730,          # Resting at y=1730, height=110, ending at y=1840 (leaving 80px bottom safe margin)
        "width": 1080,
        "height": 110,
        "tab_width": 275,   # Red HEADLINES tab width
        "track_x": 295,     # Ticker text channel starts at x=295 (clean 20px slant buffer)
        "track_width": 785, # 1080 - 295 = 785px
        "scroll_speed_px_per_frame": 4.5,
        "z_index": 50,
    },
    # Outro Branding Plate
    "outro": {
        "logo_size": 260,
        "logo_y": 740,
        "title_y": 1050,
        "follow_card_y": 1140,
        "z_index": 90,
    }
}

# 4. Color Palette Tokens
COLOR_TOKENS = {
    # Dark Navy Broadcast Panels
    "navy_primary": (11, 19, 43, 255),
    "navy_card": (0, 22, 60, 248),
    "navy_light": (28, 37, 65, 255),
    "navy_ticker": (10, 16, 42, 250),

    # News Red Accents
    "red_news": (217, 4, 41, 255),
    "red_dark": (155, 0, 20, 255),
    "red_glow": (217, 4, 41, 128),

    # Gold / Yellow Typography Highlights
    "yellow_gold": (255, 215, 0, 255),
    "yellow_highlight": (255, 209, 102, 255),
    "yellow_ticker": (255, 215, 0, 255),

    # Monochromes
    "white": (255, 255, 255, 255),
    "off_white": (240, 244, 248, 255),
    "text_muted": (160, 195, 240, 240),
    "black": (0, 0, 0, 255),
}

# 5. Typography Hierarchy
TYPOGRAPHY_TOKENS = {
    "font_headline": "BarlowCondensed-ExtraBold.ttf",
    "font_ticker": "BarlowCondensed-Bold.ttf",
    "font_caption": "BarlowCondensed-ExtraBold.ttf",
    "sizes": {
        "headline_line1": 46,
        "headline_line2": 44,
        "subheadline": 32,
        "kicker_badge": 24,
        "ticker_text": 32,
        "caption_primary": 38,
        "outro_follow": 42,
        "outro_sub": 26,
    }
}

# 6. CRT & Analog Broadcast Effects (Restrained Retro TV Aesthetic - No muddying, no text blur)
CRT_TOKENS = {
    "scanline_opacity": 0.06,  # Subtle analog broadcast scanline texture (never heavy black bars)
    "grain_intensity": 1.2,
    "chromatic_aberration": "", # Chromatic fringing eliminated for tack-sharp typography
    "color_balance": "colorbalance=rs=0.01:gs=0.01:bs=-0.01",
    "noise_filter": "noise=alls=1.2:allf=t+u",
    "phosphor_softness": "contrast(1.02) brightness(0.99) saturate(1.02)",
}

# 7. Audio Production & Mastering Constants
AUDIO_TOKENS = {
    "sample_rate": 48000,
    "channels": 2,  # Stereo
    "sample_format": "pcm_s16le",
    "target_lufs": -14.0,
    "lufs_tolerance": 1.0,
    "true_peak_ceiling": -1.0,  # dBTP
    "lra": 7.0,
    "words_per_second_target": 2.6,
    
    # Breathing Room & Transition Padding
    "scene_tail_pad_sec": 0.15,
    "scene_final_hold_sec": 0.25,     # Crisp 0.25s breath on final photo before outro
    "outro_max_dur_sec": 2.0,        # Outro plate strictly capped under 2.0s
    "master_fadeout_sec": 0.35,      # Clean final audio fadeout
}

# 8. Pacing & Narrative Rhythm Guidelines
PACING_TOKENS = {
    "target_duration_min": 24.0,
    "target_duration_max": 30.0,
    "target_word_count_min": 60,
    "target_word_count_max": 76,
    "visual_beat_interval_sec": (2.0, 4.0), # Visual change every 2-4 seconds
    "attention_reset_interval_sec": (8.0, 10.0), # Major reveal / interruption every 8-10 seconds
}
