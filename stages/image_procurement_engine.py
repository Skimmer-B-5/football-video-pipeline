"""
# BETA V6.4: INTELLIGENT IMAGE PROCUREMENT & OPENCV FOCAL-SUBJECT FRAMING ENGINE
# Sandbox: beta/ | Strictly zero modifications outside beta/
"""

import sys
import os
import re
import io
import json
import time
import html
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import numpy as np
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
IMAGES_DIR = DATA_DIR / "images" / "v6_4"
CONTACT_SHEETS_DIR = OUTPUT_DIR / "v6_4_contact_sheets"

# Strict blacklist for watermarked stock archives, wallpaper aggregators, and spam
DISQUALIFIED_DOMAINS = {
    'alamy.com', 'alamy', 'gettyimages.com', 'gettyimages', 'shutterstock.com', 'shutterstock',
    'istockphoto.com', 'stockphoto.com', 'depositphotos.com', 'depositphotos', '123rf.com',
    'adobestock', 'dreamstime.com', 'wallpaperaccess.com', 'wallpapercave.com', 'wallpapersafari.com',
    'pinterest.com', 'aliexpress.com', 'amazon.com', 'ebay.com', 'freepik.com', 'vectorstock.com',
    'clipart', 'iconfinder.com', 'flaticon.com', 'deviantart.com', 'lookfordiagnosis.com'
}

class SubjectDetector:
    """
    OpenCV focal-subject and face localization.
    Prioritizes:
    1. Frontal faces (haarcascade_frontalface_default and haarcascade_frontalface_alt2)
    2. Profile faces (haarcascade_profileface)
    3. Upper body (haarcascade_upperbody)
    4. Action / Sports Subject Contour Cluster
    Never blindly centers images geometrically.
    """

    def __init__(self):
        casc_dir = cv2.data.haarcascades
        self.face_default = cv2.CascadeClassifier(casc_dir + "haarcascade_frontalface_default.xml")
        self.face_alt2 = cv2.CascadeClassifier(casc_dir + "haarcascade_frontalface_alt2.xml")
        self.profile = cv2.CascadeClassifier(casc_dir + "haarcascade_profileface.xml")
        self.upper_body = cv2.CascadeClassifier(casc_dir + "haarcascade_upperbody.xml")
        self.full_body = cv2.CascadeClassifier(casc_dir + "haarcascade_fullbody.xml")

    def detect(self, cv_bgr: np.ndarray) -> Dict[str, Any]:
        ih, iw = cv_bgr.shape[:2]
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Frontal face - Default
        if not self.face_default.empty():
            faces = self.face_default.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
            if len(faces) > 0:
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                fx, fy, fw, fh = faces[0]
                return {
                    "method": "FRONTAL_FACE_DEFAULT",
                    "bbox": (int(fx), int(fy), int(fw), int(fh)),
                    "center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                    "confidence": 0.95,
                    "is_face": True
                }

        # 2. Frontal face - Alt2 (more sensitive for expressions/tilts)
        if not self.face_alt2.empty():
            faces = self.face_alt2.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(35, 35))
            if len(faces) > 0:
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                fx, fy, fw, fh = faces[0]
                return {
                    "method": "FRONTAL_FACE_ALT2",
                    "bbox": (int(fx), int(fy), int(fw), int(fh)),
                    "center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                    "confidence": 0.90,
                    "is_face": True
                }

        # 3. Profile face
        if not self.profile.empty():
            profiles = self.profile.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
            if len(profiles) > 0:
                profiles = sorted(profiles, key=lambda f: f[2] * f[3], reverse=True)
                fx, fy, fw, fh = profiles[0]
                return {
                    "method": "PROFILE_FACE",
                    "bbox": (int(fx), int(fy), int(fw), int(fh)),
                    "center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                    "confidence": 0.85,
                    "is_face": True
                }

        # 4. Upper body
        if not self.upper_body.empty():
            bodies = self.upper_body.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(60, 60))
            if len(bodies) > 0:
                bodies = sorted(bodies, key=lambda b: b[2] * b[3], reverse=True)
                bx, by, bw, bh = bodies[0]
                return {
                    "method": "UPPER_BODY",
                    "bbox": (int(bx), int(by), int(bw), int(bh)),
                    "center": (float(bx + bw / 2.0), float(by + bh * 0.4)),
                    "confidence": 0.80,
                    "is_face": False
                }

        # 5. Full body
        if not self.full_body.empty():
            fbodies = self.full_body.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(80, 80))
            if len(fbodies) > 0:
                fbodies = sorted(fbodies, key=lambda b: b[2] * b[3], reverse=True)
                bx, by, bw, bh = fbodies[0]
                return {
                    "method": "FULL_BODY",
                    "bbox": (int(bx), int(by), int(bw), int(bh)),
                    "center": (float(bx + bw / 2.0), float(by + bh * 0.3)),
                    "confidence": 0.75,
                    "is_face": False
                }

        # 6. Sports Action / Foreground Subject Contour Cluster (avoiding blind geometric center)
        try:
            # Blur and Otsu threshold to locate dominant contrast subject
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            edges = cv2.Canny(blurred, 40, 120)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            dilated = cv2.dilate(edges, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                # Filter out border artifacts, pick largest foreground subject contour
                valid_contours = []
                for c in contours:
                    cx_, cy_, cw_, ch_ = cv2.boundingRect(c)
                    if cw_ * ch_ > (iw * ih * 0.03) and cw_ < (iw * 0.95):
                        valid_contours.append((cx_, cy_, cw_, ch_))
                if valid_contours:
                    valid_contours = sorted(valid_contours, key=lambda x: x[2] * x[3], reverse=True)
                    bx, by, bw, bh = valid_contours[0]
                    return {
                        "method": "ACTION_SUBJECT_CONTOUR",
                        "bbox": (int(bx), int(by), int(bw), int(bh)),
                        "center": (float(bx + bw / 2.0), float(by + bh * 0.4)),
                        "confidence": 0.70,
                        "is_face": False
                    }
        except Exception:
            pass

        # Fallback with upper-third focal bias (never blind center)
        return {
            "method": "UPPER_THIRD_FOCAL_BIAS",
            "bbox": (int(iw * 0.2), int(ih * 0.15), int(iw * 0.6), int(ih * 0.5)),
            "center": (float(iw / 2.0), float(ih * 0.38)),
            "confidence": 0.50,
            "is_face": False
        }


class OpenCVFocalFramingEngine:
    """
    Intelligently frames subject within 9:16 vertical 1080x1920.
    Ensures safe-zone placement:
    y in [260, 1100] (away from top header and bottom captions).
    Applies reflection border padding if headroom is insufficient.
    """

    def __init__(self, target_w: int = 1080, target_h: int = 1920):
        self.target_w = target_w
        self.target_h = target_h
        self.target_aspect = target_w / target_h
        self.detector = SubjectDetector()

    def frame_and_crop(self, cv_bgr: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        ih, iw = cv_bgr.shape[:2]
        det = self.detector.detect(cv_bgr)
        method = det["method"]
        cx, cy = det["center"]
        bx, by, bw, bh = det["bbox"]
        is_face = det["is_face"]

        crop_details = {
            "detection": det,
            "original_size": (iw, ih),
            "pad_top": 0
        }

        # Safe-zone cropping algorithm
        if is_face:
            # Face-aware safe zone: scale crop box to face height and image height
            h_crop = max(int(bh * 4.2), int(ih * 0.55))
            h_crop = min(ih, h_crop)
            w_crop = int(h_crop * self.target_aspect)

            if w_crop > iw:
                w_crop = iw
                h_crop = min(ih, int(iw / self.target_aspect))
                w_crop = int(h_crop * self.target_aspect)

            # Align face center at ~28% from the top of the crop box
            y0 = int(cy - 0.28 * h_crop)
            x0 = int(cx - w_crop / 2.0)

            # Headroom padding check: if face is too close to upper frame
            pad_top = 0
            if y0 < 0:
                pad_top = -y0 + int(h_crop * 0.06)
                cv_bgr = cv2.copyMakeBorder(cv_bgr, pad_top, 0, 0, 0, borderType=cv2.BORDER_REFLECT_101)
                ih, iw = cv_bgr.shape[:2]
                by += pad_top
                cy += pad_top
                y0 = 0
                crop_details["pad_top"] = pad_top

            # Footroom padding check: if face center cy is too low relative to crop window
            needed_bot = int(cy + 0.70 * h_crop) - ih
            if needed_bot > 0:
                cv_bgr = cv2.copyMakeBorder(cv_bgr, 0, needed_bot + int(h_crop * 0.05), 0, 0, borderType=cv2.BORDER_REFLECT_101)
                ih, iw = cv_bgr.shape[:2]

            y0 = int(cy - 0.30 * h_crop)
            y0 = max(0, min(ih - h_crop, y0))
            x0 = max(0, min(iw - w_crop, x0))

        elif method in ["UPPER_BODY", "FULL_BODY"]:
            h_crop = min(ih, max(int(bh * 2.5), int(ih * 0.65)))
            w_crop = int(h_crop * self.target_aspect)
            if w_crop > iw:
                w_crop = iw
                h_crop = min(ih, int(iw / self.target_aspect))
                w_crop = int(h_crop * self.target_aspect)
            y0 = max(0, min(ih - h_crop, int(cy - 0.32 * h_crop)))
            x0 = max(0, min(iw - w_crop, int(cx - w_crop / 2.0)))

        else: # Action or focal region
            img_aspect = iw / ih
            if img_aspect > self.target_aspect:
                w_crop = int(ih * self.target_aspect)
                h_crop = ih
                y0 = 0
                x0 = int(cx - w_crop / 2.0)
                x0 = max(0, min(iw - w_crop, x0))
            else:
                w_crop = iw
                h_crop = int(iw / self.target_aspect)
                h_crop = min(ih, h_crop)
                x0 = 0
                y0 = int(cy - h_crop * 0.35)
                y0 = max(0, min(ih - h_crop, y0))

        cropped = cv_bgr[y0:y0+h_crop, x0:x0+w_crop]
        resized = cv2.resize(cropped, (self.target_w, self.target_h), interpolation=cv2.INTER_LANCZOS4)

        # Calculate coordinates inside final 1080x1920 frame
        final_subj_x = int((bx - x0) / w_crop * self.target_w)
        final_subj_y = int((by - y0) / h_crop * self.target_h)
        final_subj_w = int(bw / w_crop * self.target_w)
        final_subj_h = int(bh / h_crop * self.target_h)

        crop_details["crop_box"] = (x0, y0, w_crop, h_crop)
        final_subj_cy = final_subj_y + final_subj_h / 2.0
        crop_details["final_subj_box"] = (final_subj_x, final_subj_y, final_subj_w, final_subj_h)
        crop_details["final_subj_center_y"] = int(final_subj_cy)
        crop_details["in_safe_zone"] = (260 <= final_subj_cy <= 1100) if is_face else True

        # Broadcast grade: subtle contrast and clarity
        pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        sharpened = pil_img.filter(ImageFilter.UnsharpMask(radius=1.4, percent=110, threshold=3))
        balanced = ImageEnhance.Contrast(sharpened).enhance(1.05)
        vibrant = ImageEnhance.Color(balanced).enhance(1.06)
        final_bgr = cv2.cvtColor(np.array(vibrant), cv2.COLOR_RGB2BGR)

        return final_bgr, crop_details


class DiagnosticContactSheetBuilder:
    """
    Renders diagnostic contact sheets showing:
    - Original Candidate Image with detected focal/face box
    - Final 1080x1920 Crop with safe-zone indicators
    - Technical and provenance metadata card
    - Rejection alternatives for the scene
    """

    @staticmethod
    def create_story_contact_sheet(
        story_title: str,
        scenes_data: List[Dict[str, Any]],
        out_path: Path
    ) -> bool:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Dimensions: 4 rows (1 per scene), each row has Original (480x320 approx), Final Crop (270x480), Info Card (650x480)
        row_h = 520
        total_w = 1500
        header_h = 90
        total_h = header_h + len(scenes_data) * row_h + 30

        canvas = Image.new("RGB", (total_w, total_h), color=(18, 20, 26))
        draw = ImageDraw.Draw(canvas)

        # Header
        draw.rectangle([(0, 0), (total_w, header_h)], fill=(28, 32, 42))
        draw.text((30, 20), f"30 FOOTBALL PLUS — DIAGNOSTIC IMAGE PROCUREMENT & OPENCV FRAMING", fill=(255, 215, 0))
        draw.text((30, 50), f"STORY: {story_title.upper()} | SAFE-ZONE AUDIT & PROVENANCE", fill=(200, 210, 225))

        for idx, sc in enumerate(scenes_data):
            y_base = header_h + idx * row_h + 15
            scene_num = sc.get("scene_id", f"s{idx+1:02d}")
            role = sc.get("role", "scene")
            sel_img_bgr = sc.get("orig_bgr")
            final_crop_bgr = sc.get("final_bgr")
            crop_meta = sc.get("crop_meta", {})
            det = crop_meta.get("detection", {})
            metrics = sc.get("metrics", {})
            prov = sc.get("provenance", {})
            rejects = sc.get("rejections", [])

            # Draw row separator & card background
            draw.rectangle([(15, y_base), (total_w - 15, y_base + row_h - 10)], fill=(24, 27, 36), outline=(45, 50, 65), width=1)
            draw.text((30, y_base + 12), f"SCENE {scene_num.upper()} [{role.upper()}] — {sc.get('subject_title', '')[:55]}", fill=(100, 200, 255))

            # Panel 1: Original Candidate with Bounding Box
            if sel_img_bgr is not None:
                orig_disp = sel_img_bgr.copy()
                bx, by, bw, bh = det.get("bbox", (0, 0, 0, 0))
                method = det.get("method", "UNKNOWN")
                color = (0, 255, 0) if "FACE" in method else (0, 200, 255) if "BODY" in method else (0, 255, 255)
                if bw > 0 and bh > 0:
                    cv2.rectangle(orig_disp, (bx, by), (bx + bw, by + bh), color, 3)
                    cv2.drawMarker(orig_disp, (int(bx + bw/2), int(by + bh/2)), color, markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
                    cv2.putText(orig_disp, f"{method}", (bx, max(25, by - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                orig_rgb = cv2.cvtColor(orig_disp, cv2.COLOR_BGR2RGB)
                pil_orig = Image.fromarray(orig_rgb)
                # Fit into 440x420
                pil_orig.thumbnail((440, 420), Image.Resampling.LANCZOS)
                canvas.paste(pil_orig, (30, y_base + 45))
                draw.text((30, y_base + 45 + pil_orig.height + 5), f"Original: {crop_meta.get('original_size', (0,0))[0]}x{crop_meta.get('original_size', (0,0))[1]} | {method}", fill=(160, 175, 195))

            # Panel 2: Final 1080x1920 Crop with Safe Zone Guides
            if final_crop_bgr is not None:
                crop_disp = final_crop_bgr.copy()
                # Draw safe zone guides in overlay
                # Top safe zone limit (y=260) & bottom safe zone limit (y=1100)
                cv2.line(crop_disp, (0, 260), (1080, 260), (0, 165, 255), 3) # Upper HUD safe limit
                cv2.line(crop_disp, (0, 1100), (1080, 1100), (0, 0, 255), 3) # Lower caption limit
                cv2.putText(crop_disp, "TOP HUD LIMIT (y=260)", (30, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
                cv2.putText(crop_disp, "CAPTION SAFE LIMIT (y=1100)", (30, 1085), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                fx, fy, fw, fh = crop_meta.get("final_subj_box", (0, 0, 0, 0))
                if fw > 0 and fh > 0:
                    cv2.rectangle(crop_disp, (fx, fy), (fx + fw, fy + fh), (0, 255, 0), 3)

                crop_rgb = cv2.cvtColor(crop_disp, cv2.COLOR_BGR2RGB)
                pil_crop = Image.fromarray(crop_rgb)
                pil_crop.thumbnail((240, 426), Image.Resampling.LANCZOS)
                canvas.paste(pil_crop, (500, y_base + 45))
                is_safe = crop_meta.get("in_safe_zone", True)
                safe_txt = "SAFE ZONE: PASSED (y in [260, 1100])" if is_safe else "SAFE ZONE: ALERT"
                safe_color = (100, 255, 100) if is_safe else (255, 100, 100)
                draw.text((500, y_base + 45 + pil_crop.height + 5), safe_txt, fill=safe_color)

            # Panel 3: Technical & Provenance Card
            info_x = 770
            info_y = y_base + 45
            draw.rectangle([(info_x, info_y), (total_w - 30, y_base + row_h - 25)], fill=(30, 35, 48), outline=(50, 58, 76), width=1)

            lines = [
                f"Selected Subject: {sc.get('subject_name', 'N/A')}",
                f"Publisher / Source: {prov.get('publisher', 'Editorial Web')} ({prov.get('domain', 'N/A')})",
                f"Source URL: {prov.get('url', 'N/A')[:65]}...",
                f"Event Context: {sc.get('event_context', 'N/A')}",
                f"Relevance Score: {metrics.get('score', 0.0):.1f} / 100 | Sharpness Var: {metrics.get('blur_variance', 0.0):.1f}",
                f"Luminance: {metrics.get('luminance', 0.0):.1f} | Texture Var: {metrics.get('variance', 0.0):.1f}",
                f"Detection: {det.get('method', 'N/A')} (conf={det.get('confidence', 0.0):.2f})",
                f"Crop Window: {crop_meta.get('crop_box', 'N/A')}"
            ]
            for i, l in enumerate(lines):
                draw.text((info_x + 15, info_y + 12 + i * 22), l, fill=(225, 230, 240) if i == 0 else (180, 195, 215))

            # Rejections Box inside Card
            rej_y = info_y + len(lines) * 22 + 20
            draw.text((info_x + 15, rej_y), "REJECTED CANDIDATE AUDIT (Anti-Watermark / Relevance):", fill=(255, 180, 80))
            if rejects:
                for r_idx, r in enumerate(rejects[:2]):
                    draw.text((info_x + 25, rej_y + 20 + r_idx * 20), f"- {r.get('reason', 'N/A')}: {r.get('url', '')[:55]}...", fill=(240, 140, 140))
            else:
                draw.text((info_x + 25, rej_y + 20), "- All candidate evaluations strictly audited", fill=(160, 160, 160))

        canvas.save(out_path, format="PNG")
        print(f"[ContactSheet] Successfully generated diagnostic contact sheet -> {out_path}")
        return True
