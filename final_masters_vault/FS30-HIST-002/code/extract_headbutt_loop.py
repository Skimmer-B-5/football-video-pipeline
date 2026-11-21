from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageFont

RUN_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\runs\zidane_headbutt_story")
ASSETS_DIR = RUN_DIR / "assets"
ARCHIVE_DIR = ASSETS_DIR / "archival_footage"
LOOP_FRAMES_DIR = ARCHIVE_DIR / "loop_frames"
LOOP_FRAMES_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")

gif_path = ASSETS_DIR / "zidane_incident_archival_loop.gif"
im = Image.open(gif_path)
n_frames = getattr(im, "n_frames", 1)
print(f"Extracting {n_frames} frames from {gif_path.name}...")

# Target size for the embedded broadcast panel inside the collage
# E.g. 760 x 480 (16:10 or 16:9)
target_w, target_h = 760, 480

for i in range(n_frames):
    im.seek(i)
    rgb = im.convert("RGB")
    
    # im is 1200 x 675. Let's crop tight to Zidane and Materazzi in center
    # crop_box: keep center action
    w, h = rgb.size
    # crop 15% from left and right so action is centered and large
    left = int(w * 0.12)
    right = int(w * 0.88)
    top = 0
    bottom = h
    cropped = rgb.crop((left, top, right, bottom))
    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    out_f = LOOP_FRAMES_DIR / f"headbutt_loop_{i:02d}.jpg"
    resized.save(out_f, quality=95)
    
print(f"Saved {n_frames} loop frames in {LOOP_FRAMES_DIR}")

# Save sample frame to brain for inspection
sample_im = Image.open(LOOP_FRAMES_DIR / "headbutt_loop_04.jpg")
sample_im.save(BRAIN_DIR / "inspect_headbutt_loop_sample.jpg")
print("Saved sample to brain")
