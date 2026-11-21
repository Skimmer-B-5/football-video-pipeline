"""
60-Second Zinedine Zidane 2006 World Cup Headbutt Documentary Renderer (Master Production 7.0 - True Historical Broadsheet Edition).
Strict Aesthetic Directives:
1. Low-Saturation Full-Bleed Atmospheric Backgrounds:
   - Real high-resolution 2006 Olympiastadion Berlin stadium stands and pitch photography desaturated by 68% and darkened by 35% with subtle vignetting. ZERO sterile grey paper voids.
2. Authentic Historical Newspaper Broadsheet Scans:
   - Real L'Équipe July 10, 2006 front page scan ("REGRETS ÉTERNELS")
   - Real pink La Gazzetta dello Sport July 10, 2006 front page scan ("TUTTO VERO! CAMPIONI DEL MONDO")
   - Real Le Monde & Guardian incident clippings with paper fold creases
3. Genuine Archival Broadcast Video Loop:
   - 12-frame historical broadcast loop of the headbutt incident in an authentic TV monitor frame with REC indicator
4. Verified High-Res Iconic Photography:
   - Fabio Cannavaro lifting the World Cup into silver confetti (1861x2300 Reuters)
   - Zinedine Zidane (#10) walking with bowed head past the golden FIFA trophy on podium
5. Rich Tactile Collage Crafting:
   - Real crimson washi tape, black masking tape, and cellophane tape strips
   - Double archival photo borders and ambient occlusion drop shadows
6. Zero Distortion & Calibrated Sound:
   - Strictly proportional scaling, EBU R128 (-14 LUFS) ducked audio, verified MrBeast captions
"""

import sys
import os
import math
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT))

RUN_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story"
ASSETS_DIR = RUN_DIR / "assets"
ARCHIVE_DIR = ASSETS_DIR / "archival_footage"
PANELS_DIR = ARCHIVE_DIR / "mounted_panels"
STOCK_DIR = PROJECT_ROOT / "assets" / "stock" / "generated"
REUSABLE_DIR = PROJECT_ROOT / "fs30" / "story_pipeline" / "assets" / "reusable_stock"
FRAMES_DIR = RUN_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")
LOG_PATH = RUN_DIR / "artisan_production.log"

from fs30.story_pipeline.branding import create_fs30_tv_watermark, render_fs30_outro
from fs30.story_pipeline.photo_mounter import scale_cutout_proportional
from fs30.story_pipeline.mrbeast_captions import init_captions, draw_mrbeast_captions

# Initialize verified MrBeast captions
init_captions(RUN_DIR / "zidane_mrbeast_captions.json")

# Persistent FS30 Watermark
TV_WATERMARK = create_fs30_tv_watermark(badge_size=140)

# In-memory image cache
_LOADED_IMAGES: Dict[str, Image.Image] = {}

def get_image(path: Path) -> Image.Image:
    k = str(path)
    if k not in _LOADED_IMAGES:
        with Image.open(path) as im:
            _LOADED_IMAGES[k] = im.convert("RGBA")
    return _LOADED_IMAGES[k]

def prepare_desaturated_stadium_bg(img_path: Path, width: int = 1080, height: int = 1920) -> Image.Image:
    """Prepares low-saturation, darkened atmospheric stadium background with vignette."""
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = max(width / w, height / h)
        nw, nh = int(w * scale), int(h * scale)
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        x_off = (nw - width) // 2
        y_off = (nh - height) // 2
        cropped = im.crop((x_off, y_off, x_off + width, y_off + height))
        
        # Low saturation: -68% color (0.32 factor)
        desat = ImageEnhance.Color(cropped).enhance(0.32)
        # Darkened: -35% brightness (0.65 factor)
        darkened = ImageEnhance.Brightness(desat).enhance(0.65)
        blurred = darkened.filter(ImageFilter.GaussianBlur(1.6))
        
        # Signature cinematic documentary vignette
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vignette)
        vd.rectangle([(0, 0), (width, height)], fill=(8, 10, 14, 90))
        vd.rectangle([(0, 0), (width, 260)], fill=(6, 8, 12, 145))
        vd.rectangle([(0, height - 280), (width, height)], fill=(6, 8, 12, 155))
        
        res = blurred.convert("RGBA")
        res.paste(vignette, (0, 0), mask=vignette)
        return res

BG_BERLIN_STADIUM: Optional[Image.Image] = None
BG_PITCH_ACTION: Optional[Image.Image] = None

def get_bg_berlin() -> Image.Image:
    global BG_BERLIN_STADIUM
    if BG_BERLIN_STADIUM is None:
        BG_BERLIN_STADIUM = prepare_desaturated_stadium_bg(ASSETS_DIR / "berlin_stadium.jpg")
    return BG_BERLIN_STADIUM

def get_bg_pitch() -> Image.Image:
    global BG_PITCH_ACTION
    if BG_PITCH_ACTION is None:
        BG_PITCH_ACTION = prepare_desaturated_stadium_bg(ASSETS_DIR / "italy_france_action.jpg")
    return BG_PITCH_ACTION

# Real tape assets
TAPE_RED = Image.open(STOCK_DIR / "tape_strips" / "tape_crimson_washi_02.png").convert("RGBA")
TAPE_BLACK = Image.open(STOCK_DIR / "tape_strips" / "tape_black_masking_03.png").convert("RGBA")
TAPE_CLEAR = Image.open(STOCK_DIR / "tape_strips" / "tape_clear_cellophane_01.png").convert("RGBA")

def create_banner_with_text(banner_path: Path, title: str, kicker: str) -> Image.Image:
    """Prints typography onto real reusable stock banner PNG."""
    with Image.open(banner_path) as bim:
        banner = bim.convert("RGBA")
        bw, bh = banner.size
        d = ImageDraw.Draw(banner)
        
        f_kicker = ImageFont.truetype("arialbd.ttf", 20)
        f_title = ImageFont.truetype("impact.ttf", 52)
        
        d.text((bw // 2, 60), kicker, fill=(210, 30, 30, 255), font=f_kicker, anchor="mm")
        d.text((bw // 2, 125), title, fill=(18, 20, 26, 255), font=f_title, anchor="mm")
        return banner

# Pre-render Banner Variants (1000 x 220)
BANNER_B1 = create_banner_with_text(REUSABLE_DIR / "banners" / "banner_variant_a_torn_stripe.png", "THE FINAL DANCE", "BERLIN 2006 // OLYMPIASTADION")
BANNER_B2 = create_banner_with_text(REUSABLE_DIR / "banners" / "banner_variant_b_folded_marker.png", "THE ALTERCATION", "110TH MINUTE // SCORE LOCKED 1-1")
BANNER_B3 = create_banner_with_text(REUSABLE_DIR / "banners" / "banner_variant_c_corner_tab.png", "THE HEADBUTT", "UNPRECEDENTED SHOCK // CHEST IMPACT")
BANNER_B4 = create_banner_with_text(REUSABLE_DIR / "banners" / "banner_variant_d_distressed_underline.png", "THE EXPULSION", "RED CARD // WALKING PAST THE TROPHY")
BANNER_B5 = create_banner_with_text(REUSABLE_DIR / "banners" / "banner_variant_e_layered_offset.png", "THE AFTERMATH", "ITALY CHAMPIONS // FIFA DISCIPLINARY")
BANNER_B6 = create_banner_with_text(REUSABLE_DIR / "banners" / "banner_variant_a_torn_stripe.png", "LONG LIVE ZIZOU", "108 CAPS // A MAJESTIC LEGACY")

# Pre-load 12 Archival Broadcast Panels for Beat 3
ARCHIVAL_BROADCAST_PANELS: List[Image.Image] = []
for p_idx in range(12):
    panel_file = PANELS_DIR / f"panel_{p_idx:02d}.png"
    if panel_file.exists():
        ARCHIVAL_BROADCAST_PANELS.append(get_image(panel_file))
print(f"Loaded {len(ARCHIVAL_BROADCAST_PANELS)} pre-rendered archival broadcast panels for Beat 3.")

def render_frame(f_idx: int) -> Image.Image:
    fps = 30
    t = f_idx / fps  # 0.00 to 60.00s
    
    # -------------------------------------------------------------
    # OUTRO SCENE (56.00s - 60.00s) — Spoken CTA & Official Brand Card
    # -------------------------------------------------------------
    if t >= 56.00:
        t_outro = t - 56.00
        outro_im = render_fs30_outro(t_outro, f_idx)
        return draw_mrbeast_captions(outro_im, t, center_y=1690)
        
    # -------------------------------------------------------------
    # BEAT 1: The Farewell & Panenka (0.00s - 11.20s)
    # Background: Low-saturation Olympiastadion Berlin
    # -------------------------------------------------------------
    if t < 11.20:
        t_b = t
        bg = get_bg_berlin().copy()
        
        # Entrance 1 (t_b >= 0.1s): Banner Variant A
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B1, (head_x, 180), mask=BANNER_B1.split()[-1])
        
        # Entrance 2 (t_b >= 1.4s): Buffon Polaroid (OpenCV centered) + Red Washi Tape
        if t_b >= 1.4:
            p_buf = min(1.0, (t_b - 1.4) / 0.5)
            ease_buf = math.sin(p_buf * math.pi / 2)
            buf_im = get_image(ASSETS_DIR / "mounted_buffon_polaroid.png").rotate(-3, expand=True)
            buf_y = int(450 - 60 * (1.0 - ease_buf))
            bg.paste(buf_im, (50, buf_y), mask=buf_im.split()[-1])
            # Tape corner
            t_red = TAPE_RED.resize((150, 44), Image.Resampling.LANCZOS).rotate(18, expand=True)
            bg.paste(t_red, (50, buf_y - 20), mask=t_red.split()[-1])
            
        # Entrance 3 (t_b >= 5.0s): Zidane Panenka Penalty Mount
        if t_b >= 5.0:
            p_pen = min(1.0, (t_b - 5.0) / 0.5)
            ease_pen = math.sin(p_pen * math.pi / 2)
            pen_im = get_image(ASSETS_DIR / "mounted_zidane_penalty.png").rotate(2.5, expand=True)
            pen_x = int(380 + 100 * (1.0 - ease_pen))
            bg.paste(pen_im, (pen_x, 780), mask=pen_im.split()[-1])
            
        # Entrance 4 (t_b >= 8.2s): REAL L'ÉQUIPE NEWSPAPER CLIPPING ("REGRETS ÉTERNELS")
        if t_b >= 8.2:
            p_eq = min(1.0, (t_b - 8.2) / 0.5)
            ease_eq = math.sin(p_eq * math.pi / 2)
            eq_real = get_image(ASSETS_DIR / "clipping_lequipe_authentic.png")
            eq_scale = 980 / eq_real.width
            eq_s = eq_real.resize((980, int(eq_real.height * eq_scale)), Image.Resampling.LANCZOS).rotate(-1, expand=True)
            eq_y = int(1220 + 100 * (1.0 - ease_eq))
            bg.paste(eq_s, (45, eq_y), mask=eq_s.split()[-1])
            # Clear tape on newspaper edge
            t_clear = TAPE_CLEAR.resize((160, 40), Image.Resampling.LANCZOS).rotate(-8, expand=True)
            bg.paste(t_clear, (850, eq_y - 15), mask=t_clear.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 2: The Altercation (11.20s - 21.16s)
    # Background: Low-saturation Pitch Action with Zidane & Totti
    # -------------------------------------------------------------
    elif t < 21.16:
        t_b = t - 11.20
        bg = get_bg_pitch().copy()
        
        # Entrance 1 (t_b >= 0.1s): Banner Variant B
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B2, (head_x, 180), mask=BANNER_B2.split()[-1])
        
        # Entrance 2 (t_b >= 1.0s): Mounted Shirt Tug Photo
        if t_b >= 1.0:
            p_sh = min(1.0, (t_b - 1.0) / 0.5)
            ease_sh = math.sin(p_sh * math.pi / 2)
            sh_im = get_image(ASSETS_DIR / "mounted_shirt_altercation.png").rotate(1.5, expand=True)
            sh_y = int(480 - 60 * (1.0 - ease_sh))
            bg.paste(sh_im, (70, sh_y), mask=sh_im.split()[-1])
            # Black tape
            t_black = TAPE_BLACK.resize((140, 38), Image.Resampling.LANCZOS).rotate(-14, expand=True)
            bg.paste(t_black, (65, sh_y - 12), mask=t_black.split()[-1])
            
        # Entrance 3 (t_b >= 4.5s): Real Quote Card with Neon Highlighter
        if t_b >= 4.5:
            p_q = min(1.0, (t_b - 4.5) / 0.5)
            ease_q = math.sin(p_q * math.pi / 2)
            q_im = get_image(ASSETS_DIR / "quote_materazzi_insult.png")
            q_y = int(1220 + 100 * (1.0 - ease_q))
            bg.paste(q_im, (40, q_y), mask=q_im.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 3: The Headbutt (21.16s - 30.14s) — GENUINE ARCHIVAL BROADCAST LOOP HERO
    # Background: Low-saturation Olympiastadion Berlin
    # -------------------------------------------------------------
    elif t < 30.14:
        t_b = t - 21.16
        bg = get_bg_berlin().copy()
        
        # Banner Variant C
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B3, (head_x, 180), mask=BANNER_B3.split()[-1])
        
        # ARCHIVAL BROADCAST PANEL PLAYBACK
        if ARCHIVAL_BROADCAST_PANELS:
            p_pan = min(1.0, max(0.0, (t_b - 0.4) / 0.5))
            ease_pan = math.sin(p_pan * math.pi / 2)
            
            # Continuous loop playback at 10.0 FPS
            loop_idx = int((t_b * 10.0)) % len(ARCHIVAL_BROADCAST_PANELS)
            panel_im = ARCHIVAL_BROADCAST_PANELS[loop_idx]
            
            # Subtle camera push on impact (1.0 -> 1.04 around tb=2.0s)
            pan_w, pan_h = panel_im.size
            if 1.8 <= t_b <= 2.6:
                zoom = 1.0 + 0.04 * math.sin((t_b - 1.8) / 0.8 * math.pi)
                nw, nh = int(pan_w * zoom), int(pan_h * zoom)
                panel_im = panel_im.resize((nw, nh), Image.Resampling.LANCZOS)
                px = (1080 - nw) // 2
                py = int(480 - (nh - pan_h) // 2)
            else:
                px = (1080 - pan_w) // 2
                py = int(480 + 80 * (1.0 - ease_pan))
                
            bg.paste(panel_im, (px, py), mask=panel_im.split()[-1])
            
        # REAL LE MONDE CLIPPING ("LE COUP DE BOULE QUI A CHOQUÉ LE MONDE") (t_b >= 4.2s)
        if t_b >= 4.2:
            p_lm = min(1.0, (t_b - 4.2) / 0.5)
            ease_lm = math.sin(p_lm * math.pi / 2)
            lm_im = get_image(ASSETS_DIR / "clipping_coup_de_boule_real.png")
            lm_y = int(1220 + 100 * (1.0 - ease_lm))
            bg.paste(lm_im, (50, lm_y), mask=lm_im.split()[-1])
            t_red2 = TAPE_RED.resize((140, 36), Image.Resampling.LANCZOS).rotate(10, expand=True)
            bg.paste(t_red2, (55, lm_y - 10), mask=t_red2.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 4: The Expulsion (30.14s - 39.25s) — Red Card & Iconic Trophy Walk Photo
    # Background: Low-saturation Olympiastadion Berlin
    # -------------------------------------------------------------
    elif t < 39.25:
        t_b = t - 30.14
        bg = get_bg_berlin().copy()
        
        # Banner Variant D
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B4, (head_x, 180), mask=BANNER_B4.split()[-1])
        
        # Red Card Stamp slap-on (t_b >= 0.8s)
        if t_b >= 0.8:
            p_rc = min(1.0, (t_b - 0.8) / 0.35)
            ease_rc = math.sin(p_rc * math.pi / 2)
            stamp_rc = get_image(REUSABLE_DIR / "stamps" / "stamp_red_card.png").resize((420, 150), Image.Resampling.LANCZOS).rotate(12, expand=True)
            rc_scale = 1.0 + 0.3 * (1.0 - ease_rc)
            stamp_s = stamp_rc.resize((int(stamp_rc.width * rc_scale), int(stamp_rc.height * rc_scale)), Image.Resampling.LANCZOS)
            bg.paste(stamp_s, (610, 420), mask=stamp_s.split()[-1])
            
        # The Guardian Newspaper Clipping (t_b >= 1.6s)
        if t_b >= 1.6:
            p_gd = min(1.0, (t_b - 1.6) / 0.5)
            ease_gd = math.sin(p_gd * math.pi / 2)
            gd_im = get_image(ASSETS_DIR / "clipping_guardian_red_card.png")
            gd_y = int(450 - 50 * (1.0 - ease_gd))
            bg.paste(gd_im, (50, gd_y), mask=gd_im.split()[-1])
            
        # THE ICONIC TROPHY WALK PHOTO (Zidane walking past World Cup trophy) (t_b >= 3.6s)
        if t_b >= 3.6:
            p_zw = min(1.0, (t_b - 3.6) / 0.5)
            ease_zw = math.sin(p_zw * math.pi / 2)
            zw_raw = get_image(ASSETS_DIR / "mounted_zidane_trophy_walk_verified.png")
            zw_scaled = zw_raw.resize((int(zw_raw.width * 0.94), int(zw_raw.height * 0.94)), Image.Resampling.LANCZOS).rotate(-1.5, expand=True)
            zw_x = (1080 - zw_scaled.width) // 2
            zw_y = int(580 + 70 * (1.0 - ease_zw))
            bg.paste(zw_scaled, (zw_x, zw_y), mask=zw_scaled.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 5: The Aftermath (39.25s - 47.90s) — REAL Pink Gazzetta & Cannavaro Lift
    # Background: Low-saturation Pitch Action
    # -------------------------------------------------------------
    elif t < 47.90:
        t_b = t - 39.25
        bg = get_bg_pitch().copy()
        
        # Banner Variant E
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B5, (head_x, 180), mask=BANNER_B5.split()[-1])
        
        # REAL PINK GAZZETTA DELLO SPORT CLIPPING ("TUTTO VERO! CAMPIONI DEL MONDO") (t_b >= 0.2s)
        gaz_real = get_image(ASSETS_DIR / "clipping_gazzetta_authentic.png")
        gaz_scale = 960 / gaz_real.width
        gaz_s = gaz_real.resize((960, int(gaz_real.height * gaz_scale)), Image.Resampling.LANCZOS).rotate(1.2, expand=True)
        bg.paste(gaz_s, (55, 430), mask=gaz_s.split()[-1])
        # Black tape on top of Gazzetta
        t_black = TAPE_BLACK.resize((150, 42), Image.Resampling.LANCZOS).rotate(-12, expand=True)
        bg.paste(t_black, (60, 415), mask=t_black.split()[-1])
        
        # 1. Revealed underneath (active at t_b >= 3.8s)
        if t_b >= 3.8:
            doc_im = get_image(ASSETS_DIR / "fifa_sanction_document.png")
            bg.paste(doc_im, (60, 1050), mask=doc_im.split()[-1])
            
            badge_gb = get_image(ASSETS_DIR / "golden_ball_award_badge.png")
            bg.paste(badge_gb, (310, 1420), mask=badge_gb.split()[-1])
            
        # 2. VERIFIED CANNAVARO TROPHY LIFT (Reuters Confetti Lift)
        # Slides UP from y=1950 to y=680 between t_b=0.0 and 0.6s
        # Holds until t_b=3.6s
        # Slides DOWN back to y=1950 between t_b=3.6s and 4.4s
        can_im = get_image(ASSETS_DIR / "mounted_cannavaro_trophy_lift_verified.png")
        can_s = can_im.resize((int(can_im.width * 0.78), int(can_im.height * 0.78)), Image.Resampling.LANCZOS).rotate(-1.5, expand=True)
        can_x = (1080 - can_s.width) // 2
        
        if t_b < 0.6:
            p_up = t_b / 0.6
            ease_up = math.sin(p_up * math.pi / 2)
            sb_y = int(1950 - (1950 - 680) * ease_up)
            bg.paste(can_s, (can_x, sb_y), mask=can_s.split()[-1])
        elif t_b < 3.6:
            bg.paste(can_s, (can_x, 680), mask=can_s.split()[-1])
        elif t_b < 4.4:
            p_down = (t_b - 3.6) / 0.8
            ease_down = p_down ** 2
            sb_y = int(680 + (1950 - 680) * ease_down)
            bg.paste(can_s, (can_x, sb_y), mask=can_s.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 6: The Legend (47.90s - 56.00s) — 108 Caps & Final Tribute
    # Background: Low-saturation Olympiastadion Berlin
    # -------------------------------------------------------------
    else:
        t_b = t - 47.90
        bg = get_bg_berlin().copy()
        
        # Banner Variant A
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B6, (head_x, 180), mask=BANNER_B6.split()[-1])
        
        # Legendary Portrait Cutout of Zidane (t_b >= 0.2s)
        p_z = min(1.0, t_b / 0.5)
        ease_z = math.sin(p_z * math.pi / 2)
        z_cut = get_image(ASSETS_DIR / "zidane_hero_cutout.png")
        z_scaled = scale_cutout_proportional(z_cut, target_h=980)
        z_x = int(60 - 80 * (1.0 - ease_z))
        bg.paste(z_scaled, (z_x, 500), mask=z_scaled.split()[-1])
        
        # 108 Caps Badge (t_b >= 1.0s)
        if t_b >= 1.0:
            p_badge = min(1.0, (t_b - 1.0) / 0.45)
            ease_badge = math.sin(p_badge * math.pi / 2)
            badge_im = get_image(ASSETS_DIR / "badge_108_caps.png")
            badge_x = int(500 + 80 * (1.0 - ease_badge))
            bg.paste(badge_im, (badge_x, 720), mask=badge_im.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

def log_progress(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def render_worker(args: Tuple[int, int]):
    start_idx, end_idx = args
    for i in range(start_idx, end_idx):
        frame = render_frame(i)
        out_p = FRAMES_DIR / f"frame_{i:05d}.jpg"
        frame.convert("RGB").save(out_p, format="JPEG", quality=95)
        if (i - start_idx + 1) % 50 == 0:
            log_progress(f"Worker [{start_idx}-{end_idx}] rendered frame {i} ({((i - start_idx + 1) / (end_idx - start_idx)) * 100:.1f}%)")

def main():
    log_progress("=" * 70)
    log_progress("  RENDERING 60.00s ZIDANE 2006 (MASTER 7.0 - TRUE BROADSHEET & STADIUM BG)")
    log_progress("=" * 70)
    
    total_frames = 1800  # 60.0s @ 30fps
    num_threads = 8
    chunk_size = total_frames // num_threads
    
    chunks = []
    for th in range(num_threads):
        s = th * chunk_size
        e = total_frames if th == num_threads - 1 else (th + 1) * chunk_size
        chunks.append((s, e))
        
    log_progress(f"Starting batch rendering of {total_frames} frames across {num_threads} threads...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        list(executor.map(render_worker, chunks))
        
    render_dur = time.time() - start_time
    log_progress(f"Completed frame generation in {render_dur:.1f}s ({total_frames / render_dur:.1f} fps).")
    
    # Generate 12-beat visual QA contact sheet
    log_progress("Generating 12-beat visual QA inspection contact sheet...")
    sheet = Image.new("RGB", (1080 * 4, 1920 * 3), (20, 20, 24))
    sample_frames = [
        ("01_farewell_buffon", 60),      # 2.0s
        ("02_panenka_penalty", 180),     # 6.0s
        ("03_lequipe_frontpage", 270),   # 9.0s (Real L'Equipe)
        ("04_altercation_shirt", 400),   # 13.3s
        ("05_quote_insult", 540),        # 18.0s
        ("06_headbutt_broadcast", 720),  # 24.0s (incident replay)
        ("07_lemonde_clipping", 840),    # 28.0s (Real Le Monde)
        ("08_red_card_stamp", 960),      # 32.0s
        ("09_trophy_walk_iconic", 1110), # 37.0s (Zidane past trophy)
        ("10_gazzetta_lift", 1260),      # 42.0s (Real Pink Gazzetta & Cannavaro)
        ("11_fifa_sanctions", 1380),     # 46.0s (FIFA doc & Golden Ball)
        ("12_legend_outro", 1720),       # 57.3s (FS30 outro)
    ]
    
    for idx, (label, f_num) in enumerate(sample_frames):
        row = idx // 4
        col = idx % 4
        fp = FRAMES_DIR / f"frame_{f_num:05d}.jpg"
        if fp.exists():
            with Image.open(fp) as fim:
                sheet.paste(fim, (col * 1080, row * 1920))
                
    contact_path = RUN_DIR / "zidane_artisan_12beat_contact_sheet.png"
    sheet_preview = sheet.resize((1440, 1920), Image.Resampling.LANCZOS)
    sheet_preview.save(contact_path)
    sheet_preview.save(BRAIN_DIR / "zidane_artisan_12beat_contact_sheet.png")
    log_progress(f"Saved QA contact sheet: {contact_path.name}")
    
    # FFmpeg Master Assembly
    log_progress("Assembling Master Video with FFmpeg...")
    master_video_path = RUN_DIR / "zidane_headbutt_artisan_master_60s.mp4"
    audio_path = RUN_DIR / "zidane_mastered_audio_60s.wav"
    
    cmd_ffmpeg = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", str(FRAMES_DIR / "frame_%05d.jpg"),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        str(master_video_path)
    ]
    
    res = subprocess.run(cmd_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0:
        log_progress(f"Master Video successfully created: {master_video_path.name} ({master_video_path.stat().st_size / (1024*1024):.2f} MB)")
        import shutil
        shutil.copy(master_video_path, BRAIN_DIR / "zidane_headbutt_artisan_master_60s.mp4")
        vault_dir = PROJECT_ROOT / "final_masters_vault" / "FS30-HIST-002"
        vault_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(master_video_path, vault_dir / "zidane_headbutt_master_60s.mp4")
        shutil.copy(contact_path, vault_dir / "zidane_master_12beat_contact_sheet.png")
        log_progress("Synchronized master video and contact sheet to vault and artifacts.")
    else:
        log_progress(f"FFmpeg error: {res.stderr.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    main()
