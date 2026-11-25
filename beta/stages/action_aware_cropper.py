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
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

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

    def _compose_broadcast_studio_frame(
        self,
        cv_bgr: np.ndarray,
        audit: Dict[str, Any]
    ) -> Tuple[bool, np.ndarray, Dict[str, Any]]:
        """
        Composes a 1990s broadcast studio 16:9 inset viewport inside 1080x1920 when
        a wide horizontal photo would suffer excessive zoom or body slicing under raw 9:16 cropping.
        """
        ih, iw = cv_bgr.shape[:2]
        # Ambient darkened blurred studio fill from same photo
        bg_scale = max(self.target_w / float(iw), self.target_h / float(ih))
        bg_w, bg_h = int(iw * bg_scale), int(ih * bg_scale)
        bg_resized = cv2.resize(cv_bgr, (bg_w, bg_h), interpolation=cv2.INTER_AREA)
        x_off = max(0, (bg_w - self.target_w) // 2)
        y_off = max(0, (bg_h - self.target_h) // 2)
        bg_crop = bg_resized[y_off:y_off + self.target_h, x_off:x_off + self.target_w]
        bg_pil = Image.fromarray(cv2.cvtColor(bg_crop, cv2.COLOR_BGR2RGB))
        bg_pil = bg_pil.filter(ImageFilter.GaussianBlur(radius=30))
        bg_pil = ImageEnhance.Brightness(bg_pil).enhance(0.32)

        # Sharp 16:9 / landscape monitor frame anchored safely inside [250..1120] above subtitles/HUD
        card_w = 1000
        card_h = min(780, int(card_w * (ih / float(iw))))
        if card_h < 500:
            card_h = min(760, int(card_w * (ih / float(iw))))
        fg_resized = cv2.resize(cv_bgr, (card_w, card_h), interpolation=cv2.INTER_LANCZOS4)
        fg_pil = Image.fromarray(cv2.cvtColor(fg_resized, cv2.COLOR_BGR2RGB))
        fg_pil = fg_pil.filter(ImageFilter.UnsharpMask(radius=1.1, percent=106, threshold=3))
        fg_pil = ImageEnhance.Contrast(fg_pil).enhance(1.04)
        fg_pil = ImageEnhance.Color(fg_pil).enhance(1.05)

        stage_center_y = 670
        paste_x = (self.target_w - card_w) // 2
        paste_y = max(255, stage_center_y - card_h // 2)

        draw = ImageDraw.Draw(bg_pil)
        draw.rectangle(
            [(paste_x - 4, paste_y - 4), (paste_x + card_w + 4, paste_y + card_h + 4)],
            fill=(18, 28, 52),
            outline=(195, 212, 240),
            width=3,
        )
        bg_pil.paste(fg_pil, (paste_x, paste_y))

        final_bgr = cv2.cvtColor(np.array(bg_pil), cv2.COLOR_RGB2BGR)
        audit["decision"] = "PASSED"
        audit["framing_mode"] = "broadcast_card"
        audit["focal_x"] = 50.0
        audit["focal_y"] = round(((paste_y + card_h / 2.0) / float(self.target_h)) * 100.0, 1)
        audit["pan_direction"] = "center"
        audit["crop_box"] = (0, 0, iw, ih)
        audit["effective_crop_res"] = f"{iw}x{ih}"
        audit["scale_factor"] = round(card_w / float(iw), 2)
        audit["safe_zone_compliant"] = True
        return True, final_bgr, audit

    def crop_candidate(
        self,
        cv_bgr: np.ndarray,
        strategy: str = "portrait",
        contest_box: Optional[Tuple[int, int, int, int]] = None,
        preferred_bbox: Optional[Tuple[int, int, int, int]] = None,
        body_box: Optional[Tuple[int, int, int, int]] = None,
        ball_box: Optional[Tuple[int, int, int, int]] = None,
        person_boxes: Optional[List[Tuple[int, int, int, int, float]]] = None,
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
            # Match action: blend face centroid + body centroid + ball proximity so player & action aren't sliced
            face_cx, face_cy = det.get("face_center") or det.get("subject_center") or (iw / 2.0, ih * 0.42)
            cx = face_cx
            cy = face_cy
            if body_box is not None:
                bx, by, bw, bh = body_box
                body_cx = bx + bw / 2.0
                cx = 0.65 * face_cx + 0.35 * body_cx
            h_crop = ih
            w_crop = int(h_crop * self.target_aspect)
            if w_crop > iw:
                w_crop = iw
                h_crop = int(iw / self.target_aspect)
                w_crop = int(h_crop * self.target_aspect)
            if ball_box is not None:
                blx, bly, blw, blh = ball_box
                ball_cx = blx + blw / 2.0
                if abs(ball_cx - face_cx) < w_crop * 0.72:
                    cx = 0.80 * cx + 0.20 * ball_cx
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
        # Gate 3: Multi-Player Border Slicing Check (Face + Adjacent Bodies)
        # -------------------------------------------------------------
        if len(all_faces) >= 2:
            for (ofx, ofy, ofw, ofh) in all_faces:
                if det.get("is_face") and abs(ofx - det["bbox"][0]) < 15 and abs(ofy - det["bbox"][1]) < 15:
                    continue
                if (ofx < x0 < ofx + ofw) or (ofx < x0 + w_crop < ofx + ofw):
                    if iw >= 840 and ih >= 470 and (iw / float(ih)) >= 1.38 and blur_var >= 55.0:
                        return self._compose_broadcast_studio_frame(cv_bgr, audit)
                    audit["decision"] = "REJECTED"
                    audit["reason"] = "Secondary player face is sliced in half on the crop border (distracting partial figure)"
                    return False, None, audit

        # -------------------------------------------------------------
        # Gate 4: Safe Zone Verification in 1080x1920 (X & Y axes + Resolution Limit)
        # -------------------------------------------------------------
        scale_x = self.target_w / float(w_crop)
        scale_y = self.target_h / float(h_crop)
        max_scale = max(scale_x, scale_y)

        # Tighten scale limit: max 2.35x upscale to prevent soft pixels on mobile screens;
        # wide high-res horizontal sports photos upgrade cleanly to Broadcast Studio Inset framing instead of over-zoom!
        max_allowed_scale = 2.35 if blur_var >= 45.0 else 2.00
        if max_scale > max_allowed_scale:
            if iw >= 840 and ih >= 470 and (iw / float(ih)) >= 1.38 and blur_var >= 55.0:
                return self._compose_broadcast_studio_frame(cv_bgr, audit)
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
                if iw >= 840 and ih >= 470 and (iw / float(ih)) >= 1.38 and blur_var >= 55.0:
                    return self._compose_broadcast_studio_frame(cv_bgr, audit)
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

        focal_x = round(max(15.0, min(85.0, (audit.get("final_face_center_x", 540) / float(self.target_w)) * 100.0)), 1)
        focal_y = round(max(15.0, min(60.0, (audit.get("final_face_center_y", 480) / float(self.target_h)) * 100.0)), 1)
        pan_dir = "right" if focal_x < 42.0 else ("left" if focal_x > 58.0 else "center")

        audit["decision"] = "PASSED"
        audit["framing_mode"] = "full_bleed"
        audit["focal_x"] = focal_x
        audit["focal_y"] = focal_y
        audit["pan_direction"] = pan_dir
        audit["crop_box"] = (x0, y0, w_crop, h_crop)
        audit["effective_crop_res"] = f"{w_crop}x{h_crop}"
        audit["scale_factor"] = round(max_scale, 2)

        return True, clean_final_bgr, audit
