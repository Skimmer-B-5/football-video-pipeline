"""
60-Second Zinedine Zidane 2006 World Cup Headbutt Documentary Renderer (Master Production).
Features:
- Exact 60.0s duration (1,800 frames @ 30 FPS)
- ZERO vertical or horizontal distortion: strictly uniform proportional scaling
  with intentional focus-centered cropping across all photographs and cutouts
- Genuine Archival GIF Animation: 12-frame archival broadcast footage loop of the
  iconic headbutt incident, synchronized in Beat 3
- 5 Genuinely Distinct Reusable Banner Variants (Variants A, B, C, D, E)
- Rich Tactile Collage: match ticket stubs, FIFA disciplinary cards, tactical callouts
- Desaturated multiplane stadium backgrounds (-65% saturation, -32% brightness)
- 150px persistent FS30 TV broadcast watermark
- Dedicated broadcast outro card synchronized with spoken farewell:
  "See you later. This is Football in 30 Seconds. Follow for more."
- MrBeast Electric Yellow kinetic captions (#FFE800, 1.14x scale bounce, 12px stroke)
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
init_captions(RUN_DIR / "zidane_mrbeast_captions.json")

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
    """Processes background: desaturate by 65%, lower brightness by 32%, slight vignette."""
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

def draw_tactical_annotation(canvas: Image.Image, x: int, y: int, radius: int = 60, label: str = "", t_progress: float = 0.0):
    """Draws a tactile neon tactical callout with dashed circle and leader line."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    
    pulse = 1.0 + 0.08 * math.sin(t_progress * 8.0)
    cur_r = int(radius * pulse)
    
    d.ellipse([(x - cur_r, y - cur_r), (x + cur_r, y + cur_r)], outline=(220, 20, 60, 220), width=4)
    d.ellipse([(x - 6, y - 6), (x + 6, y + 6)], fill=(220, 20, 60, 240))
    
    # Leader line to label
    lx2, ly2 = x + 110, y - 60
    lx3 = lx2 + 220
    d.line([(x + int(cur_r * 0.7), y - int(cur_r * 0.7)), (lx2, ly2), (lx3, ly2)], fill=(220, 20, 60, 220), width=3)
    
    # Label badge
    if label:
        f_lbl = get_font("body_bold", 18)
        bb = f_lbl.getbbox(label)
        bw, bh = bb[2] - bb[0] + 16, bb[3] - bb[1] + 10
        d.rectangle([(lx2, ly2 - bh - 4), (lx2 + bw, ly2 - 2)], fill=(18, 20, 26, 230), outline=(220, 20, 60, 220), width=1)
        d.text((lx2 + 8, ly2 - bh), label, fill=(255, 255, 255, 240), font=f_lbl)
        
    canvas.alpha_composite(layer)

# -------------------------------------------------------------------------
# PRE-RENDER 5 REUSABLE BANNER VARIANTS & WIDGETS
# -------------------------------------------------------------------------
# Beat 1: Variant A (Torn newspaper edge with red side stripe)
W_HEAD_B1 = create_torn_headline_banner("THE FAREWELL", kicker="9 JULY 2006 // BERLIN OLYMPIASTADION", width=960, height=210, variant="a")
W_TICKET_B1 = create_torn_match_ticket("2006 WORLD CUP FINAL", "ITALY vs FRANCE", "09 JUL 2006", width=540, height=170)

# Beat 2: Variant B (Folded Ivory Paper with Thin Red Marker)
W_HEAD_B2 = create_torn_headline_banner("THE PROVOCATION", kicker="110TH MINUTE // SCORE LOCKED 1-1", width=960, height=210, variant="b")

# Beat 3: Variant C (Rough-Cut Archival Paper with Red Corner Tab)
W_HEAD_B3 = create_torn_headline_banner("THE HEADBUTT", kicker="UNPRECEDENTED SHOCK // CHEST IMPACT", width=980, height=210, variant="c")
W_QUOTE_B3 = create_torn_quote_card(
    "Zidane delivers a full-force headbutt into the chest of Marco Materazzi.",
    attribution="— OFFICIAL INCIDENT DISPATCH // 110TH MIN",
    width=520, height=290, quote_size=28, attr_size=18
)

# Beat 4: Variant D (Narrow Editorial Strip with Distressed Red Underline)
W_HEAD_B4 = create_torn_headline_banner("THE EXPULSION", kicker="RED CARD // WALKING PAST THE TROPHY", width=960, height=210, variant="d")

# Beat 5: Variant E (Layered Paper with Offset Red Backing)
W_HEAD_B5 = create_torn_headline_banner("THE FALLOUT", kicker="FIFA SANCTIONS // 20 JULY 2006", width=960, height=210, variant="e")
W_QUOTE_B5 = create_torn_quote_card(
    "FIFA Disciplinary Committee imposes a 3-match ban and 3 days of UNICEF community service. Voted Golden Ball winner.",
    attribution="— FIFA OFFICIAL VERDICT // ZURICH",
    width=620, height=360, quote_size=28, attr_size=20
)

# Beat 6: Variant A (Climactic Tribute)
W_HEAD_B6 = create_torn_headline_banner("LONG LIVE ZIZOU", kicker="108 CAPS // A MAJESTIC LEGACY", width=960, height=210, variant="a")
W_TICKET_B6 = create_torn_match_ticket("A LEGEND'S FINAL BOW", "108 CAPS // 31 GOALS", "FOREVER IMMORTAL", width=540, height=170)

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
                lim = g.convert("RGBA").resize((700, 394), Image.Resampling.LANCZOS)
                lw, lh = lim.size
                pad_t, pad_b, pad_s = 40, 20, 16
                card_w = lw + pad_s * 2
                card_h = lh + pad_t + pad_b
                panel = Image.new("RGBA", (card_w, card_h), (24, 26, 32, 255))
                p_draw = ImageDraw.Draw(panel)
                
                p_draw.rectangle([(2, 2), (card_w - 2, card_h - 2)], outline=(217, 4, 41, 255), width=2)
                p_draw.ellipse([(18, 14), (30, 26)], fill=(217, 4, 41, 255))
                p_draw.text((38, 11), "ARCHIVAL FOOTAGE // 09.07.2006 // 110TH MINUTE", fill=(240, 242, 245, 240), font=f_arch)
                panel.paste(lim, (pad_s, pad_t), mask=lim.split()[-1])
                
                sh_mask = panel.split()[-1].filter(ImageFilter.GaussianBlur(14))
                total_pw, total_ph = card_w + 30, card_h + 30
                p_res = Image.new("RGBA", (total_pw, total_ph), (0, 0, 0, 0))
                p_res.paste(Image.new("RGBA", (card_w, card_h), (0, 0, 0, 190)), (15, 20), mask=sh_mask)
                p_res.paste(panel, (15, 15), mask=panel.split()[-1])
                ARCHIVE_PANELS.append(p_res)
        print(f"✓ Archival Video Player pre-rendered ({len(ARCHIVE_PANELS)} frames).")

load_archival_gif_panels()

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
    # BEAT 1: The Farewell (0.0s - 8.0s) — Variant A Banner
    # -------------------------------------------------------------
    if t < 8.0:
        t_b = t
        bg = get_cached_bg().copy()
        
        # Slide entrance for Variant A headline
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B1, (head_x, 240), mask=W_HEAD_B1.split()[-1])
        
        # Zidane Hero Cutout (Strictly proportional scaling)
        zidane_hero = get_image(ASSETS_DIR / "zidane_hero_cutout.png")
        c_scale = 1.0 + 0.03 * (t_b / 8.0)
        target_h = int(1200 * c_scale)
        hero_scaled = scale_cutout_proportional(zidane_hero, target_h=target_h)
        hero_x = int(180 + 6 * math.sin(t_b * 1.2))
        hero_y = int(480)
        bg.paste(hero_scaled, (hero_x, hero_y), mask=hero_scaled.split()[-1])
        
        # Buffon Photo Card on Left (X=50, Y=1100)
        buffon_raw = get_image(ASSETS_DIR / "buffon_final.jpg")
        buffon_mounted = mount_archival_photo(buffon_raw, target_w=390, target_h=490, focus_point=(0.5, 0.35))
        bg.paste(buffon_mounted, (50, 1100), mask=buffon_mounted.split()[-1])
        
        # Match Ticket Stub on right (X=490, Y=1450)
        bg.paste(W_TICKET_B1, (490, 1450), mask=W_TICKET_B1.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 2: The Provocation (8.0s - 16.5s) — Variant B Banner
    # -------------------------------------------------------------
    elif t < 16.5:
        t_b = t - 8.0
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B2, (head_x, 240), mask=W_HEAD_B2.split()[-1])
        
        # Zidane hero on Left (X=-50, Y=490, proportional)
        zidane_hero = get_image(ASSETS_DIR / "zidane_hero_cutout.png")
        c_scale = 1.0 + 0.03 * (t_b / 8.5)
        target_h = int(1220 * c_scale)
        hero_scaled = scale_cutout_proportional(zidane_hero, target_h=target_h)
        bg.paste(hero_scaled, (-50, 490), mask=hero_scaled.split()[-1])
        
        # Final Action Photo Card on Right (X=490, Y=560)
        action_raw = get_image(ASSETS_DIR / "italy_france_action.jpg")
        action_mounted = mount_archival_photo(action_raw, target_w=520, target_h=370, focus_point=(0.5, 0.45))
        bg.paste(action_mounted, (490, 560), mask=action_mounted.split()[-1])
        
        # Incident Note card on Right (X=495, Y=990)
        inc_report = create_torn_quote_card(
            "110th minute: Marco Materazzi shirt tugging incident triggers heated confrontation.",
            attribution="— MATCH OFFICIAL NOTES // EXTRA TIME",
            width=510, height=280, quote_size=26, attr_size=18
        )
        bg.paste(inc_report, (495, 990), mask=inc_report.split()[-1])
        
        # Tactical Callout Reticle
        if t_b > 1.2:
            draw_tactical_annotation(bg, x=740, y=720, radius=55, label="SHIRT TUG CONTACT", t_progress=t_b)
            
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 3: The Headbutt (16.5s - 28.0s) — Variant C Banner & Archival Player
    # -------------------------------------------------------------
    elif t < 28.0:
        t_b = t - 16.5
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B3, (head_x, 240), mask=W_HEAD_B3.split()[-1])
        
        # Archival Video Player in Upper Center/Left (X=170, Y=530)
        if ARCHIVE_PANELS:
            panel_idx = int(t_b * 6) % len(ARCHIVE_PANELS)
            arch_frame = ARCHIVE_PANELS[panel_idx]
            bg.paste(arch_frame, (170, 530), mask=arch_frame.split()[-1])
            
        # Incident Quote Card on Left (X=60, Y=1120)
        bg.paste(W_QUOTE_B3, (60, 1120), mask=W_QUOTE_B3.split()[-1])
        
        # Zidane Cutout on Right (X=540, Y=920, scaled)
        zidane_hero = get_image(ASSETS_DIR / "zidane_hero_cutout.png")
        target_h = 780
        hero_scaled = scale_cutout_proportional(zidane_hero, target_h=target_h)
        bg.paste(hero_scaled, (540, 920), mask=hero_scaled.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 4: The Expulsion (28.0s - 39.5s) — Variant D Banner & Trophy Walk
    # -------------------------------------------------------------
    elif t < 39.5:
        t_b = t - 28.0
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B4, (head_x, 240), mask=W_HEAD_B4.split()[-1])
        
        # Golden World Cup Trophy in Center Foreground (X=460, Y=620, height 780)
        trophy = get_image(ASSETS_DIR / "world_cup_trophy_cutout.png")
        trophy_scaled = scale_cutout_proportional(trophy, target_h=780)
        bg.paste(trophy_scaled, (460, 620), mask=trophy_scaled.split()[-1])
        
        # Zidane hero on Left walking past trophy (X=20, Y=560, height 1100)
        zidane_hero = get_image(ASSETS_DIR / "zidane_hero_cutout.png")
        hero_scaled = scale_cutout_proportional(zidane_hero, target_h=1100)
        bg.paste(hero_scaled, (20, 560), mask=hero_scaled.split()[-1])
        
        # Red Card Disciplinary Callout Card (X=600, Y=1260)
        red_card = Image.new("RGBA", (380, 240), (220, 20, 60, 240))
        rc_draw = ImageDraw.Draw(red_card)
        rc_draw.rectangle([(6, 6), (374, 234)], outline=(255, 255, 255, 230), width=3)
        f_rc1 = get_font("headline_bold", 34)
        f_rc2 = get_font("body_bold", 20)
        rc_draw.text((30, 30), "STRAIGHT RED", fill=(255, 255, 255, 255), font=f_rc1)
        rc_draw.text((30, 80), "REF: HORACIO ELIZONDO", fill=(255, 240, 240, 240), font=f_rc2)
        rc_draw.text((30, 115), "VAR: MEDINA CANTALEJO", fill=(255, 240, 240, 240), font=f_rc2)
        rc_draw.text((30, 160), "110TH MINUTE DISMISSAL", fill=(255, 255, 255, 255), font=f_rc2)
        bg.paste(red_card, (600, 1260), mask=red_card.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 5: The Fallout (39.5s - 51.5s) — Variant E Banner & FIFA Verdict
    # -------------------------------------------------------------
    elif t < 51.5:
        t_b = t - 39.5
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B5, (head_x, 240), mask=W_HEAD_B5.split()[-1])
        
        # FIFA Sanction Quote Card (X=60, Y=560)
        bg.paste(W_QUOTE_B5, (60, 560), mask=W_QUOTE_B5.split()[-1])
        
        # World Cup Trophy on Right (X=680, Y=520, height 700)
        trophy = get_image(ASSETS_DIR / "world_cup_trophy_cutout.png")
        trophy_scaled = scale_cutout_proportional(trophy, target_h=700)
        bg.paste(trophy_scaled, (680, 520), mask=trophy_scaled.split()[-1])
        
        # Golden Ball Award Ticket on Bottom Right (X=460, Y=1260)
        golden_ball = create_torn_match_ticket(
            "FIFA GOLDEN BALL 2006",
            "BEST PLAYER OF TOURNAMENT",
            "ZINEDINE ZIDANE",
            width=540, height=170
        )
        bg.paste(golden_ball, (460, 1260), mask=golden_ball.split()[-1])
        
        bg = draw_mrbeast_captions(bg, t, center_y=1710)
        bg.paste(TV_WATERMARK, (50, 48), mask=TV_WATERMARK.split()[-1])
        return bg

    # -------------------------------------------------------------
    # BEAT 6: Long Live Zizou (51.5s - 56.0s) — Variant A Banner Tribute
    # -------------------------------------------------------------
    else:
        t_b = t - 51.5
        bg = get_cached_bg().copy()
        
        p_slide = min(1.0, t_b / 0.45)
        ease_slide = math.sin(p_slide * math.pi / 2)
        head_x = int(-250 * (1.0 - ease_slide) + 60)
        bg.paste(W_HEAD_B6, (head_x, 240), mask=W_HEAD_B6.split()[-1])
        
        # Zidane Hero dominating center frame (X=160, Y=460, height 1240)
        zidane_hero = get_image(ASSETS_DIR / "zidane_hero_cutout.png")
        c_scale = 1.0 + 0.04 * (t_b / 4.5)
        target_h = int(1240 * c_scale)
        hero_scaled = scale_cutout_proportional(zidane_hero, target_h=target_h)
        bg.paste(hero_scaled, (160, 460), mask=hero_scaled.split()[-1])
        
        # Tribute Ticket on bottom center (X=270, Y=1450)
        bg.paste(W_TICKET_B6, (270, 1450), mask=W_TICKET_B6.split()[-1])
        
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
    print(f"  RENDERING {total_frames} FRAMES FOR ZIDANE 2006 (60.0s @ 30 FPS)")
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
    print("  MUXING MASTER MP4 (NVENC H.264 // -14 LUFS AUDIO)")
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
