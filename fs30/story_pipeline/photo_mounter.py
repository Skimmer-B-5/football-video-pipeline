"""
Universal Archival Photo & Cutout Mounter for FS30 Documentary Pipeline.
STRICT GUARANTEE: Zero vertical or horizontal distortion.
Never independently modifies X and Y dimensions.
Always preserves intrinsic aspect ratio using proportional scaling
and intentional focus-centered cropping.
"""

from typing import Tuple, Optional
from PIL import Image, ImageOps, ImageDraw, ImageFilter
import numpy as np

def mount_archival_photo(
    img: Image.Image,
    target_w: int,
    target_h: int,
    border_width: int = 10,
    border_color: Tuple[int, int, int] = (245, 242, 235),
    outer_border_width: int = 2,
    outer_border_color: Tuple[int, int, int] = (180, 175, 165),
    shadow_radius: int = 14,
    shadow_alpha: int = 180,
    shadow_offset: Tuple[int, int] = (15, 20),
    focus_point: Tuple[float, float] = (0.5, 0.5)
) -> Image.Image:
    """
    Mounts an archival photograph into a specified canvas target size.
    Calculates uniform proportional scale = max(target_w / orig_w, target_h / orig_h).
    Crops intentionally around focus_point.
    Adds realistic archival ivory frame, outer bevel, and soft drop shadow.
    """
    orig_w, orig_h = img.size
    scale = max(target_w / orig_w, target_h / orig_h)
    new_w = int(round(orig_w * scale))
    new_h = int(round(orig_h * scale))
    
    # Proportional resize preserving aspect ratio exactly
    scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Intentional cropping centered around focus_point
    fx, fy = focus_point
    desired_center_x = int(new_w * fx)
    desired_center_y = int(new_h * fy)
    
    crop_x1 = max(0, min(new_w - target_w, desired_center_x - target_w // 2))
    crop_y1 = max(0, min(new_h - target_h, desired_center_y - target_h // 2))
    crop_x2 = crop_x1 + target_w
    crop_y2 = crop_y1 + target_h
    
    cropped = scaled.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    
    # Add inner border & outer bevel
    bordered = ImageOps.expand(cropped, border=border_width, fill=border_color)
    if outer_border_width > 0:
        bordered = ImageOps.expand(bordered, border=outer_border_width, fill=outer_border_color)
        
    # Realistic soft drop shadow
    bw, bh = bordered.size
    pad = shadow_radius * 2
    canvas = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    sh_mask = Image.new("L", (bw, bh), 255).filter(ImageFilter.GaussianBlur(shadow_radius))
    
    sh_x = pad + shadow_offset[0]
    sh_y = pad + shadow_offset[1]
    canvas.paste(Image.new("RGBA", (bw, bh), (10, 12, 16, shadow_alpha)), (sh_x, sh_y), mask=sh_mask)
    canvas.paste(bordered.convert("RGBA"), (pad, pad))
    return canvas

def scale_cutout_proportional(
    cutout: Image.Image,
    target_h: Optional[int] = None,
    target_w: Optional[int] = None
) -> Image.Image:
    """
    Scales a transparent cutout PNG strictly proportionally.
    Guarantees zero aspect ratio distortion.
    """
    cw, ch = cutout.size
    if target_h is not None and target_w is not None:
        # Use fit scale
        scale = min(target_w / cw, target_h / ch)
    elif target_h is not None:
        scale = target_h / ch
    elif target_w is not None:
        scale = target_w / cw
    else:
        scale = 1.0
        
    nw = int(round(cw * scale))
    nh = int(round(ch * scale))
    return cutout.resize((nw, nh), Image.Resampling.LANCZOS)
