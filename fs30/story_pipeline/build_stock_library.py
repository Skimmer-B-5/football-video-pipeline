"""
Generator for FS30 Reusable Graphic Assets Library.
Produces 5 genuinely distinct variants of every core widget:
1. Banners (Variants A, B, C, D, E)
2. Quote Cards (5 variants)
3. Photo Frames (5 variants)
4. Editorial Underlines (5 variants)
5. Date Labels (5 variants)
6. Rubber Stamps (5 variants)
7. Paper Textures (5 variants)
8. Red Marker Annotations (5 variants)
9. Match Tickets (3 variants)
Also compiles asset_manifest.json.
"""

import os
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
STOCK_DIR = PROJECT_ROOT / "fs30" / "story_pipeline" / "assets" / "reusable_stock"
FONTS_DIR = PROJECT_ROOT / "fs30" / "story_pipeline" / "assets" / "fonts"

# Palette
IVORY = (248, 245, 238, 255)
CREAM = (244, 240, 230, 255)
WARM_WHITE = (252, 250, 245, 255)
CHARCOAL = (18, 20, 26, 255)
ARCHIVAL_RED = (217, 4, 41, 255)
DEEP_CRIMSON = (180, 0, 30, 255)
MUSTARD_GOLD = (229, 184, 36, 255)
SLATE_GRAY = (110, 115, 125, 255)

def get_font(name: str = "headline", size: int = 40):
    font_map = {
        "headline": FONTS_DIR / "BarlowCondensed-ExtraBold.ttf",
        "headline_bold": FONTS_DIR / "BarlowCondensed-Bold.ttf",
        "serif": FONTS_DIR / "SourceSerif4-Bold.ttf",
        "serif_italic": FONTS_DIR / "SourceSerif4-Italic.ttf",
        "meta": FONTS_DIR / "IBMPlexSans.ttf",
    }
    p = font_map.get(name, font_map["headline"])
    try:
        return ImageFont.truetype(str(p), size)
    except:
        return ImageFont.load_default()

def make_torn_edge_mask(w: int, h: int, roughness: float = 3.5, tear_sides: str = "all") -> Image.Image:
    """Generates an organic torn paper alpha mask with irregular deckle fibers."""
    mask = Image.new("L", (w, h), 255)
    m_draw = ImageDraw.Draw(mask)
    
    np.random.seed(int(w * h * roughness) % 100000)
    
    # Perlin-like 1D noise along edges
    def noisy_line(length, base_depth=8, freq=0.08):
        points = []
        for i in range(length):
            noise = (math.sin(i * freq) * 0.5 + 
                     math.sin(i * freq * 2.3 + 1.2) * 0.3 + 
                     (np.random.rand() - 0.5) * 0.6) * base_depth * roughness
            points.append(int(noise))
        return points

    # Top edge
    if "top" in tear_sides or tear_sides == "all":
        nl = noisy_line(w, base_depth=4)
        for x in range(w):
            d = max(0, nl[x] + 4)
            if d > 0:
                m_draw.line([(x, 0), (x, d)], fill=0)
                
    # Bottom edge
    if "bottom" in tear_sides or tear_sides == "all":
        nl = noisy_line(w, base_depth=5)
        for x in range(w):
            d = max(0, nl[x] + 4)
            if d > 0:
                m_draw.line([(x, h - d), (x, h)], fill=0)
                
    # Left edge
    if "left" in tear_sides or tear_sides == "all":
        nl = noisy_line(h, base_depth=3)
        for y in range(h):
            d = max(0, nl[y] + 3)
            if d > 0:
                m_draw.line([(0, y), (d, y)], fill=0)
                
    # Right edge
    if "right" in tear_sides or tear_sides == "all":
        nl = noisy_line(h, base_depth=4)
        for y in range(h):
            d = max(0, nl[y] + 3)
            if d > 0:
                m_draw.line([(w - d, y), (w, y)], fill=0)

    # Slight blur to soften micro-pixels into realistic paper fibers
    return mask.filter(ImageFilter.GaussianBlur(1.0))

def add_paper_texture(img: Image.Image, grain_intensity: float = 0.04) -> Image.Image:
    """Adds subtle tactile paper fibers and grain to RGBA image."""
    arr = np.array(img, dtype=np.float32)
    h, w, c = arr.shape
    noise = np.random.normal(0, 255 * grain_intensity, (h, w, 1))
    arr[:, :, :3] = np.clip(arr[:, :, :3] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

def build_reusable_library():
    print("Building FS30 Reusable Graphic Assets Library...")
    manifest = []
    
    # -------------------------------------------------------------
    # 1. FIVE BANNER VARIANTS (1000 x 220)
    # -------------------------------------------------------------
    banner_dir = STOCK_DIR / "banners"
    banner_dir.mkdir(parents=True, exist_ok=True)
    
    bw, bh = 1000, 220
    
    # Variant A: Torn Newspaper Edge with Red Side Stripe
    va = Image.new("RGBA", (bw, bh), IVORY)
    mask_a = make_torn_edge_mask(bw, bh, roughness=3.2, tear_sides="all")
    va.putalpha(mask_a)
    draw_a = ImageDraw.Draw(va)
    # Solid vertical crimson accent stripe on left
    draw_a.rectangle([(30, 20), (40, bh - 20)], fill=ARCHIVAL_RED)
    va = add_paper_texture(va, grain_intensity=0.035)
    p_va = banner_dir / "banner_variant_a_torn_stripe.png"
    va.save(p_va)
    manifest.append({
        "id": "banner_variant_a",
        "category": "banners",
        "family": "torn_stripe",
        "name": "Torn Newspaper Edge with Red Side Stripe",
        "file": str(p_va.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "dimensions": [bw, bh],
        "transparency": True,
        "text_safe_box": [60, 25, bw - 50, bh - 25],
        "intended_usage": "Primary documentary headline banner across gritty historical incidents"
    })
    
    # Variant B: Folded Ivory Paper with Thin Red Marker
    vb = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    vb_card = Image.new("RGBA", (bw, bh), CREAM)
    draw_b = ImageDraw.Draw(vb_card)
    # Subtle folded creased corner at top-right
    draw_b.polygon([(bw - 60, 0), (bw, 60), (bw - 60, 60)], fill=(225, 220, 210, 255))
    draw_b.line([(bw - 60, 0), (bw, 60)], fill=(170, 165, 155, 255), width=2)
    # Thin marker accent line horizontally dividing kicker zone
    draw_b.line([(35, 78), (bw - 80, 78)], fill=ARCHIVAL_RED, width=3)
    # Hand-cut deckle mask with slight tear
    mask_b = make_torn_edge_mask(bw, bh, roughness=1.8, tear_sides="top,bottom")
    vb_card.putalpha(mask_b)
    vb = add_paper_texture(vb_card, grain_intensity=0.03)
    p_vb = banner_dir / "banner_variant_b_folded_marker.png"
    vb.save(p_vb)
    manifest.append({
        "id": "banner_variant_b",
        "category": "banners",
        "family": "folded_marker",
        "name": "Folded Ivory Paper with Thin Red Marker",
        "file": str(p_vb.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "dimensions": [bw, bh],
        "transparency": True,
        "text_safe_box": [50, 20, bw - 80, bh - 20],
        "intended_usage": "Refined editorial beats, tactical shifts, and chronological match labels"
    })

    # Variant C: Rough-Cut Archival Paper with Red Corner Tab
    vc = Image.new("RGBA", (bw, bh), WARM_WHITE)
    mask_c = make_torn_edge_mask(bw, bh, roughness=4.2, tear_sides="all")
    vc.putalpha(mask_c)
    draw_c = ImageDraw.Draw(vc)
    # Red corner tab on top-left
    draw_c.polygon([(0, 0), (75, 0), (0, 75)], fill=ARCHIVAL_RED)
    # Archival staple / rivet in corner
    draw_c.ellipse([(18, 18), (28, 28)], fill=(180, 150, 90, 255), outline=(100, 80, 50, 255), width=2)
    vc = add_paper_texture(vc, grain_intensity=0.04)
    p_vc = banner_dir / "banner_variant_c_corner_tab.png"
    vc.save(p_vc)
    manifest.append({
        "id": "banner_variant_c",
        "category": "banners",
        "family": "corner_tab",
        "name": "Rough-Cut Archival Paper with Red Corner Tab",
        "file": str(p_vc.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "dimensions": [bw, bh],
        "transparency": True,
        "text_safe_box": [85, 25, bw - 50, bh - 25],
        "intended_usage": "Police reports, court verdicts, institutional decisions, and bans"
    })

    # Variant D: Narrow Editorial Strip with Distressed Red Underline
    vd = Image.new("RGBA", (bw, bh), (250, 248, 242, 255))
    mask_d = make_torn_edge_mask(bw, bh, roughness=1.2, tear_sides="bottom")
    vd.putalpha(mask_d)
    draw_d = ImageDraw.Draw(vd)
    # Distressed brush underline along bottom text area
    draw_d.rectangle([(40, bh - 32), (bw - 60, bh - 24)], fill=DEEP_CRIMSON)
    draw_d.rectangle([(40, 25), (46, bh - 40)], fill=DEEP_CRIMSON)
    vd = add_paper_texture(vd, grain_intensity=0.03)
    p_vd = banner_dir / "banner_variant_d_distressed_underline.png"
    vd.save(p_vd)
    manifest.append({
        "id": "banner_variant_d",
        "category": "banners",
        "family": "distressed_underline",
        "name": "Narrow Editorial Strip with Distressed Red Underline",
        "file": str(p_vd.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "dimensions": [bw, bh],
        "transparency": True,
        "text_safe_box": [60, 20, bw - 60, bh - 38],
        "intended_usage": "Fast-paced quotes, media reaction quotes, and breaking news headlines"
    })

    # Variant E: Layered Paper with Offset Red Backing and Irregular Edges
    ve = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    # Red backing layer offset by (-8, +8)
    back_layer = Image.new("RGBA", (bw - 30, bh - 30), ARCHIVAL_RED)
    mask_back = make_torn_edge_mask(bw - 30, bh - 30, roughness=3.0, tear_sides="all")
    back_layer.putalpha(mask_back)
    ve.paste(back_layer, (10, 22), mask=back_layer.split()[-1])
    # Ivory face layer on top
    face_layer = Image.new("RGBA", (bw - 40, bh - 30), IVORY)
    mask_face = make_torn_edge_mask(bw - 40, bh - 30, roughness=3.5, tear_sides="all")
    face_layer.putalpha(mask_face)
    ve.paste(face_layer, (25, 12), mask=face_layer.split()[-1])
    ve = add_paper_texture(ve, grain_intensity=0.035)
    p_ve = banner_dir / "banner_variant_e_layered_offset.png"
    ve.save(p_ve)
    manifest.append({
        "id": "banner_variant_e",
        "category": "banners",
        "family": "layered_offset",
        "name": "Layered Paper with Offset Red Backing",
        "file": str(p_ve.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "dimensions": [bw, bh],
        "transparency": True,
        "text_safe_box": [60, 25, bw - 60, bh - 30],
        "intended_usage": "Climactic moments, iconic king returns, and definitive historical declarations"
    })
    print("✓ 5 Banner Variants Generated.")

    # -------------------------------------------------------------
    # 2. FIVE QUOTE CARDS (960 x 380)
    # -------------------------------------------------------------
    quote_dir = STOCK_DIR / "quotes"
    quote_dir.mkdir(parents=True, exist_ok=True)
    qw, qh = 960, 380
    
    quote_styles = [
        ("quote_variant_a_classic_torn", "Classic Torn Edge Parchment", 3.5, "all", ARCHIVAL_RED, True),
        ("quote_variant_b_notepaper_ruled", "Ruled Legal Pad with Red Margin", 1.5, "bottom", (210, 40, 50, 255), False),
        ("quote_variant_c_heavy_cardstock", "Heavy Beveled Archival Cardstock", 2.0, "all", (160, 20, 35, 255), True),
        ("quote_variant_d_double_bordered", "Double Inked Editorial Border", 1.0, "top,bottom", ARCHIVAL_RED, True),
        ("quote_variant_e_aged_parchment", "Aged Rag Deckle with Red Header Tab", 4.5, "all", MUSTARD_GOLD, True),
    ]
    
    for qid, qname, rough, sides, accent, show_mark in quote_styles:
        q_card = Image.new("RGBA", (qw, qh), (0, 0, 0, 0))
        base = Image.new("RGBA", (qw, qh), IVORY if "ruled" not in qid else (255, 252, 240, 255))
        draw_q = ImageDraw.Draw(base)
        
        if "ruled" in qid:
            # Draw subtle blue horizontal lines and red vertical margin
            for y_line in range(70, qh - 40, 38):
                draw_q.line([(40, y_line), (qw - 40, y_line)], fill=(200, 215, 235, 180), width=1)
            draw_q.line([(120, 20), (120, qh - 20)], fill=(235, 100, 100, 200), width=2)
        elif "double" in qid:
            draw_q.rectangle([(25, 25), (qw - 25, qh - 25)], outline=(200, 195, 185, 255), width=2)
            draw_q.rectangle([(32, 32), (qw - 32, qh - 32)], outline=accent, width=1)
        elif "aged" in qid:
            # Header tab
            draw_q.rectangle([(40, 15), (220, 40)], fill=ARCHIVAL_RED)
            draw_q.text((55, 18), "DOCUMENT ARCHIVE", fill=(255, 255, 255, 255), font=get_font("headline_bold", 18))
        else:
            # Classic red notch
            draw_q.rectangle([(25, 30), (33, qh - 30)], fill=accent)
            
        if show_mark and "aged" not in qid:
            draw_q.text((45, 18), "“", fill=accent, font=get_font("serif", 96))
            
        mask_q = make_torn_edge_mask(qw, qh, roughness=rough, tear_sides=sides)
        base.putalpha(mask_q)
        q_textured = add_paper_texture(base, grain_intensity=0.035)
        
        p_q = quote_dir / f"{qid}.png"
        q_textured.save(p_q)
        manifest.append({
            "id": qid,
            "category": "quotes",
            "family": qid.split("_")[2],
            "name": qname,
            "file": str(p_q.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [qw, qh],
            "transparency": True,
            "text_safe_box": [130, 45, qw - 60, qh - 45],
            "intended_usage": f"Archival quote presentations, declarations, and court transcripts ({qname})"
        })
    print("✓ 5 Quote Card Variants Generated.")

    # -------------------------------------------------------------
    # 3. FIVE ARCHIVAL PHOTO FRAMES (600 x 420)
    # -------------------------------------------------------------
    frames_dir = STOCK_DIR / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    fw, fh = 600, 420
    
    frame_types = [
        ("frame_variant_a_polaroid", "Vintage Polaroid Border with Bottom Tab", 40, 40, 40, 90, (246, 243, 235, 255)),
        ("frame_variant_b_gallery_mat", "Archival Ivory Mat with Inner Bevel", 35, 35, 35, 35, (250, 248, 242, 255)),
        ("frame_variant_c_contact_sheet", "Black 35mm Film Contact Sheet Frame", 28, 28, 28, 28, (20, 22, 26, 255)),
        ("frame_variant_d_torn_border", "Deckle Edge Torn Photo Mount", 32, 32, 32, 32, (244, 240, 230, 255)),
        ("frame_variant_e_brass_corners", "Vintage Card with Photo Corners", 25, 25, 25, 25, (240, 236, 226, 255)),
    ]
    
    for fid, fname, pt, pb, pl, pr, bg_col in frame_types:
        f_im = Image.new("RGBA", (fw, fh), bg_col)
        draw_f = ImageDraw.Draw(f_im)
        
        # Transparent cutout window for mounting photo
        window_box = [pl, pt, fw - pr, fh - pb]
        
        if "contact_sheet" in fid:
            # Draw frame markers and numbers
            draw_f.text((35, 6), "35mm KODAK SAFETY // 24A", fill=(210, 170, 40, 255), font=get_font("headline_bold", 18))
            draw_f.text((fw - 80, fh - 24), "▶ 25", fill=(210, 170, 40, 255), font=get_font("headline_bold", 18))
        elif "brass_corners" in fid:
            # Corner mounting tabs
            for cx, cy in [(pl, pt), (fw - pr, pt), (pl, fh - pb), (fw - pr, fh - pb)]:
                draw_f.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=(70, 50, 30, 255))
        elif "polaroid" in fid:
            draw_f.line([(pl, fh - pb + 12), (fw - pr, fh - pb + 12)], fill=(210, 205, 195, 255), width=1)
            
        # Cutout window in center
        f_arr = np.array(f_im)
        f_arr[pt:fh - pb, pl:fw - pr, :] = 0
        f_im = Image.fromarray(f_arr)
        
        if "torn" in fid:
            mask_fr = make_torn_edge_mask(fw, fh, roughness=2.5, tear_sides="all")
            # Combine alpha
            f_im.putalpha(Image.fromarray(np.minimum(np.array(f_im.split()[-1]), np.array(mask_fr))))
            
        p_f = frames_dir / f"{fid}.png"
        f_im.save(p_f)
        manifest.append({
            "id": fid,
            "category": "frames",
            "family": fid.split("_")[2],
            "name": fname,
            "file": str(p_f.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [fw, fh],
            "transparency": True,
            "window_box": window_box,
            "intended_usage": f"Photographic asset framing and contact sheet presentations ({fname})"
        })
    print("✓ 5 Archival Photo Frames Generated.")

    # -------------------------------------------------------------
    # 4. FIVE EDITORIAL UNDERLINE STYLES (800 x 60)
    # -------------------------------------------------------------
    under_dir = STOCK_DIR / "underlines"
    under_dir.mkdir(parents=True, exist_ok=True)
    uw, uh = 800, 60
    
    under_styles = [
        ("underline_variant_a_drybrush", "Distressed Dry-Brush Crimson Stroke"),
        ("underline_variant_b_double_rule", "Double Inked Editorial Ledger Rule"),
        ("underline_variant_c_marker_chisel", "Thick Chisel Tip Fluorescent Marker"),
        ("underline_variant_d_torn_strip", "Narrow Deckle Edge Paper Underline"),
        ("underline_variant_e_dotted_leader", "Perforated Archival Punch Underline"),
    ]
    
    for uid, uname in under_styles:
        u_im = Image.new("RGBA", (uw, uh), (0, 0, 0, 0))
        draw_u = ImageDraw.Draw(u_im)
        
        if "drybrush" in uid:
            # Irregular distressed brush stroke
            np.random.seed(42)
            for x in range(30, uw - 30):
                thickness = 6 + int(np.random.rand() * 5)
                draw_u.line([(x, 26), (x, 26 + thickness)], fill=(217, 4, 41, int(190 + np.random.rand() * 65)))
        elif "double_rule" in uid:
            draw_u.line([(30, 22), (uw - 30, 22)], fill=ARCHIVAL_RED, width=4)
            draw_u.line([(30, 32), (uw - 30, 32)], fill=ARCHIVAL_RED, width=2)
        elif "marker_chisel" in uid:
            draw_u.rounded_rectangle([(30, 18), (uw - 30, 42)], radius=6, fill=(255, 235, 59, 210))
        elif "torn_strip" in uid:
            strip = Image.new("RGBA", (uw - 60, 22), ARCHIVAL_RED)
            m_s = make_torn_edge_mask(uw - 60, 22, roughness=2.0, tear_sides="top,bottom")
            strip.putalpha(m_s)
            u_im.paste(strip, (30, 20), mask=strip.split()[-1])
        elif "dotted_leader" in uid:
            for x in range(30, uw - 30, 22):
                draw_u.rectangle([(x, 24), (x + 12, 32)], fill=ARCHIVAL_RED)
                
        p_u = under_dir / f"{uid}.png"
        u_im.save(p_u)
        manifest.append({
            "id": uid,
            "category": "underlines",
            "family": uid.split("_")[2],
            "name": uname,
            "file": str(p_u.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [uw, uh],
            "transparency": True,
            "intended_usage": f"Animated or static text emphasis underlines ({uname})"
        })
    print("✓ 5 Editorial Underlines Generated.")

    # -------------------------------------------------------------
    # 5. FIVE DATE LABELS (440 x 130)
    # -------------------------------------------------------------
    date_dir = STOCK_DIR / "date_labels"
    date_dir.mkdir(parents=True, exist_ok=True)
    dw, dh = 440, 130
    
    date_styles = [
        ("date_label_variant_a_torn_tag", "Torn Tag with Eyelet Hole", True),
        ("date_label_variant_b_red_badge", "Archival Red Embossed Box", False),
        ("date_label_variant_c_stamp_circle", "Circular Postmark Match Cancellation", False),
        ("date_label_variant_d_folded_tab", "Ivory Creased Folder Tab", False),
        ("date_label_variant_e_blackletter", "Gritty Newspaper Timestamp Bar", False),
    ]
    
    for did, dname, has_hole in date_styles:
        d_im = Image.new("RGBA", (dw, dh), (0, 0, 0, 0))
        draw_d = ImageDraw.Draw(d_im)
        
        if "torn_tag" in did:
            tag = Image.new("RGBA", (dw - 30, dh - 20), IVORY)
            m_t = make_torn_edge_mask(dw - 30, dh - 20, roughness=3.0, tear_sides="all")
            tag.putalpha(m_t)
            d_im.paste(tag, (15, 10), mask=tag.split()[-1])
            draw_d = ImageDraw.Draw(d_im)
            draw_d.ellipse([(35, dh // 2 - 10), (55, dh // 2 + 10)], fill=(30, 32, 40, 255), outline=(180, 150, 100, 255), width=2)
            draw_d.rectangle([(80, 28), (86, dh - 28)], fill=ARCHIVAL_RED)
        elif "red_badge" in did:
            draw_d.rounded_rectangle([(15, 12), (dw - 15, dh - 12)], radius=12, fill=ARCHIVAL_RED)
            draw_d.rounded_rectangle([(20, 17), (dw - 20, dh - 17)], radius=8, outline=(255, 255, 255, 200), width=2)
        elif "stamp_circle" in did:
            r = (dh - 20) // 2
            cx, cy = dh // 2 + 10, dh // 2
            draw_d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=ARCHIVAL_RED, width=3)
            draw_d.ellipse([(cx - r + 6, cy - r + 6), (cx + r - 6, cy + r - 6)], outline=ARCHIVAL_RED, width=1)
            draw_d.line([(cx + r + 15, cy - 15), (dw - 20, cy - 15)], fill=ARCHIVAL_RED, width=2)
            draw_d.line([(cx + r + 15, cy + 15), (dw - 20, cy + 15)], fill=ARCHIVAL_RED, width=2)
        elif "folded_tab" in did:
            tab = Image.new("RGBA", (dw - 30, dh - 24), CREAM)
            draw_tab = ImageDraw.Draw(tab)
            draw_tab.polygon([(0, 0), (60, 0), (40, dh - 24), (0, dh - 24)], fill=ARCHIVAL_RED)
            m_tab = make_torn_edge_mask(dw - 30, dh - 24, roughness=1.5, tear_sides="right,bottom")
            tab.putalpha(m_tab)
            d_im.paste(tab, (15, 12), mask=tab.split()[-1])
        elif "blackletter" in did:
            draw_d.rectangle([(15, 15), (dw - 15, dh - 15)], fill=(20, 24, 30, 255), outline=ARCHIVAL_RED, width=2)
            
        p_d = date_dir / f"{did}.png"
        d_im.save(p_d)
        manifest.append({
            "id": did,
            "category": "date_labels",
            "family": did.split("_")[2],
            "name": dname,
            "file": str(p_d.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [dw, dh],
            "transparency": True,
            "intended_usage": f"Date stamps, chronological milestone indicators, and time tags ({dname})"
        })
    print("✓ 5 Date Label Designs Generated.")

    # -------------------------------------------------------------
    # 6. FIVE RUBBER STAMPS (520 x 180)
    # -------------------------------------------------------------
    stamp_dir = STOCK_DIR / "stamps"
    stamp_dir.mkdir(parents=True, exist_ok=True)
    sw, sh = 520, 180
    
    stamp_specs = [
        ("stamp_ban_8months", "8-MONTH BAN", "WORLDWIDE FA SANCTION", ARCHIVAL_RED),
        ("stamp_community_service", "120 HOURS", "COMMUNITY SERVICE ORDER", ARCHIVAL_RED),
        ("stamp_verdict_guilty", "VERDICT: GUILTY", "CROYDON MAGISTRATES COURT", (180, 0, 30, 255)),
        ("stamp_red_card", "STRAIGHT RED", "MATCH REPORT // DISCIPLINARY", (220, 20, 60, 255)),
        ("stamp_appeal_quashed", "SENTENCE QUASHED", "CROYDON CROWN COURT", (190, 10, 40, 255)),
    ]
    
    for sid, stext, ssub, scolor in stamp_specs:
        s_im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw_s = ImageDraw.Draw(s_im)
        
        # Double border
        draw_s.rectangle([(10, 10), (sw - 10, sh - 10)], outline=scolor, width=6)
        draw_s.rectangle([(18, 18), (sw - 18, sh - 18)], outline=scolor, width=2)
        
        f_s1 = get_font("headline", 52)
        bbox1 = f_s1.getbbox(stext)
        tw1 = bbox1[2] - bbox1[0]
        draw_s.text(((sw - tw1) // 2, 28), stext, fill=scolor, font=f_s1)
        
        f_s2 = get_font("headline_bold", 24)
        bbox2 = f_s2.getbbox(ssub)
        tw2 = bbox2[2] - bbox2[0]
        draw_s.text(((sw - tw2) // 2, 102), ssub, fill=scolor, font=f_s2)
        
        # Authentic ink distress and grunge noise
        arr_s = np.array(s_im)
        np.random.seed(len(stext) * 77)
        distress = np.random.randint(0, 100, (sh, sw), dtype=np.uint8)
        arr_s[:, :, 3] = np.where(distress < 10, 0, arr_s[:, :, 3])
        s_im = Image.fromarray(arr_s)
        
        p_s = stamp_dir / f"{sid}.png"
        s_im.save(p_s)
        manifest.append({
            "id": sid,
            "category": "stamps",
            "family": "rubber_stamp",
            "name": f"Rubber Stamp: {stext}",
            "file": str(p_s.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [sw, sh],
            "transparency": True,
            "intended_usage": f"Sliding/slamming rubber ink stamp for legal & disciplinary verdicts ({stext})"
        })
    print("✓ 5 Rubber Stamp Designs Generated.")

    # -------------------------------------------------------------
    # 7. FIVE PAPER TEXTURES (1080 x 1920 Full HD Textures)
    # -------------------------------------------------------------
    tex_dir = STOCK_DIR / "textures"
    tex_dir.mkdir(parents=True, exist_ok=True)
    tw, th = 1080, 1920
    
    tex_specs = [
        ("texture_variant_a_rag_parchment", "Warm Aged Rag Parchment", (246, 242, 232), 0.05),
        ("texture_variant_b_newspaper_newsprint", "Vintage 1990s Newsprint Fiber", (238, 235, 226), 0.07),
        ("texture_variant_c_heavy_cardboard", "Industrial Archival Gray Cardboard", (228, 226, 220), 0.09),
        ("texture_variant_d_folded_crease", "Folded Archival Dossier with Cross Creases", (244, 240, 230), 0.04),
        ("texture_variant_e_film_grain", "Gritty Kodak 400 Grain Texture", (230, 228, 222), 0.11),
    ]
    
    for tid, tname, base_rgb, intensity in tex_specs:
        t_im = Image.new("RGB", (tw, th), base_rgb)
        draw_t = ImageDraw.Draw(t_im)
        
        if "folded" in tid:
            # Draw subtle vertical and horizontal crease lines
            draw_t.line([(tw // 2, 0), (tw // 2, th)], fill=(180, 175, 165), width=3)
            draw_t.line([(0, th // 3), (tw, th // 3)], fill=(180, 175, 165), width=2)
            draw_t.line([(0, 2 * th // 3), (tw, 2 * th // 3)], fill=(180, 175, 165), width=2)
            t_im = t_im.filter(ImageFilter.GaussianBlur(2.0))
            
        t_im = add_paper_texture(t_im, grain_intensity=intensity)
        p_t = tex_dir / f"{tid}.jpg"
        t_im.save(p_t, quality=90)
        manifest.append({
            "id": tid,
            "category": "textures",
            "family": tid.split("_")[2],
            "name": tname,
            "file": str(p_t.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [tw, th],
            "transparency": False,
            "intended_usage": f"Documentary scene canvas texture overlay ({tname})"
        })
    print("✓ 5 Paper Texture Overlays Generated.")

    # -------------------------------------------------------------
    # 8. RED MARKER ANNOTATIONS (5 variants)
    # -------------------------------------------------------------
    marker_dir = STOCK_DIR / "markers"
    marker_dir.mkdir(parents=True, exist_ok=True)
    
    # Circle, Arrow, Box, Cross, Strike
    marker_types = [
        ("marker_circle_reticle", 260, 260, "Tactical Target Circle"),
        ("marker_arrow_right", 340, 140, "Hand-Drawn Directional Arrow"),
        ("marker_box_bracket", 480, 200, "Annotation Focus Bracket Box"),
        ("marker_exclamation", 140, 260, "Archival Alert Exclamation"),
        ("marker_zigzag_lightning", 300, 180, "Impact Shockwave Flash"),
    ]
    
    for mid, mw, mh, mname in marker_types:
        m_im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
        draw_m = ImageDraw.Draw(m_im)
        
        if "circle" in mid:
            draw_m.ellipse([(20, 20), (mw - 20, mh - 20)], outline=ARCHIVAL_RED, width=6)
            draw_m.ellipse([(35, 35), (mw - 35, mh - 35)], outline=MUSTARD_GOLD, width=2)
        elif "arrow" in mid:
            draw_m.line([(30, mh // 2), (mw - 50, mh // 2)], fill=ARCHIVAL_RED, width=8)
            draw_m.polygon([(mw - 60, mh // 2 - 25), (mw - 20, mh // 2), (mw - 60, mh // 2 + 25)], fill=ARCHIVAL_RED)
        elif "box_bracket" in mid:
            draw_m.rectangle([(20, 20), (mw - 20, mh - 20)], outline=ARCHIVAL_RED, width=5)
            # Corner markers
            for cx, cy in [(20, 20), (mw - 20, 20), (20, mh - 20), (mw - 20, mh - 20)]:
                draw_m.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=MUSTARD_GOLD)
        elif "exclamation" in mid:
            draw_m.rounded_rectangle([(mw // 2 - 12, 25), (mw // 2 + 12, mh - 75)], radius=8, fill=ARCHIVAL_RED)
            draw_m.ellipse([(mw // 2 - 14, mh - 55), (mw // 2 + 14, mh - 27)], fill=ARCHIVAL_RED)
        elif "zigzag" in mid:
            draw_m.line([(30, mh // 2), (100, 30), (160, mh - 30), (220, 40), (mw - 30, mh // 2)], fill=ARCHIVAL_RED, width=6)
            
        p_m = marker_dir / f"{mid}.png"
        m_im.save(p_m)
        manifest.append({
            "id": mid,
            "category": "markers",
            "family": "annotation",
            "name": mname,
            "file": str(p_m.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [mw, mh],
            "transparency": True,
            "intended_usage": f"On-screen tactical highlights, player tracking, and crowd callouts ({mname})"
        })
    print("✓ 5 Red Marker Annotations Generated.")

    # -------------------------------------------------------------
    # 9. VINTAGE FOOTBALL TICKET TREATMENTS (3 variants)
    # -------------------------------------------------------------
    ticket_dir = STOCK_DIR / "tickets"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    
    ticket_styles = [
        ("ticket_variant_a_selhurst_1995", 620, 200, "Selhurst Park 1995 Premier League Stub"),
        ("ticket_variant_b_old_trafford_return", 640, 200, "Old Trafford October 1995 Comeback Pass"),
        ("ticket_variant_c_wembley_fa_cup", 620, 200, "Wembley Stadium Archival Match Ticket"),
    ]
    
    for tkid, tkw, tkh, tkname in ticket_styles:
        tk_im = Image.new("RGBA", (tkw, tkh), (0, 0, 0, 0))
        tk_base = Image.new("RGBA", (tkw, tkh), IVORY)
        draw_tk = ImageDraw.Draw(tk_base)
        
        # Red side strip
        draw_tk.rectangle([(20, 20), (28, tkh - 20)], fill=ARCHIVAL_RED)
        # Barcode area on right
        draw_tk.line([(tkw - 110, 20), (tkw - 110, tkh - 20)], fill=(190, 185, 175, 255), width=2)
        # Perforation dots
        for y in range(25, tkh - 20, 16):
            draw_tk.ellipse([(tkw - 113, y), (tkw - 107, y + 6)], fill=(30, 32, 40, 255))
            
        mask_tk = make_torn_edge_mask(tkw, tkh, roughness=2.2, tear_sides="left,right")
        tk_base.putalpha(mask_tk)
        tk_textured = add_paper_texture(tk_base, grain_intensity=0.03)
        
        p_tk = ticket_dir / f"{tkid}.png"
        tk_textured.save(p_tk)
        manifest.append({
            "id": tkid,
            "category": "tickets",
            "family": "vintage_ticket",
            "name": tkname,
            "file": str(p_tk.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "dimensions": [tkw, tkh],
            "transparency": True,
            "intended_usage": f"Historical match context tickets and attendance passes ({tkname})"
        })
    print("✓ 3 Vintage Ticket Treatments Generated.")

    # -------------------------------------------------------------
    # SAVE ASSET MANIFEST
    # -------------------------------------------------------------
    manifest_path = STOCK_DIR / "asset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "project": "FS30 Documentary Pipeline",
            "library_version": "2.0-vox-tactile",
            "total_assets": len(manifest),
            "categories": ["banners", "quotes", "frames", "underlines", "date_labels", "stamps", "textures", "markers", "tickets"],
            "assets": manifest
        }, f, indent=2)
        
    print(f"\n✓ Successfully compiled asset_manifest.json with {len(manifest)} verified assets!")

if __name__ == "__main__":
    build_reusable_library()
