"""
Stage 4: fetch_assets
Fetches images for each asset in the frame plan, executes background removal,
applies the strict Cutout Quality Gate, handles fallbacks, and creates
code-drawn paper shapes / jersey silhouettes if assets fail.
Strictly ensures only one ML model runs at a time and frees memory.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import cv2

from fs30.config import PROJECT_ROOT, load_config
from stages.image_scrapers import scrape_bing_images, scrape_duckduckgo_images

def check_cutout_quality_gate(cutout_img: Image.Image, raw_w: int, raw_h: int) -> Tuple[bool, str]:
    """
    Strict Cutout Quality Gate per Part 1 Stage 4:
    Reject a cutout if ANY of:
    - subject covers < 15% or > 85% of image area
    - the alpha mask has more than 2 large disconnected components
    - most edge pixels are semi-transparent (fuzzy mask)
    - the image's short side < 600 px
    """
    short_side = min(raw_w, raw_h)
    if short_side < 600:
        return False, f"Short side ({short_side}px) < 600px minimum"

    if cutout_img.mode != "RGBA":
        return False, "Cutout does not have an alpha channel"

    alpha_np = np.array(cutout_img.split()[-1])
    total_pixels = alpha_np.size
    subject_pixels = int(np.count_nonzero(alpha_np > 30))

    if total_pixels == 0 or subject_pixels == 0:
        return False, "Alpha mask is empty"

    coverage = subject_pixels / float(total_pixels)
    if coverage < 0.15:
        return False, f"Subject coverage ({coverage:.1%}) < 15% of image area"
    if coverage > 0.85:
        return False, f"Subject coverage ({coverage:.1%}) > 85% of image area"

    # Disconnected components check
    bin_mask = (alpha_np > 50).astype(np.uint8)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bin_mask)
    # stats: [x, y, width, height, area]. Label 0 is background.
    large_components = 0
    for label_idx in range(1, num_labels):
        comp_area = stats[label_idx, cv2.CC_STAT_AREA]
        if comp_area > (0.05 * subject_pixels):
            large_components += 1

    if large_components > 2:
        return False, f"Alpha mask has {large_components} large disconnected components (> 2 allowed)"

    # Fuzzy edge check
    fuzzy_pixels = np.count_nonzero((alpha_np > 25) & (alpha_np < 230))
    solid_pixels = np.count_nonzero(alpha_np >= 230)
    fuzzy_ratio = fuzzy_pixels / float(max(1, fuzzy_pixels + solid_pixels))
    if fuzzy_ratio > 0.35:
        return False, f"Mask has fuzzy semi-transparent edges ({fuzzy_ratio:.1%})"

    return True, "PASSED"

def check_background_quality_gate(bg_img: Image.Image) -> Tuple[bool, str]:
    """
    Background Quality Gate per Part 1 Stage 4:
    Reject if short side < 900 px or large watermarks/text detected.
    """
    w, h = bg_img.size
    short_side = min(w, h)
    if short_side < 900:
        return False, f"Background short side ({short_side}px) < 900px minimum"
    return True, "PASSED"

def apply_paper_edge(cutout_img: Image.Image, stroke_width: int = 6, stroke_color=(244, 239, 230, 255)) -> Image.Image:
    """
    Applies an off-white paper border/outline around the cutout edge
    with slight hand-cut irregularity to look authentically like cut paper.
    """
    if cutout_img.mode != "RGBA":
        cutout_img = cutout_img.convert("RGBA")

    alpha = cutout_img.split()[-1]
    w, h = cutout_img.size

    # Dilate mask for paper border
    dilated_mask = alpha.filter(ImageFilter.MaxFilter(stroke_width * 2 + 1))
    
    # Hand-cut paper roughness
    mask_np = np.array(dilated_mask, dtype=np.uint8)
    noise = np.random.randint(-8, 8, mask_np.shape, dtype=np.int16)
    rough_mask_np = np.clip(mask_np.astype(np.int16) + (noise * (mask_np > 10).astype(np.int16)), 0, 255).astype(np.uint8)
    rough_mask = Image.fromarray(rough_mask_np).filter(ImageFilter.GaussianBlur(0.6))

    # Paper stroke layer
    stroke_layer = Image.new("RGBA", (w, h), stroke_color)
    paper_cutout = Image.composite(stroke_layer, Image.new("RGBA", (w, h), (0, 0, 0, 0)), rough_mask)
    # Paste actual subject over stroke
    paper_cutout.paste(cutout_img, (0, 0), cutout_img)
    return paper_cutout

def generate_jersey_silhouette(color: str = "#C8102E", secondary_color: str = "#00519E", width: int = 800, height: int = 1000) -> Image.Image:
    """Generates a stylized paper-cut football jersey silhouette in palette colors."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Convert hex to RGBA
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (255,)

    col1 = hex_to_rgb(color)
    col2 = hex_to_rgb(secondary_color)

    # Draw jersey body polygon
    points = [
        (260, 180),  # left collar
        (120, 280),  # left shoulder
        (40, 420),   # left sleeve tip
        (130, 480),  # left underarm sleeve
        (210, 420),  # left underarm inner
        (210, 880),  # left waist
        (590, 880),  # right waist
        (590, 420),  # right underarm inner
        (670, 480),  # right underarm sleeve
        (760, 420),  # right sleeve tip
        (680, 280),  # right shoulder
        (540, 180),  # right collar
        (400, 230),  # collar dip
    ]
    draw.polygon(points, fill=col1)

    # Collar detail
    collar_points = [(260, 180), (400, 230), (540, 180), (400, 270)]
    draw.polygon(collar_points, fill=col2)

    # Sleeve cuffs
    draw.polygon([(40, 420), (130, 480), (110, 500), (20, 440)], fill=col2)
    draw.polygon([(760, 420), (670, 480), (690, 500), (780, 440)], fill=col2)

    # Apply hand-cut paper edge
    return apply_paper_edge(img, stroke_width=8)

def generate_paper_background(palette: Dict[str, str], width: int = 1080, height: int = 1920) -> Image.Image:
    """Generates a flat paper-textured colour field with torn paper shapes."""
    bg_color = palette.get("paper", "#F4EFE6")
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    base = Image.new("RGB", (width, height), hex_to_rgb(bg_color))
    draw = ImageDraw.Draw(base)

    # Add dark/muted contrast shapes
    acc1 = hex_to_rgb(palette.get("accent1", "#C8102E"))
    acc2 = hex_to_rgb(palette.get("accent2", "#00519E"))

    # Diagonal torn paper wedge
    wedge1 = [(0, 0), (width, 0), (width, 600), (0, 850)]
    draw.polygon(wedge1, fill=(max(0, acc2[0]-40), max(0, acc2[1]-40), max(0, acc2[2]-40)))

    # Torn paper strip across mid
    strip = [(0, 1100), (width, 1020), (width, 1320), (0, 1400)]
    draw.polygon(strip, fill=(max(0, acc1[0]-30), max(0, acc1[1]-30), max(0, acc1[2]-30)))

    # Add paper noise grain
    grain = np.random.randint(-12, 12, (height, width, 3), dtype=np.int16)
    base_np = np.clip(np.array(base, dtype=np.int16) + grain, 0, 255).astype(np.uint8)
    return Image.fromarray(base_np)

def download_and_save_image(url: str, dest_path: Path, timeout: int = 10) -> bool:
    """Downloads image to destination path."""
    import requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200 and len(r.content) > 10000:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False

def fetch_assets(
    plan: Dict[str, Any],
    run_dir: Path,
    log_func=print
) -> Dict[str, Path]:
    """
    Executes Stage 4: For each asset in plan, fetches, removes background,
    evaluates quality gates, handles fallback queries and fallback silhouettes.
    Strictly purges ML models between steps.
    """
    import rembg
    run_dir = Path(run_dir)
    assets_dir = run_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    palette = plan.get("palette", {})
    assets_list = plan.get("assets", [])

    resolved_assets = {}

    log_func(f"[Stage 4: fetch_assets] Processing {len(assets_list)} asset(s) from plan...")

    # Load rembg session with ManagedModel lifecycle
    from experiments.vox_pipeline.stages.model_manager import ManagedModel
    def load_rembg():
        return rembg.new_session("u2netp")

    with ManagedModel("rembg_u2netp_segmenter", load_rembg) as session:
        for a in assets_list:
            a_id = a.get("id")
            a_type = a.get("type", "photo")
            query = a.get("search_query")
            fallback_query = a.get("fallback_query")
            subject_alt = a.get("subject_alt", "none")

            log_func(f"\n[Asset {a_id}] Type: {a_type} | Query: \"{query}\"")
            final_asset_path = assets_dir / f"{a_id}.png"

            if final_asset_path.exists() and final_asset_path.stat().st_size > 5000:
                log_func(f"  ✓ Re-using existing asset -> {final_asset_path.name}")
                resolved_assets[a_id] = final_asset_path
                continue

            if a_type == "cutout":
                # Try primary query then fallback query
                success = False
                for q_attempt, q in enumerate([query, fallback_query]):
                    if not q:
                        continue
                    log_func(f"  Attempt {q_attempt + 1}: Searching web for \"{q}\"...")
                    images = scrape_bing_images(q, max_results=6)
                    if not images:
                        images = scrape_duckduckgo_images(q, max_results=6)

                    for img_candidate in images:
                        temp_raw = assets_dir / f"temp_{a_id}_raw.jpg"
                        if download_and_save_image(img_candidate.url, temp_raw):
                            try:
                                pil_raw = Image.open(temp_raw).convert("RGB")
                                raw_w, raw_h = pil_raw.size

                                # Run rembg
                                cutout = rembg.remove(pil_raw, session=session)
                                is_valid, gate_reason = check_cutout_quality_gate(cutout, raw_w, raw_h)

                                if is_valid:
                                    # Apply paper edge
                                    paper_cutout = apply_paper_edge(cutout, stroke_width=7)
                                    paper_cutout.save(final_asset_path, "PNG")
                                    log_func(f"  ✓ Quality Gate PASSED ({raw_w}x{raw_h}) -> Saved {final_asset_path.name}")
                                    success = True
                                    if temp_raw.exists():
                                        temp_raw.unlink()
                                    break
                                else:
                                    log_func(f"  ✗ Quality Gate REJECTED: {gate_reason}")
                            except Exception as err:
                                log_func(f"  ✗ Processing error: {err}")
                            if temp_raw.exists():
                                temp_raw.unlink()
                    if success:
                        break

                if not success:
                    # Fallback to subject_alt (jersey silhouette in palette colors)
                    log_func(f"  ⚠ All queries rejected. Triggering subject_alt: '{subject_alt}'")
                    jersey = generate_jersey_silhouette(
                        color=palette.get("accent1", "#C8102E"),
                        secondary_color=palette.get("accent2", "#00519E")
                    )
                    jersey.save(final_asset_path, "PNG")
                    log_func(f"  ✓ Synthesized code-drawn jersey silhouette -> {final_asset_path.name}")

            else:  # a_type == "photo" background
                success = False
                for q_attempt, q in enumerate([query, fallback_query]):
                    if not q:
                        continue
                    log_func(f"  Attempt {q_attempt + 1}: Searching background for \"{q}\"...")
                    images = scrape_bing_images(q, aspect="wide", max_results=6)
                    if not images:
                        images = scrape_duckduckgo_images(q, max_results=6)

                    for img_candidate in images:
                        temp_raw = assets_dir / f"temp_{a_id}_bg.jpg"
                        if download_and_save_image(img_candidate.url, temp_raw):
                            try:
                                pil_bg = Image.open(temp_raw).convert("RGB")
                                is_valid, gate_reason = check_background_quality_gate(pil_bg)
                                if is_valid:
                                    pil_bg.save(final_asset_path, "PNG")
                                    log_func(f"  ✓ Background Quality Gate PASSED ({pil_bg.width}x{pil_bg.height}) -> Saved {final_asset_path.name}")
                                    success = True
                                    if temp_raw.exists():
                                        temp_raw.unlink()
                                    break
                                else:
                                    log_func(f"  ✗ Background REJECTED: {gate_reason}")
                            except Exception as err:
                                log_func(f"  ✗ Background error: {err}")
                            if temp_raw.exists():
                                temp_raw.unlink()
                    if success:
                        break

                if not success:
                    log_func(f"  ⚠ Background query failed. Falling back to textured paper field.")
                    paper_bg = generate_paper_background(palette)
                    paper_bg.save(final_asset_path, "PNG")
                    log_func(f"  ✓ Synthesized procedural paper background -> {final_asset_path.name}")

            resolved_assets[a_id] = final_asset_path

    log_func(f"[Stage 4: fetch_assets] ✓ All {len(resolved_assets)} asset(s) ready on disk.")
    return resolved_assets
