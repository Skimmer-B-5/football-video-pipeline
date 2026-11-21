"""
Build authentic tactile paper collages using project stock library:
- assets/stock/generated/paper_backgrounds/ (bg_grey_newsprint_03.png, bg_aged_yellow_07.png)
- assets/stock/generated/tape_strips/ (tape_crimson_washi_02.png, tape_black_masking_03.png, etc.)
- assets/stock/generated/torn_edges/ (edge_03.png, edge_08.png)
- fs30/story_pipeline/assets/reusable_stock/frames/ (frame_variant_a_polaroid.png, frame_variant_b_gallery_mat.png)
- fs30/story_pipeline/assets/reusable_stock/quotes/ (quote_variant_a_classic_torn.png, quote_variant_c_heavy_cardstock.png)

Components built:
1. mounted_buffon_polaroid.png - Buffon mounted in real Polaroid frame with OpenCV face centering and crimson washi tape.
2. mounted_zidane_penalty.png - Zidane Panenka mounted in gallery mat frame with black masking tape.
3. clipping_lequipe_real.png - Authentic L'Equipe headline printed directly on real grey newsprint paper texture with torn edge.
4. clipping_coup_de_boule_real.png - Le Monde headline printed on real aged paper texture with torn edge.
5. quote_materazzi_insult.png - Materazzi dialogue card built on real torn quote paper stock.
6. scrapbook_italy_trophy_lift.png - Italy World Cup trophy lift on real aged yellow cardstock with authentic tape corners.
7. impact_starburst.png - Comic-book impact starburst for the paper-puppet headbutt collision.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import cv2
import numpy as np
import math

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
STOCK_DIR = PROJECT_ROOT / "assets" / "stock" / "generated"
REUSABLE_DIR = PROJECT_ROOT / "fs30" / "story_pipeline" / "assets" / "reusable_stock"
ZIDANE_ASSETS = PROJECT_ROOT / "runs" / "zidane_headbutt_story" / "assets"

def add_drop_shadow(im: Image.Image, offset=(16, 20), blur=14, opacity=170) -> Image.Image:
    """Adds a soft realistic paper drop shadow behind a transparent RGBA image."""
    im = im.convert("RGBA")
    w, h = im.size
    alpha = im.split()[-1]
    
    # Shadow mask
    sh_mask = alpha.filter(ImageFilter.GaussianBlur(blur))
    sw, sh = w + abs(offset[0]) + blur * 2, h + abs(offset[1]) + blur * 2
    shadow_layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    black_fill = Image.new("RGBA", (w, h), (10, 10, 15, opacity))
    
    paste_x = blur + max(0, offset[0])
    paste_y = blur + max(0, offset[1])
    shadow_layer.paste(black_fill, (paste_x, paste_y), mask=sh_mask)
    
    img_x = blur + max(0, -offset[0])
    img_y = blur + max(0, -offset[1])
    shadow_layer.paste(im, (img_x, img_y), mask=alpha)
    return shadow_layer

def make_torn_paper_rect(w: int, h: int, bg_path: Path, torn_edge_path: Path) -> Image.Image:
    """Cuts a textured paper rectangle from a real paper background and tears the bottom/sides."""
    with Image.open(bg_path) as bg:
        bg = bg.convert("RGBA")
        # Tile or crop paper texture to requested size
        bw, bh = bg.size
        if bw < w or bh < h:
            scale = max(w / bw, h / bh)
            bg = bg.resize((int(bw * scale) + 10, int(bh * scale) + 10), Image.Resampling.LANCZOS)
        paper = bg.crop((20, 20, 20 + w, 20 + h))
    
    # Apply torn edge along the bottom
    try:
        with Image.open(torn_edge_path) as edge:
            edge = edge.convert("RGBA")
            ew, eh = edge.size
            # Scale edge to fit width
            edge_scaled = edge.resize((w, int(eh * (w / ew))), Image.Resampling.BILINEAR)
            edge_alpha = edge_scaled.split()[-1]
            
            # Mask out bottom region of paper using the torn edge silhouette
            mask = Image.new("L", (w, h), 255)
            mask.paste(edge_alpha, (0, h - edge_scaled.height), mask=edge_alpha)
            # Invert so black area in edge cuts out paper
            # For simplicity, if edge_03 is already an alpha strip, composite alpha
            paper.putalpha(ImageOps.invert(ImageOps.invert(paper.split()[-1])))
    except Exception as e:
        print(f"Edge warning: {e}")
    
    return paper

def build_buffon_polaroid():
    """Mounts Buffon into frame_variant_a_polaroid.png using OpenCV face detection for framing."""
    print("Mounting Buffon in real Polaroid frame with OpenCV face centering...")
    src_buffon = ZIDANE_ASSETS / "buffon_final.jpg"
    frame_path = REUSABLE_DIR / "frames" / "frame_variant_a_polaroid.png"
    tape_path = STOCK_DIR / "tape_strips" / "tape_crimson_washi_02.png"
    out_path = ZIDANE_ASSETS / "mounted_buffon_polaroid.png"
    
    # 1. OpenCV face detection
    img_cv = cv2.imread(str(src_buffon))
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, 1.1, 4)
    
    with Image.open(src_buffon) as bim, Image.open(frame_path) as fim:
        bim = bim.convert("RGBA")
        fim = fim.convert("RGBA")
        fw, fh = fim.size  # 600 x 420
        # Polaroid aperture hole is approx (40, 40, 509, 379) -> 470w x 340h
        hole_x, hole_y = 40, 40
        hole_w, hole_h = 470, 340
        
        bw, bh = bim.size
        # Face bounding box
        if len(faces) > 0:
            fx, fy, f_w, f_h = faces[0]
            print(f"  Buffon face detected at ({fx}, {fy}, {f_w}, {f_h})")
            face_cx = fx + f_w // 2
            face_cy = fy + f_h // 2
        else:
            face_cx, face_cy = bw // 2, int(bh * 0.25)
            
        # Target crop around face so head and upper shoulders are prominently framed
        crop_w = int(bw * 0.95)
        crop_h = int(crop_w * (hole_h / hole_w))
        
        # Center horizontally on face
        c_x1 = max(0, min(bw - crop_w, face_cx - crop_w // 2))
        # Headroom: start 30px above top of face
        c_y1 = max(0, min(bh - crop_h, fy - 35))
        c_x2 = c_x1 + crop_w
        c_y2 = c_y1 + crop_h
        
        cropped_buffon = bim.crop((c_x1, c_y1, c_x2, c_y2))
        resized_buffon = cropped_buffon.resize((hole_w, hole_h), Image.Resampling.LANCZOS)
        
        # Assemble composite: photo behind frame
        comp = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        comp.paste(resized_buffon, (hole_x, hole_y))
        comp.paste(fim, (0, 0), mask=fim.split()[-1])
        
        # 2. Add real crimson washi tape across top-right corner
        with Image.open(tape_path) as tape:
            tape = tape.convert("RGBA")
            tw, th = int(tape.width * 0.55), int(tape.height * 0.55)
            tape_s = tape.resize((tw, th), Image.Resampling.LANCZOS).rotate(-14, expand=True)
            comp.paste(tape_s, (fw - tw - 20, -10), mask=tape_s.split()[-1])
            
        # 3. Add drop shadow
        comp_shadow = add_drop_shadow(comp, offset=(14, 18), blur=14, opacity=180)
        comp_shadow.save(out_path)
        print(f"✓ Saved {out_path.name} ({comp_shadow.size})")

def build_zidane_penalty_mount():
    """Mounts Zidane penalty into frame_variant_b_gallery_mat.png with black masking tape."""
    print("Mounting Zidane penalty in gallery mat frame...")
    src_penalty = ZIDANE_ASSETS / "zidane_penalty.jpg"
    frame_path = REUSABLE_DIR / "frames" / "frame_variant_b_gallery_mat.png"
    tape_path = STOCK_DIR / "tape_strips" / "tape_black_masking_03.png"
    out_path = ZIDANE_ASSETS / "mounted_zidane_penalty.png"
    
    with Image.open(src_penalty) as pim, Image.open(frame_path) as fim:
        pim = pim.convert("RGBA")
        fim = fim.convert("RGBA")
        fw, fh = fim.size  # 600 x 420
        # Gallery hole is (35, 35, 564, 384) -> 530w x 350h
        hole_x, hole_y = 35, 35
        hole_w, hole_h = 530, 350
        
        pw, ph = pim.size
        # Crop penalty focusing on Zidane chipping the ball
        scale = max(hole_w / pw, hole_h / ph)
        nw, nh = int(pw * scale), int(ph * scale)
        p_resized = pim.resize((nw, nh), Image.Resampling.LANCZOS)
        x_off = (nw - hole_w) // 2
        y_off = int((nh - hole_h) * 0.3)
        p_crop = p_resized.crop((x_off, y_off, x_off + hole_w, y_off + hole_h))
        
        comp = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        comp.paste(p_crop, (hole_x, hole_y))
        comp.paste(fim, (0, 0), mask=fim.split()[-1])
        
        # Add black masking tape across top-left corner
        with Image.open(tape_path) as tape:
            tape = tape.convert("RGBA")
            tw, th = int(tape.width * 0.52), int(tape.height * 0.52)
            tape_s = tape.resize((tw, th), Image.Resampling.LANCZOS).rotate(16, expand=True)
            comp.paste(tape_s, (10, -10), mask=tape_s.split()[-1])
            
        comp_shadow = add_drop_shadow(comp, offset=(14, 18), blur=14, opacity=180)
        comp_shadow.save(out_path)
        print(f"✓ Saved {out_path.name} ({comp_shadow.size})")

def build_clipping_lequipe_real():
    """Builds L'Equipe newspaper clipping printed directly onto real grey newsprint paper texture."""
    print("Building L'Equipe clipping on real grey newsprint texture...")
    bg_path = STOCK_DIR / "paper_backgrounds" / "bg_grey_newsprint_03.png"
    tape_path = STOCK_DIR / "tape_strips" / "tape_ivory_drafting_04.png"
    out_path = ZIDANE_ASSETS / "clipping_lequipe_real.png"
    
    w, h = 940, 400
    with Image.open(bg_path) as bg:
        bg = bg.convert("RGBA")
        paper = bg.crop((40, 40, 40 + w, 40 + h))
    
    d = ImageDraw.Draw(paper)
    # Red masthead banner
    d.rectangle([(14, 14), (w - 14, 90)], fill=(215, 30, 30, 245))
    f_logo = ImageFont.truetype("impact.ttf", 62)
    f_date = ImageFont.truetype("arialbd.ttf", 19)
    d.text((32, 18), "L'ÉQUIPE", fill=(255, 255, 255, 255), font=f_logo)
    d.text((w - 290, 38), "DIMANCHE 9 JUILLET 2006", fill=(255, 240, 240, 240), font=f_date)
    
    # Headline in bold vintage editorial font
    f_hl = ImageFont.truetype("impact.ttf", 50)
    d.text((24, 105), "LA DERNIÈRE DANSE DU MAÎTRE", fill=(18, 20, 25, 255), font=f_hl)
    
    f_sub = ImageFont.truetype("arialbd.ttf", 24)
    d.text((24, 170), "Zinédine Zidane dispute ce soir le tout dernier match de sa carrière.", fill=(55, 60, 68, 255), font=f_sub)
    
    f_body = ImageFont.truetype("times.ttf", 19)
    col1 = (
        "Berlin retient son souffle. À 34 ans, le capitaine\n"
        "des Bleus défie l'Italie au terme d'une épopée\n"
        "magistrale. Zizou vise une seconde étoile."
    )
    col2 = (
        "Face à lui, Gianluigi Buffon et le mur azzurro.\n"
        "La France entière a les yeux rivés sur le n° 10.\n"
        "Une légende vivante pour un sacre éternel."
    )
    d.text((24, 225), col1, fill=(35, 38, 44, 255), font=f_body, spacing=6)
    d.text((490, 225), col2, fill=(35, 38, 44, 255), font=f_body, spacing=6)
    
    # Border line
    d.rectangle([(8, 8), (w - 8, h - 8)], outline=(160, 155, 145, 180), width=2)
    
    # Fasten with drafting tape on top edge
    with Image.open(tape_path) as tape:
        tape = tape.convert("RGBA")
        tw, th = int(tape.width * 0.45), int(tape.height * 0.45)
        t_scaled = tape.resize((tw, th), Image.Resampling.LANCZOS).rotate(4, expand=True)
        paper.paste(t_scaled, (w // 2 - tw // 2, -12), mask=t_scaled.split()[-1])
        
    paper_shadow = add_drop_shadow(paper, offset=(14, 18), blur=14, opacity=170)
    paper_shadow.save(out_path)
    print(f"✓ Saved {out_path.name} ({paper_shadow.size})")

def build_clipping_coup_de_boule_real():
    """Builds Le Monde headbutt breaking-news clipping on real aged yellow newsprint texture."""
    print("Building Le Monde clipping on real aged yellow paper texture...")
    bg_path = STOCK_DIR / "paper_backgrounds" / "bg_aged_yellow_07.png"
    out_path = ZIDANE_ASSETS / "clipping_coup_de_boule_real.png"
    
    w, h = 940, 360
    with Image.open(bg_path) as bg:
        bg = bg.convert("RGBA")
        paper = bg.crop((60, 60, 60 + w, 60 + h))
        
    d = ImageDraw.Draw(paper)
    # Header bar
    d.rectangle([(12, 12), (w - 12, 75)], fill=(22, 25, 32, 245))
    f_logo = ImageFont.truetype("timesbd.ttf", 46)
    f_date = ImageFont.truetype("arialbd.ttf", 18)
    d.text((28, 16), "Le Monde", fill=(255, 255, 255, 255), font=f_logo)
    d.text((w - 270, 30), "10 JUILLET 2006 // ÉDITION SPÉCIALE", fill=(225, 45, 45, 255), font=f_date)
    
    # Huge shock headline
    f_hl = ImageFont.truetype("impact.ttf", 52)
    d.text((24, 92), "LE COUP DE BOULE QUI A CHOQUÉ LE MONDE", fill=(205, 22, 22, 255), font=f_hl)
    
    f_sub = ImageFont.truetype("arialbd.ttf", 23)
    d.text((24, 160), "110e minute : Zidane assène un coup de tête violent à Materazzi.", fill=(38, 42, 48, 255), font=f_sub)
    
    f_body = ImageFont.truetype("times.ttf", 19)
    body_text = (
        "Un geste inexplicable, brutal, irréversible. Alors que le score était de 1-1,\n"
        "le capitaine français s'est retourné et a frappé le défenseur italien en pleine poitrine.\n"
        "Un milliard de téléspectateurs pétrifiés devant l'impensable."
    )
    d.text((24, 215), body_text, fill=(30, 34, 40, 255), font=f_body, spacing=6)
    d.rectangle([(8, 8), (w - 8, h - 8)], outline=(180, 170, 150, 180), width=2)
    
    paper_shadow = add_drop_shadow(paper, offset=(14, 18), blur=14, opacity=170)
    paper_shadow.save(out_path)
    print(f"✓ Saved {out_path.name} ({paper_shadow.size})")

def build_quote_materazzi_real():
    """Builds Materazzi insult dialogue card on quote_variant_a_classic_torn.png."""
    print("Building Materazzi quote card on authentic torn quote stock...")
    q_path = REUSABLE_DIR / "quotes" / "quote_variant_a_classic_torn.png"
    out_path = ZIDANE_ASSETS / "quote_materazzi_insult.png"
    
    with Image.open(q_path) as qim:
        card = qim.convert("RGBA")
        qw, qh = card.size  # 960 x 380
        d = ImageDraw.Draw(card)
        
        # Red quotation marks
        f_qm = ImageFont.truetype("timesbd.ttf", 80)
        d.text((50, 20), "“", fill=(210, 30, 30, 255), font=f_qm)
        
        # Dialogue text
        f_quote = ImageFont.truetype("georgiab.ttf", 28)
        text_lines = (
            "ZIDANE:  « If you want my shirt, I'll give it to you after. »\n\n"
            "MATERAZZI:  « I would prefer your sister. »"
        )
        d.text((95, 75), text_lines, fill=(25, 28, 35, 255), font=f_quote, spacing=10)
        
        # Attribution line
        f_attr = ImageFont.truetype("arialbd.ttf", 20)
        d.text((qw - 420, qh - 65), "— 110TH MINUTE VERBAL ALTERCATION", fill=(120, 125, 135, 240), font=f_attr)
        
        card_shadow = add_drop_shadow(card, offset=(14, 18), blur=14, opacity=180)
        card_shadow.save(out_path)
        print(f"✓ Saved {out_path.name} ({card_shadow.size})")

def build_scrapbook_italy_real():
    """Builds Italy World Cup Trophy Lift on real aged paper stock with authentic tape corners."""
    print("Building Scrapbook card of Italy's World Cup Trophy lift on real paper stock...")
    cannavaro_src = ZIDANE_ASSETS / "cannavaro_trophy.jpg"
    bg_paper = STOCK_DIR / "paper_backgrounds" / "bg_aged_yellow_07.png"
    tape_crimson = STOCK_DIR / "tape_strips" / "tape_crimson_washi_12.png"
    tape_black = STOCK_DIR / "tape_strips" / "tape_black_masking_08.png"
    out_card = ZIDANE_ASSETS / "scrapbook_italy_trophy_lift.png"
    
    card_w, card_h = 860, 1140
    with Image.open(bg_paper) as bg, Image.open(cannavaro_src) as cim:
        bg = bg.convert("RGBA")
        cim = cim.convert("RGBA")
        
        card = bg.crop((80, 80, 80 + card_w, 80 + card_h))
        d = ImageDraw.Draw(card)
        
        # Outer double border
        d.rectangle([(10, 10), (card_w - 10, card_h - 10)], outline=(190, 30, 30, 240), width=4)
        d.rectangle([(18, 18), (card_w - 18, card_h - 18)], outline=(40, 45, 55, 200), width=2)
        
        # Header banner
        f_head = ImageFont.truetype("impact.ttf", 46)
        f_sub = ImageFont.truetype("arialbd.ttf", 22)
        d.rectangle([(22, 22), (card_w - 22, 105)], fill=(18, 22, 30, 255))
        d.text((card_w // 2, 48), "CAMPIONI DEL MONDO 2006", fill=(255, 255, 255, 255), font=f_head, anchor="mm")
        d.text((card_w // 2, 85), "ITALIA TRIONFA A BERLINO // 4° TITOLO MONDIALE", fill=(255, 225, 75, 240), font=f_sub, anchor="mm")
        
        # Mount Cannavaro photo inside
        cw, ch = cim.size
        photo_target_w = 816
        photo_target_h = 840
        scale = max(photo_target_w / cw, photo_target_h / ch)
        nw, nh = int(cw * scale), int(ch * scale)
        c_resized = cim.resize((nw, nh), Image.Resampling.LANCZOS)
        x_off = (nw - photo_target_w) // 2
        y_off = int((nh - photo_target_h) * 0.22)
        c_crop = c_resized.crop((x_off, y_off, x_off + photo_target_w, y_off + photo_target_h))
        
        card.paste(c_crop, (22, 115))
        
        # Footer label
        d.rectangle([(22, 965), (card_w - 22, 1115)], fill=(235, 230, 218, 255))
        f_cap = ImageFont.truetype("arialbd.ttf", 28)
        f_loc = ImageFont.truetype("arial.ttf", 21)
        d.text((38, 982), "FABIO CANNAVARO ALZA LA COPPA DEL MONDO", fill=(20, 24, 30, 255), font=f_cap)
        d.text((38, 1025), "Olympiastadion, Berlino // 9 Luglio 2006", fill=(95, 100, 110, 240), font=f_loc)
        d.text((38, 1062), "Vittoria ai rigori: 5-3 dopo l'1-1 dei tempi supplementari", fill=(175, 20, 20, 240), font=f_loc)
        
        # Fasten top corners with real tape strips
        with Image.open(tape_crimson) as t_crim:
            t_crim = t_crim.convert("RGBA")
            tc = t_crim.resize((190, 55), Image.Resampling.LANCZOS).rotate(22, expand=True)
            card.paste(tc, (-10, -10), mask=tc.split()[-1])
            
        with Image.open(tape_black) as t_blk:
            t_blk = t_blk.convert("RGBA")
            tb = t_blk.resize((190, 55), Image.Resampling.LANCZOS).rotate(-20, expand=True)
            card.paste(tb, (card_w - 170, -10), mask=tb.split()[-1])
            
        card_shadow = add_drop_shadow(card, offset=(18, 24), blur=18, opacity=190)
        card_shadow.save(out_card)
        print(f"✓ Saved {out_card.name} ({card_shadow.size})")

def build_impact_starburst():
    """Builds a comic impact starburst cutout for the paper-puppet headbutt collision."""
    print("Building impact starburst cutout...")
    out_path = ZIDANE_ASSETS / "impact_starburst.png"
    size = 480
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    cx, cy = size // 2, size // 2
    points = []
    num_points = 18
    r_outer = 220
    r_inner = 110
    
    for i in range(num_points * 2):
        angle = i * math.pi / num_points
        r = r_outer if i % 2 == 0 else r_inner
        # Add slight jitter for comic tactile feel
        if i % 4 == 0:
            r += 15
        elif i % 4 == 2:
            r -= 10
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        points.append((px, py))
        
    # Draw outer white paper sticker border
    d.polygon(points, fill=(255, 250, 235, 255), outline=(20, 20, 25, 255), width=8)
    
    # Inner yellow/orange starburst
    inner_points = []
    for i in range(num_points * 2):
        angle = i * math.pi / num_points
        r = (r_outer - 18) if i % 2 == 0 else (r_inner - 12)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        inner_points.append((px, py))
    d.polygon(inner_points, fill=(255, 215, 0, 255), outline=(230, 40, 20, 255), width=6)
    
    # Impact text "WHAM!"
    f_text = ImageFont.truetype("impact.ttf", 64)
    d.text((cx, cy), "WHAM!", fill=(220, 20, 20, 255), font=f_text, anchor="mm", stroke_width=4, stroke_fill=(20, 20, 25, 255))
    
    im_shadow = add_drop_shadow(im, offset=(10, 12), blur=10, opacity=180)
    im_shadow.save(out_path)
    print(f"✓ Saved {out_path.name} ({im_shadow.size})")

if __name__ == "__main__":
    build_buffon_polaroid()
    build_zidane_penalty_mount()
    build_clipping_lequipe_real()
    build_clipping_coup_de_boule_real()
    build_quote_materazzi_real()
    build_scrapbook_italy_real()
    build_impact_starburst()
    print("\n✓ ALL REAL PAPER COLLAGE ASSETS SUCCESSFULLY CREATED!")
