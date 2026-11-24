"""
# PROVENANCE: Copied from stages/image_quality_sensor.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Computer Vision Quality & Subject Framing Arbiter for @Footballin30sec.
Stage Component: stages/image_quality_sensor.py

Responsibilities:
1. Strict Visual Quality Gate:
   - Minimum resolution: Reject ANY image where max(width, height) < 1080.
   - Minimum file size: Reject images < 80 KB (81,920 bytes).
   - Sharpness scoring: OpenCV Laplacian variance. Reject images with variance < 80.0.
   - Artifact / Stock Watermark detection: Reject heavy stock text (Alamy, Getty, Shutterstock)
     and thumbnail artifacts (letterbox bars, pillarbox bars, low variance solid boxes).
   - Aspect ratio classification: Tag images as NATIVE_VERTICAL (< 0.8), SQUARE (0.8 - 1.2),
     or WIDE_LANDSCAPE (> 1.2).

2. OpenCV Subject Centering & Editorial 9:16 Framing:
   - Detect face and upper-body centroids using Haar cascades with saliency & gradient fallback.
   - NATIVE_VERTICAL: Crop centered on subject centroid into exact 1080x1920 with upper-third
     rule-of-thirds headroom.
   - WIDE_LANDSCAPE: Editorial broadcast presentation without cutting people in half:
     * Blurred background fill (scaled up, Gaussian blur 35, darkened) + Sharp centered
       foreground window with subtle broadcast border & drop shadow.
     * Optional 2.5D subject cutout on editorial matte backdrop.
   - SQUARE: Smart rule-of-thirds vertical crop if subject fits safely; otherwise broadcast blur window.
   - Broadcast color grading: Unsharp mask, balanced contrast, clean vibrancy, and brightness boost.
"""

import os
import sys
import io
import time
import math
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Union

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageOps

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration Constants
MIN_DIMENSION_LIMIT = 1080          # max(width, height) must be >= 1080
MIN_FILE_SIZE_BYTES = 80 * 1024    # 80 KB minimum
MIN_SHARPNESS_LAPLACIAN = 80.0     # Reject blurry/out-of-focus (< 80)
ASPECT_VERTICAL_MAX = 0.8          # < 0.8 -> NATIVE_VERTICAL
ASPECT_SQUARE_MAX = 1.2            # 0.8 <= aspect <= 1.2 -> SQUARE, > 1.2 -> WIDE_LANDSCAPE
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_ASPECT = TARGET_WIDTH / TARGET_HEIGHT  # 9/16 = 0.5625

# Stock Agency Watermark Keywords
STOCK_WATERMARK_KEYWORDS = {
    "alamy", "gettyimages", "getty", "shutterstock", "istockphoto", "istock",
    "dreamstime", "depositphotos", "vectorstock", "123rf", "stockphoto",
    "fotolia", "bigstockphoto", "canstockphoto", "watermark", "preview_wm"
}


# ============================================================================
# Dataclasses
# ============================================================================

class AspectRatioTag:
    NATIVE_VERTICAL = "NATIVE_VERTICAL"
    SQUARE = "SQUARE"
    WIDE_LANDSCAPE = "WIDE_LANDSCAPE"


@dataclass
class QualityGateResult:
    """Detailed diagnostic results from the Strict Visual Quality Gate."""
    passed: bool
    rejection_reasons: List[str]
    width: int
    height: int
    aspect_ratio: float
    aspect_tag: str
    file_size_bytes: int
    file_size_kb: float
    laplacian_variance: float
    texture_variance: float
    mean_luminance: float
    has_watermark: bool
    watermark_details: str
    has_thumbnail_artifacts: bool
    artifact_details: str
    quality_score: float  # Composite 0.0 - 100.0
    metrics: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        status = "PASSED" if self.passed else "REJECTED"
        reasons = "; ".join(self.rejection_reasons) if self.rejection_reasons else "None"
        return (
            f"[{status}] {self.width}x{self.height} ({self.aspect_tag}, r={self.aspect_ratio:.2f}) | "
            f"Size: {self.file_size_kb:.1f} KB | Sharpness: {self.laplacian_variance:.1f} | "
            f"Score: {self.quality_score:.1f}/100 | Reasons: {reasons}"
        )


@dataclass
class SubjectCentroidResult:
    """Localized subject coordinates and detection provenance."""
    cx: float
    cy: float
    method: str
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)
    confidence: float = 1.0
    detected_faces: List[Tuple[int, int, int, int]] = field(default_factory=list)
    detected_bodies: List[Tuple[int, int, int, int]] = field(default_factory=list)
    detect_time_ms: float = 0.0


@dataclass
class FramingResult:
    """Final 9:16 editorial framing results."""
    image: Image.Image
    output_path: Optional[Path]
    original_size: Tuple[int, int]
    final_size: Tuple[int, int]
    aspect_tag: str
    framing_mode: str
    centroid: Tuple[float, float]
    headroom_applied: bool
    render_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# OpenCV Cascade Cache & Initialization
# ============================================================================

_FACE_CASCADE_DEFAULT = None
_FACE_CASCADE_ALT2 = None
_PROFILE_CASCADE = None
_UPPERBODY_CASCADE = None
_FULLBODY_CASCADE = None
_REMBG_SESSION = None


def _get_cascades():
    """Lazily load OpenCV Haar cascade classifiers once."""
    global _FACE_CASCADE_DEFAULT, _FACE_CASCADE_ALT2, _PROFILE_CASCADE, _UPPERBODY_CASCADE, _FULLBODY_CASCADE
    if _FACE_CASCADE_DEFAULT is None:
        casc_dir = Path(cv2.data.haarcascades)
        try:
            _FACE_CASCADE_DEFAULT = cv2.CascadeClassifier(str(casc_dir / 'haarcascade_frontalface_default.xml'))
            _FACE_CASCADE_ALT2 = cv2.CascadeClassifier(str(casc_dir / 'haarcascade_frontalface_alt2.xml'))
            _PROFILE_CASCADE = cv2.CascadeClassifier(str(casc_dir / 'haarcascade_profileface.xml'))
            _UPPERBODY_CASCADE = cv2.CascadeClassifier(str(casc_dir / 'haarcascade_upperbody.xml'))
            _FULLBODY_CASCADE = cv2.CascadeClassifier(str(casc_dir / 'haarcascade_fullbody.xml'))
        except Exception as e:
            print(f"[ImageQualitySensor] OpenCV cascade init note: {e}")
    return _FACE_CASCADE_DEFAULT, _FACE_CASCADE_ALT2, _PROFILE_CASCADE, _UPPERBODY_CASCADE, _FULLBODY_CASCADE


def get_rembg_session():
    """Lazily load lightweight rembg u2netp session if available."""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        try:
            import rembg
            _REMBG_SESSION = rembg.new_session("u2netp")
        except Exception:
            _REMBG_SESSION = False
    return _REMBG_SESSION if _REMBG_SESSION is not False else None


# ============================================================================
# Part 1: Visual Quality Gate Implementation
# ============================================================================

def classify_aspect_ratio(width: int, height: int) -> Tuple[float, str]:
    """
    Classify image aspect ratio into editorial buckets:
    - NATIVE_VERTICAL: aspect < 0.8
    - SQUARE: 0.8 <= aspect <= 1.2
    - WIDE_LANDSCAPE: aspect > 1.2
    """
    if height <= 0:
        return 0.0, AspectRatioTag.WIDE_LANDSCAPE
    aspect = width / height
    if aspect < ASPECT_VERTICAL_MAX:
        tag = AspectRatioTag.NATIVE_VERTICAL
    elif aspect <= ASPECT_SQUARE_MAX:
        tag = AspectRatioTag.SQUARE
    else:
        tag = AspectRatioTag.WIDE_LANDSCAPE
    return aspect, tag


def calculate_laplacian_variance(cv_img: np.ndarray) -> float:
    """
    Compute OpenCV Laplacian variance as standard focus / sharpness measure.
    Blurry or out-of-focus images yield low variance (< 80).
    """
    if cv_img is None or cv_img.size == 0:
        return 0.0
    if len(cv_img.shape) == 3:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv_img
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def detect_stock_watermarks_and_artifacts(
    cv_img: np.ndarray,
    source_ref: Optional[str] = None
) -> Tuple[bool, str, bool, str]:
    """
    Detect commercial stock watermarks (Alamy, Getty, Shutterstock) and thumbnail artifacts:
    1. Keyword match on source path/URL.
    2. Corner watermark badge / high-density text overlay.
    3. Center repeating diagonal watermark patterns.
    4. Letterbox / pillarbox black bars.
    5. Blank / solid color rectangles or extreme luminance.

    Returns:
        (has_watermark: bool, watermark_details: str,
         has_artifacts: bool, artifact_details: str)
    """
    has_watermark = False
    watermark_reasons = []
    has_artifacts = False
    artifact_reasons = []

    # 1. Source reference check (URL / file path)
    if source_ref:
        ref_lower = source_ref.lower()
        for kw in STOCK_WATERMARK_KEYWORDS:
            if kw in ref_lower:
                has_watermark = True
                watermark_reasons.append(f"Stock watermark agency keyword detected in source reference: '{kw}'")
                break

    if cv_img is None or cv_img.size == 0:
        return has_watermark, "; ".join(watermark_reasons), True, "Empty or invalid image data"

    h, w = cv_img.shape[:2]
    if len(cv_img.shape) == 3:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv_img

    # 2. Blank / Solid Color Check
    texture_var = float(np.var(cv_img))
    if texture_var < 20.0:
        has_artifacts = True
        artifact_reasons.append(f"Solid/blank image with low texture variance ({texture_var:.1f})")

    # 3. Extreme Luminance Check
    mean_lum = float(np.mean(gray))
    if mean_lum < 10.0:
        has_artifacts = True
        artifact_reasons.append(f"Severely underexposed / pitch black frame (mean lum {mean_lum:.1f})")
    elif mean_lum > 248.0:
        has_artifacts = True
        artifact_reasons.append(f"Severely overexposed / blown out white frame (mean lum {mean_lum:.1f})")

    # 4. Letterbox Black Bars Detection (e.g. 16:9 rips with black borders)
    top_strip = gray[:max(2, int(h * 0.04)), :]
    bot_strip = gray[max(2, int(h * 0.96)):, :]
    center_y1, center_y2 = int(h * 0.25), int(h * 0.75)
    center_strip = gray[center_y1:center_y2, :]

    if (np.mean(top_strip) < 14.0 and np.mean(bot_strip) < 14.0 and
            np.var(top_strip) < 5.0 and np.var(bot_strip) < 5.0 and
            np.mean(center_strip) > 35.0):
        has_artifacts = True
        artifact_reasons.append("Letterbox black bars detected on top and bottom")

    # 5. Pillarbox Black Bars Detection
    left_strip = gray[:, :max(2, int(w * 0.04))]
    right_strip = gray[:, max(2, int(w * 0.96)):]
    center_x1, center_x2 = int(w * 0.25), int(w * 0.75)
    center_x_strip = gray[:, center_x1:center_x2]

    if (np.mean(left_strip) < 14.0 and np.mean(right_strip) < 14.0 and
            np.var(left_strip) < 5.0 and np.var(right_strip) < 5.0 and
            np.mean(center_x_strip) > 35.0):
        has_artifacts = True
        artifact_reasons.append("Pillarbox black bars detected on left and right")

    # 6. Corner Stock Watermark Badge Detection (Alamy / Getty / Shutterstock corner logos)
    # Check bottom-left and bottom-right corner patches (bottom 10% height, outer 22% width)
    corner_h = max(20, int(h * 0.10))
    corner_w = max(40, int(w * 0.22))
    
    corners = [
        ("bottom-left", gray[h - corner_h:, :corner_w]),
        ("bottom-right", gray[h - corner_h:, w - corner_w:])
    ]
    
    for corner_name, patch in corners:
        if patch.size > 0:
            # Look for sharp contrasting text overlay badges
            edges = cv2.Canny(patch, 60, 160)
            edge_density = float(np.mean(edges > 0))
            patch_var = float(np.var(patch))
            # Text badges have dense edge transitions with significant local variance
            # and sharp horizontal text runs
            if edge_density > 0.18 and patch_var > 600.0:
                # Check horizontal stroke structure characteristic of typography
                kernel_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 1))
                closed_h = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_horiz)
                horiz_lines = float(np.mean(closed_h > 0))
                if horiz_lines > 0.12:
                    has_watermark = True
                    watermark_reasons.append(
                        f"Stock text/logo watermark badge detected in {corner_name} corner"
                    )
                    break

    # 7. Repeating Diagonal Watermark Grid Pattern (Alamy/Getty center diagonal watermark)
    cy1, cy2 = int(h * 0.25), int(h * 0.75)
    cx1, cx2 = int(w * 0.20), int(w * 0.80)
    center_patch = gray[cy1:cy2, cx1:cx2]
    if center_patch.size > 1000:
        # Scale to manageable size for fast gradient analysis
        scale = 400.0 / max(center_patch.shape)
        if scale < 1.0:
            small_center = cv2.resize(center_patch, (int(center_patch.shape[1] * scale), int(center_patch.shape[0] * scale)))
        else:
            small_center = center_patch

        gx = cv2.Sobel(small_center, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(small_center, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2)
        strong = mag > 35.0
        if np.sum(strong) > 200:
            angles = np.abs(np.arctan2(gy[strong], gx[strong]) * 180.0 / np.pi)
            # Diagonal angles typically clustered near 35°-55° or 125°-145°
            diag_mask = ((angles >= 35.0) & (angles <= 55.0)) | ((angles >= 125.0) & (angles <= 145.0))
            diag_ratio = float(np.mean(diag_mask))
            # If diagonal orientations strongly dominate natural image gradients
            if diag_ratio > 0.45 and float(np.var(mag[strong])) > 300.0:
                has_watermark = True
                watermark_reasons.append("Repeating diagonal watermark pattern detected across center frame")

    wm_text = "; ".join(watermark_reasons) if watermark_reasons else "Clean (No stock watermarks)"
    art_text = "; ".join(artifact_reasons) if artifact_reasons else "Clean (No thumbnail artifacts)"
    return has_watermark, wm_text, has_artifacts, art_text


def evaluate_quality_gate(
    image_input: Union[str, Path, bytes, Image.Image, np.ndarray],
    source_ref: Optional[str] = None,
    min_dimension: int = MIN_DIMENSION_LIMIT,
    min_file_size_kb: float = 80.0,
    min_sharpness: float = MIN_SHARPNESS_LAPLACIAN
) -> QualityGateResult:
    """
    Strict Visual Quality Gate:
    Evaluates resolution, file size, sharpness, stock watermarks, and thumbnail artifacts.
    """
    rejection_reasons: List[str] = []
    file_size_bytes = 0
    cv_img: Optional[np.ndarray] = None
    pil_img: Optional[Image.Image] = None

    # Resolve image input
    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        if not p.exists():
            return QualityGateResult(
                passed=False,
                rejection_reasons=[f"File does not exist: {p}"],
                width=0, height=0, aspect_ratio=0.0, aspect_tag=AspectRatioTag.WIDE_LANDSCAPE,
                file_size_bytes=0, file_size_kb=0.0, laplacian_variance=0.0, texture_variance=0.0,
                mean_luminance=0.0, has_watermark=False, watermark_details="File missing",
                has_thumbnail_artifacts=False, artifact_details="File missing", quality_score=0.0
            )
        file_size_bytes = p.stat().st_size
        source_ref = source_ref or str(p)
        try:
            pil_img = Image.open(p).convert("RGB")
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return QualityGateResult(
                passed=False,
                rejection_reasons=[f"Failed to decode image file: {e}"],
                width=0, height=0, aspect_ratio=0.0, aspect_tag=AspectRatioTag.WIDE_LANDSCAPE,
                file_size_bytes=file_size_bytes, file_size_kb=file_size_bytes / 1024.0,
                laplacian_variance=0.0, texture_variance=0.0, mean_luminance=0.0,
                has_watermark=False, watermark_details="Corrupt file",
                has_thumbnail_artifacts=False, artifact_details="Corrupt file", quality_score=0.0
            )

    elif isinstance(image_input, bytes):
        file_size_bytes = len(image_input)
        try:
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            return QualityGateResult(
                passed=False,
                rejection_reasons=[f"Failed to decode image bytes: {e}"],
                width=0, height=0, aspect_ratio=0.0, aspect_tag=AspectRatioTag.WIDE_LANDSCAPE,
                file_size_bytes=file_size_bytes, file_size_kb=file_size_bytes / 1024.0,
                laplacian_variance=0.0, texture_variance=0.0, mean_luminance=0.0,
                has_watermark=False, watermark_details="Corrupt bytes",
                has_thumbnail_artifacts=False, artifact_details="Corrupt bytes", quality_score=0.0
            )

    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("RGB")
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        file_size_bytes = buf.tell()

    elif isinstance(image_input, np.ndarray):
        cv_img = image_input
        pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        file_size_bytes = buf.tell()

    else:
        return QualityGateResult(
            passed=False,
            rejection_reasons=["Unsupported image input type"],
            width=0, height=0, aspect_ratio=0.0, aspect_tag=AspectRatioTag.WIDE_LANDSCAPE,
            file_size_bytes=0, file_size_kb=0.0, laplacian_variance=0.0, texture_variance=0.0,
            mean_luminance=0.0, has_watermark=False, watermark_details="Invalid type",
            has_thumbnail_artifacts=False, artifact_details="Invalid type", quality_score=0.0
        )

    w, h = pil_img.size
    aspect, aspect_tag = classify_aspect_ratio(w, h)
    file_size_kb = file_size_bytes / 1024.0

    # Rule 1: Resolution Gate - max(width, height) < 1080
    max_dim = max(w, h)
    if max_dim < min_dimension:
        rejection_reasons.append(
            f"Resolution too low: max dimension {max_dim}px < {min_dimension}px threshold ({w}x{h})"
        )

    # Rule 2: File Size Gate - < 80 KB
    min_bytes = int(min_file_size_kb * 1024)
    if file_size_bytes < min_bytes:
        rejection_reasons.append(
            f"File size too small: {file_size_kb:.1f} KB < {min_file_size_kb:.1f} KB threshold ({file_size_bytes} bytes)"
        )

    # Rule 3: Sharpness Scoring - Laplacian variance < 80
    lap_var = calculate_laplacian_variance(cv_img)
    if lap_var < min_sharpness:
        rejection_reasons.append(
            f"Image is blurry/out-of-focus: Laplacian variance {lap_var:.1f} < {min_sharpness:.1f} threshold"
        )

    # Rule 4: Artifact & Stock Watermark Detection
    has_wm, wm_detail, has_art, art_detail = detect_stock_watermarks_and_artifacts(cv_img, source_ref)
    if has_wm:
        rejection_reasons.append(f"Commercial stock watermark detected: {wm_detail}")
    if has_art:
        rejection_reasons.append(f"Thumbnail / visual artifact detected: {art_detail}")

    # Calculate overall quality score (0.0 to 100.0)
    # Higher sharpness, high resolution, healthy texture variance contributes to high score
    texture_var = float(np.var(cv_img))
    mean_lum = float(np.mean(cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)))

    score = 0.0
    if not rejection_reasons:
        # Base 60 for passing gates
        score = 60.0
        # Sharpness bonus up to 20 pts (log scale up to 1000 variance)
        sharp_bonus = min(20.0, math.log10(max(1.0, lap_var / min_sharpness) + 1.0) * 20.0)
        # Resolution bonus up to 15 pts (1080 up to 3840)
        res_bonus = min(15.0, ((max_dim - min_dimension) / 2000.0) * 15.0)
        # Texture & contrast bonus up to 5 pts
        tex_bonus = 5.0 if texture_var > 150.0 else 2.5
        score = min(100.0, score + sharp_bonus + res_bonus + tex_bonus)
    else:
        # Partial credit score based on what passed
        score = max(5.0, 45.0 - len(rejection_reasons) * 12.0)

    passed = len(rejection_reasons) == 0

    return QualityGateResult(
        passed=passed,
        rejection_reasons=rejection_reasons,
        width=w,
        height=h,
        aspect_ratio=round(aspect, 4),
        aspect_tag=aspect_tag,
        file_size_bytes=file_size_bytes,
        file_size_kb=round(file_size_kb, 2),
        laplacian_variance=round(lap_var, 2),
        texture_variance=round(texture_var, 2),
        mean_luminance=round(mean_lum, 2),
        has_watermark=has_wm,
        watermark_details=wm_detail,
        has_thumbnail_artifacts=has_art,
        artifact_details=art_detail,
        quality_score=round(score, 1),
        metrics={
            "max_dimension": max_dim,
            "min_dimension_limit": min_dimension,
            "min_sharpness_limit": min_sharpness,
            "min_size_kb_limit": min_file_size_kb
        }
    )


# ============================================================================
# Part 2: OpenCV Subject Centering & Detection
# ============================================================================

def detect_subject_centroid(cv_img: np.ndarray) -> SubjectCentroidResult:
    """
    Detect the center-of-mass (cx, cy) and bounding box of the main subject
    using OpenCV Haar cascades (frontal face, profile, upper body, full body)
    with edge energy / saliency centroid fallback.
    """
    t0 = time.time()
    h, w = cv_img.shape[:2]
    face_casc, face_alt, prof_casc, upper_casc, full_casc = _get_cascades()

    if len(cv_img.shape) == 3:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv_img

    # Speed optimization: downscale large images (> 1200px) for Haar cascade search
    max_dim = max(w, h)
    scale = 1.0
    if max_dim > 1200:
        scale = 1200.0 / max_dim
        sw, sh = int(round(w * scale)), int(round(h * scale))
        detect_gray = cv2.resize(gray, (sw, sh), interpolation=cv2.INTER_AREA)
    else:
        detect_gray = gray

    inv_scale = 1.0 / scale
    detected_faces: List[Tuple[int, int, int, int]] = []
    detected_bodies: List[Tuple[int, int, int, int]] = []

    # 1. Frontal Face Detection
    faces_raw = []
    if face_casc and not face_casc.empty():
        faces_raw = list(face_casc.detectMultiScale(detect_gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)))
    if len(faces_raw) == 0 and face_alt and not face_alt.empty():
        faces_raw = list(face_alt.detectMultiScale(detect_gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)))

    if len(faces_raw) > 0:
        for (fx, fy, fw, fh) in faces_raw:
            detected_faces.append((
                int(round(fx * inv_scale)),
                int(round(fy * inv_scale)),
                int(round(fw * inv_scale)),
                int(round(fh * inv_scale))
            ))
        # Rank by face area weighted by horizontal central proximity
        center_x = w / 2.0
        best_face = max(
            detected_faces,
            key=lambda f: (f[2] * f[3]) * (1.0 - 0.30 * (abs((f[0] + f[2] / 2.0) - center_x) / center_x))
        )
        fx, fy, fw, fh = best_face
        dt = (time.time() - t0) * 1000.0
        return SubjectCentroidResult(
            cx=float(fx + fw / 2.0),
            cy=float(fy + fh / 2.0),
            method="FRONTAL_FACE",
            bbox=best_face,
            confidence=0.95,
            detected_faces=detected_faces,
            detected_bodies=[],
            detect_time_ms=round(dt, 2)
        )

    # 2. Profile Face Detection (player looking sideways, celebrating)
    if prof_casc and not prof_casc.empty():
        profs_raw = prof_casc.detectMultiScale(detect_gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
        if len(profs_raw) > 0:
            for (px, py, pw, ph) in profs_raw:
                detected_faces.append((
                    int(round(px * inv_scale)),
                    int(round(py * inv_scale)),
                    int(round(pw * inv_scale)),
                    int(round(ph * inv_scale))
                ))
            center_x = w / 2.0
            best_prof = max(
                detected_faces,
                key=lambda f: (f[2] * f[3]) * (1.0 - 0.25 * (abs((f[0] + f[2] / 2.0) - center_x) / center_x))
            )
            fx, fy, fw, fh = best_prof
            dt = (time.time() - t0) * 1000.0
            return SubjectCentroidResult(
                cx=float(fx + fw / 2.0),
                cy=float(fy + fh / 2.0),
                method="PROFILE_FACE",
                bbox=best_prof,
                confidence=0.88,
                detected_faces=detected_faces,
                detected_bodies=[],
                detect_time_ms=round(dt, 2)
            )

    # 3. Upper Body Detection (action shot, ball strike, sliding)
    if upper_casc and not upper_casc.empty():
        bodies_raw = upper_casc.detectMultiScale(detect_gray, scaleFactor=1.1, minNeighbors=3, minSize=(50, 50))
        if len(bodies_raw) > 0:
            for (bx, by, bw, bh) in bodies_raw:
                detected_bodies.append((
                    int(round(bx * inv_scale)),
                    int(round(by * inv_scale)),
                    int(round(bw * inv_scale)),
                    int(round(bh * inv_scale))
                ))
            center_x = w / 2.0
            best_body = max(
                detected_bodies,
                key=lambda b: (b[2] * b[3]) * (1.0 - 0.25 * (abs((b[0] + b[2] / 2.0) - center_x) / center_x))
            )
            bx, by, bw, bh = best_body
            dt = (time.time() - t0) * 1000.0
            return SubjectCentroidResult(
                cx=float(bx + bw / 2.0),
                cy=float(by + bh * 0.38),  # Neck/chest line
                method="UPPER_BODY",
                bbox=best_body,
                confidence=0.82,
                detected_faces=[],
                detected_bodies=detected_bodies,
                detect_time_ms=round(dt, 2)
            )

    # 4. Full Body Detection
    if full_casc and not full_casc.empty():
        full_raw = full_casc.detectMultiScale(detect_gray, scaleFactor=1.1, minNeighbors=3, minSize=(70, 70))
        if len(full_raw) > 0:
            for (bx, by, bw, bh) in full_raw:
                detected_bodies.append((
                    int(round(bx * inv_scale)),
                    int(round(by * inv_scale)),
                    int(round(bw * inv_scale)),
                    int(round(bh * inv_scale))
                ))
            best_full = max(detected_bodies, key=lambda b: b[2] * b[3])
            bx, by, bw, bh = best_full
            dt = (time.time() - t0) * 1000.0
            return SubjectCentroidResult(
                cx=float(bx + bw / 2.0),
                cy=float(by + bh * 0.25),  # Chest/head line
                method="FULL_BODY",
                bbox=best_full,
                confidence=0.78,
                detected_faces=[],
                detected_bodies=detected_bodies,
                detect_time_ms=round(dt, 2)
            )

    # 5. Saliency / Gradient Edge Energy Centroid
    try:
        edges = cv2.Canny(detect_gray, 50, 150)
        total_energy = float(np.sum(edges))
        if total_energy > 500.0:
            sh, sw = detect_gray.shape[:2]
            x_coords = np.arange(sw)
            y_coords = np.arange(sh)
            col_sums = np.sum(edges, axis=0)
            row_sums = np.sum(edges, axis=1)
            cx_small = float(np.sum(x_coords * col_sums) / total_energy)
            cy_small = float(np.sum(y_coords * row_sums) / total_energy)
            cx = float(cx_small * inv_scale)
            cy = float(cy_small * inv_scale)
            dt = (time.time() - t0) * 1000.0
            return SubjectCentroidResult(
                cx=cx,
                cy=cy,
                method="SALIENCY_EDGE_CENTROID",
                bbox=None,
                confidence=0.60,
                detected_faces=[],
                detected_bodies=[],
                detect_time_ms=round(dt, 2)
            )
    except Exception:
        pass

    # 6. Fallback: Upper optical center
    dt = (time.time() - t0) * 1000.0
    return SubjectCentroidResult(
        cx=float(w / 2.0),
        cy=float(h * 0.38),
        method="DEFAULT_CENTER",
        bbox=None,
        confidence=0.50,
        detected_faces=[],
        detected_bodies=[],
        detect_time_ms=round(dt, 2)
    )


# ============================================================================
# Part 3: Editorial 9:16 Framing Engine
# ============================================================================

def apply_broadcast_grading(img: Image.Image) -> Image.Image:
    """
    Signature @Footballin30sec broadcast visual grading:
    1. Unsharp mask for high-definition edge sharpness.
    2. Subtle natural contrast punch.
    3. Vibrant color saturation.
    4. Clean brightness enhancement (avoids gloomy shadow crushing).
    """
    sharpened = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=115, threshold=3))
    balanced = ImageEnhance.Contrast(sharpened).enhance(1.04)
    vibrant = ImageEnhance.Color(balanced).enhance(1.05)
    final_img = ImageEnhance.Brightness(vibrant).enhance(1.02)
    return final_img


def frame_native_vertical(
    pil_img: Image.Image,
    subject: SubjectCentroidResult,
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Frame NATIVE_VERTICAL (< 0.8) image into exact 1080x1920:
    - Centers horizontally on subject centroid cx.
    - Applies upper-third rule-of-thirds headroom vertically.
    """
    iw, ih = pil_img.size
    target_ratio = target_w / target_h  # 0.5625
    img_ratio = iw / ih

    headroom_applied = False

    if img_ratio >= target_ratio:
        # Wider than 9:16 (e.g. 0.75 or 0.65)
        # Keep full height, crop width to match target ratio
        crop_h = ih
        crop_w = int(round(ih * target_ratio))
        left = int(round(subject.cx - crop_w / 2.0))
        left = max(0, min(iw - crop_w, left))
        top = 0
        right = left + crop_w
        bottom = ih
    else:
        # Narrower/taller than 9:16 (e.g. 0.50)
        # Keep full width, crop height with rule-of-thirds headroom
        crop_w = iw
        crop_h = int(round(iw / target_ratio))
        left = 0
        right = iw

        # Rule of thirds: place face/subject in upper third (approx 30-35% from top)
        if subject.bbox and subject.method in ("FRONTAL_FACE", "PROFILE_FACE"):
            _, fy, _, fh = subject.bbox
            eye_y = fy + fh * 0.35
            target_eye_pos = crop_h * 0.32
            top = int(round(eye_y - target_eye_pos))
            headroom_applied = True
        elif subject.method == "UPPER_BODY":
            target_body_pos = crop_h * 0.38
            top = int(round(subject.cy - target_body_pos))
            headroom_applied = True
        else:
            top = int(round(subject.cy - crop_h * 0.35))
            headroom_applied = True

        top = max(0, min(ih - crop_h, top))
        bottom = top + crop_h

    cropped = pil_img.crop((left, top, right, bottom))
    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    graded = apply_broadcast_grading(resized)

    meta = {
        "crop_box": (left, top, right, bottom),
        "crop_size": (right - left, bottom - top),
        "headroom_applied": headroom_applied,
        "centroid_used": (round(subject.cx, 1), round(subject.cy, 1)),
        "detection_method": subject.method
    }
    return graded, meta


def frame_editorial_blur_window(
    pil_img: Image.Image,
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT,
    blur_sigma: int = 35,
    inset_margin: int = 20,
    border_width: int = 2,
    border_color: Tuple[int, int, int, int] = (255, 255, 255, 195)
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Professional editorial presentation for WIDE_LANDSCAPE (> 1.2) images:
    - Background: Scaled-up original covering 1080x1920, heavy Gaussian blur (sigma 35),
      darkened by 38% with subtle vignette so foreground pops with contrast.
    - Foreground: Sharp centered broadcast window with subtle 2px border and soft drop shadow.
    - Prevents brutal horizontal cropping that cuts players/managers in half.
    """
    iw, ih = pil_img.size
    aspect = iw / ih

    # 1. Background Fill Layer (Aspect Fill 1080x1920)
    scale = max(target_w / iw, target_h / ih)
    bg_w = int(round(iw * scale))
    bg_h = int(round(ih * scale))
    bg_resized = pil_img.resize((bg_w, bg_h), Image.Resampling.LANCZOS)

    bg_left = (bg_w - target_w) // 2
    bg_top = (bg_h - target_h) // 2
    bg_cropped = bg_resized.crop((bg_left, bg_top, bg_left + target_w, bg_top + target_h))

    # Apply Gaussian Blur using OpenCV
    bg_cv = cv2.cvtColor(np.array(bg_cropped), cv2.COLOR_RGB2BGR)
    # Kernel size must be odd; sigma=35
    ksize = blur_sigma * 2 + 1
    bg_blurred = cv2.GaussianBlur(bg_cv, (ksize, ksize), blur_sigma)

    # Darken background by 38% (alpha=0.62)
    bg_darkened = cv2.convertScaleAbs(bg_blurred, alpha=0.62, beta=0)

    # Subtle vignette overlay in OpenCV
    vignette = np.zeros((target_h, target_w), dtype=np.float32)
    cv2.circle(vignette, (target_w // 2, target_h // 2), int(target_h * 0.70), 1.0, -1)
    vignette = cv2.GaussianBlur(vignette, (201, 201), 100)
    vignette_3ch = cv2.merge([vignette, vignette, vignette])
    bg_final_cv = (bg_darkened * (0.75 + 0.25 * vignette_3ch)).astype(np.uint8)

    bg_img = Image.fromarray(cv2.cvtColor(bg_final_cv, cv2.COLOR_BGR2RGB)).convert("RGBA")

    # 2. Foreground Broadcast Window
    fg_w = target_w - inset_margin * 2
    fg_h = int(round(fg_w / aspect))

    # Ensure foreground does not overflow screen height
    if fg_h > int(target_h * 0.75):
        fg_h = int(target_h * 0.75)
        fg_w = int(round(fg_h * aspect))

    fg_resized = pil_img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
    # Apply crisp unsharp mask for foreground pop
    fg_sharp = fg_resized.filter(ImageFilter.UnsharpMask(radius=1.5, percent=125, threshold=2))
    fg_rgba = fg_sharp.convert("RGBA")

    # Broadcast border on foreground window
    if border_width > 0:
        b_draw = ImageDraw.Draw(fg_rgba)
        b_draw.rectangle(
            [0, 0, fg_w - 1, fg_h - 1],
            outline=border_color,
            width=border_width
        )
        # Inner subtle dark stroke for depth
        b_draw.rectangle(
            [border_width, border_width, fg_w - border_width - 1, fg_h - border_width - 1],
            outline=(0, 0, 0, 70),
            width=1
        )

    # 3. Soft Drop Shadow
    shadow_pad = 24
    shadow_img = Image.new("RGBA", (fg_w + shadow_pad * 2, fg_h + shadow_pad * 2), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_draw.rectangle(
        [shadow_pad, shadow_pad + 6, shadow_pad + fg_w, shadow_pad + fg_h + 6],
        fill=(0, 0, 0, 150)
    )
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(16))

    # 4. Position: Optical center for vertical shorts (46% height)
    fg_x = (target_w - fg_w) // 2
    fg_y = int(round((target_h - fg_h) * 0.46))

    # Composite layers
    canvas = bg_img.copy()
    canvas.paste(shadow_img, (fg_x - shadow_pad, fg_y - shadow_pad), shadow_img)
    canvas.paste(fg_rgba, (fg_x, fg_y), fg_rgba)

    final_rgb = canvas.convert("RGB")
    meta = {
        "framing_mode": "EDITORIAL_BLUR_WINDOW",
        "foreground_box": (fg_x, fg_y, fg_x + fg_w, fg_y + fg_h),
        "foreground_size": (fg_w, fg_h),
        "blur_sigma": blur_sigma,
        "aspect_ratio": aspect
    }
    return final_rgb, meta


def frame_editorial_2_5d_cutout(
    pil_img: Image.Image,
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT,
    stroke_width: int = 6,
    stroke_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Editorial presentation with 2.5D subject cutout on matte backdrop.
    Uses rembg (u2netp) for cutout, applies signature white paper sticker outline
    and soft drop shadow, placing subject with head in the upper third.
    Falls back gracefully to blur window if rembg is unavailable or fails.
    """
    session = get_rembg_session()
    if not session:
        return frame_editorial_blur_window(pil_img, target_w, target_h)

    try:
        import rembg
        cutout_rgba = rembg.remove(pil_img.convert("RGBA"), session=session)
        alpha = cutout_rgba.split()[-1]
        alpha_arr = np.array(alpha)
        if np.sum(alpha_arr > 30) < 5000:
            # Cutout failed or mask is empty
            return frame_editorial_blur_window(pil_img, target_w, target_h)

        # 1. White Paper Sticker Outline
        stroke_mask = alpha.filter(ImageFilter.MaxFilter(stroke_width * 2 + 1))
        stroke_layer = Image.new("RGBA", cutout_rgba.size, stroke_color)
        stroke_layer.putalpha(stroke_mask)

        # 2. Soft Drop Shadow
        shadow_mask = stroke_mask.filter(ImageFilter.MaxFilter(21))
        shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(14))
        shadow_np = (np.array(shadow_mask, dtype=np.float32) * (120.0 / 255.0)).astype(np.uint8)
        shadow_layer = Image.new("RGBA", cutout_rgba.size, (0, 0, 0, 0))
        shadow_layer.putalpha(Image.fromarray(shadow_np))

        # Composite cutout with sticker and shadow
        cw, ch = cutout_rgba.size
        cutout_comp = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cutout_comp.paste(shadow_layer, (0, 10), shadow_layer)
        cutout_comp.paste(stroke_layer, (0, 0), stroke_layer)
        cutout_comp.paste(cutout_rgba, (0, 0), cutout_rgba)

        # Bounding box of content
        bbox = cutout_comp.getbbox()
        if bbox:
            cutout_comp = cutout_comp.crop(bbox)
            cw, ch = cutout_comp.size

        # 3. Create Backdrop (Dark Editorial Graphite Matte)
        backdrop = Image.new("RGBA", (target_w, target_h), (18, 20, 26, 255))
        # Add subtle radial studio lighting
        b_draw = ImageDraw.Draw(backdrop)
        for r in range(400, 50, -50):
            alpha_val = int(25 * (1.0 - r / 400.0))
            b_draw.ellipse(
                [target_w // 2 - r, int(target_h * 0.42) - r, target_w // 2 + r, int(target_h * 0.42) + r],
                fill=(38, 44, 58, alpha_val)
            )

        # 4. Scale cutout to fit vertical composition (max width 960, max height 1400)
        fit_scale = min(960 / cw, 1400 / ch, 1.25)
        scaled_w = int(round(cw * fit_scale))
        scaled_h = int(round(ch * fit_scale))
        cutout_scaled = cutout_comp.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

        pos_x = (target_w - scaled_w) // 2
        # Position subject head in upper third (approx 28% from top)
        pos_y = int(round((target_h - scaled_h) * 0.52))
        pos_y = max(80, min(target_h - scaled_h - 40, pos_y))

        backdrop.paste(cutout_scaled, (pos_x, pos_y), cutout_scaled)
        final_rgb = backdrop.convert("RGB")
        meta = {
            "framing_mode": "EDITORIAL_2.5D_CUTOUT",
            "cutout_box": (pos_x, pos_y, pos_x + scaled_w, pos_y + scaled_h),
            "scale": fit_scale
        }
        return final_rgb, meta

    except Exception as e:
        print(f"[ImageQualitySensor] Cutout fallback notice: {e}")
        return frame_editorial_blur_window(pil_img, target_w, target_h)


def frame_square(
    pil_img: Image.Image,
    subject: SubjectCentroidResult,
    target_w: int = TARGET_WIDTH,
    target_h: int = TARGET_HEIGHT,
    mode: str = "auto"
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Frame SQUARE (0.8 <= aspect <= 1.2) images into exact 1080x1920:
    - If subject fits comfortably inside 9:16 crop width without clipping (and mode != 'blur'):
      smart vertical crop centered on cx with rule-of-thirds headroom.
    - Otherwise: editorial blur window presentation so players are not cut in half.
    """
    iw, ih = pil_img.size
    target_ratio = target_w / target_h  # 0.5625
    crop_w = int(round(ih * target_ratio))

    can_crop = False
    if mode != "blur_window" and mode != "blur":
        # Check if subject bounding box fits safely within crop_w
        if subject.bbox:
            fx, fy, fw, fh = subject.bbox
            if fw < crop_w * 0.75:
                # Subject face/body is compact enough to fit without clipping
                left = int(round(subject.cx - crop_w / 2.0))
                if left >= 0 and left + crop_w <= iw:
                    can_crop = True
        elif subject.method == "SALIENCY_EDGE_CENTROID":
            left = int(round(subject.cx - crop_w / 2.0))
            if 0 <= left <= iw - crop_w:
                can_crop = True

    if can_crop and mode != "editorial":
        return frame_native_vertical(pil_img, subject, target_w, target_h)
    else:
        return frame_editorial_blur_window(pil_img, target_w, target_h, blur_sigma=35, inset_margin=24)


# ============================================================================
# Part 4: Unified Master Pipeline Interface
# ============================================================================

class ImageQualitySensor:
    """
    Unified Computer Vision Quality & Subject Framing Arbiter.
    Integrates Quality Gate, Subject Centering, and 9:16 Editorial Framing.
    """

    def __init__(
        self,
        min_dimension: int = MIN_DIMENSION_LIMIT,
        min_file_size_kb: float = 80.0,
        min_sharpness: float = MIN_SHARPNESS_LAPLACIAN,
        target_width: int = TARGET_WIDTH,
        target_height: int = TARGET_HEIGHT
    ):
        self.min_dimension = min_dimension
        self.min_file_size_kb = min_file_size_kb
        self.min_sharpness = min_sharpness
        self.target_width = target_width
        self.target_height = target_height

    def inspect(
        self,
        image_input: Union[str, Path, bytes, Image.Image, np.ndarray],
        source_ref: Optional[str] = None
    ) -> QualityGateResult:
        """Run strict visual quality gate checks on an image candidate."""
        return evaluate_quality_gate(
            image_input=image_input,
            source_ref=source_ref,
            min_dimension=self.min_dimension,
            min_file_size_kb=self.min_file_size_kb,
            min_sharpness=self.min_sharpness
        )

    def locate_subject(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray]
    ) -> SubjectCentroidResult:
        """Detect subject centroid and bounding box using OpenCV."""
        if isinstance(image_input, (str, Path)):
            cv_img = cv2.imread(str(image_input))
        elif isinstance(image_input, Image.Image):
            cv_img = cv2.cvtColor(np.array(image_input.convert("RGB")), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            cv_img = image_input
        else:
            raise ValueError(f"Unsupported image input for locate_subject: {type(image_input)}")
        return detect_subject_centroid(cv_img)

    def frame_editorial(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        output_path: Optional[Union[str, Path]] = None,
        framing_mode: str = "auto"
    ) -> FramingResult:
        """
        Frame image into exact 1080x1920 editorial format:
        - NATIVE_VERTICAL: centered crop with upper-third rule-of-thirds headroom.
        - WIDE_LANDSCAPE: blurred background fill + sharp centered foreground window.
        - SQUARE: smart crop or editorial blur window.
        - Supports 'editorial_blur', '2.5d_cutout', or 'auto'.
        """
        t0 = time.time()
        # Resolve PIL Image and OpenCV image
        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            pil_img = Image.open(p).convert("RGB")
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            cv_img = image_input
            pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        else:
            raise ValueError(f"Unsupported image input for framing: {type(image_input)}")

        w, h = pil_img.size
        aspect, aspect_tag = classify_aspect_ratio(w, h)

        # Detect subject centroid
        subject = detect_subject_centroid(cv_img)

        # Route by aspect ratio and mode
        mode_applied = ""
        headroom_applied = False
        meta = {}

        if framing_mode == "2.5d_cutout" or framing_mode == "cutout_matte":
            final_img, meta = frame_editorial_2_5d_cutout(pil_img, self.target_width, self.target_height)
            mode_applied = meta.get("framing_mode", "EDITORIAL_2.5D_CUTOUT")

        elif aspect_tag == AspectRatioTag.NATIVE_VERTICAL:
            final_img, meta = frame_native_vertical(pil_img, subject, self.target_width, self.target_height)
            mode_applied = "NATIVE_VERTICAL_CROP"
            headroom_applied = meta.get("headroom_applied", False)

        elif aspect_tag == AspectRatioTag.WIDE_LANDSCAPE:
            final_img, meta = frame_editorial_blur_window(pil_img, self.target_width, self.target_height)
            mode_applied = "EDITORIAL_BLUR_WINDOW"

        else:  # SQUARE
            final_img, meta = frame_square(pil_img, subject, self.target_width, self.target_height, mode=framing_mode)
            mode_applied = meta.get("framing_mode", "SQUARE_FRAMING")
            headroom_applied = meta.get("headroom_applied", False)

        render_ms = (time.time() - t0) * 1000.0

        # Save to output path if specified
        out_p = None
        if output_path:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            final_img.save(out_p, quality=95)

        return FramingResult(
            image=final_img,
            output_path=out_p,
            original_size=(w, h),
            final_size=final_img.size,
            aspect_tag=aspect_tag,
            framing_mode=mode_applied,
            centroid=(subject.cx, subject.cy),
            headroom_applied=headroom_applied,
            render_time_ms=round(render_ms, 2),
            metadata=meta
        )

    def process_image(
        self,
        image_input: Union[str, Path, bytes, Image.Image, np.ndarray],
        output_path: Optional[Union[str, Path]] = None,
        source_ref: Optional[str] = None,
        strict_gate: bool = True,
        framing_mode: str = "auto"
    ) -> Tuple[bool, Optional[FramingResult], QualityGateResult]:
        """
        Complete end-to-end arbiter:
        1. Evaluates strict visual quality gate.
        2. If passed (or strict_gate=False), frames into exact 1080x1920 editorial format.
        3. Saves output and returns full diagnostics.
        """
        gate_res = self.inspect(image_input, source_ref=source_ref)
        if not gate_res.passed and strict_gate:
            return False, None, gate_res

        framing_res = self.frame_editorial(image_input, output_path=output_path, framing_mode=framing_mode)
        return True, framing_res, gate_res


# Module-level Singleton Instance
_DEFAULT_SENSOR = None

def get_image_quality_sensor() -> ImageQualitySensor:
    """Retrieve shared singleton instance of ImageQualitySensor."""
    global _DEFAULT_SENSOR
    if _DEFAULT_SENSOR is None:
        _DEFAULT_SENSOR = ImageQualitySensor()
    return _DEFAULT_SENSOR


# Module-level convenience functions
def inspect_image(image_input: Any, source_ref: Optional[str] = None) -> QualityGateResult:
    return get_image_quality_sensor().inspect(image_input, source_ref=source_ref)

def detect_subject(image_input: Any) -> SubjectCentroidResult:
    return get_image_quality_sensor().locate_subject(image_input)

def frame_editorial_image(
    image_input: Any,
    output_path: Optional[Union[str, Path]] = None,
    framing_mode: str = "auto"
) -> FramingResult:
    return get_image_quality_sensor().frame_editorial(image_input, output_path=output_path, framing_mode=framing_mode)

def process_and_frame(
    image_input: Any,
    output_path: Optional[Union[str, Path]] = None,
    source_ref: Optional[str] = None,
    strict_gate: bool = True,
    framing_mode: str = "auto"
) -> Tuple[bool, Optional[FramingResult], QualityGateResult]:
    return get_image_quality_sensor().process_image(
        image_input=image_input,
        output_path=output_path,
        source_ref=source_ref,
        strict_gate=strict_gate,
        framing_mode=framing_mode
    )
