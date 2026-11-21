"""
60-Second Zinedine Zidane 2006 World Cup Headbutt Documentary Renderer (Master Production 5.0).
Strict Production Refinements:
1. Real Paper Assets Only: Reusable stock banners (variant A-E), real Polaroid/gallery frames,
   real tape strips, real aged paper backgrounds, real stamps. Zero flat PIL color rectangles.
2. Zero Photo Repetition: Strictly max 1 scene per photograph across all 6 beats.
   - Beat 1: buffon_final.jpg (Polaroid) & zidane_penalty.jpg (Gallery mat)
   - Beat 2: zidane_shirt_2006.jpg (Ivory mat) & quote_materazzi_insult.png
   - Beat 3: puppet_headbutt_unified.png (Iconic headbutt paper puppet) & clipping_coup_de_boule_real.png
   - Beat 4: clipping_guardian_red_card.png & stamp_red_card.png & world_cup_trophy_cutout.png
   - Beat 5: cannavaro_trophy.jpg (Scrapbook lift & retract) & fifa_sanction_document.png & golden_ball_award_badge.png
   - Beat 6: zidane_hero_cutout.png (Legendary portrait) & badge_108_caps.png
3. Unobstructed Unified Paper-Puppet Headbutt: Front, center hero of Beat 3. No cards covering it.
   Smooth wind-up, violent forward strike, "WHAM!" impact starburst, screen shake, and collapse.
4. Animated Scrapbook Slide: Cannavaro trophy lift slides up from below, holds for Italy victory,
   then slides down to reveal the FIFA sanction document and Golden Ball award badge.
5. Sequential Entrances: Assets enter one-by-one synchronized with spoken narration cues.
6. OpenCV Face Framing: Buffon centered in Polaroid aperture without cutting his head or torso.
7. Calibrated Timing: 60.00s total duration at 30fps (1800 frames), aligned with calm unhurried British narration.
8. MrBeast Kinetic Captions: 100% verified spelling for all player names and milestones.
"""

import sys
import os
import math
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
from concurrent.futures import ThreadPoolExecutor

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT))

RUN_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story"
ASSETS_DIR = RUN_DIR / "assets"
STOCK_DIR = PROJECT_ROOT / "assets" / "stock" / "generated"
REUSABLE_DIR = PROJECT_ROOT / "fs30" / "story_pipeline" / "assets" / "reusable_stock"
FRAMES_DIR = RUN_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

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

def prepare_textured_bg(bg_path: Path, width: int = 1080, height: int = 1920) -> Image.Image:
    """Prepares textured paper background with subtle archival vignette."""
    with Image.open(bg_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = max(width / w, height / h)
        nw, nh = int(w * scale), int(h * scale)
        resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
        x_off = (nw - width) // 2
        y_off = (nh - height) // 2
        cropped = resized.crop((x_off, y_off, x_off + width, y_off + height))
        
        # Archival warm grade
        enh_b = ImageEnhance.Brightness(cropped)
        dark = enh_b.enhance(0.92)
        
        vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vignette)
        vd.rectangle([(0, 0), (width, height)], fill=(12, 14, 20, 85))
        vd.rectangle([(0, 0), (width, 240)], fill=(8, 10, 14, 120))
        vd.rectangle([(0, height - 260), (width, height)], fill=(8, 10, 14, 130))
        
        res = dark.convert("RGBA")
        res.alpha_composite(vignette)
        return res

BG_NEWSPRINT: Optional[Image.Image] = None
BG_PARCHMENT: Optional[Image.Image] = None

def get_bg_newsprint() -> Image.Image:
    global BG_NEWSPRINT
    if BG_NEWSPRINT is None:
        BG_NEWSPRINT = prepare_textured_bg(STOCK_DIR / "paper_backgrounds" / "bg_grey_newsprint_03.png")
    return BG_NEWSPRINT

def get_bg_parchment() -> Image.Image:
    global BG_PARCHMENT
    if BG_PARCHMENT is None:
        BG_PARCHMENT = prepare_textured_bg(STOCK_DIR / "paper_backgrounds" / "bg_aged_yellow_07.png")
    return BG_PARCHMENT

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

def render_puppet_headbutt(t_b: float) -> Tuple[Image.Image, int, int]:
    """
    Renders the unified paper-puppet headbutt animation.
    Zidane's upper body winds up, then strikes violently forward at waist,
    slamming his bald head straight into Materazzi's chest with an impact starburst!
    Returns (layer, shake_x, shake_y).
    """
    layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    
    puppet = get_image(ASSETS_DIR / "puppet_headbutt_unified.png")
    star = get_image(ASSETS_DIR / "impact_starburst.png")
    
    scale = 1.75
    pw, ph = int(puppet.width * scale), int(puppet.height * scale)
    p_scaled = puppet.resize((pw, ph), Image.Resampling.LANCZOS)
    
    cx = 1080 // 2
    cy = 880
    
    shake_x = 0
    shake_y = 0
    show_star = False
    
    # Timing of the strike:
    # t_b in [0.0, 1.0]: Entrance and staredown
    # t_b in [1.0, 1.7]: Wind up backwards (angle -10 deg, dx -40px)
    # t_b in [1.7, 2.1]: Violent headbutt forward (angle reaches +18 deg, dx +80px)
    # t_b in [2.1, 2.8]: Impact hold with WHAM! starburst and camera shake
    # t_b in [2.8, 4.2]: Materazzi collapse: tilts back -35 deg and drops down +220px
    if t_b < 1.0:
        p_in = min(1.0, t_b / 0.5)
        ease_in = math.sin(p_in * math.pi / 2)
        cur_x = int(cx - 150 * (1.0 - ease_in))
        cur_y = cy
        cur_angle = -2.0 + 1.5 * math.sin(t_b * 4.0)
    elif t_b < 1.7:
        p = (t_b - 1.0) / 0.7
        cur_x = int(cx - 45 * p)
        cur_y = cy
        cur_angle = -2.0 - 10.0 * p
    elif t_b < 2.1:
        p = (t_b - 1.7) / 0.4
        cur_x = int((cx - 45) + 125 * (p ** 2))
        cur_y = cy
        cur_angle = -12.0 + 30.0 * (p ** 2)  # Hits +18 deg
        show_star = p > 0.6
    elif t_b < 2.8:
        p_imp = (t_b - 2.1) / 0.7
        cur_x = cx + 80
        cur_y = cy
        cur_angle = 18.0 - 15.0 * p_imp
        show_star = True
        # Camera shake
        if t_b <= 2.4:
            s_mag = 14 * math.sin((t_b - 2.1) * 70)
            shake_x = int(s_mag)
            shake_y = int(s_mag * 0.5)
    else:
        # Collapse downward
        p_col = min(1.0, (t_b - 2.8) / 1.0)
        cur_x = cx + 80 + int(40 * p_col)
        cur_y = int(cy + 260 * (p_col ** 1.5))
        cur_angle = 3.0 - 32.0 * p_col
        show_star = False
        
    # Rotate puppet around its center
    p_box = Image.new("RGBA", (pw * 2, ph * 2), (0, 0, 0, 0))
    p_box.paste(p_scaled, (pw // 2, ph // 2))
    rot_p = p_box.rotate(cur_angle, resample=Image.Resampling.BICUBIC)
    
    layer.paste(rot_p, (cur_x - pw, cur_y - ph), mask=rot_p.split()[-1])
    
    # Impact starburst
    if show_star:
        star_s = star.resize((380, 380), Image.Resampling.LANCZOS)
        layer.paste(star_s, (cur_x - 100, cur_y - 200), mask=star_s.split()[-1])
        
    return layer, shake_x, shake_y

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
    # -------------------------------------------------------------
    if t < 11.20:
        t_b = t
        bg = get_bg_newsprint().copy()
        
        # Entrance 1 (t_b >= 0.1s): Banner Variant A
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B1, (head_x, 180), mask=BANNER_B1.split()[-1])
        
        # Entrance 2 (t_b >= 1.4s): Buffon Polaroid (OpenCV centered)
        if t_b >= 1.4:
            p_buf = min(1.0, (t_b - 1.4) / 0.5)
            ease_buf = math.sin(p_buf * math.pi / 2)
            buf_im = get_image(ASSETS_DIR / "mounted_buffon_polaroid.png").rotate(-3, expand=True)
            buf_y = int(480 - 60 * (1.0 - ease_buf))
            bg.paste(buf_im, (50, buf_y), mask=buf_im.split()[-1])
            
        # Entrance 3 (t_b >= 5.0s): Zidane Panenka Penalty Mount
        if t_b >= 5.0:
            p_pen = min(1.0, (t_b - 5.0) / 0.5)
            ease_pen = math.sin(p_pen * math.pi / 2)
            pen_im = get_image(ASSETS_DIR / "mounted_zidane_penalty.png").rotate(2.5, expand=True)
            pen_x = int(380 + 100 * (1.0 - ease_pen))
            bg.paste(pen_im, (pen_x, 820), mask=pen_im.split()[-1])
            
        # Entrance 4 (t_b >= 8.2s): L'Equipe Newspaper Clipping
        if t_b >= 8.2:
            p_eq = min(1.0, (t_b - 8.2) / 0.5)
            ease_eq = math.sin(p_eq * math.pi / 2)
            eq_im = get_image(ASSETS_DIR / "clipping_lequipe_real.png")
            eq_y = int(1280 + 120 * (1.0 - ease_eq))
            bg.paste(eq_im, (50, eq_y), mask=eq_im.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 2: The Altercation (11.20s - 21.16s)
    # -------------------------------------------------------------
    elif t < 21.16:
        t_b = t - 11.20
        bg = get_bg_parchment().copy()
        
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
            
        # Entrance 3 (t_b >= 4.5s): Real Quote Card
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
    # BEAT 3: The Headbutt (21.16s - 30.14s) — Paper Puppet HERO
    # -------------------------------------------------------------
    elif t < 30.14:
        t_b = t - 21.16
        bg = get_bg_newsprint().copy()
        
        # Banner Variant C
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B3, (head_x, 180), mask=BANNER_B3.split()[-1])
        
        # HERO PAPER PUPPET HEADBUTT (Center of screen, completely unobstructed)
        puppet_layer, shake_x, shake_y = render_puppet_headbutt(t_b)
        bg.paste(puppet_layer, (shake_x, shake_y), mask=puppet_layer.split()[-1])
        
        # Le Monde Breaking News Clipping (enters underneath at t_b >= 4.2s)
        if t_b >= 4.2:
            p_lm = min(1.0, (t_b - 4.2) / 0.5)
            ease_lm = math.sin(p_lm * math.pi / 2)
            lm_im = get_image(ASSETS_DIR / "clipping_coup_de_boule_real.png")
            lm_y = int(1440 + 120 * (1.0 - ease_lm))
            bg.paste(lm_im, (50, lm_y), mask=lm_im.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 4: The Expulsion (30.14s - 39.25s) — Red Card & Guardian Headline
    # -------------------------------------------------------------
    elif t < 39.25:
        t_b = t - 30.14
        bg = get_bg_parchment().copy()
        
        # Banner Variant D
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B4, (head_x, 180), mask=BANNER_B4.split()[-1])
        
        # Red Card Stamp slap-on (t_b >= 1.0s)
        if t_b >= 1.0:
            p_rc = min(1.0, (t_b - 1.0) / 0.35)
            ease_rc = math.sin(p_rc * math.pi / 2)
            stamp_rc = get_image(REUSABLE_DIR / "stamps" / "stamp_red_card.png").resize((420, 150), Image.Resampling.LANCZOS).rotate(12, expand=True)
            rc_scale = 1.0 + 0.3 * (1.0 - ease_rc)
            stamp_s = stamp_rc.resize((int(stamp_rc.width * rc_scale), int(stamp_rc.height * rc_scale)), Image.Resampling.LANCZOS)
            bg.paste(stamp_s, (600, 420), mask=stamp_s.split()[-1])
            
        # The Guardian Newspaper Clipping (t_b >= 2.2s)
        if t_b >= 2.2:
            p_gd = min(1.0, (t_b - 2.2) / 0.5)
            ease_gd = math.sin(p_gd * math.pi / 2)
            gd_im = get_image(ASSETS_DIR / "clipping_guardian_red_card.png")
            gd_y = int(540 - 50 * (1.0 - ease_gd))
            bg.paste(gd_im, (50, gd_y), mask=gd_im.split()[-1])
            
        # Foreground World Cup Trophy Cutout (t_b >= 4.8s)
        if t_b >= 4.8:
            p_tr = min(1.0, (t_b - 4.8) / 0.5)
            ease_tr = math.sin(p_tr * math.pi / 2)
            tr_im = get_image(ASSETS_DIR / "world_cup_trophy_cutout.png")
            tr_scaled = scale_cutout_proportional(tr_im, target_h=820)
            tr_x = int(620 + 80 * (1.0 - ease_tr))
            bg.paste(tr_scaled, (tr_x, 820), mask=tr_scaled.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 5: The Aftermath (39.25s - 47.90s) — Scrapbook Lift & Retract
    # -------------------------------------------------------------
    elif t < 47.90:
        t_b = t - 39.25
        bg = get_bg_newsprint().copy()
        
        # Banner Variant E
        p_b = min(1.0, t_b / 0.45)
        ease_b = math.sin(p_b * math.pi / 2)
        head_x = int(-200 * (1.0 - ease_b) + 40)
        bg.paste(BANNER_B5, (head_x, 180), mask=BANNER_B5.split()[-1])
        
        # 1. Revealed underneath (active at t_b >= 3.8s)
        if t_b >= 3.8:
            # FIFA Sanction Document
            doc_im = get_image(ASSETS_DIR / "fifa_sanction_document.png")
            bg.paste(doc_im, (60, 480), mask=doc_im.split()[-1])
            
            # Golden Ball Award Badge
            badge_gb = get_image(ASSETS_DIR / "golden_ball_award_badge.png")
            bg.paste(badge_gb, (310, 940), mask=badge_gb.split()[-1])
            
        # 2. Scrapbook Card Slide Animation (Cannavaro Trophy Lift)
        # Slides UP from y=1950 to y=440 between t_b=0.0 and 0.6s
        # Holds until t_b=3.6s
        # Slides DOWN back to y=1950 between t_b=3.6s and 4.4s
        scrapbook_im = get_image(ASSETS_DIR / "scrapbook_italy_trophy_lift.png")
        if t_b < 0.6:
            p_up = t_b / 0.6
            ease_up = math.sin(p_up * math.pi / 2)
            sb_y = int(1950 - (1950 - 440) * ease_up)
            bg.paste(scrapbook_im, (80, sb_y), mask=scrapbook_im.split()[-1])
        elif t_b < 3.6:
            bg.paste(scrapbook_im, (80, 440), mask=scrapbook_im.split()[-1])
        elif t_b < 4.4:
            p_down = (t_b - 3.6) / 0.8
            ease_down = p_down ** 2
            sb_y = int(440 + (1950 - 440) * ease_down)
            bg.paste(scrapbook_im, (80, sb_y), mask=scrapbook_im.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 6: The Legend (47.90s - 56.00s) — 108 Caps & Final Tribute
    # -------------------------------------------------------------
    else:
        t_b = t - 47.90
        bg = get_bg_parchment().copy()
        
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

def render_worker(args: Tuple[int, int]):
    start_idx, end_idx = args
    for i in range(start_idx, end_idx):
        frame = render_frame(i)
        out_p = FRAMES_DIR / f"frame_{i:05d}.jpg"
        frame.convert("RGB").save(out_p, format="JPEG", quality=95)

def main():
    print("=" * 70)
    print("  RENDERING 60.00s ZIDANE 2006 DOCUMENTARY (MASTER 5.0)")
    print("=" * 70)
    
    total_frames = 1800  # 60.00s * 30fps
    num_workers = min(os.cpu_count() or 4, 8)
    chunk_size = math.ceil(total_frames / num_workers)
    
    chunks = []
    for w in range(num_workers):
        s_idx = w * chunk_size
        e_idx = min(total_frames, s_idx + chunk_size)
        if s_idx < total_frames:
            chunks.append((s_idx, e_idx))
            
    print(f"Rendering {total_frames} frames across {len(chunks)} threads...")
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        list(executor.map(render_worker, chunks))
        
    print(f"✓ All {total_frames} frames successfully rendered to {FRAMES_DIR}")
    
    # Mux final MP4 with mastered 60s soundtrack
    out_mp4 = RUN_DIR / "zidane_headbutt_master_60s.mp4"
    audio_wav = RUN_DIR / "zidane_mastered_audio_60s.wav"
    
    print("\nMuxing final MP4 with mastered 60s soundtrack...")
    cmd_mux = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", str(FRAMES_DIR / "frame_%05d.jpg"),
        "-i", str(audio_wav),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        str(out_mp4)
    ]
    subprocess.run(cmd_mux, check=True)
    print(f"✓ Master MP4 generated: {out_mp4.name} ({out_mp4.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    main()
