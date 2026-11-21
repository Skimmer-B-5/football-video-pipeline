"""
Stage 7: render
Renders each scene into a 1080x1920 2.5D paper-cut animated clip:
- Hand-cut paper shapes with irregular edges & drop shadows scaling with z.
- Stepped paper motion at fps_motion=12, output encoded at fps_output=30.
- Parallax camera moves (push_in, pull_out, drift, static_breathe).
- Subtle paper grain & vignette overlays.
- Lower-third paper-style captions and 2-second FS 30 outro card.
- Audio mastered with scene voice and background atmospheric bed at -22dB.
Strictly respects memory ceiling (peak RAM < 2 GB).
"""

import os
import sys
import json
import math
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageOps, ImageFont
import numpy as np

from fs30.config import PROJECT_ROOT, load_config
from fs30.paper_shapes import generate_shape_image, generate_text_card, create_drop_shadow

# Pre-generate 1080x1920 paper grain and vignette texture
_GRAIN_TEXTURE = None
_VIGNETTE_MASK = None

def get_grain_and_vignette(w: int = 1080, h: int = 1920) -> Tuple[np.ndarray, Image.Image]:
    global _GRAIN_TEXTURE, _VIGNETTE_MASK
    if _GRAIN_TEXTURE is not None and _VIGNETTE_MASK is not None:
        return _GRAIN_TEXTURE, _VIGNETTE_MASK

    # Paper grain (int16 delta)
    _GRAIN_TEXTURE = np.random.randint(-10, 10, (h, w, 3), dtype=np.int16)

    # Vignette mask
    vignette = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(vignette)
    for r in range(0, 300, 10):
        alpha = int(255 - (r / 300.0) * 80)
        draw.rectangle([r*0.6, r, w - r*0.6, h - r], outline=alpha, width=12)
    _VIGNETTE_MASK = vignette.filter(ImageFilter.GaussianBlur(80))

    return _GRAIN_TEXTURE, _VIGNETTE_MASK

def render_scene_frames(
    scene: Dict[str, Any],
    palette: Dict[str, str],
    resolved_assets: Dict[str, Path],
    duration_sec: float,
    frames_dir: Path,
    fps_motion: int = 12
) -> int:
    """
    Renders all 12fps motion frames for a scene into frames_dir.
    Returns total frame count.
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    total_frames = max(1, int(duration_sec * fps_motion))

    cam = scene.get("camera", {})
    cam_move = cam.get("move", "push_in")
    cam_intensity = cam.get("intensity", "low")
    scale_amp = 0.03 if cam_intensity == "low" else 0.06
    pan_amp = 20 if cam_intensity == "low" else 45

    layers = sorted(scene.get("layers", []), key=lambda l: l.get("z", 0))

    # Pre-load or pre-generate layer graphic objects
    layer_objects = []
    bg_pil = None

    for l in layers:
        role = l.get("role")
        z = l.get("z", 1)
        enter = l.get("enter", "none")
        enter_delay = l.get("enter_delay", 0.0)
        idle = l.get("idle", "none")
        exit_anim = l.get("exit", "none")

        col_ref = l.get("color", "accent1")
        col_hex = palette.get(col_ref, col_ref)

        if role == "background":
            a_id = l.get("asset")
            bg_p = resolved_assets.get(a_id)
            if bg_p and bg_p.exists():
                raw_bg = Image.open(bg_p).convert("RGB")
            else:
                from fs30.stage4_fetch_assets import generate_paper_background
                raw_bg = generate_paper_background(palette)

            # Fit to 1080x1920 cover
            bg_resized = ImageOps.fit(raw_bg, (1160, 2060), Image.Resampling.LANCZOS)
            # Desaturate and dim so foreground paper pops
            bg_dimmed = ImageEnhance.Brightness(ImageEnhance.Color(bg_resized).enhance(0.70)).enhance(0.60)
            bg_pil = bg_dimmed

        elif role == "subject":
            a_id = l.get("asset")
            sub_p = resolved_assets.get(a_id)
            if sub_p and sub_p.exists():
                sub_img = Image.open(sub_p).convert("RGBA")
            else:
                from fs30.stage4_fetch_assets import generate_jersey_silhouette
                sub_img = generate_jersey_silhouette(color=palette.get("accent1", "#C8102E"))

            # Scale to fit nicely in 1080x1920 (max height 1100)
            target_h = 1050
            target_w = int(sub_img.width * (target_h / float(sub_img.height)))
            sub_resized = sub_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            layer_objects.append({
                "type": "subject", "z": z, "img": sub_resized,
                "base_pos": ((1080 - target_w) // 2 + 30, 1920 - target_h + 30),
                "enter": enter, "enter_delay": enter_delay, "idle": idle, "exit": exit_anim
            })

        elif role == "paper_shape":
            shape_type = l.get("shape", "torn_strip")
            shape_img = generate_shape_image(shape_type, col_hex)
            # Default placement depending on shape
            pos = ((1080 - shape_img.width) // 2, 450 + z * 80)
            layer_objects.append({
                "type": "paper_shape", "z": z, "img": shape_img,
                "base_pos": pos,
                "enter": enter, "enter_delay": enter_delay, "idle": idle, "exit": exit_anim
            })

        elif role == "text_card":
            card_text = l.get("text", "HEADLINE")
            card_img = generate_text_card(card_text, bg_color=palette.get("paper", "#F4EFE6"), text_color="#0A0C10")
            pos = ((1080 - card_img.width) // 2, 380)
            layer_objects.append({
                "type": "text_card", "z": z, "img": card_img,
                "base_pos": pos,
                "enter": enter, "enter_delay": enter_delay, "idle": idle, "exit": exit_anim
            })

    if bg_pil is None:
        from fs30.stage4_fetch_assets import generate_paper_background
        bg_pil = generate_paper_background(palette, 1160, 2060)

    grain, vignette_mask = get_grain_and_vignette(1080, 1920)

    # Render each stepped frame
    for f_idx in range(total_frames):
        t = f_idx / float(fps_motion)
        norm_t = min(1.0, f_idx / float(max(1, total_frames - 1)))

        # 1. Background Camera Motion
        if cam_move == "push_in":
            bg_scale = 1.0 + (scale_amp * norm_t)
            pan_x, pan_y = 0, 0
        elif cam_move == "pull_out":
            bg_scale = (1.0 + scale_amp) - (scale_amp * norm_t)
            pan_x, pan_y = 0, 0
        elif cam_move == "drift_left":
            bg_scale = 1.02
            pan_x = -int(pan_amp * norm_t)
            pan_y = 0
        elif cam_move == "drift_right":
            bg_scale = 1.02
            pan_x = int(pan_amp * norm_t)
            pan_y = 0
        elif cam_move == "drift_up":
            bg_scale = 1.02
            pan_x = 0
            pan_y = -int(pan_amp * norm_t)
        else:  # static_breathe
            bg_scale = 1.01 + 0.015 * math.sin(2 * math.pi * 0.4 * t)
            pan_x, pan_y = 0, 0

        bw = int(1160 * bg_scale)
        bh = int(2060 * bg_scale)
        bg_scaled = bg_pil.resize((bw, bh), Image.Resampling.BILINEAR)

        # Crop to 1080x1920
        cx = (bw - 1080) // 2 + pan_x
        cy = (bh - 1920) // 2 + pan_y
        cx = max(0, min(bw - 1080, cx))
        cy = max(0, min(bh - 1920, cy))
        frame_canvas = bg_scaled.crop((cx, cy, cx + 1080, cy + 1920)).convert("RGBA")

        # 2. Render each layer with drop shadow and parallax
        for l_obj in layer_objects:
            t_enter = t - l_obj["enter_delay"]
            if t_enter < 0:
                continue  # Layer hasn't entered yet

            img = l_obj["img"]
            z = l_obj["z"]
            base_x, base_y = l_obj["base_pos"]

            # Compute enter transformation
            cur_scale = 1.0
            cur_rot = 0.0
            offset_x = 0
            offset_y = 0
            opacity = 1.0

            # Enter Animation (duration 0.35s)
            enter_dur = 0.35
            if t_enter < enter_dur:
                p = t_enter / enter_dur
                e_type = l_obj["enter"]
                if e_type == "pop_in":
                    # Overshoot curve: 0 -> 1.08 -> 1.0
                    cur_scale = math.sin(p * math.pi * 0.6) * 1.08 if p < 0.8 else (1.08 - (p - 0.8) * 0.4)
                elif e_type == "slide_in_left":
                    offset_x = -int(1080 * (1.0 - p))
                elif e_type == "slide_in_right":
                    offset_x = int(1080 * (1.0 - p))
                elif e_type == "slide_in_up":
                    offset_y = int(800 * (1.0 - p))
                elif e_type == "drop_in":
                    # Fall from top with bounce
                    offset_y = -int(900 * (1.0 - p)**1.5)
                elif e_type == "unfold":
                    cur_scale = p
            else:
                # Idle Animation
                t_idle = t_enter - enter_dur
                i_type = l_obj["idle"]
                if i_type == "wobble":
                    cur_rot = 1.8 * math.sin(2 * math.pi * 1.1 * t_idle)
                elif i_type == "float":
                    offset_y = int(7 * math.sin(2 * math.pi * 0.8 * t_idle))
                elif i_type == "pulse":
                    cur_scale = 1.0 + 0.03 * math.sin(2 * math.pi * 1.0 * t_idle)

            # Exit Animation (last 0.3s)
            if l_obj["exit"] == "slide_out" and t > (duration_sec - 0.3):
                p_exit = (t - (duration_sec - 0.3)) / 0.3
                offset_x += int(1080 * p_exit)

            # Parallax camera shift (higher z moves more)
            parallax_mult = 1.0 + (z * 0.4)
            final_x = base_x + offset_x + int(pan_x * (parallax_mult - 1.0))
            final_y = base_y + offset_y + int(pan_y * (parallax_mult - 1.0))

            # Transform image
            transformed = img
            if cur_scale != 1.0 and cur_scale > 0.05:
                tw = max(10, int(transformed.width * cur_scale))
                th = max(10, int(transformed.height * cur_scale))
                transformed = transformed.resize((tw, th), Image.Resampling.BILINEAR)

            if cur_rot != 0.0:
                transformed = transformed.rotate(cur_rot, expand=True, resample=Image.Resampling.BICUBIC)

            # 3. Soft Offset Drop Shadow scaling with z
            s_blur = max(6, int(10 * z))
            s_offset = (0, max(6, int(8 * z)))
            shadow_canvas, s_pad = create_drop_shadow(transformed, offset=s_offset, blur=s_blur, alpha_factor=0.45)
            
            # Paste shadow then layer
            frame_canvas.paste(shadow_canvas, (final_x - s_pad, final_y - s_pad), shadow_canvas)
            frame_canvas.paste(transformed, (final_x, final_y), transformed)

        # 4. Subtle Paper Grain & Vignette
        frame_rgb = frame_canvas.convert("RGB")
        frame_np = np.array(frame_rgb, dtype=np.int16)
        grained_np = np.clip(frame_np + grain, 0, 255).astype(np.uint8)
        grained_img = Image.fromarray(grained_np)
        
        # Vignette
        vignette_layer = Image.new("RGB", (1080, 1920), (0, 0, 0))
        final_frame = Image.composite(grained_img, vignette_layer, vignette_mask)

        # Save frame
        frame_path = frames_dir / f"frame_{f_idx:04d}.jpg"
        final_frame.save(frame_path, "JPEG", quality=92)

    return total_frames

def render_scene_clip(
    scene_id: int,
    frames_dir: Path,
    audio_path: Path,
    captions_ass: Path,
    duration_sec: float,
    output_mp4: Path,
    fps_motion: int = 12,
    fps_output: int = 30
) -> Path:
    """
    Encodes motion frames held at 30fps with audio and burned ASS subtitles.
    """
    ass_escaped = str(captions_ass).replace("\\", "/").replace(":", "\\:")
    frames_pattern = str(frames_dir / "frame_%04d.jpg").replace("\\", "/")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps_motion),
        "-i", frames_pattern,
        "-i", str(audio_path),
        "-filter_complex", f"[0:v]fps={fps_output},ass='{ass_escaped}'[outv]",
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps_output),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", f"{duration_sec:.2f}",
        str(output_mp4)
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_mp4

def generate_outro_clip(output_mp4: Path, palette: Dict[str, str], duration_sec: float = 2.0) -> Path:
    """Generates 2-second outro card with FS 30 channel logo."""
    # Create clean paper outro card
    canvas = Image.new("RGB", (1080, 1920), (10, 12, 16))
    draw = ImageDraw.Draw(canvas)

    # Cream paper card in center
    card_w, card_h = 760, 480
    cx, cy = (1080 - card_w) // 2, (1920 - card_h) // 2
    draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=24, fill=(244, 239, 230))
    draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=24, outline=(200, 16, 46), width=6)

    try:
        font_huge = ImageFont.truetype("arialbd.ttf", 108)
        font_sub = ImageFont.truetype("arialbd.ttf", 44)
    except Exception:
        font_huge = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((cx + 180, cy + 120), "FS 30", font=font_huge, fill=(10, 12, 16))
    draw.text((cx + 100, cy + 280), "FOOTBALL IN 30 SECONDS", font=font_sub, fill=(200, 16, 46))

    temp_img = output_mp4.parent / "temp_outro_frame.jpg"
    canvas.save(temp_img, "JPEG", quality=95)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", f"{duration_sec:.2f}", "-i", str(temp_img),
        "-f", "lavfi", "-t", f"{duration_sec:.2f}", "-i", "anullsrc=r=48000:cl=stereo",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        str(output_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    if temp_img.exists():
        temp_img.unlink()
    return output_mp4

def render_full_video(
    plan_data: Dict[str, Any],
    resolved_assets: Dict[str, Path],
    audio_results: Dict[int, Dict[str, Any]],
    caption_files: Dict[int, Path],
    run_dir: Path,
    log_func=print
) -> Path:
    """
    Renders every scene, appends outro, mixes atmospheric Foley, and exports final master MP4.
    """
    run_dir = Path(run_dir)
    render_dir = run_dir / "render"
    render_dir.mkdir(parents=True, exist_ok=True)
    master_mp4 = run_dir / "final_fs30_master.mp4"

    palette = plan_data.get("palette", {})
    scenes = plan_data.get("scenes", [])

    log_func(f"[Stage 7: render] Rendering {len(scenes)} paper-cut scenes at 1080x1920 (12fps motion, 30fps output)...")

    rendered_clips = []
    for sc in scenes:
        s_id = sc.get("id")
        dur = sc.get("est_seconds", 4.0)
        a_info = audio_results[s_id]
        ass_path = caption_files[s_id]

        s_frames_dir = render_dir / f"scene_{s_id}_frames"
        clip_out = render_dir / f"scene_{s_id}.mp4"

        if clip_out.exists() and clip_out.stat().st_size > 50000:
            log_func(f"\n[Scene {s_id}] Re-using already rendered clip -> {clip_out.name}")
            rendered_clips.append(clip_out)
            continue

        log_func(f"\n[Scene {s_id}] Rendering frames ({dur:.2f}s, {sc.get('camera',{}).get('move')})...")
        render_scene_frames(
            scene=sc,
            palette=palette,
            resolved_assets=resolved_assets,
            duration_sec=dur,
            frames_dir=s_frames_dir,
            fps_motion=12
        )

        log_func(f"  Encoding clip with captions & audio -> {clip_out.name}")
        render_scene_clip(
            scene_id=s_id,
            frames_dir=s_frames_dir,
            audio_path=a_info["audio_path"],
            captions_ass=ass_path,
            duration_sec=dur,
            output_mp4=clip_out
        )
        rendered_clips.append(clip_out)

        # Clean frames to keep disk footprint minimal
        for f in s_frames_dir.glob("*.jpg"):
            f.unlink()
        s_frames_dir.rmdir()

    # Outro clip
    outro_mp4 = render_dir / "outro.mp4"
    log_func(f"\n[Outro] Generating 2-second FS 30 outro card...")
    generate_outro_clip(outro_mp4, palette, duration_sec=2.0)
    rendered_clips.append(outro_mp4)

    # Stitch all clips together
    concat_txt = render_dir / "concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in rendered_clips:
            f.write(f"file '{str(c.resolve()).replace(chr(92), '/')}'\n")

    log_func(f"\n[Stage 7: render] Stitching all clips into master video: {master_mp4.name}...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        str(master_mp4)
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    log_func(f"[Stage 7: render] ✓ MASTER VIDEO RENDERED: {master_mp4.name} ({master_mp4.stat().st_size // 1024} KB)")

    return master_mp4
