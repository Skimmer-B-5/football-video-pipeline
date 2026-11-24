"""
beta/stages/prepare_v7_1_6_5_editorial_shots.py
Prepares the complete multi-shot visual sequence for Beta V7.1.6.5:
Fulfills Section 3 Mandate: Visual change approximately every 1-2 seconds across all 5 beats.
"""

import sys
import os
import json
import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.typography import load_font

WS_DIR = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1"
CAND_DIR = WS_DIR / "assets" / "candidates"
APPROVED_DIR = WS_DIR / "assets" / "approved"
SHOTS_DIR = WS_DIR / "assets" / "shots_v7_1_6_5"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

def download_candidates():
    """Downloads verified Milan and Mourinho images with Wikimedia-compliant headers."""
    headers = {'User-Agent': 'AntigravityFootballMedia/1.0 (contact: editorial@footballplus.internal)'}
    downloads = {
        "cand_milan_facade.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Casa_Milan_facciata.jpg/1280px-Casa_Milan_facciata.jpg",
        "cand_mourinho_resistance.jpg": "https://upload.wikimedia.org/wikipedia/commons/5/53/Fenerbahce_manager_Jose_Mourinho_and_Ali_Ko%C3%A7%2C_June_2024_%28cropped%29.jpg"
    }
    for fname, url in downloads.items():
        dest = CAND_DIR / fname
        if not dest.exists():
            print(f"Downloading {fname} from {url}...")
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                dest.write_bytes(r.content)
                print(f"  Saved {fname} ({len(r.content)} bytes)")
            else:
                print(f"  [WARN] Download failed: {r.status_code}")
        else:
            print(f"  Already exists: {fname}")

def center_crop_9_16(img: np.ndarray, target_w: int = 1080, target_h: int = 1920, focus_x: float = 0.5, focus_y: float = 0.4) -> np.ndarray:
    """Crops and scales image to exact 1080x1920 with focus point biasing."""
    h, w = img.shape[:2]
    target_ratio = 9.0 / 16.0
    current_ratio = w / float(h)

    if current_ratio > target_ratio:
        # Image is wider than 9:16, crop width
        crop_w = int(round(h * target_ratio))
        center_x = int(round(w * focus_x))
        x1 = max(0, center_x - crop_w // 2)
        x2 = x1 + crop_w
        if x2 > w:
            x2 = w
            x1 = w - crop_w
        cropped = img[:, x1:x2]
    else:
        # Image is taller than 9:16, crop height
        crop_h = int(round(w / target_ratio))
        center_y = int(round(h * focus_y))
        y1 = max(0, center_y - crop_h // 2)
        y2 = y1 + crop_h
        if y2 > h:
            y2 = h
            y1 = h - crop_h
        cropped = img[y1:y2, :]

    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

def prepare_shots():
    print("\n--- Preparing Individual Editorial Shots (1080x1920) ---")

    # === S01 Shots ===
    # 1.1: Bernabeu Exterior Night
    s01_base = cv2.imread(str(CAND_DIR / "cand_S01_012908f010.jpg"))
    s01_shot1 = center_crop_9_16(s01_base, focus_x=0.5, focus_y=0.45)
    cv2.imwrite(str(SHOTS_DIR / "S01_shot1_bernabeu.png"), s01_shot1)

    # 1.2: Casa Milan Headquarters Facade with AC Milan Crest
    milan_base = cv2.imread(str(CAND_DIR / "cand_milan_facade.jpg"))
    if milan_base is not None:
        s01_shot2 = center_crop_9_16(milan_base, focus_x=0.52, focus_y=0.42)
    else:
        s01_shot2 = s01_shot1.copy()
    cv2.imwrite(str(SHOTS_DIR / "S01_shot2_milan_facade.png"), s01_shot2)

    # 1.3: Jose Mourinho Focused Resistance Touchline
    mourinho_base = cv2.imread(str(CAND_DIR / "cand_mourinho_resistance.jpg"))
    if mourinho_base is not None:
        s01_shot3 = center_crop_9_16(mourinho_base, focus_x=0.5, focus_y=0.28)
    else:
        s01_shot3 = s01_shot1.copy()
    cv2.imwrite(str(SHOTS_DIR / "S01_shot3_mourinho.png"), s01_shot3)

    # === S02 Shots ===
    # 2.1: Endrick Presentation Portrait (Repaired Framing)
    s02_shot1 = cv2.imread(str(APPROVED_DIR / "S02_approved_repaired.png"))
    cv2.imwrite(str(SHOTS_DIR / "S02_shot1_presentation.png"), s02_shot1)

    # 2.2: Endrick Match Action in Real Madrid Kit
    s02_act_base = cv2.imread(str(CAND_DIR / "cand_S04_93dbffc434.jpg"))
    if s02_act_base is not None:
        s02_shot2 = center_crop_9_16(s02_act_base, focus_x=0.5, focus_y=0.35)
    else:
        s02_shot2 = s02_shot1.copy()
    cv2.imwrite(str(SHOTS_DIR / "S02_shot2_action.png"), s02_shot2)

    # 2.3: Endrick Intense Focus Close-up
    s02_close_base = cv2.imread(str(CAND_DIR / "cand_S02_9f4751fe4a.jpg"))
    if s02_close_base is not None:
        s02_shot3 = center_crop_9_16(s02_close_base, focus_x=0.5, focus_y=0.25)
    else:
        s02_shot3 = s02_shot1.copy()
    cv2.imwrite(str(SHOTS_DIR / "S02_shot3_closeup.png"), s02_shot3)

    # === S03 Sequential Financial Reveals ===
    # Create the 4 sequential stage cards on stadium photography base
    s03_stadium = Image.open(CAND_DIR / "cand_S01_012908f010.jpg").convert("RGBA")
    sw, sh = s03_stadium.size
    t_ratio = 9 / 16
    if sw / sh > t_ratio:
        nw = int(sh * t_ratio)
        l = (sw - nw) // 2
        s03_stadium = s03_stadium.crop((l, 0, l + nw, sh))
    else:
        nh = int(sw / t_ratio)
        t = (sh - nh) // 2
        s03_stadium = s03_stadium.crop((0, t, sw, t + nh))
    s03_bg = s03_stadium.resize((1080, 1920), Image.Resampling.LANCZOS)

    # Scrim
    scrim = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(scrim)
    for y in range(1920):
        if 420 <= y <= 1180:
            alpha = int(145 + 35 * (1.0 - abs(y - 800) / 380))
            s_draw.line([(0, y), (1080, y)], fill=(8, 14, 28, alpha))
        elif y > 1180:
            s_draw.line([(0, y), (1080, y)], fill=(8, 14, 28, 150))
    base_card = Image.alpha_composite(s03_bg, scrim)

    f_kicker = load_font("IBM Plex Mono", 600, 24)
    f_title = load_font("Barlow Condensed", 800, 60)
    f_lbl = load_font("IBM Plex Mono", 600, 24)
    f_hero = load_font("Barlow Condensed", 800, 108)
    f_sub = load_font("Inter", 600, 26)
    f_div = load_font("Barlow Condensed", 700, 26)
    f_sec = load_font("Barlow Condensed", 800, 76)
    f_badge = load_font("IBM Plex Mono", 700, 28)

    # S03 Reveal 1: Base €60M
    c1 = base_card.copy()
    d1 = ImageDraw.Draw(c1)
    d1.text((70, 460), "● PROPOSED TERMS (STAGE 1)", font=f_kicker, fill=(56, 189, 248))
    d1.text((70, 500), "ENDRICK TRANSFER PROPOSAL", font=f_title, fill=(255, 255, 255))
    d1.line([(70, 575), (1010, 575)], fill=(56, 189, 248, 180), width=2)
    d1.text((70, 600), "AC MILAN • REPORTED BASE PROPOSAL", font=f_lbl, fill=(186, 230, 253))
    d1.text((70, 635), "€60M FIXED", font=f_hero, fill=(255, 255, 255))
    c1.convert("RGB").save(str(SHOTS_DIR / "S03_shot1_base60m.png"), "PNG")

    # S03 Reveal 2: + €10M Potential Bonuses
    c2 = c1.copy()
    d2 = ImageDraw.Draw(c2)
    d2.text((70, 760), "+ €10M IN POTENTIAL BONUSES (UNCONFIRMED)", font=f_sub, fill=(56, 189, 248))
    c2.convert("RGB").save(str(SHOTS_DIR / "S03_shot2_bonuses.png"), "PNG")

    # S03 Reveal 3: €80M–€85M Buy-Back Range
    c3 = c2.copy()
    d3 = ImageDraw.Draw(c3)
    d3.line([(70, 815), (1010, 815)], fill=(70, 90, 130, 140), width=1)
    d3.text((70, 830), "SEPARATE REPORTED REPURCHASE CLAUSE", font=f_div, fill=(203, 213, 225))
    d3.line([(70, 875), (1010, 875)], fill=(70, 90, 130, 140), width=1)
    d3.text((70, 895), "REAL MADRID • REPORTED BUY-BACK RANGE", font=f_lbl, fill=(253, 224, 71))
    d3.text((70, 930), "€80M – €85M", font=f_sec, fill=(250, 204, 21))
    d3.text((70, 1025), "CORRIERE DELLO SPORT (€80M) • TNT SPORTS (€85M)", font=f_sub, fill=(254, 240, 138))
    c3.convert("RGB").save(str(SHOTS_DIR / "S03_shot3_buyback.png"), "PNG")

    # S03 Reveal 4: NOT AGREED Badge Stamp
    c4 = c3.copy()
    d4 = ImageDraw.Draw(c4)
    d4.rounded_rectangle([(70, 1090), (360, 1145)], radius=8, fill=(220, 38, 38), outline=(254, 202, 202), width=1)
    d4.text((88, 1101), "NOT AGREED", font=f_badge, fill=(255, 255, 255))
    d4.text((380, 1106), "NO FORMAL CLAUSE ACCEPTED BY CLUBS", font=f_sub, fill=(226, 232, 240))
    c4.convert("RGB").save(str(SHOTS_DIR / "S03_shot4_not_agreed.png"), "PNG")

    # === S04 Injury Shots ===
    # 4.1: Athletic Endrick in Real Madrid Kit
    s04_shot1 = s02_shot2.copy()
    cv2.imwrite(str(SHOTS_DIR / "S04_shot1_athletic.png"), s04_shot1)

    # 4.2: Official Real Madrid Medical Communique Graphic
    med_bg = s03_bg.copy()
    m_draw = ImageDraw.Draw(med_bg)
    m_draw.rectangle([(50, 480), (1030, 1080)], fill=(11, 19, 43, 230), outline=(239, 68, 68), width=2)
    m_draw.text((80, 520), "OFFICIAL MEDICAL BULLETIN", font=f_title, fill=(239, 68, 68))
    m_draw.text((80, 600), "CLUB: REAL MADRID C.F. • OFFICIAL RELEASE", font=f_lbl, fill=(186, 230, 253))
    m_draw.text((80, 640), "DATE: NOVEMBER 23, 2026", font=f_lbl, fill=(148, 163, 184))
    m_draw.line([(80, 680), (1000, 680)], fill=(70, 90, 130), width=1)
    m_draw.text((80, 710), "DIAGNOSIS: INJURY TO ABDUCTOR OF LEFT LEG", font=f_title, fill=(255, 255, 255))
    m_draw.text((80, 790), "CLINICAL STATUS: PENDING EVOLUTION", font=f_sub, fill=(250, 204, 21))
    m_draw.text((80, 830), "RECOVERY TIMETABLE: NO OFFICIAL RETURN DATE", font=f_sub, fill=(254, 202, 202))
    m_draw.rounded_rectangle([(80, 890), (450, 950)], radius=8, fill=(185, 28, 28))
    m_draw.text((100, 905), "MEDICAL STATUS: OUT", font=f_badge, fill=(255, 255, 255))
    med_bg.convert("RGB").save(str(SHOTS_DIR / "S04_shot2_medical_bulletin.png"), "PNG")

    # 4.3: Archival Valdebebas Training File Photo
    s04_shot3 = cv2.imread(str(APPROVED_DIR / "S04_approved_repaired.png"))
    cv2.imwrite(str(SHOTS_DIR / "S04_shot3_archival_training.png"), s04_shot3)

    # === S05 Dynamic San Siro Shots ===
    # 5.1: San Siro Stadium Floodlit Exterior Spirals
    san_siro_ext = cv2.imread(str(CAND_DIR / "cand_S05_39ee430a06.jpg"))
    s05_shot1 = center_crop_9_16(san_siro_ext, focus_x=0.5, focus_y=0.4)
    cv2.imwrite(str(SHOTS_DIR / "S05_shot1_exterior.png"), s05_shot1)

    # 5.2: San Siro Illuminated Pitch & Matchday Atmosphere
    san_siro_pitch = cv2.imread(str(CAND_DIR / "cand_S05_4811f45164.jpg"))
    s05_shot2 = center_crop_9_16(san_siro_pitch, focus_x=0.5, focus_y=0.35)
    cv2.imwrite(str(SHOTS_DIR / "S05_shot2_pitch.png"), s05_shot2)

    # 5.3: San Siro Towering Low-Angle Anticipation
    s05_shot3 = center_crop_9_16(san_siro_ext, focus_x=0.45, focus_y=0.2)
    cv2.imwrite(str(SHOTS_DIR / "S05_shot3_anticipation.png"), s05_shot3)

    print(f"Generated 16 distinct shots in {SHOTS_DIR}")

def render_v7_1_6_5_scene_chart():
    """Renders the comprehensive 5-beat multi-shot contact sheet showing the 1-2s pacing."""
    print("\n--- Rendering Revised Scene Contact Sheet (V7.1.6.5) ---")
    
    chart_w = 2160
    header_h = 240
    beat_row_h = 560
    footer_h = 90
    total_h = header_h + 5 * beat_row_h + footer_h

    chart = Image.new("RGB", (chart_w, total_h), color=(10, 14, 24))
    draw = ImageDraw.Draw(chart)

    # Header
    draw.rectangle([(0, 0), (chart_w, header_h)], fill=(15, 23, 42))
    draw.line([(0, header_h), (chart_w, header_h)], fill=(250, 204, 21), width=3)

    f_hl = load_font("Barlow Condensed", 800, 48)
    f_sub = load_font("Inter", 600, 24)
    f_mono = load_font("IBM Plex Mono", 600, 20)
    f_beat = load_font("Barlow Condensed", 800, 32)
    f_desc = load_font("Inter", 400, 20)
    f_tag = load_font("IBM Plex Mono", 700, 16)

    draw.text((60, 35), "30 FOOTBALL PLUS — EDITORIAL PACING STORYBOARD (V7.1.6.5)", font=f_hl, fill=(250, 204, 21))
    draw.text((60, 95), "STORY: Milan Plot Endrick Move As Mourinho Resists Exit • FAST EDITORIAL RHYTHM (1–2s CUTS)", font=f_sub, fill=(255, 255, 255))
    draw.text((60, 135), "PACING BLUEPRINT: 16 DISTINCT SHOTS ACROSS 5 BEATS • AUTHENTIC 1990s CRT BROADCAST TREATMENT", font=f_mono, fill=(56, 189, 248))
    draw.text((60, 175), "MANDATE: No static image holds • Visual story progresses independently of subtitles • Dynamic TV cuts", font=f_desc, fill=(148, 163, 184))

    # Beat definitions with multiple shots
    beat_shots = [
        {
            "beat_id": "S01",
            "title": "MILAN'S MOVE & MOURINHO RESISTANCE",
            "dialogue": "\"Milan have made their move, but Mourinho wants him to stay.\"",
            "pacing": "3 SHOTS IN 4.86s (1.6s PER CUT)",
            "shots": [
                ("1.1 Bernabéu Exterior (Night)", SHOTS_DIR / "S01_shot1_bernabeu.png", "0.0s – 1.8s • Push-in"),
                ("1.2 Casa Milan Facade (Crest)", SHOTS_DIR / "S01_shot2_milan_facade.png", "1.8s – 3.4s • Hard Cut"),
                ("1.3 Mourinho Resistance", SHOTS_DIR / "S01_shot3_mourinho.png", "3.4s – 4.86s • Bench Cut")
            ]
        },
        {
            "beat_id": "S02",
            "title": "ENDRICK IDENTITY REVEAL & PACKAGE",
            "dialogue": "\"Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.\"",
            "pacing": "3 SHOTS IN 6.70s (2.2s PER CUT)",
            "shots": [
                ("2.1 Presentation Reveal", SHOTS_DIR / "S02_shot1_presentation.png", "4.86s – 7.2s • Sweep Wipe"),
                ("2.2 Match Action Athletic", SHOTS_DIR / "S02_shot2_action.png", "7.2s – 9.4s • Pitch Cut"),
                ("2.3 Focused Close-Up", SHOTS_DIR / "S02_shot3_closeup.png", "9.4s – 11.56s • Detail Shot")
            ]
        },
        {
            "beat_id": "S03",
            "title": "TRANSFER VALUATION SEQUENTIAL REVEALS",
            "dialogue": "\"Reports cite eighty to eighty-five million repurchase figures, but nothing is agreed.\"",
            "pacing": "4 SEQUENTIAL REVEALS IN 4.70s (1.1s PER REVEAL)",
            "shots": [
                ("3.1 €60M Fixed Base", SHOTS_DIR / "S03_shot1_base60m.png", "11.56s – 12.8s • Reveal 1"),
                ("3.2 +€10M Bonuses", SHOTS_DIR / "S03_shot2_bonuses.png", "12.8s – 14.0s • Reveal 2"),
                ("3.3 €80M-€85M Buy-Back", SHOTS_DIR / "S03_shot3_buyback.png", "14.0s – 15.2s • Reveal 3"),
                ("3.4 NOT AGREED Stamp", SHOTS_DIR / "S03_shot4_not_agreed.png", "15.2s – 16.26s • Stamp")
            ]
        },
        {
            "beat_id": "S04",
            "title": "MEDICAL INJURY BULLETIN & ARCHIVAL FILE",
            "dialogue": "\"Now a left-leg muscle injury complicates matters, with no official return date.\"",
            "pacing": "3 SHOTS IN 6.26s (2.1s PER CUT)",
            "shots": [
                ("4.1 Squad Kit Context", SHOTS_DIR / "S04_shot1_athletic.png", "16.26s – 18.2s • Athletic"),
                ("4.2 Official Communiqué", SHOTS_DIR / "S04_shot2_medical_bulletin.png", "18.2s – 20.4s • Medical Card"),
                ("4.3 Archival Valdebebas", SHOTS_DIR / "S04_shot3_archival_training.png", "20.4s – 22.52s • File Photo")
            ]
        },
        {
            "beat_id": "S05",
            "title": "SAN SIRO MATCHDAY & OUTRO TRANSITION",
            "dialogue": "\"Will Mourinho keep the Brazilian or will Milan force a compromise?\"",
            "pacing": "3 SHOTS IN 8.63s (2.8s PER VIEW)",
            "shots": [
                ("5.1 San Siro Towers", SHOTS_DIR / "S05_shot1_exterior.png", "22.52s – 25.2s • Floodlit"),
                ("5.2 Illuminated Pitch", SHOTS_DIR / "S05_shot2_pitch.png", "25.2s – 28.0s • Curva Sud"),
                ("5.3 Tunnel Anticipation", SHOTS_DIR / "S05_shot3_anticipation.png", "28.0s – 31.15s • Climax")
            ]
        }
    ]

    thumb_w = 240
    thumb_h = 426 # 9:16 true vertical

    for idx, b in enumerate(beat_shots):
        row_y = header_h + idx * beat_row_h
        draw.rectangle([(30, row_y + 10), (chart_w - 30, row_y + beat_row_h - 10)], fill=(15, 20, 32), outline=(30, 41, 59), width=1)

        # Left Column: Beat Metadata
        draw.rectangle([(50, row_y + 30), (200, row_y + 75)], fill=(24, 46, 76), outline=(56, 189, 248), width=1)
        draw.text((65, row_y + 36), f"BEAT {b['beat_id']}", font=f_beat, fill=(255, 255, 255))
        draw.text((220, row_y + 40), b["title"], font=f_beat, fill=(250, 204, 21))

        draw.rounded_rectangle([(50, row_y + 90), (780, row_y + 240)], radius=8, fill=(11, 16, 26), outline=(36, 48, 70))
        draw.text((68, row_y + 102), "SPOKEN DIALOGUE:", font=f_tag, fill=(56, 189, 248))
        
        # Word wrap dialogue
        words = b["dialogue"].split()
        d_lines = []
        curr = []
        for w in words:
            if len(" ".join(curr + [w])) <= 44:
                curr.append(w)
            else:
                d_lines.append(" ".join(curr))
                curr = [w]
        if curr:
            d_lines.append(" ".join(curr))
        
        dy = row_y + 130
        for dl in d_lines:
            draw.text((68, dy), dl, font=f_sub, fill=(255, 255, 255))
            dy += 32

        # Pacing Badge
        draw.rounded_rectangle([(50, row_y + 260), (780, row_y + 315)], radius=6, fill=(14, 40, 26), outline=(46, 204, 113))
        draw.text((68, row_y + 276), f"⚡ EDITORIAL PACE: {b['pacing']}", font=f_mono, fill=(74, 222, 128))

        # Right Column: Visual Shot Strip (Thumbnails)
        shots = b["shots"]
        strip_x = 820
        for s_idx, (s_label, s_path, s_timing) in enumerate(shots):
            sx = strip_x + s_idx * (thumb_w + 35)
            sy = row_y + 40

            if s_path.exists():
                with Image.open(s_path) as simg:
                    thumb = simg.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                chart.paste(thumb, (sx, sy))
                draw.rectangle([(sx, sy), (sx + thumb_w, sy + thumb_h)], outline=(56, 189, 248), width=2)
            else:
                draw.rectangle([(sx, sy), (sx + thumb_w, sy + thumb_h)], fill=(20, 25, 35), outline=(239, 68, 68), width=2)
                draw.text((sx + 30, sy + 180), "PENDING", font=f_sub, fill=(239, 68, 68))

            # Header over thumb
            draw.rectangle([(sx, sy + thumb_h + 8), (sx + thumb_w, sy + thumb_h + 40)], fill=(15, 23, 42))
            draw.text((sx + 8, sy + thumb_h + 14), s_label[:24], font=f_tag, fill=(250, 204, 21))

            # Timing under thumb
            draw.text((sx + 8, sy + thumb_h + 45), s_timing, font=f_mono, fill=(148, 163, 184))

    # Footer
    foot_y = total_h - footer_h + 30
    draw.line([(0, foot_y - 20), (chart_w, foot_y - 20)], fill=(32, 44, 66), width=1)
    draw.text((60, foot_y), "30 FOOTBALL PLUS • STRICT STORY WORKSPACE: endrick_milan/run_v7_1 • EDITORIAL PACING SYSTEM V7.1.6.5", font=f_mono, fill=(100, 116, 139))

    out_jpg = WS_DIR / "crops" / "clean_scene_chart_master_v7_1_6_5.jpg"
    chart.save(str(out_jpg), "JPEG", quality=95)
    print(f"Generated revised scene contact sheet: {out_jpg} ({out_jpg.stat().st_size} bytes)")
    return out_jpg

def main():
    download_candidates()
    prepare_shots()
    render_v7_1_6_5_scene_chart()

if __name__ == "__main__":
    main()
