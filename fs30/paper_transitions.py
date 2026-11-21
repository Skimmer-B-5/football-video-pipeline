"""
FS 30 Paper Transitions Subsystem (D4).
Implements 5 distinct paper-cut transitions lasting 0.25-0.45s:
1. paper_wipe (torn paper sweeping across frame)
2. page_flip (perspective curl/turn peel)
3. tape_rip (packing tape snapping across cut)
4. glass_distortion_dissolve (using 04_Glass distortions PNG displacement maps)
5. crumple_cut (wrinkled paper crinkle wipe)
"""

import math
import random
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops
import numpy as np

from fs30.assets.library import library

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def transition_paper_wipe(frame_a: Image.Image, frame_b: Image.Image, progress: float) -> Image.Image:
    """
    1. paper_wipe: A torn paper edge sweeps across from left to right (or top to bottom).
    progress: 0.0 -> 1.0
    """
    w, h = frame_a.size
    # Current sweep x position
    sweep_x = int((w + 200) * progress) - 100

    # Create torn paper mask
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)

    # Jagged torn edge contour
    pts = [(0, 0)]
    for y in range(0, h + 20, 30):
        jitter = int(18 * math.sin(y * 0.04) + 12 * math.cos(y * 0.08))
        pts.append((sweep_x + jitter, y))
    pts.append((0, h))

    draw.polygon(pts, fill=255)

    # Add a thin white torn paper edge line
    edge_mask = mask.filter(ImageFilter.MaxFilter(11))
    edge_diff = ImageChops.difference(edge_mask, mask)

    # Composite: where mask is 255, show frame_b, else frame_a
    comp = Image.composite(frame_b, frame_a, mask)
    
    # Draw white fibrous tear edge
    tear_edge = Image.new("RGB", (w, h), (248, 245, 238))
    final = Image.composite(tear_edge, comp, edge_diff)
    return final

def transition_glass_distortion_dissolve(
    frame_a: Image.Image,
    frame_b: Image.Image,
    progress: float
) -> Image.Image:
    """
    2. glass_distortion_dissolve: Uses 04_Glass distortions PNG heightmap
    to refract and dissolve pixels across the cut.
    """
    w, h = frame_a.size

    # Pick glass distortion map from asset library
    glass_asset = library.pick("glass_distortion")
    if glass_asset and Path(glass_asset["path"]).exists():
        disp_map = Image.open(glass_asset["path"]).convert("L").resize((w, h))
    else:
        # Fallback generated fluted glass stripes
        disp_map = Image.new("L", (w, h), 128)
        d_draw = ImageDraw.Draw(disp_map)
        for x in range(0, w, 24):
            val = int(128 + 120 * math.sin(x * 0.2))
            d_draw.rectangle([x, 0, x + 12, h], fill=val)

    # Displacement strength peaks at progress = 0.5
    strength = math.sin(progress * math.pi) * 35.0

    map_np = np.array(disp_map, dtype=np.float32) / 255.0 - 0.5
    dx = (map_np * strength).astype(np.float32)

    # Displace frame_a and frame_b horizontally
    np_a = np.array(frame_a)
    np_b = np.array(frame_b)

    # Cross-fade blend factor
    alpha = progress
    blended = Image.blend(frame_a, frame_b, alpha)

    # Apply glass displacement to blended image
    blended_np = np.array(blended)
    h_idx, w_idx = np.indices((h, w))
    new_w = np.clip(w_idx + dx, 0, w - 1).astype(np.int32)

    displaced_np = blended_np[h_idx, new_w]
    return Image.fromarray(displaced_np)

def transition_tape_rip(frame_a: Image.Image, frame_b: Image.Image, progress: float) -> Image.Image:
    """
    3. tape_rip: Packing tape strip snaps across the seam, then rips open to reveal frame_b.
    """
    w, h = frame_a.size
    mid_y = h // 2

    if progress < 0.5:
        # Tape slides across frame_a
        t_prog = progress / 0.5
        tape_len = int(w * t_prog)
        base = frame_a.copy()
        draw = ImageDraw.Draw(base)
        # Draw translucent amber tape
        tape_h = 140
        draw.rounded_rectangle([0, mid_y - tape_h//2, tape_len, mid_y + tape_h//2], radius=10, fill=(185, 120, 60))
        return base
    else:
        # Tape rips and reveals frame_b expanding from center
        t_prog = (progress - 0.5) / 0.5
        rip_h = int(h * t_prog)
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle([0, mid_y - rip_h//2, w, mid_y + rip_h//2], fill=255)
        return Image.composite(frame_b, frame_a, mask)

def transition_crumple_cut(frame_a: Image.Image, frame_b: Image.Image, progress: float) -> Image.Image:
    """
    4. crumple_cut: Paper texture wrinkle wipe contracts and unfolds into frame_b.
    """
    w, h = frame_a.size
    if progress < 0.5:
        p = progress / 0.5
        # Frame a shrinks slightly like being crumpled
        scale = 1.0 - 0.25 * p
        tw, th = int(w * scale), int(h * scale)
        shrunk = frame_a.resize((tw, th), Image.Resampling.BILINEAR)
        canvas = Image.new("RGB", (w, h), (14, 16, 22))
        canvas.paste(shrunk, ((w - tw) // 2, (h - th) // 2))
        return canvas
    else:
        p = (progress - 0.5) / 0.5
        scale = 0.75 + 0.25 * p
        tw, th = int(w * scale), int(h * scale)
        expanded = frame_b.resize((tw, th), Image.Resampling.BILINEAR)
        canvas = Image.new("RGB", (w, h), (14, 16, 22))
        canvas.paste(expanded, ((w - tw) // 2, (h - th) // 2))
        return canvas

def transition_page_flip(frame_a: Image.Image, frame_b: Image.Image, progress: float) -> Image.Image:
    """
    5. page_flip: Diagonal peel / page curl across the screen.
    """
    w, h = frame_a.size
    peel_x = int(w * (1.0 - progress))
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(peel_x, 0), (w, 0), (w, h), (max(0, peel_x - 200), h)], fill=255)
    return Image.composite(frame_b, frame_a, mask)

def render_transition(
    trans_type: str,
    frame_a: Image.Image,
    frame_b: Image.Image,
    progress: float
) -> Image.Image:
    """Dispatches to one of the 5 paper transitions."""
    if trans_type == "paper_wipe":
        return transition_paper_wipe(frame_a, frame_b, progress)
    elif trans_type == "glass_distortion_dissolve":
        return transition_glass_distortion_dissolve(frame_a, frame_b, progress)
    elif trans_type == "tape_rip":
        return transition_tape_rip(frame_a, frame_b, progress)
    elif trans_type == "crumple_cut":
        return transition_crumple_cut(frame_a, frame_b, progress)
    elif trans_type == "page_flip":
        return transition_page_flip(frame_a, frame_b, progress)
    else:
        return transition_paper_wipe(frame_a, frame_b, progress)
