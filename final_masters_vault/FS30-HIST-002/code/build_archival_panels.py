from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageFont
import numpy as np

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
RUN_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story"
ASSETS_DIR = RUN_DIR / "assets"
ARCHIVE_DIR = ASSETS_DIR / "archival_footage"
LOOP_FRAMES_DIR = ARCHIVE_DIR / "loop_frames"
PANELS_DIR = ARCHIVE_DIR / "mounted_panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")

def add_drop_shadow(im: Image.Image, offset=(10, 16), blur=16, alpha=140) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    pad_x = abs(offset[0]) + blur * 2
    pad_y = abs(offset[1]) + blur * 2
    canvas = Image.new("RGBA", (w + pad_x * 2, h + pad_y * 2), (0, 0, 0, 0))
    alpha_mask = im.split()[-1]
    
    sh_mask = alpha_mask.filter(ImageFilter.GaussianBlur(blur))
    sh_arr = np.array(sh_mask, dtype=np.float32) * (alpha / 255.0)
    sh_mask = Image.fromarray(sh_arr.astype(np.uint8))
    
    black_fill = Image.new("RGBA", (w, h), (10, 12, 16, 255))
    canvas.paste(black_fill, (pad_x + offset[0], pad_y + offset[1]), mask=sh_mask)
    canvas.paste(im, (pad_x, pad_y), mask=alpha_mask)
    
    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas

def build_archival_panels():
    loop_files = sorted(LOOP_FRAMES_DIR.glob("headbutt_loop_*.jpg"))
    if not loop_files:
        print("No loop files found!")
        return
        
    try:
        font_header = ImageFont.truetype("arialbd.ttf", 24)
        font_sub = ImageFont.truetype("arial.ttf", 16)
    except:
        font_header = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    card_w = 880
    card_h = 660
    photo_w = 800
    photo_h = 505
    
    for i, lf in enumerate(loop_files):
        with Image.open(lf) as lim:
            resized_lim = lim.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
            
            # Parchment Archival Broadcast Card
            card = Image.new("RGBA", (card_w, card_h), (246, 244, 238, 255))
            draw = ImageDraw.Draw(card)
            
            # Double borders
            draw.rectangle([(8, 8), (card_w - 9, card_h - 9)], outline=(210, 204, 190, 255), width=2)
            draw.rectangle([(14, 14), (card_w - 15, card_h - 15)], outline=(180, 172, 155, 255), width=1)
            
            # Top Header Bar (dark archival plate)
            draw.rectangle([(30, 26), (card_w - 30, 72)], fill=(20, 24, 30, 255))
            # Blinking red REC indicator dot
            draw.ellipse([(44, 42), (56, 54)], fill=(220, 30, 30, 255))
            draw.text((66, 38), "ARCHIVAL BROADCAST // 110TH MINUTE", fill=(255, 255, 255, 255), font=font_header)
            draw.text((card_w - 220, 42), "BERLIN 2006 • REPLAY", fill=(235, 200, 80, 255), font=font_sub)
            
            # Paste Video Frame
            card.paste(resized_lim, (40, 85))
            
            # Dark outer screen bezel border around video
            draw.rectangle([(38, 83), (40 + photo_w + 1, 85 + photo_h + 1)], outline=(30, 35, 42, 255), width=2)
            
            # Bottom caption line
            draw.text((45, 608), "INCIDENT: CHEST STRIKE • ZIDANE (FRA #10) vs MATERAZZI (ITA #23)", fill=(50, 55, 65, 255), font=font_sub)
            
            # Authentic black washi tape at top right (tucked onto border, clear of text)
            tape = Image.new("RGBA", (130, 36), (35, 40, 48, 220))
            tape = tape.rotate(8, expand=True)
            card.paste(tape, (card_w - 110, -5), mask=tape)
            
            # Drop shadow
            shadowed = add_drop_shadow(card, offset=(10, 16), blur=16, alpha=150)
            out_p = PANELS_DIR / f"panel_{i:02d}.png"
            shadowed.save(out_p)
            
    print(f"Pre-rendered {len(loop_files)} archival broadcast panels in {PANELS_DIR}")
    
    # Save sample to brain
    sample_p = PANELS_DIR / "panel_04.png"
    sample_im = Image.open(sample_p)
    sample_im.save(BRAIN_DIR / "inspect_mounted_headbutt_panel.png")
    print("Saved inspect_mounted_headbutt_panel.png to brain")

if __name__ == "__main__":
    build_archival_panels()
