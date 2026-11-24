"""
beta/stages/generate_v7_1_6_5_crt_comparison.py
Generates the 3-Way 1990s CRT Broadcast Treatment Comparison for Beta V7.1.6.5:
1. Original Image (Raw Photograph)
2. Current Treatment (Previous Faint Scanlines)
3. Revised 1990s CRT Treatment (Clearly Visible Scanlines, Phosphor Highlight Glow, RGB Chromatic Separation, Analog Softening & Warmth)
"""

import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.typography import load_font

OUTPUT_DIR = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "visuals" / "crt_comparison_v7_1_6_5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def apply_current_faint_treatment(img_rgb: np.ndarray) -> np.ndarray:
    """Simulates the previous faint treatment (opacity ~0.09)."""
    h, w = img_rgb.shape[:2]
    out = img_rgb.copy().astype(np.float32)
    # Very faint scanlines: multiplying by ~0.91 every other 2 lines
    for y in range(0, h, 4):
        out[y:y+2] *= 0.91
    return np.clip(out, 0, 255).astype(np.uint8)

def apply_revised_1990s_crt_treatment(img_rgb: np.ndarray) -> np.ndarray:
    """
    Applies authentic 1990s CRT television broadcast processing:
    1. Rich CRT analog contrast & warm saturation
    2. Broadcast resolution softening (480i/576i cathode ray upscale)
    3. Phosphor highlight glow (screen blend bloom on bright areas)
    4. Trinitron RGB chromatic separation (red left 2px, cyan right 2px)
    5. Clearly visible horizontal scanlines (calibrated for 1080p and mobile screens)
    6. Gentle analog RF signal noise
    """
    h, w = img_rgb.shape[:2]
    base = img_rgb.astype(np.float32)

    # 1. Analog broadcast grade: contrast 1.08, warm midtones, saturation boost
    base = (base - 128.0) * 1.08 + 128.0
    base[:, :, 0] *= 1.04  # Red/warm boost
    base[:, :, 1] *= 1.01  # Green balance
    base[:, :, 2] *= 0.98  # Blue slight analog roll-off
    base = np.clip(base, 0, 255)

    # 2. Broadcast softening: 576i cathode upscale
    blurred_base = cv2.GaussianBlur(base, (3, 3), 0.6)

    # 3. Phosphor highlight bloom (radiant glow on lights and white kits)
    gray = cv2.cvtColor(blurred_base.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    mask = np.clip((gray - 140.0) / 115.0, 0, 1.0) # Highlight mask
    bloom = cv2.GaussianBlur(blurred_base, (21, 21), 7.0)
    # Screen blend: 1 - (1 - A)*(1 - B)
    comp = 255.0 - (255.0 - blurred_base) * (255.0 - (bloom * mask[:, :, np.newaxis] * 0.45)) / 255.0

    # 4. RGB Chromatic Separation (Trinitron aperture grille fringing: 2px offset)
    r_shift = np.zeros_like(comp[:, :, 0])
    r_shift[:, 2:] = comp[:, :-2, 0] # Shift red 2px left
    r_shift[:, :2] = comp[:, 0:1, 0]

    b_shift = np.zeros_like(comp[:, :, 2])
    b_shift[:, :-2] = comp[:, 2:, 2] # Shift blue 2px right
    b_shift[:, -2:] = comp[:, -1:, 2]

    chroma = comp.copy()
    chroma[:, :, 0] = chroma[:, :, 0] * 0.7 + r_shift * 0.3
    chroma[:, :, 2] = chroma[:, :, 2] * 0.7 + b_shift * 0.3

    # 5. Clearly Visible 1990s CRT Scanlines (2px dark scanline every 4px, ~40% darkness)
    scanline_mult = np.ones((h, w, 1), dtype=np.float32)
    for y in range(0, h, 4):
        scanline_mult[y:y+2] = 0.58  # 42% opacity darkness - clearly recognizable on phones!

    scanned = chroma * scanline_mult

    # 6. Gentle analog RF signal noise
    noise = np.random.normal(0, 2.5, (h, w, 3)).astype(np.float32)
    final_crt = np.clip(scanned + noise, 0, 255).astype(np.uint8)

    # Subtle Trinitron curved tube vignette
    Y, X = np.ogrid[:h, :w]
    center_y, center_x = h / 2.0, w / 2.0
    dist_sq = ((X - center_x) / (w * 0.6)) ** 2 + ((Y - center_y) / (h * 0.6)) ** 2
    vignette = np.clip(1.0 - dist_sq * 0.22, 0.72, 1.0)[:, :, np.newaxis]
    final_crt = (final_crt * vignette).astype(np.uint8)

    return final_crt

def create_comparison():
    print("==================================================================")
    print("  GENERATING 1990s CRT BROADCAST TREATMENT COMPARISON           ")
    print("==================================================================")

    # Use S02 repaired portrait (Endrick presentation) and S01 Bernabeu
    s02_path = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "assets" / "approved" / "S02_approved_repaired.png"
    assert s02_path.exists(), f"Missing {s02_path}"

    raw_img = cv2.imread(str(s02_path))
    raw_rgb = cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB)

    faint_rgb = apply_current_faint_treatment(raw_rgb)
    revised_rgb = apply_revised_1990s_crt_treatment(raw_rgb)

    # Create a 3-panel side-by-side horizontal comparison for desktop/mobile inspection (1920x1080)
    # Target size per panel: 640x1080 (cropped center 9:16 slice or scaled)
    panel_w = 640
    panel_h = 1080
    
    # Crop center 640x1080 from the 1080x1920 canvas
    # S02 face is in upper center
    crop_x1 = (1080 - panel_w) // 2 # 220
    crop_x2 = crop_x1 + panel_w     # 860
    crop_y1 = 80
    crop_y2 = crop_y1 + panel_h    # 1160

    panel_raw = cv2.resize(raw_rgb[crop_y1:crop_y2, crop_x1:crop_x2], (panel_w, panel_h))
    panel_faint = cv2.resize(faint_rgb[crop_y1:crop_y2, crop_x1:crop_x2], (panel_w, panel_h))
    panel_revised = cv2.resize(revised_rgb[crop_y1:crop_y2, crop_x1:crop_x2], (panel_w, panel_h))

    # Stitch panels into 1920x1080 canvas
    canvas = np.zeros((1080, 1920, 3), dtype=np.uint8)
    canvas[:, 0:640] = panel_raw
    canvas[:, 640:1280] = panel_faint
    canvas[:, 1280:1920] = panel_revised

    # Draw separator lines
    cv2.line(canvas, (640, 0), (640, 1080), (56, 189, 248), 2)
    cv2.line(canvas, (1280, 0), (1280, 1080), (250, 204, 21), 2)

    # Convert to PIL for clean typographic annotations
    pil_img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(pil_img)

    f_title = load_font("Barlow Condensed", 800, 36)
    f_sub = load_font("IBM Plex Mono", 600, 20)
    f_tag = load_font("Inter", 600, 18)

    # Header Badges for each panel
    # Panel 1: Original
    draw.rectangle([(20, 30), (620, 115)], fill=(11, 19, 43))
    draw.text((35, 40), "1. ORIGINAL PHOTOGRAPH (RAW)", font=f_title, fill=(255, 255, 255))
    draw.text((35, 82), "Digital HD Capture • Zero CRT Character", font=f_sub, fill=(148, 163, 184))

    # Panel 2: Current
    draw.rectangle([(660, 30), (1260, 115)], fill=(11, 19, 43))
    draw.text((675, 40), "2. CURRENT TREATMENT (FAINT)", font=f_title, fill=(239, 68, 68))
    draw.text((675, 82), "Faint ~9% Scanline Texture • Invisible on Phone", font=f_sub, fill=(252, 165, 165))

    # Panel 3: Revised 1990s CRT
    draw.rectangle([(1300, 30), (1900, 115)], fill=(11, 19, 43), outline=(250, 204, 21), width=2)
    draw.text((1315, 40), "3. REVISED 1990s CRT BROADCAST", font=f_title, fill=(250, 204, 21))
    draw.text((1315, 82), "Visible Scanlines • Phosphor Glow • RGB Fringing", font=f_sub, fill=(254, 240, 138))

    # Footer feature pills on Panel 3
    pills = [
        "✓ Visible 576i Scanlines",
        "✓ Highlight Phosphor Bloom",
        "✓ Trinitron RGB Fringing",
        "✓ Analog Warmth & RF Noise"
    ]
    py = 920
    for p in pills:
        draw.rounded_rectangle([(1315, py), (1750, py + 32)], radius=4, fill=(12, 60, 36), outline=(46, 204, 113))
        draw.text((1330, py + 5), p, font=f_tag, fill=(255, 255, 255))
        py += 38

    out_png = OUTPUT_DIR / "crt_treatment_comparison_v7_1_6_5.png"
    out_jpg = OUTPUT_DIR / "crt_treatment_comparison_v7_1_6_5.jpg"
    pil_img.save(str(out_png), "PNG")
    pil_img.save(str(out_jpg), "JPEG", quality=95)
    print(f"Generated CRT Comparison Image: {out_png} ({out_png.stat().st_size} bytes)")

    # Also generate a 4-second comparison MP4 video showing the live CRT treatment with phosphor shimmer!
    out_mp4 = OUTPUT_DIR / "crt_treatment_comparison_v7_1_6_5.mp4"
    temp_dir = OUTPUT_DIR / "temp_frames"
    temp_dir.mkdir(parents=True, exist_ok=True)

    fps = 30
    total_frames = 90 # 3.0 seconds
    for f in range(total_frames):
        # Add frame-varying jitter and shimmer
        jitter_x = int(round(np.sin(f * 0.45) * 1.0))
        shimmer_mult = 1.0 + np.sin(f * 0.35) * 0.02

        f_crt = revised_rgb.copy()
        if jitter_x != 0:
            M = np.float32([[1, 0, jitter_x], [0, 1, 0]])
            f_crt = cv2.warpAffine(f_crt, M, (1080, 1920))
        f_crt = np.clip(f_crt * shimmer_mult, 0, 255).astype(np.uint8)

        p_revised = cv2.resize(f_crt[crop_y1:crop_y2, crop_x1:crop_x2], (panel_w, panel_h))
        frame_canvas = canvas.copy()
        frame_canvas[:, 1280:1920] = p_revised

        # Save frame
        frame_file = temp_dir / f"frame_{f:03d}.png"
        cv2.imwrite(str(frame_file), cv2.cvtColor(frame_canvas, cv2.COLOR_RGB2BGR))

    subprocess.run([
        "ffmpeg", "-y",
        "-r", str(fps),
        "-i", str(temp_dir / "frame_%03d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        str(out_mp4)
    ], check=True, capture_output=True)

    # Clean up temp frames
    for f in temp_dir.glob("*.png"):
        f.unlink()
    temp_dir.rmdir()

    print(f"Generated CRT Comparison Video: {out_mp4} ({out_mp4.stat().st_size} bytes)")
    return out_png, out_jpg, out_mp4

if __name__ == "__main__":
    create_comparison()
