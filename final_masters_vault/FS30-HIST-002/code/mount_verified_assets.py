from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageFont
import numpy as np

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
ASSETS_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story" / "assets"
CAND_DIR = ASSETS_DIR / "candidates"
BRAIN_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")

def add_drop_shadow(im: Image.Image, offset=(12, 18), blur=16, alpha=140) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    pad_x = abs(offset[0]) + blur * 2
    pad_y = abs(offset[1]) + blur * 2
    canvas = Image.new("RGBA", (w + pad_x * 2, h + pad_y * 2), (0, 0, 0, 0))
    alpha_mask = im.split()[-1]
    
    sh_mask = alpha_mask.filter(ImageFilter.GaussianBlur(blur))
    sh_arr = np.array(sh_mask, dtype=np.float32) * (alpha / 255.0)
    sh_mask = Image.fromarray(sh_arr.astype(np.uint8))
    
    black_fill = Image.new("RGBA", (w, h), (12, 14, 18, 255))
    canvas.paste(black_fill, (pad_x + offset[0], pad_y + offset[1]), mask=sh_mask)
    canvas.paste(im, (pad_x, pad_y), mask=alpha_mask)
    
    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas

def mount_cannavaro_trophy_lift():
    # Source image: candidate_cannavaro_trophy_lift_reuters.jpg (1861x2300)
    src_path = CAND_DIR / "cannavaro_trophy_lift_reuters.jpg"
    im = Image.open(src_path).convert("RGB")
    
    # We want a vertical card (e.g. 880 x 1150)
    target_card_w, target_card_h = 880, 1150
    photo_w, photo_h = 820, 960
    
    # Crop image preserving the trophy at the top and Cannavaro in the middle
    # im is 1861 x 2300. Ratio = 820 / 960 = 0.854.
    crop_w = int(im.height * 0.854)
    if crop_w > im.width:
        crop_w = im.width
        crop_h = int(crop_w / 0.854)
    else:
        crop_h = im.height
        
    left = (im.width - crop_w) // 2
    top = 0 # keep very top where trophy is!
    cropped = im.crop((left, top, left + crop_w, top + crop_h))
    resized_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
    
    # Create Scrapbook / Editorial Card
    card = Image.new("RGBA", (target_card_w, target_card_h), (248, 246, 240, 255))
    draw = ImageDraw.Draw(card)
    
    # Double archival border
    draw.rectangle([(8, 8), (target_card_w - 9, target_card_h - 9)], outline=(210, 204, 190, 255), width=2)
    draw.rectangle([(16, 16), (target_card_w - 17, target_card_h - 17)], outline=(180, 172, 155, 255), width=1)
    
    # Paste photo at (30, 30)
    card.paste(resized_photo, (30, 30))
    
    # Bottom editorial caption plate
    caption_y = 30 + photo_h + 15
    try:
        font_head = ImageFont.truetype("arialbd.ttf", 34)
        font_sub = ImageFont.truetype("arial.ttf", 22)
    except:
        font_head = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    draw.text((40, caption_y), "FABIO CANNAVARO // CAMPIONI DEL MONDO", fill=(20, 24, 30, 255), font=font_head)
    draw.text((42, caption_y + 44), "Olympiastadion, Berlino • 9 Luglio 2006 • 4° Titolo Mondiale", fill=(120, 25, 35, 255), font=font_sub)
    
    # Add authentic washi tape at top-left
    tape = Image.new("RGBA", (180, 48), (210, 35, 45, 210))
    tape = tape.rotate(14, expand=True)
    card.paste(tape, (10, -5), mask=tape)
    
    # Cast 3D drop shadow
    shadowed = add_drop_shadow(card, offset=(10, 16), blur=18, alpha=150)
    out_path = ASSETS_DIR / "mounted_cannavaro_trophy_lift_verified.png"
    shadowed.save(out_path)
    shadowed.save(BRAIN_DIR / "inspect_mounted_cannavaro_verified.png")
    print(f"Mounted Cannavaro: {out_path.name} ({shadowed.size})")

def mount_zidane_trophy_walk():
    # Source image: candidate_zidane_walk_trophy_2.jpg (663x920)
    src_path = CAND_DIR / "zidane_walk_trophy_2.jpg"
    im = Image.open(src_path).convert("RGB")
    
    target_card_w, target_card_h = 860, 1140
    photo_w, photo_h = 800, 960
    
    # Preserve full height: im is 663 x 920.
    # We want 800 x 960 (ratio 0.833).
    # im ratio: 663/920 = 0.72. So we need to crop slightly from top/bottom or fit with margins.
    # Both Zidane's head and the trophy must stay!
    # Trophy is at the bottom-left, Zidane's head is at top-center.
    # Let's crop proportionally without losing either!
    crop_h = int(im.width / 0.833) # 663 / 0.833 = 795
    if crop_h > im.height:
        crop_h = im.height
        crop_w = int(crop_h * 0.833)
        left = (im.width - crop_w) // 2
        top = 0
    else:
        crop_w = im.width
        left = 0
        top = 0 # keep top (head) and bottom (trophy)
        
    cropped = im.crop((left, 0, left + crop_w, crop_h))
    resized_photo = cropped.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
    
    card = Image.new("RGBA", (target_card_w, target_card_h), (248, 246, 240, 255))
    draw = ImageDraw.Draw(card)
    
    draw.rectangle([(8, 8), (target_card_w - 9, target_card_h - 9)], outline=(210, 204, 190, 255), width=2)
    draw.rectangle([(16, 16), (target_card_w - 17, target_card_h - 17)], outline=(180, 172, 155, 255), width=1)
    
    card.paste(resized_photo, (30, 30))
    
    caption_y = 30 + photo_h + 15
    try:
        font_head = ImageFont.truetype("arialbd.ttf", 34)
        font_sub = ImageFont.truetype("arial.ttf", 22)
    except:
        font_head = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    draw.text((40, caption_y), "ZINÉDINE ZIDANE // LA SORTIE DU ROI", fill=(20, 24, 30, 255), font=font_head)
    draw.text((42, caption_y + 44), "110e Minute • Le dernier adieu au trophée mondial", fill=(180, 30, 35, 255), font=font_sub)
    
    tape = Image.new("RGBA", (180, 48), (40, 45, 55, 210))
    tape = tape.rotate(-12, expand=True)
    card.paste(tape, (target_card_w - 170, -5), mask=tape)
    
    shadowed = add_drop_shadow(card, offset=(10, 16), blur=18, alpha=150)
    out_path = ASSETS_DIR / "mounted_zidane_trophy_walk_verified.png"
    shadowed.save(out_path)
    shadowed.save(BRAIN_DIR / "inspect_mounted_zidane_verified.png")
    print(f"Mounted Zidane: {out_path.name} ({shadowed.size})")

if __name__ == "__main__":
    mount_cannavaro_trophy_lift()
    mount_zidane_trophy_walk()
