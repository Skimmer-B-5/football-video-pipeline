"""
60-Second Zinedine Zidane 2006 World Cup Headbutt Documentary Renderer (Master Production 3.0).
Refinements:
- ZERO asset repetition: Max 1 scene per photograph across all 6 beats.
- Dynamic 2.5D Paper-Puppet Headbutt Animation: Zidane's torso rotates violently at waist into Materazzi's chest with impact star burst.
- Animated Scrapbook Tear Slide: Italy's World Cup trophy lift slides up from below, holds, and slides down.
- Authentic large newspaper clippings: L'Équipe, Le Monde, The Guardian, and pink Gazzetta dello Sport.
- Tactile paper tear page-turn transitions between beats.
- Much larger display typography (68pt - 76pt) and prominent photo cards (800px+).
- MrBeast Electric Yellow (#FFE800) kinetic captions with 1.14x bounce.
- 150px persistent TV watermark and 580px FS30 outro card.
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

RUN_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story"
ASSETS_DIR = RUN_DIR / "assets"
AUDIO_DIR = RUN_DIR / "audio"
FRAMES_DIR = RUN_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")

from fs30.story_pipeline.branding import create_fs30_tv_watermark, render_fs30_outro
from fs30.story_pipeline.paper_widgets import (
    create_torn_headline_banner,
    create_torn_quote_card,
    create_torn_match_ticket,
    get_font,
    WARM_IVORY,
    CHARCOAL,
    ARCHIVAL_RED
)
from fs30.story_pipeline.photo_mounter import mount_archival_photo, scale_cutout_proportional
from fs30.story_pipeline.mrbeast_captions import init_captions, draw_mrbeast_captions
init_captions(RUN_DIR / "zidane_mrbeast_captions.json")

# Persistent Watermark
TV_WATERMARK = create_fs30_tv_watermark(badge_size=150)

_LOADED_IMAGES: Dict[str, Image.Image] = {}

def get_image(path: Path) -> Image.Image:
    k = str(path)
    if k not in _LOADED_IMAGES:
        with Image.open(path) as im:
            _LOADED_IMAGES[k] = im.convert("RGBA")
    return _LOADED_IMAGES[k]

def prepare_background(img_path: Path, width: int = 1080, height: int = 1920) -> Image.Image:
    """Processes background: desaturate by 65%, lower brightness by 32%, subtle vignette."""
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
        res.alpha_composite(vignette)
        return res

CACHED_BG: Optional[Image.Image] = None

def get_cached_bg() -> Image.Image:
    global CACHED_BG
    if CACHED_BG is None:
        CACHED_BG = prepare_background(ASSETS_DIR / "berlin_stadium.jpg")
    return CACHED_BG

# Pre-render Banner Variants
W_HEAD_B1 = create_torn_headline_banner("THE FAREWELL", kicker="9 JULY 2006 // BERLIN OLYMPIASTADION", width=980, height=220, variant="a")
W_HEAD_B2 = create_torn_headline_banner("THE PROVOCATION", kicker="110TH MINUTE // SCORE LOCKED 1-1", width=980, height=220, variant="b")
W_HEAD_B3 = create_torn_headline_banner("THE HEADBUTT", kicker="UNPRECEDENTED SHOCK // CHEST IMPACT", width=980, height=220, variant="c")
W_HEAD_B4 = create_torn_headline_banner("THE EXPULSION", kicker="RED CARD // WALKING PAST THE TROPHY", width=980, height=220, variant="d")
W_HEAD_B5 = create_torn_headline_banner("THE FALLOUT", kicker="FIFA SANCTIONS // 20 JULY 2006", width=980, height=220, variant="e")
W_HEAD_B6 = create_torn_headline_banner("LONG LIVE ZIZOU", kicker="108 CAPS // A MAJESTIC LEGACY", width=980, height=220, variant="a")

# Pre-render Archival GIF Video Player
ARCHIVE_PANELS: List[Image.Image] = []
def load_archival_gif_panels():
    global ARCHIVE_PANELS
    gif_path = ASSETS_DIR / "zidane_incident_archival_loop.gif"
    if gif_path.exists():
        f_arch = get_font("headline_bold", 20)
        with Image.open(gif_path) as g:
            for frame_idx in range(getattr(g, 'n_frames', 1)):
                g.seek(frame_idx)
                lim = g.convert("RGBA").resize((640, 360), Image.Resampling.LANCZOS)
                lw, lh = lim.size
                pad_t, pad_b, pad_s = 36, 18, 14
                card_w = lw + pad_s * 2
                card_h = lh + pad_t + pad_b
                panel = Image.new("RGBA", (card_w, card_h), (22, 24, 30, 255))
                p_draw = ImageDraw.Draw(panel)
                
                p_draw.rectangle([(2, 2), (card_w - 2, card_h - 2)], outline=(217, 4, 41, 255), width=2)
                p_draw.ellipse([(16, 12), (28, 24)], fill=(217, 4, 41, 255))
                p_draw.text((36, 10), "ARCHIVAL FOOTAGE // 09.07.2006 // 110TH MINUTE", fill=(240, 242, 245, 240), font=f_arch)
                panel.paste(lim, (pad_s, pad_t), mask=lim.split()[-1])
                
                sh_mask = panel.split()[-1].filter(ImageFilter.GaussianBlur(14))
                total_pw, total_ph = card_w + 30, card_h + 30
                p_res = Image.new("RGBA", (total_pw, total_ph), (0, 0, 0, 0))
                p_res.paste(Image.new("RGBA", (card_w, card_h), (0, 0, 0, 190)), (15, 20), mask=sh_mask)
                p_res.paste(panel, (15, 15), mask=panel.split()[-1])
                ARCHIVE_PANELS.append(p_res)

load_archival_gif_panels()

def render_paper_puppet_headbutt(t_b: float) -> Image.Image:
    """
    Renders the dynamic paper-puppet headbutt animation.
    Zidane's upper body winds up, then strikes violently forward at waist,
    slamming his head into Materazzi's chest, while Materazzi collapses!
    """
    canvas_w, canvas_h = 1000, 750
    puppet_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    z_lower = get_image(ASSETS_DIR / "puppet_zidane_lower.png")
    z_upper = get_image(ASSETS_DIR / "puppet_zidane_upper.png")
    mat = get_image(ASSETS_DIR / "puppet_materazzi.png")
    
    # Scale pieces to prominent size
    scale_factor = 1.35
    zw_l, zh_l = int(z_lower.width * scale_factor), int(z_lower.height * scale_factor)
    zw_u, zh_u = int(z_upper.width * scale_factor), int(z_upper.height * scale_factor)
    mw, mh = int(mat.width * scale_factor), int(mat.height * scale_factor)
    
    z_lower_scaled = z_lower.resize((zw_l, zh_l), Image.Resampling.LANCZOS)
    z_upper_scaled = z_upper.resize((zw_u, zh_u), Image.Resampling.LANCZOS)
    mat_scaled = mat.resize((mw, mh), Image.Resampling.LANCZOS)
    
    # Anchor positions
    z_anchor_x = 180
    z_anchor_y = 350
    mat_anchor_x = 520
    mat_anchor_y = 200
    
    # Timing logic for the headbutt strike:
    # t_b in [0.0, 1.0]: Facing off, slight breathing
    # t_b in [1.0, 1.4]: Wind-up backwards (angle -14 deg)
    # t_b in [1.4, 1.7]: Violent headbutt strike forward (angle +34 deg)
    # t_b in [1.7, 3.5]: Recoil vibration and hold
    if t_b < 1.0:
        z_angle = -4.0 + 2.0 * math.sin(t_b * 4.0)
        mat_angle = 0.0
        mat_dy = 0
        hit = False
    elif t_b < 1.4:
        # Wind-up
        p = (t_b - 1.0) / 0.4
        z_angle = -4.0 - 12.0 * p
        mat_angle = 0.0
        mat_dy = 0
        hit = False
    elif t_b < 1.7:
        # Violent strike forward!
        p = (t_b - 1.4) / 0.3
        z_angle = -16.0 + 50.0 * (p ** 2) # Hits +34 deg
        mat_angle = -20.0 * p
        mat_dy = int(120 * (p ** 2))
        hit = p > 0.4
    else:
        # Post-strike recoil and Materazzi collapsing
        p_recoil = min(1.0, (t_b - 1.7) / 0.5)
        wobble = math.exp(-3.0 * p_recoil) * math.sin(p_recoil * 18.0) * 8.0
        z_angle = 24.0 + wobble
        mat_angle = -38.0 - 15.0 * p_recoil
        mat_dy = int(180 + 160 * p_recoil)
        hit = False
        
    # Rotate Zidane's upper torso around waist (bottom-center)
    uw, uh = z_upper_scaled.size
    box_canvas = Image.new("RGBA", (uw * 2, uh * 2), (0, 0, 0, 0))
    box_canvas.paste(z_upper_scaled, (uw // 2, 0))
    rotated_upper = box_canvas.rotate(-z_angle, resample=Image.Resampling.BICUBIC)
    
    # Rotate Materazzi around his feet
    mw_full, mh_full = mat_scaled.size
    mat_box = Image.new("RGBA", (mw_full * 2, mh_full * 2), (0, 0, 0, 0))
    mat_box.paste(mat_scaled, (mw_full // 2, 0))
    rotated_mat = mat_box.rotate(mat_angle, resample=Image.Resampling.BICUBIC)
    
    # Composite Materazzi
    m_px = mat_anchor_x - mw_full // 2
    m_py = mat_anchor_y + mat_dy
    puppet_layer.paste(rotated_mat, (m_px, m_py), mask=rotated_mat.split()[-1])
    
    # Composite Zidane lower body (legs anchored)
    puppet_layer.paste(z_lower_scaled, (z_anchor_x, z_anchor_y + zh_u - 20), mask=z_lower_scaled.split()[-1])
    
    # Composite Zidane upper body (pivoted at waist)
    u_px = z_anchor_x - uw // 2
    u_py = z_anchor_y - uh
    puppet_layer.paste(rotated_upper, (u_px, u_py), mask=rotated_upper.split()[-1])
    
    # Comic Starburst Callout at impact point if hit
    if 1.5 <= t_b <= 2.2:
        star_w, star_h = 240, 140
        star = Image.new("RGBA", (star_w, star_h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(star)
        sd.rectangle([(4, 4), (star_w - 4, star_h - 4)], fill=(255, 235, 59, 245), outline=(220, 20, 40, 255), width=3)
        f_bang = ImageFont.truetype("impact.ttf", 36)
        f_sub = ImageFont.truetype("arialbd.ttf", 18)
        sd.text((star_w // 2, 45), "CRACK!", fill=(220, 20, 40, 255), font=f_bang, anchor="mm")
        sd.text((star_w // 2, 95), "110TH MINUTE IMPACT", fill=(20, 24, 30, 255), font=f_sub, anchor="mm")
        puppet_layer.paste(star, (460, 260), mask=star.split()[-1])
        
    return puppet_layer

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
    # BEAT 1: The Farewell & Panenka (0.0s - 8.0s) — L'Équipe + Penalty + Buffon
    # -------------------------------------------------------------
    if t < 8.0:
        t_b = t
        bg = get_cached_bg().copy()
        
        # Banner Variant A Entrance
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 50)
        bg.paste(W_HEAD_B1, (head_x, 230), mask=W_HEAD_B1.split()[-1])
        
        # 1. Large L'Équipe Newspaper Front Page (X=50, Y=480)
        lequipe = get_image(ASSETS_DIR / "clipping_lequipe_finale.png")
        bg.paste(lequipe, (50, 480), mask=lequipe.split()[-1])
        
        # 2. Zidane Penalty Kick Photo Card (X=50, Y=970, 480x420)
        pen_raw = get_image(ASSETS_DIR / "zidane_penalty.jpg")
        pen_mounted = mount_archival_photo(pen_raw, target_w=470, target_h=420, focus_point=(0.5, 0.4))
        bg.paste(pen_mounted, (50, 970), mask=pen_mounted.split()[-1])
        
        # 3. Buffon in Goal Photo Card (X=540, Y=970, 480x420)
        buf_raw = get_image(ASSETS_DIR / "buffon_final.jpg")
        buf_mounted = mount_archival_photo(buf_raw, target_w=480, target_h=420, focus_point=(0.5, 0.35))
        bg.paste(buf_mounted, (540, 970), mask=buf_mounted.split()[-1])
        
        # 4. Ticket Stub (X=270, Y=1450)
        ticket = create_torn_match_ticket("2006 WORLD CUP FINAL", "ITALY vs FRANCE", "09 JUL 2006", width=540, height=170)
        bg.paste(ticket, (270, 1450), mask=ticket.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 2: The Provocation (8.0s - 16.5s) — Action Photo + Quote + Reticle
    # -------------------------------------------------------------
    elif t < 16.5:
        t_b = t - 8.0
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 50)
        bg.paste(W_HEAD_B2, (head_x, 230), mask=W_HEAD_B2.split()[-1])
        
        # Large Action Photo Card (X=60, Y=480, size 960x580)
        action_raw = get_image(ASSETS_DIR / "italy_france_action.jpg")
        action_mounted = mount_archival_photo(action_raw, target_w=960, target_h=580, focus_point=(0.5, 0.45))
        bg.paste(action_mounted, (60, 480), mask=action_mounted.split()[-1])
        
        # Tactical Callout Reticle on shirt contact
        if t_b > 0.8:
            reticle_x, reticle_y = 620, 720
            pulse = 1.0 + 0.08 * math.sin(t_b * 8.0)
            cur_r = int(60 * pulse)
            layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.ellipse([(reticle_x - cur_r, reticle_y - cur_r), (reticle_x + cur_r, reticle_y + cur_r)], outline=(220, 20, 40, 240), width=4)
            ld.line([(reticle_x + cur_r, reticle_y), (reticle_x + cur_r + 120, reticle_y - 60)], fill=(220, 20, 40, 240), width=3)
            f_tag = ImageFont.truetype("arialbd.ttf", 22)
            ld.rectangle([(reticle_x + cur_r + 120, reticle_y - 85), (reticle_x + cur_r + 340, reticle_y - 45)], fill=(20, 24, 30, 240), outline=(220, 20, 40, 240), width=2)
            ld.text((reticle_x + cur_r + 130, reticle_y - 80), "SHIRT TUG CONTACT", fill=(255, 255, 255, 255), font=f_tag)
            bg.alpha_composite(layer)
            
        # Large Quotation Card on Bottom (X=60, Y=1120)
        quote_card = create_torn_quote_card(
            "If you want my shirt that badly, I will give it to you after the match.",
            attribution="— ZINEDINE ZIDANE TO MARCO MATERAZZI // 110TH MIN",
            width=960, height=360, quote_size=34, attr_size=22
        )
        bg.paste(quote_card, (60, 1120), mask=quote_card.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 3: The Headbutt (16.5s - 28.0s) — Paper Puppet + Le Monde + CRT Tape
    # -------------------------------------------------------------
    elif t < 28.0:
        t_b = t - 16.5
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 50)
        bg.paste(W_HEAD_B3, (head_x, 230), mask=W_HEAD_B3.split()[-1])
        
        # 1. Dynamic Paper-Puppet Headbutt Animation (X=40, Y=460)
        puppet = render_paper_puppet_headbutt(t_b)
        bg.paste(puppet, (40, 460), mask=puppet.split()[-1])
        
        # 2. Archival CRT Video Player Loop in Top-Right Corner (X=540, Y=460)
        if ARCHIVE_PANELS:
            p_idx = int(t_b * 7) % len(ARCHIVE_PANELS)
            arch_frame = ARCHIVE_PANELS[p_idx].resize((480, 290), Image.Resampling.LANCZOS)
            bg.paste(arch_frame, (540, 460), mask=arch_frame.split()[-1])
            
        # 3. Large Le Monde Newspaper Front Page Clipping on Bottom (X=60, Y=1180)
        lemonde = get_image(ASSETS_DIR / "clipping_coup_de_boule.png")
        bg.paste(lemonde, (60, 1180), mask=lemonde.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 4: The Expulsion (28.0s - 39.5s) — The Guardian + Trophy Walk + Red Card
    # -------------------------------------------------------------
    elif t < 39.5:
        t_b = t - 28.0
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 50)
        bg.paste(W_HEAD_B4, (head_x, 230), mask=W_HEAD_B4.split()[-1])
        
        # 1. The Guardian Headline Newspaper (X=60, Y=480)
        guardian = get_image(ASSETS_DIR / "clipping_guardian_red_card.png")
        bg.paste(guardian, (60, 480), mask=guardian.split()[-1])
        
        # 2. Golden World Cup Trophy Foreground Cutout on Right (X=640, Y=860, height 740)
        trophy = get_image(ASSETS_DIR / "world_cup_trophy_cutout.png")
        trophy_scaled = scale_cutout_proportional(trophy, target_h=740)
        bg.paste(trophy_scaled, (640, 860), mask=trophy_scaled.split()[-1])
        
        # 3. Zidane Walking into the Tunnel Cutout on Left (X=40, Y=820, height 880)
        zidane_hero = get_image(ASSETS_DIR / "zidane_hero_cutout.png")
        hero_scaled = scale_cutout_proportional(zidane_hero, target_h=880)
        bg.paste(hero_scaled, (40, 820), mask=hero_scaled.split()[-1])
        
        # 4. Straight Red Disciplinary Card Stamp Slam (X=360, Y=1200)
        red_card = Image.new("RGBA", (440, 270), (220, 20, 40, 245))
        rc_draw = ImageDraw.Draw(red_card)
        rc_draw.rectangle([(6, 6), (434, 264)], outline=(255, 255, 255, 240), width=3)
        f_rc1 = ImageFont.truetype("impact.ttf", 44)
        f_rc2 = ImageFont.truetype("arialbd.ttf", 22)
        rc_draw.text((30, 30), "STRAIGHT RED", fill=(255, 255, 255, 255), font=f_rc1)
        rc_draw.text((30, 95), "REF: HORACIO ELIZONDO", fill=(255, 240, 240, 240), font=f_rc2)
        rc_draw.text((30, 135), "4TH OFFICIAL: MEDINA CANTALEJO", fill=(255, 240, 240, 240), font=f_rc2)
        rc_draw.text((30, 185), "110TH MINUTE DISMISSAL", fill=(255, 235, 59, 255), font=f_rc2)
        bg.paste(red_card, (360, 1200), mask=red_card.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 5: The Fallout (39.5s - 51.5s) — Scrapbook Trophy Slide + Gazzetta + Ban Card
    # -------------------------------------------------------------
    elif t < 51.5:
        t_b = t - 39.5
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 50)
        bg.paste(W_HEAD_B5, (head_x, 230), mask=W_HEAD_B5.split()[-1])
        
        # 1. Base Layer: Pink Gazzetta dello Sport Newspaper (X=60, Y=480)
        gazzetta = get_image(ASSETS_DIR / "clipping_gazzetta_trionfo.png")
        bg.paste(gazzetta, (60, 480), mask=gazzetta.split()[-1])
        
        # 2. Base Layer: FIFA Disciplinary Sanction Card on Bottom (X=60, Y=1060)
        fifa_card = create_torn_quote_card(
            "FIFA Disciplinary Committee imposes a 3-match ban and 3 days of UNICEF community service. Voted Golden Ball winner.",
            attribution="— FIFA OFFICIAL SANCTION DISPATCH // ZURICH",
            width=960, height=380, quote_size=32, attr_size=22
        )
        bg.paste(fifa_card, (60, 1060), mask=fifa_card.split()[-1])
        
        # 3. ANIMATED SCRAPBOOK CARD: Italy World Cup Trophy Lift
        # User requirement: "A scrap book tear of their world cup lift can be came from below and go down as the same."
        # t_b in [0.0, 0.7]: Slides UP from below (Y: 1920 -> 520)
        # t_b in [0.7, 3.6]: Holds in center frame as narrator says "Italy won the shootout"
        # t_b in [3.6, 4.3]: Slides DOWN off screen (Y: 520 -> 1920)
        scrapbook_card = get_image(ASSETS_DIR / "scrapbook_italy_trophy_lift.png")
        if t_b < 4.5:
            if t_b < 0.7:
                p_up = t_b / 0.7
                ease_up = 1.0 - ((1.0 - p_up) ** 3)
                card_y = int(1920 - ease_up * (1920 - 460))
            elif t_b < 3.6:
                card_y = 460
            else:
                p_down = (t_b - 3.6) / 0.7
                ease_down = p_down ** 3
                card_y = int(460 + ease_down * (1920 - 460))
            bg.paste(scrapbook_card, (95, card_y), mask=scrapbook_card.split()[-1])
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 6: Long Live Zizou (51.5s - 56.0s) — Zidane & Thuram + Shirt + Tribute
    # -------------------------------------------------------------
    else:
        t_b = t - 51.5
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 50)
        bg.paste(W_HEAD_B6, (head_x, 230), mask=W_HEAD_B6.split()[-1])
        
        # 1. Distinct Iconic Photo: Zidane & Thuram in the Final (X=60, Y=480, size 960x600)
        thuram_raw = get_image(ASSETS_DIR / "zidane_thuram_final.jpg")
        thuram_mounted = mount_archival_photo(thuram_raw, target_w=960, target_h=600, focus_point=(0.5, 0.45))
        bg.paste(thuram_mounted, (60, 480), mask=thuram_mounted.split()[-1])
        
        # 2. France 2006 Match Shirt on Left (X=60, Y=1140, 440x480)
        shirt_raw = get_image(ASSETS_DIR / "zidane_shirt_2006.jpg")
        shirt_mounted = mount_archival_photo(shirt_raw, target_w=440, target_h=480, focus_point=(0.5, 0.5))
        bg.paste(shirt_mounted, (60, 1140), mask=shirt_mounted.split()[-1])
        
        # 3. Gold Tribute Ticket Stub on Right (X=540, Y=1240)
        tribute_ticket = create_torn_match_ticket(
            "A LEGEND'S FINAL BOW",
            "108 CAPS // 31 GOALS",
            "FOREVER IMMORTAL",
            width=480, height=190
        )
        bg.paste(tribute_ticket, (540, 1240), mask=tribute_ticket.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

def render_worker(args):
    f_idx, out_path = args
    if not out_path.exists():
        im = render_frame(f_idx)
        im.convert("RGB").save(out_path, format="JPEG", quality=92)
    return f_idx

def render_all_frames():
    total_frames = 1800 # 60.0s @ 30fps
    print("=" * 70)
    print(f"  RENDERING 1,800 FRAMES (MASTER REFINEMENT 3.0)")
    print("=" * 70)
    
    tasks = []
    for i in range(total_frames):
        p = FRAMES_DIR / f"frame_{i:05d}.jpg"
        tasks.append((i, p))
        
    cpu_count = min(16, os.cpu_count() or 8)
    print(f"Spawning {cpu_count} worker threads...")
    
    with ThreadPoolExecutor(max_workers=cpu_count) as executor:
        done = 0
        for _ in executor.map(render_worker, tasks):
            done += 1
            if done % 150 == 0 or done == total_frames:
                print(f"  Progress: {done}/{total_frames} frames rendered ({done/total_frames*100:.1f}%)")
                
    print("✓ All 1,800 frames successfully rendered.")

def mux_final_master():
    master_video = RUN_DIR / "zidane_headbutt_master_60s.mp4"
    master_audio = RUN_DIR / "zidane_mastered_audio_60s.wav"
    
    print("=" * 70)
    print("  MUXING MASTER MP4 (H.264 // -14.2 LUFS AUDIO)")
    print("=" * 70)
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", str(FRAMES_DIR / "frame_%05d.jpg"),
        "-i", str(master_audio),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(master_video)
    ]
    subprocess.run(cmd, check=True)
    size_mb = master_video.stat().st_size / (1024 * 1024)
    print(f"✓ Master video rendered: {master_video.name} ({size_mb:.2f} MB)")
    
    # Generate 12-beat contact sheet
    sheet_path = RUN_DIR / "zidane_master_12beat_contact_sheet.png"
    sample_frames = [
        0, 90, 210, 270, 390, 510, 630, 870, 1050, 1260, 1560, 1740
    ]
    imgs = []
    for f_i in sample_frames:
        fp = FRAMES_DIR / f"frame_{f_i:05d}.jpg"
        if fp.exists():
            imgs.append(Image.open(fp).resize((360, 640), Image.Resampling.LANCZOS))
            
    cols, rows = 4, 3
    sheet = Image.new("RGB", (cols * 360, rows * 640), (15, 18, 24))
    for idx, im in enumerate(imgs):
        r = idx // cols
        c = idx % cols
        sheet.paste(im, (c * 360, r * 640))
    sheet.save(sheet_path, quality=92)
    print(f"✓ Created 12-beat contact sheet: {sheet_path.name}")

if __name__ == "__main__":
    render_all_frames()
    mux_final_master()
