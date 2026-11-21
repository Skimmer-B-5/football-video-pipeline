from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFilter

raw_frames_dir = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\runs\cantona_kungfu_kick_story\assets\archival_footage\kick_frames_hd")
out_dir = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\runs\cantona_kungfu_kick_story\assets\archival_footage\loop_frames")
out_dir.mkdir(parents=True, exist_ok=True)
art_dir = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")

# Range: frames 38 to 54 (17 frames covering run-up, kick impact, and reaction)
frame_indices = list(range(38, 55))
processed_frames = []

crop_box = (320, 40, 1600, 1040) # (1280 x 1000) pure action, no border artifacts
target_w, target_h = 460, 360 # Compact archival panel size

for idx, f_num in enumerate(frame_indices):
    p = raw_frames_dir / f"frame_{f_num:03d}.png"
    im = Image.open(p)
    cropped = im.crop(crop_box)
    scaled = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Save raw loop frame
    scaled.save(out_dir / f"kick_loop_{idx:02d}.jpg", quality=92)
    processed_frames.append(scaled)

# Also create animated GIF for standalone playback
gif_path = out_dir / "cantona_kick_archival_loop.gif"
processed_frames[0].save(
    gif_path,
    save_all=True,
    append_images=processed_frames[1:],
    duration=80, # ~12.5 fps
    loop=0
)
import shutil
shutil.copyfile(str(gif_path), str(art_dir / "cantona_kick_archival_loop.gif"))
print(f"Created {gif_path.name} ({len(processed_frames)} frames)")
