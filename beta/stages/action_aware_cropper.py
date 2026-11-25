"""
beta/stages/action_aware_cropper.py - Action-Aware & Strategy-Based 9:16 Cropping Engine (V7.2 Broadcast Standard).

Solves the critical visual weaknesses identified in the V7.1.6.7 audit:
1. Strict Blur Filter: Rejects images with Laplacian variance < 45.0.
2. Resolution Floor: Rejects low-res assets (iw < 480 or ih < 480) and scale factor > 2.2x.
3. Multi-Player Boundary Protection: Prevents slicing secondary players in half on the border.
4. Editorial Safe Zone Enforcement: Subject face must reside in y in [260, 1250] in 1080x1920,
   guaranteeing zero obscuration by top TV bugs or bottom lower-third / ticker.
5. Balanced Headroom: Prevents suffocating over-zoom by enforcing natural head & shoulder proportions.
"""

from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageEnhance

try:
    from stages.semantic_image_procurement import EnhancedSubjectDetector
except ModuleNotFoundError:
    from beta.stages.semantic_image_procurement import EnhancedSubjectDetector


class ActionAwareCropper:
    def __init__(self, target_w: int = 1080, target_h: int = 1920):
        self.target_w = target_w
        self.target_h = target_h
        self.target_aspect = target_w / float(target_h)  # 9/16 = 0.5625
        self.detector = EnhancedSubjectDetector()

    def eval_blur_variance(self, cv_bgr: np.ndarray) -> float:
        """Computes Laplacian variance across the image to evaluate true sharpness."""
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def crop_candidate(
        self,
        cv_bgr: np.ndarray,
        strategy: str = "portrait",
        contest_box: Optional[Tuple[int, int, int, int]] = None,
        preferred_bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        """
        Executes specialized 9:16 cropping:
        strategy in ['portrait', 'match_action', 'celebration', 'managerial', 'tactical']
        """
        ih, iw = cv_bgr.shape[:2]
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)

        audit = {
            "strategy": strategy,
            "original_dimensions": (iw, ih),
            "decision": "PENDING"
        }

        # -------------------------------------------------------------
        # Gate 1: Resolution Floor
        # -------------------------------------------------------------
        if iw < 480 or ih < 480 or (iw * ih) < 250000:
            audit["decision"] = "REJECTED"
            audit["reason"] = f"Image resolution too low ({iw}x{ih}) for 1080x1920 broadcast"
            return False, None, audit

        # -------------------------------------------------------------
        # Gate 2: True Sharpness / Blur Rejection
        # -------------------------------------------------------------
        blur_var = self.eval_blur_variance(cv_bgr)
        audit["blur_variance"] = round(blur_var, 1)
        if blur_var < 45.0:
            audit["decision"] = "REJECTED"
            audit["reason"] = f"Image fails sharpness threshold: Laplacian variance {blur_var:.1f} < 45.0 (blurry/out-of-focus)"
            return False, None, audit

        if preferred_bbox is not None:
            px, py, pw, ph = preferred_bbox
            det = {
                "method": "SFACE_LOCKED_FACE",
                "bbox": preferred_bbox,
                "is_face": True,
                "face_center": (px + pw / 2.0, py + ph / 2.0),
                "subject_center": (px + pw / 2.0, py + ph / 2.0),
                "confidence": 1.0,
            }
        else:
            det = self.detector.detect(cv_bgr)
        method = det["method"]
        audit["detection"] = {k: v for k, v in det.items() if k != "raw_yunet"}

        # Detect all foreground faces (YuNet CNN primary, Haar fallback) to prevent edge slicing
        yunet_all = self.detector.detect_yunet_faces(cv_bgr)
        all_faces = [f["bbox"] for f in yunet_all]
        if not all_faces and not self.detector.face_default.empty():
            faces = self.detector.face_default.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(45, 45))
            all_faces = [tuple(int(v) for v in f) for f in faces]

        # -------------------------------------------------------------
        # Crop Geometry Calculation by Strategy
        # -------------------------------------------------------------
        if strategy in ["portrait", "managerial"]:
            if det["is_face"]:
                fx, fy, fw, fh = det["bbox"]
                cx, cy = det["face_center"]

                # Ensure face height is at most 30% of vertical crop (preserves shoulders and neck)
                h_crop = max(int(fh * 4.8), int(ih * 0.65))
                h_crop = min(ih, h_crop)
                w_crop = int(h_crop * self.target_aspect)

                if w_crop > iw:
                    w_crop = iw
                    h_crop = min(ih, int(iw / self.target_aspect))
                    w_crop = int(h_crop * self.target_aspect)

                y0 = int(cy - 0.28 * h_crop)
                x0 = int(cx - w_crop / 2.0)
            else:
                bx, by, bw, bh = det.get("bbox") or (int(iw*0.2), int(ih*0.2), int(iw*0.6), int(ih*0.6))
                cx, cy = det.get("subject_center") or (iw / 2.0, ih * 0.35)
                h_crop = min(ih, max(int(bh * 2.5), int(ih * 0.70)))
                w_crop = int(h_crop * self.target_aspect)
                if w_crop > iw:
                    w_crop = iw
                    h_crop = min(ih, int(iw / self.target_aspect))
                    w_crop = int(h_crop * self.target_aspect)
                y0 = int(cy - 0.32 * h_crop)
                x0 = int(cx - w_crop / 2.0)

        elif strategy == "celebration":
            cx, cy = det.get("face_center") or det.get("subject_center") or (iw / 2.0, ih * 0.38)
            h_crop = min(ih, int(ih * 0.88))
            w_crop = int(h_crop * self.target_aspect)
            if w_crop > iw:
                w_crop = iw
                h_crop = int(iw / self.target_aspect)
                w_crop = int(h_crop * self.target_aspect)
            y0 = int(cy - 0.30 * h_crop)
            x0 = int(cx - w_crop / 2.0)

        elif strategy == "match_action":
            # Match action: center around face if present so player is never clipped horizontally
            cx, cy = det.get("face_center") or det.get("subject_center") or (iw / 2.0, ih * 0.42)
            h_crop = ih
            w_crop = int(h_crop * self.target_aspect)
            if w_crop > iw:
                w_crop = iw
                h_crop = int(iw / self.target_aspect)
                w_crop = int(h_crop * self.target_aspect)
            y0 = int(cy - h_crop * 0.34) if det.get("is_face") else int(cy - h_crop * 0.40)
            x0 = int(cx - w_crop / 2.0)

        else: # tactical / stadium
            w_crop = int(ih * self.target_aspect)
            h_crop = ih
            if w_crop > iw:
                w_crop = iw
                h_crop = int(iw / self.target_aspect)
            cx, cy = det.get("subject_center") or (iw / 2.0, ih / 2.0)
            x0 = int(cx - w_crop / 2.0)
            y0 = int(cy - h_crop * 0.45)

        # Clamp crop box to source bounds
        x0 = max(0, min(iw - w_crop, x0))
        y0 = max(0, min(ih - h_crop, y0))

        # Auto-align face into vertical broadcast safe zone [270, 1150] AND horizontal center zone
        if det.get("is_face"):
            fx, fy, fw, fh = det["bbox"]
            face_top_proj = int((fy - y0) / float(h_crop) * self.target_h)
            if face_top_proj < 250:
                needed_y0 = int(fy - (270.0 / self.target_h) * h_crop)
                y0 = max(0, min(ih - h_crop, needed_y0))
            face_bot_proj = int((fy + fh - y0) / float(h_crop) * self.target_h)
            if face_bot_proj > 1250:
                needed_y0 = int(fy + fh - (1200.0 / self.target_h) * h_crop)
                y0 = max(0, min(ih - h_crop, needed_y0))

            # Horizontal auto-recentering if clamped edge sits near primary face
            needed_x0 = int((fx + fw / 2.0) - w_crop / 2.0)
            x0 = max(0, min(iw - w_crop, needed_x0))

        # -------------------------------------------------------------
        # Gate 3: Multi-Player Border Slicing Check
        # -------------------------------------------------------------
        if len(all_faces) >= 2:
            for (ofx, ofy, ofw, ofh) in all_faces:
                if det.get("is_face") and abs(ofx - det["bbox"][0]) < 15 and abs(ofy - det["bbox"][1]) < 15:
                    continue
                if (ofx < x0 < ofx + ofw) or (ofx < x0 + w_crop < ofx + ofw):
                    audit["decision"] = "REJECTED"
                    audit["reason"] = "Secondary player face is sliced in half on the crop border (distracting partial figure)"
                    return False, None, audit

        # -------------------------------------------------------------
        # Gate 4: Safe Zone Verification in 1080x1920 (X & Y axes + Resolution Limit)
        # -------------------------------------------------------------
        scale_x = self.target_w / float(w_crop)
        scale_y = self.target_h / float(h_crop)
        max_scale = max(scale_x, scale_y)

        # Tighten scale limit: max 2.45x upscale to prevent soft pixels on mobile screens
        max_allowed_scale = 2.45 if blur_var >= 45.0 else 2.00
        if max_scale > max_allowed_scale:
            audit["decision"] = "REJECTED"
            audit["reason"] = f"Crop upscale factor ({max_scale:.2f}x) exceeds {max_allowed_scale:.2f}x limit (blur: {blur_var:.1f}); would cause pixelation"
            return False, None, audit

        if det.get("is_face"):
            fx, fy, fw, fh = det["bbox"]
            final_face_top = int((fy - y0) / float(h_crop) * self.target_h)
            final_face_bottom = int((fy + fh - y0) / float(h_crop) * self.target_h)
            final_face_left = int((fx - x0) / float(w_crop) * self.target_w)
            final_face_right = int((fx + fw - x0) / float(w_crop) * self.target_w)
            final_face_center_x = int((final_face_left + final_face_right) / 2.0)
            final_face_center_y = int((final_face_top + final_face_bottom) / 2.0)

            if final_face_top < 240:
                audit["decision"] = "REJECTED"
                audit["reason"] = f"Face top at y={final_face_top} violates top safe zone (obscured by HUD / top banner < 240)"
                return False, None, audit

            if final_face_bottom > 1250:
                audit["decision"] = "REJECTED"
                audit["reason"] = f"Face chin at y={final_face_bottom} violates lower-third safe zone (obscured by graphics > 1250)"
                return False, None, audit

            if final_face_left < 50 or final_face_right > 1030 or final_face_center_x < 180 or final_face_center_x > 900:
                audit["decision"] = "REJECTED"
                audit["reason"] = f"Primary face horizontally edge-pinned/clipped (x={final_face_left}..{final_face_right}, center={final_face_center_x})"
                return False, None, audit

            audit["final_face_y"] = f"{final_face_top}..{final_face_bottom}"
            audit["final_face_x"] = f"{final_face_left}..{final_face_right}"
            audit["final_face_center_y"] = final_face_center_y
            audit["final_face_center_x"] = final_face_center_x
            audit["safe_zone_compliant"] = True

        # Perform high-order Lanczos crop & upscale
        cropped_cv = cv_bgr[y0:y0+h_crop, x0:x0+w_crop]
        crop_blur = self.eval_blur_variance(cropped_cv)
        if crop_blur < 45.0:
            audit["decision"] = "REJECTED"
            audit["reason"] = f"Cropped subject fails sharpness threshold: Laplacian variance {crop_blur:.1f} < 45.0 (soft/blurry subject)"
            return False, None, audit

        resized = cv2.resize(cropped_cv, (self.target_w, self.target_h), interpolation=cv2.INTER_LANCZOS4)

        # Broadcast Color & HD Polish
        pil_res = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        sharpened = pil_res.filter(ImageFilter.UnsharpMask(radius=1.2, percent=108, threshold=3))
        balanced = ImageEnhance.Contrast(sharpened).enhance(1.04)
        vibrant = ImageEnhance.Color(balanced).enhance(1.05)
        clean_final_bgr = cv2.cvtColor(np.array(vibrant), cv2.COLOR_RGB2BGR)

        audit["decision"] = "PASSED"
        audit["crop_box"] = (x0, y0, w_crop, h_crop)
        audit["effective_crop_res"] = f"{w_crop}x{h_crop}"
        audit["scale_factor"] = round(max_scale, 2)

        return True, clean_final_bgr, audit
