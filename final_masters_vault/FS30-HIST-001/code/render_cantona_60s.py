"""
60-Second Eric Cantona Kung-Fu Kick Documentary Renderer (Master Production 2.0).
Features:
- Exact 60.0s duration (1,800 frames @ 30 FPS)
- ZERO vertical or horizontal distortion: strictly uniform proportional scaling
  with intentional focus-centered cropping across all photographs and cutouts
- Genuine Archival GIF Animation: 17-frame Sky Sports broadcast footage loop of the
  iconic kick, synchronized to start precisely at narration impact cue (tb >= 3.8s)
- 5 Genuinely Distinct Reusable Banner Variants (Variants A, B, C, D, E)
- Rich Tactile Collage: Daily Mirror front page clipping, vintage ticket stubs,
  inked rubber stamp slams for court verdicts, animated neon highlighter wipes
- Desaturated multiplane stadium backgrounds (-65% saturation, -30% brightness)
- 150px persistent FS30 TV broadcast watermark
- Dedicated broadcast outro card synchronized with spoken farewell:
  "See you later. This is Football in 30 Seconds. Follow for more."
- Multi-threaded batch rendering and FFmpeg master encoding
"""

import sys
import os
import math
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
import numpy as np
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT))

RUN_DIR = PROJECT_ROOT / "runs" / "cantona_kungfu_kick_story"
ASSETS_DIR = RUN_DIR / "assets"
RAW_DIR = ASSETS_DIR / "raw"
CUTOUT_DIR = RUN_DIR / "cutouts"
ARCHIVE_DIR = ASSETS_DIR / "archival_footage"
LOOP_FRAMES_DIR = ARCHIVE_DIR / "loop_frames"
FRAMES_DIR = RUN_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")

from fs30.story_pipeline.branding import create_fs30_tv_watermark, render_fs30_outro
from fs30.story_pipeline.paper_widgets import (
    create_torn_headline_banner,
    create_torn_quote_card,
    create_torn_match_ticket,
    create_torn_caption_ribbon,
    get_font,
    WARM_IVORY,
    CHARCOAL,
    ARCHIVAL_RED,
    MUSTARD_GOLD,
    MUTED_SLATE
)
from fs30.story_pipeline.photo_mounter import mount_archival_photo, scale_cutout_proportional
from fs30.story_pipeline.mrbeast_captions import init_captions, draw_mrbeast_captions
init_captions(RUN_DIR / "cantona_mrbeast_captions.json")

# Colors
FLUORESCENT_YELLOW = (255, 235, 59, 140)
TARGET_RED = (220, 20, 60, 240)

# Load TV Watermark
TV_WATERMARK = create_fs30_tv_watermark(badge_size=150)

_LOADED_IMAGES: Dict[str, Image.Image] = {}

def get_image(path: Path) -> Image.Image:
    k = str(path)
    if k not in _LOADED_IMAGES:
        with Image.open(path) as im:
            _LOADED_IMAGES[k] = im.convert("RGBA")
    return _LOADED_IMAGES[k]

def prepare_background(img_path: Path, width: int = 1080, height: int = 1920) -> Image.Image:
    """Processes background: desaturate by 65%, lower brightness by 30%, slight vignette."""
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = max(width / w, height / h)
        nw, nh = int(w * scale), int(h * scale)
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        x_off = (nw - width) // 2
        y_off = (nh - height) // 2
        cropped = im.crop((x_off, y_off, x_off + width, y_off + height))
        
        enh_color = ImageEnhance.Color(cropped)
        desat = enh_color.enhance(0.35)
        enh_bright = ImageEnhance.Brightness(desat)
        darkened = enh_bright.enhance(0.68)
        blurred = darkened.filter(ImageFilter.GaussianBlur(1.8))
        
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        v_draw.rectangle([(0, 0), (width, height)], fill=(10, 12, 18, 110))
        v_draw.rectangle([(0, 0), (width, 240)], fill=(8, 10, 14, 140))
        v_draw.rectangle([(0, height - 260), (width, height)], fill=(8, 10, 14, 150))
        
        res = blurred.convert("RGBA")
        res.paste(vignette, (0, 0), mask=vignette)
        return res

def draw_tactical_annotation(canvas: Image.Image, x: int, y: int, radius: int, label: str, t_progress: float):
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    pulse = 1.0 + 0.08 * math.sin(t_progress * math.pi * 4)
    r = int(radius * pulse)
    
    draw.ellipse([(x - r, y - r), (x + r, y + r)], outline=(220, 20, 60, 230), width=4)
    draw.ellipse([(x - r + 8, y - r + 8), (x + r - 8, y + r - 8)], outline=(255, 235, 59, 210), width=2)
    draw.line([(x - r - 12, y), (x + r + 12, y)], fill=(220, 20, 60, 240), width=2)
    draw.line([(x, y - r - 12), (x, y + r + 12)], fill=(220, 20, 60, 240), width=2)
    
    f_lbl = get_font("headline_bold", 26)
    bbox = f_lbl.getbbox(label.upper())
    lbl_w = bbox[2] - bbox[0] + 32
    lbl_h = bbox[3] - bbox[1] + 18
    
    bx = x - lbl_w // 2
    by = y + r + 14
    draw.rectangle([(bx, by), (bx + lbl_w, by + lbl_h)], fill=(18, 20, 26, 240), outline=(220, 20, 60, 255), width=2)
    draw.text((bx + 16, by + 6), label.upper(), fill=(255, 255, 255, 255), font=f_lbl)
    
    canvas.paste(overlay, (0, 0), mask=overlay)

def draw_rubber_stamp(canvas: Image.Image, stamp_id: str, center_x: int, center_y: int, progress: float):
    """Draws procedural rubber stamp with elastic slam physics."""
    if progress <= 0:
        return
        
    if progress < 0.6:
        p_norm = progress / 0.6
        scale = 1.35 - 0.41 * (math.sin(p_norm * math.pi / 2))
        alpha = int(255 * p_norm)
    else:
        p_settle = (progress - 0.6) / 0.4
        scale = 0.94 + 0.06 * math.sin(p_settle * math.pi / 2)
        alpha = 255

    stamp_path = PROJECT_ROOT / "fs30" / "story_pipeline" / "assets" / "reusable_stock" / "stamps" / f"{stamp_id}.png"
    if not stamp_path.exists():
        return
        
    stamp_raw = get_image(stamp_path)
    cur_w = int(stamp_raw.size[0] * scale)
    cur_h = int(stamp_raw.size[1] * scale)
    scaled = stamp_raw.resize((cur_w, cur_h), Image.Resampling.LANCZOS)
    rotated = scaled.rotate(-5.5, expand=True, resample=Image.Resampling.BICUBIC)
    
    pos_x = center_x - rotated.size[0] // 2
    pos_y = center_y - rotated.size[1] // 2
    canvas.paste(rotated, (pos_x, pos_y), mask=rotated.split()[-1])

def apply_neon_highlighter_wipe(canvas: Image.Image, box: Tuple[int, int, int, int], wipe_progress: float):
    x, y, w, h = box
    cur_w = int(w * min(1.0, max(0.0, wipe_progress)))
    if cur_w <= 0:
        return
        
    hl_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    hl_draw = ImageDraw.Draw(hl_layer)
    hl_draw.rounded_rectangle([(x, y), (x + cur_w, y + h)], radius=6, fill=FLUORESCENT_YELLOW)
    
    canvas_np = np.array(canvas, dtype=np.float32)
    hl_np = np.array(hl_layer, dtype=np.float32)
    
    alpha = hl_np[:, :, 3:4] / 255.0
    tint = np.array([255, 235, 59], dtype=np.float32)
    for c in range(3):
        canvas_np[:, :, c] = (1.0 - alpha[:, :, 0] * 0.45) * canvas_np[:, :, c] + (alpha[:, :, 0] * 0.45) * (canvas_np[:, :, c] * tint[c] / 255.0)
        
    res = Image.fromarray(np.clip(canvas_np, 0, 255).astype(np.uint8))
    canvas.paste(res, (0, 0))

# Pre-render Backgrounds
BG_CACHE = {}
def get_cached_bg(key: str) -> Image.Image:
    if key not in BG_CACHE:
        bg_paths = {
            "selhurst_floodlit": ASSETS_DIR / "selhurst_park_1995_floodlit.jpg",
            "selhurst_terrace": RAW_DIR / "bg_selhurst_terrace_0.jpg",
            "selhurst_crowd": RAW_DIR / "bg_selhurst_terrace_1.jpg",
            "croydon_court": RAW_DIR / "bg_croydon_court_0.jpg",
            "press_room": RAW_DIR / "bg_press_room_0.jpg",
            "old_trafford": ASSETS_DIR / "selhurst_park_1995_floodlit.jpg"
        }
        p = bg_paths.get(key, bg_paths["selhurst_floodlit"])
        BG_CACHE[key] = prepare_background(p)
    return BG_CACHE[key]

# Pre-render 5 Genuinely Distinct Banner Variants & Widgets
print("Pre-rendering components with 5 distinct banner variants...")

# Beat 1: Variant A (Torn Newspaper Edge with Red Side Stripe)
W_HEAD_B1 = create_torn_headline_banner("THE BOILING POT", kicker="25 JAN 1995 // SELHURST PARK", width=960, height=210, variant="a")
W_TICKET_B1 = create_torn_match_ticket("PREMIER LEAGUE", "CRYSTAL PALACE VS MAN UNITED", "25 JAN 1995", width=520, height=170)
W_RIBBON_B1 = create_torn_caption_ribbon(["FORTY-EIGHT", "MINUTES", "OF", "RELENTLESS", "PROVOCATION."], active_idx=3, width=960, height=110)

# Beat 2: Variant B (Folded Ivory Paper with Thin Red Marker)
W_HEAD_B2 = create_torn_headline_banner("THE RED CARD", kicker="48TH MINUTE // ALAN WILKIE", width=960, height=210, variant="b")
W_RIBBON_B2 = create_torn_caption_ribbon(["A", "STREAM", "OF", "UNCHECKED", "VILE", "ABUSE."], active_idx=4, width=960, height=110)

# Beat 3: Variant C (Rough-Cut Archival Paper with Red Corner Tab)
W_HEAD_B3 = create_torn_headline_banner("THE KUNG-FU KICK", kicker="SELHURST HOARDINGS // UNPRECEDENTED", width=980, height=210, variant="c")
W_RIBBON_B3 = create_torn_caption_ribbon(["AN", "AIRBORNE", "STUDS-FIRST", "IMPACT", "SHATTERS", "FOOTBALL."], active_idx=3, width=980, height=110, font_size=42)

# Beat 4: Variant D (Narrow Editorial Strip with Distressed Red Underline)
W_HEAD_B4 = create_torn_headline_banner("CRIMINAL CONVICTION", kicker="CROYDON MAGISTRATES // FA VERDICT", width=960, height=210, variant="d")
W_QUOTE_B4 = create_torn_quote_card(
    "Croydon Magistrates sentences Cantona to two weeks prison, commuted to 120 hours community service.",
    attribution="— CROYDON MAGISTRATES // FA 1995",
    width=500, height=440, quote_size=30, attr_size=18
)
W_RIBBON_B4 = create_torn_caption_ribbon(["EIGHT", "MONTHS", "BANISHED", "FROM", "WORLD", "FOOTBALL."], active_idx=2, width=960, height=110)

# Beat 5: Variant E (Layered Paper with Offset Red Backing)
W_HEAD_B5 = create_torn_headline_banner("SEAGULLS & SARDINES", kicker="DOVER HOUSE // 31 MARCH 1995", width=960, height=210, variant="e")
W_QUOTE_B5 = create_torn_quote_card(
    "When the seagulls follow the trawler, it is because they think sardines will be thrown into the sea. Thank you very much.",
    attribution="— ERIC CANTONA, 1995 PRESS CONFERENCE",
    width=960, height=380, quote_size=38, attr_size=26
)
W_RIBBON_B5 = create_torn_caption_ribbon(["FIFTEEN", "CRYPTIC", "WORDS", "THAT", "CEMENTED", "A", "MYTH."], active_idx=4, width=960, height=110)

# Beat 6: Variant E (Climactic Declaration)
W_HEAD_B6 = create_torn_headline_banner("THE KING RETURNS", kicker="OCTOBER 1995 // OLD TRAFFORD", width=960, height=210, variant="e")
W_TICKET_B6 = create_torn_match_ticket("PREMIER LEAGUE RETURN", "MAN UNITED 2-2 LIVERPOOL", "01 OCT 1995", width=540, height=170)
W_RIBBON_B6 = create_torn_caption_ribbon(["LONG", "LIVE", "THE", "KING."], active_idx=2, width=820, height=110)

# Pre-render Archival GIF Animation Frame Sequence
ARCHIVE_PANELS: List[Image.Image] = []
loop_files = sorted(LOOP_FRAMES_DIR.glob("kick_loop_*.jpg"))
if loop_files:
    f_arch = get_font("headline_bold", 20)
    for lf in loop_files:
        with Image.open(lf) as lim:
            lw, lh = lim.size
            pad_t, pad_b, pad_s = 40, 20, 16
            card_w = lw + pad_s * 2
            card_h = lh + pad_t + pad_b
            panel = Image.new("RGBA", (card_w, card_h), (24, 26, 32, 255))
            p_draw = ImageDraw.Draw(panel)
            
            p_draw.rectangle([(2, 2), (card_w - 2, card_h - 2)], outline=(217, 4, 41, 255), width=2)
            p_draw.ellipse([(18, 14), (30, 26)], fill=(217, 4, 41, 255))
            p_draw.text((38, 11), "ARCHIVAL FOOTAGE // 25.01.1995 // 48TH MINUTE", fill=(240, 242, 245, 240), font=f_arch)
            
            panel.paste(lim.convert("RGBA"), (pad_s, pad_t))
            
            sh_mask = panel.split()[-1].filter(ImageFilter.GaussianBlur(14))
            total_pw, total_ph = card_w + 30, card_h + 30
            p_res = Image.new("RGBA", (total_pw, total_ph), (0, 0, 0, 0))
            p_res.paste(Image.new("RGBA", (card_w, card_h), (0, 0, 0, 190)), (15, 20), mask=sh_mask)
            p_res.paste(panel, (15, 15), mask=panel.split()[-1])
            ARCHIVE_PANELS.append(p_res)

print(f"✓ Archival Video Player pre-rendered ({len(ARCHIVE_PANELS)} frames).")

def render_frame(f_idx: int) -> Image.Image:
    fps = 30
    t = f_idx / fps # 0.0 to 60.0s
    
    # -------------------------------------------------------------
    # OUTRO SCENE (56.0s - 60.0s) — Synchronized with Spoken Outro
    # -------------------------------------------------------------
    if t >= 56.0:
        t_outro = t - 56.0
        outro_im = render_fs30_outro(t_outro, f_idx)
        return draw_mrbeast_captions(outro_im, t, center_y=1690)
        
    # -------------------------------------------------------------
    # BEAT 1: The Boiling Pot (0.0s - 8.0s) — Variant A Banner
    # -------------------------------------------------------------
    if t < 8.0:
        t_b = t
        bg = get_cached_bg("selhurst_floodlit").copy()
        
        # Smooth slide entrance for Variant A headline
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B1, (head_x, 240), mask=W_HEAD_B1.split()[-1])
        
        # Cantona Collar Scowl hero cutout (Strict proportional scaling)
        cantona_hero = get_image(CUTOUT_DIR / "cantona_collar_scowl.png")
        c_scale = 1.0 + 0.04 * (t_b / 8.0)
        target_w = int(980 * c_scale)
        hero_scaled = scale_cutout_proportional(cantona_hero, target_w=target_w)
        hero_x = int(100 + 8 * math.sin(t_b * 1.2))
        hero_y = int(540)
        bg.paste(hero_scaled, (hero_x, hero_y), mask=hero_scaled.split()[-1])
        
        # Richard Shaw Match Card on Left (X=50, Y=1120)
        # Original: 1267x1600 (portrait). Target: 390x480. Zero distortion via mount_archival_photo!
        shaw_raw = get_image(RAW_DIR / "b1_shaw_palace_0.jpg")
        shaw_mounted = mount_archival_photo(shaw_raw, target_w=390, target_h=480, focus_point=(0.5, 0.4))
        bg.paste(shaw_mounted, (50, 1120), mask=shaw_mounted.split()[-1])
        
        # Match Ticket Stub on right (X=490, Y=1450)
        bg.paste(W_TICKET_B1, (490, 1450), mask=W_TICKET_B1.split()[-1])
        
        # MrBeast Dynamic Captions & TV Watermark
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 2: The Red Card (8.0s - 16.5s) — Variant B Banner
    # -------------------------------------------------------------
    elif t < 16.5:
        t_b = t - 8.0
        bg = get_cached_bg("selhurst_terrace").copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B2, (head_x, 240), mask=W_HEAD_B2.split()[-1])
        
        # Cantona Black Kit on Left (X=-70, Y=510, height 1140px, strictly proportional)
        cantona_hero = get_image(CUTOUT_DIR / "cantona_black_kit.png")
        c_scale = 1.0 + 0.04 * (t_b / 8.5)
        target_h = int(1140 * c_scale)
        hero_scaled = scale_cutout_proportional(cantona_hero, target_h=target_h)
        hero_x = int(-70 + 6 * math.sin(t_b * 1.3))
        hero_y = int(510)
        bg.paste(hero_scaled, (hero_x, hero_y), mask=hero_scaled.split()[-1])
        
        # Touchline Escort Photo Card on Right (X=530, Y=560)
        # Original: 4096x2722 (landscape 1.505). Target: 490x325 (aspect 1.507). Zero distortion!
        escort_raw = get_image(RAW_DIR / "b2_cantona_red_card_2.jpg")
        escort_mounted = mount_archival_photo(escort_raw, target_w=490, target_h=325, focus_point=(0.5, 0.45))
        bg.paste(escort_mounted, (530, 560), mask=escort_mounted.split()[-1])
        
        # Incident Report card on Right (X=535, Y=980)
        inc_report = create_torn_quote_card(
            "Referee Alan Wilkie issues straight red card for retaliation.",
            attribution="— MATCH REPORT // 48TH MIN",
            width=480, height=270, quote_size=28, attr_size=18
        )
        bg.paste(inc_report, (535, 980), mask=inc_report.split()[-1])
        
        # Tactical Reticle
        if t_b > 1.2:
            draw_tactical_annotation(bg, x=780, y=710, radius=50, label="TERRACE SPRINT (11 ROWS)", t_progress=t_b)
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 3: The Kung-Fu Kick & Archival GIF (16.5s - 28.0s) — Variant C Banner
    # -------------------------------------------------------------
    elif t < 28.0:
        t_b = t - 16.5
        bg = get_cached_bg("selhurst_crowd").copy()
        
        if t_b < 0.35:
            flash_alpha = int(220 * (1.0 - t_b / 0.35))
            flash_layer = Image.new("RGBA", (1080, 1920), (255, 255, 255, flash_alpha))
            bg.paste(flash_layer, (0, 0), mask=flash_layer)
            
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 50)
        bg.paste(W_HEAD_B3, (head_x, 240), mask=W_HEAD_B3.split()[-1])
        
        # Main Action Photograph (Full focus on Cantona airborne kick)
        # Original: 1200x1702. Proportional mount into 980x620 with focus at (0.55, 0.48)
        kick_raw = get_image(RAW_DIR / "b3_cantona_kungfu_kick_1.jpg")
        kick_mounted = mount_archival_photo(kick_raw, target_w=980, target_h=620, focus_point=(0.55, 0.48))
        bg.paste(kick_mounted, (25, 430), mask=kick_mounted.split()[-1])
        
        if t_b > 1.8:
            draw_tactical_annotation(bg, x=360, y=780, radius=50, label="STUD CONTACT // CHEST", t_progress=t_b)
            
        # Daily Mirror clipping
        mirror_clipping = get_image(ASSETS_DIR / "daily_mirror_clipping.png")
        bg.paste(mirror_clipping, (40, 1160), mask=mirror_clipping.split()[-1])
        
        # Neon highlighter wipe across headline
        if t_b > 1.5:
            wipe_p = (t_b - 1.5) / 2.5
            apply_neon_highlighter_wipe(bg, (180, 1300, 520, 58), wipe_p)
            
        # ---------------------------------------------------------
        # GENUINE ARCHIVAL GIF ANIMATION INTEGRATION (tb >= 3.5s)
        # Starts precisely when narrator introduces the kick!
        # Loops 17 frames at ~12.5 FPS in dedicated contact sheet panel
        # ---------------------------------------------------------
        if t_b >= 3.5 and ARCHIVE_PANELS:
            t_anim = t_b - 3.5
            p_enter = min(1.0, t_anim / 0.35)
            ease_enter = math.sin(p_enter * math.pi / 2)
            
            # 12.5 FPS playback
            frame_idx = int(t_anim * 12.5) % len(ARCHIVE_PANELS)
            active_panel = ARCHIVE_PANELS[frame_idx]
            
            # Position panel smoothly onto upper-right zone (X=530, Y=470)
            panel_x = int(530 + (1.0 - ease_enter) * 80)
            panel_y = int(470)
            bg.paste(active_panel, (panel_x, panel_y), mask=active_panel.split()[-1])

        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 4: The Courtroom & Criminal Ban (28.0s - 39.5s) — Variant D Banner
    # -------------------------------------------------------------
    elif t < 39.5:
        t_b = t - 28.0
        bg = get_cached_bg("croydon_court").copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B4, (head_x, 240), mask=W_HEAD_B4.split()[-1])
        
        # Archival Press Photo of Cantona arriving at Court on Right (X=510, Y=520)
        # Original: 1200x772 (landscape 1.554). Target: 500x340 (aspect 1.471). Zero vertical distortion!
        court_raw = get_image(RAW_DIR / "b4_cantona_court_1.jpg")
        court_mounted = mount_archival_photo(court_raw, target_w=500, target_h=340, focus_point=(0.5, 0.4))
        bg.paste(court_mounted, (510, 520), mask=court_mounted.split()[-1])
        
        # Archival Quote & Judgement Card on Left (X=45, Y=540)
        bg.paste(W_QUOTE_B4, (45, 540), mask=W_QUOTE_B4.split()[-1])
        
        # Rubber Stamp 1: 8-MONTH BAN (Slams at t_b = 1.5s on bottom-left)
        if t_b > 1.5:
            p_stamp1 = (t_b - 1.5) / 0.45
            draw_rubber_stamp(bg, "stamp_ban_8months", center_x=300, center_y=1120, progress=p_stamp1)
            
        # Rubber Stamp 2: 120 HOURS COMMUNITY SERVICE (Slams at t_b = 3.5s on bottom-right)
        if t_b > 3.5:
            p_stamp2 = (t_b - 3.5) / 0.45
            draw_rubber_stamp(bg, "stamp_community_service", center_x=700, center_y=1350, progress=p_stamp2)
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 5: The Seagulls & The Sardines (39.5s - 51.5s) — Variant E Banner
    # -------------------------------------------------------------
    elif t < 51.5:
        t_b = t - 39.5
        bg = get_cached_bg("press_room").copy()
        
        if t_b < 0.35:
            flash_alpha = int(190 * (1.0 - t_b / 0.35))
            flash_layer = Image.new("RGBA", (1080, 1920), (255, 255, 255, flash_alpha))
            bg.paste(flash_layer, (0, 0), mask=flash_layer)
            
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B5, (head_x, 240), mask=W_HEAD_B5.split()[-1])
        
        # Cantona at Press Conference with Water Glass (Centered, Y=470, strictly proportional)
        cantona_hero = get_image(CUTOUT_DIR / "cantona_press_conference.png")
        c_scale = 1.0 + 0.045 * (t_b / 12.0)
        target_w = int(840 * c_scale)
        hero_scaled = scale_cutout_proportional(cantona_hero, target_w=target_w)
        hero_x = int((1080 - hero_scaled.size[0]) // 2 + 5 * math.sin(t_b * 1.1))
        hero_y = int(470)
        bg.paste(hero_scaled, (hero_x, hero_y), mask=hero_scaled.split()[-1])
        
        # Archival Quote Scroll on Bottom (X=60, Y=1060)
        bg.paste(W_QUOTE_B5, (60, 1060), mask=W_QUOTE_B5.split()[-1])
        
        if t_b > 1.8:
            wipe_p = (t_b - 1.8) / 3.0
            apply_neon_highlighter_wipe(bg, (140, 1110, 780, 52), wipe_p)
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 6: The King Returns (51.5s - 56.0s) — Variant E Banner
    # -------------------------------------------------------------
    else:
        t_b = t - 51.5
        bg = get_cached_bg("old_trafford").copy()
        
        p_slide = min(1.0, t_b / 0.35)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B6, (head_x, 240), mask=W_HEAD_B6.split()[-1])
        
        # Cantona Arms Outstretched King Celebration (Strictly proportional, zero stretching!)
        cantona_hero = get_image(CUTOUT_DIR / "cantona_arms_outstretched.png")
        c_scale = 1.0 + 0.04 * (t_b / 4.5)
        target_h = int(1140 * c_scale)
        hero_scaled = scale_cutout_proportional(cantona_hero, target_h=target_h)
        hero_x = int(-40)
        hero_y = int(500) # Placed below headline banner so fingers never occlude text!
        bg.paste(hero_scaled, (hero_x, hero_y), mask=hero_scaled.split()[-1])
        
        # Match Ticket Stub on Right (X=500, Y=1420)
        bg.paste(W_TICKET_B6, (500, 1420), mask=W_TICKET_B6.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

def render_worker(f_idx: int):
    frame = render_frame(f_idx)
    out_p = FRAMES_DIR / f"frame_{f_idx:05d}.jpg"
    frame.convert("RGB").save(out_p, "JPEG", quality=93)
    if f_idx % 150 == 0:
        print(f"Rendered frame {f_idx} / 1800 ({(f_idx/1800)*100:.1f}%)", flush=True)

def render_all_frames():
    print("=" * 70)
    print("  BATCH RENDERING ALL 1,800 FRAMES (60.0 SECONDS @ 30 FPS)")
    print("=" * 70)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(render_worker, idx) for idx in range(1800)]
        for f in futures:
            f.result()
            
    print("\n✓ All 1,800 frames successfully rendered!")

def mux_final_master_video():
    print("=" * 70)
    print("  MUXING MASTER 60-SECOND MP4 (H.264 + REFINED MASTERED AUDIO)")
    print("=" * 70)
    
    audio_path = RUN_DIR / "cantona_mastered_audio_60s.wav"
    output_mp4 = RUN_DIR / "cantona_kungfu_master_60s.mp4"
    artifact_mp4 = ARTIFACT_DIR / "cantona_kungfu_master_60s.mp4"
    
    cmd_mux = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", str(FRAMES_DIR / "frame_%05d.jpg"),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        str(output_mp4)
    ]
    subprocess.run(cmd_mux, check=True)
    print(f"✓ Master MP4 generated: {output_mp4.name} ({output_mp4.stat().st_size / 1024 / 1024:.2f} MB)")
    
    shutil.copyfile(str(output_mp4), str(artifact_mp4))
    print(f"✓ Copied master video to artifacts: {artifact_mp4.name}")

def make_12beat_contact_sheet():
    print("=" * 70)
    print("  GENERATING 12-KEYFRAME CONTACT SHEET ACROSS 60-SECOND RUN")
    print("=" * 70)
    
    timestamps = [2.0, 6.0, 11.5, 16.0, 21.0, 24.5, 33.0, 38.0, 44.0, 50.0, 55.5, 58.5]
    cols = 4
    rows = 3
    thumb_w, thumb_h = 360, 640
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (14, 16, 22))
    draw = ImageDraw.Draw(sheet)
    f_lbl = get_font("headline_bold", 28)
    
    for idx, sec in enumerate(timestamps):
        f_idx = int(sec * 30)
        im = render_frame(f_idx)
        thumb = im.resize((thumb_w - 12, thumb_h - 40), Image.Resampling.LANCZOS)
        r = idx // cols
        c = idx % cols
        pos_x = c * thumb_w + 6
        pos_y = r * thumb_h + 6
        sheet.paste(thumb, (pos_x, pos_y))
        draw.text((pos_x + 10, pos_y + thumb_h - 32), f"T = {sec:.1f}s (Frame {f_idx})", fill=(255, 235, 59), font=f_lbl)
        
    out_sheet = RUN_DIR / "cantona_master_12beat_contact_sheet.png"
    sheet.save(out_sheet, "PNG")
    shutil.copyfile(str(out_sheet), str(ARTIFACT_DIR / "cantona_master_12beat_contact_sheet.png"))
    print(f"✓ Saved 12-beat contact sheet: {out_sheet.name}")

if __name__ == "__main__":
    render_all_frames()
    mux_final_master_video()
    make_12beat_contact_sheet()
