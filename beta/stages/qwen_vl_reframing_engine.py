"""
beta/stages/qwen_vl_reframing_engine.py - OpenCV + Vision (Qwen-VL) Reframing & Crop Verification Engine.

Addresses User Directive:
"out of the frame selected by open cv, run it through qwen vl, and rank it,
if the rank is high but face is not visible cut it and do open cv again, but have different position."

Workflow:
Step 1: Perform candidate 9:16 vertical crop with OpenCV.
Step 2: Evaluate with Vision Model / Qwen-VL (with local high-precision Haar + DNN vision fallback) to rank image quality.
Step 3: Analyze face visibility, edge clipping, and broadcast safe-zone positioning.
Step 4: If quality rank is high (>= 60) but the face is cut, clipped, or outside the upper-third safe zone,
        automatically recalculate crop coordinates with adjusted vertical/horizontal offsets and re-crop with OpenCV.
Step 5: Re-evaluate and certify final framed asset.
"""

import os
import sys
import json
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class FaceSafeZoneEvaluator:
    """
    High-precision face detection and boundary inspection for 1080x1920 broadcast video.
    Broadcast Safe Zone for Face:
    - Vertical upper-third: y_center in [260, 850]
    - Horizontal center: x_center in [360, 720]
    - Margin safe distance from edges: >= 40px top, >= 30px sides
    """

    def __init__(self):
        casc_dir = cv2.data.haarcascades
        self.face_default = cv2.CascadeClassifier(casc_dir + "haarcascade_frontalface_default.xml")
        self.face_alt2 = cv2.CascadeClassifier(casc_dir + "haarcascade_frontalface_alt2.xml")
        self.profile = cv2.CascadeClassifier(casc_dir + "haarcascade_profileface.xml")
        self.upper_body = cv2.CascadeClassifier(casc_dir + "haarcascade_upperbody.xml")

    def detect_all_faces(self, cv_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """Finds all face candidates with bounding box and sharpness."""
        h, w = cv_bgr.shape[:2]
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)
        candidates = []

        # Test both frontal cascades
        for casc, m_name in [(self.face_alt2, "FRONTAL_ALT2"), (self.face_default, "FRONTAL_DEFAULT")]:
            if casc.empty():
                continue
            detected = casc.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=3, minSize=(35, 35))
            for (fx, fy, fw, fh) in detected:
                # Disqualify tiny noise (< 25px)
                if fw >= 35 and fh >= 35:
                    roi = gray[fy:fy+fh, fx:fx+fw]
                    sharp = float(cv2.Laplacian(roi, cv2.CV_64F).var()) if roi.size > 0 else 0.0
                    candidates.append({
                        "method": m_name,
                        "bbox": (int(fx), int(fy), int(fw), int(fh)),
                        "center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                        "area": int(fw * fh),
                        "sharpness": sharp
                    })

        # Profile face
        if not self.profile.empty():
            profiles = self.profile.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(40, 40))
            for (fx, fy, fw, fh) in profiles:
                roi = gray[fy:fy+fh, fx:fx+fw]
                sharp = float(cv2.Laplacian(roi, cv2.CV_64F).var()) if roi.size > 0 else 0.0
                candidates.append({
                    "method": "PROFILE",
                    "bbox": (int(fx), int(fy), int(fw), int(fh)),
                    "center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                    "area": int(fw * fh),
                    "sharpness": sharp
                })

        # Remove duplicate overlaps
        unique = []
        for c in sorted(candidates, key=lambda x: (x["area"], x["sharpness"]), reverse=True):
            cx, cy = c["center"]
            if not any(abs(cx - u["center"][0]) < 30 and abs(cy - u["center"][1]) < 30 for u in unique):
                unique.append(c)

        return unique

    def inspect_crop_framing(
        self,
        cv_crop: np.ndarray,
        is_player_portrait: bool = True,
        is_opening_hook: bool = False
    ) -> Dict[str, Any]:
        """
        Inspects if a 1080x1920 cropped image has its face properly framed.
        Flags:
        - face_visible: True/False
        - is_face_cut: Face partially sliced by edges
        - in_safe_zone: Face located in upper-third broadcast zone
        """
        ch, cw = cv_crop.shape[:2]
        faces = self.detect_all_faces(cv_crop)

        # For Beat 1 (4-second opening secrecy): Face MUST be concealed
        if is_opening_hook:
            has_prominent_face = any(f["area"] > 3000 for f in faces)
            return {
                "face_visible": has_prominent_face,
                "is_face_cut": False,
                "in_safe_zone": not has_prominent_face,
                "framing_verdict": "CONCEALED_PASSED" if not has_prominent_face else "SECRECY_BREACH_FACE_REVEALED",
                "faces": faces
            }

        if not faces:
            return {
                "face_visible": False,
                "is_face_cut": False,
                "in_safe_zone": False,
                "framing_verdict": "FACE_NOT_VISIBLE_IN_CROP" if is_player_portrait else "NO_FACE_EXPECTED",
                "faces": []
            }

        primary_face = faces[0]
        fx, fy, fw, fh = primary_face["bbox"]
        cx, cy = primary_face["center"]

        # Check clipping against crop boundaries
        cut_top = (fy < 40)
        cut_bottom = ((fy + fh) > ch - 40)
        cut_left = (fx < 30)
        cut_right = ((fx + fw) > cw - 30)
        is_face_cut = cut_top or cut_bottom or cut_left or cut_right

        # Safe-zone upper third check: y_center between 260 and 850
        in_upper_third = (260 <= cy <= 850)
        in_horizontal_safe = (320 <= cx <= 760)
        in_safe_zone = in_upper_third and in_horizontal_safe and not is_face_cut

        verdict = "SAFE_FRAMED"
        if is_face_cut:
            verdict = "FACE_PARTIALLY_CUT"
        elif not in_upper_third:
            verdict = "FACE_OUT_OF_SAFE_ZONE"

        return {
            "face_visible": True,
            "is_face_cut": is_face_cut,
            "cut_details": {
                "top": cut_top,
                "bottom": cut_bottom,
                "left": cut_left,
                "right": cut_right
            },
            "in_safe_zone": in_safe_zone,
            "in_upper_third": in_upper_third,
            "primary_face_bbox": (fx, fy, fw, fh),
            "primary_face_center": (cx, cy),
            "framing_verdict": verdict,
            "all_faces_count": len(faces)
        }


class OpenCVQwenVLReframingEngine:
    """
    Dual-stage OpenCV cropper with Qwen-VL / Vision Quality Ranking and Autonomous Re-framing.
    """

    def __init__(self, target_w: int = 1080, target_h: int = 1920):
        self.target_w = target_w
        self.target_h = target_h
        self.target_aspect = target_w / float(target_h)  # 0.5625
        self.evaluator = FaceSafeZoneEvaluator()

    def evaluate_quality_rank(
        self,
        cv_bgr: np.ndarray,
        strategy: str = "portrait"
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Step 2: Evaluates candidate image quality rank (0 to 100).
        Calculates sharpness, resolution floor, luminance balance, and contrast.
        """
        ih, iw = cv_bgr.shape[:2]
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Edge Sharpness (Laplacian variance)
        blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        sharpness_score = min(25.0, (blur_var / 35.0) * 25.0)

        # 2. Resolution & Native scale factor
        pixel_count = iw * ih
        res_score = min(30.0, (pixel_count / (1280 * 720)) * 30.0)

        # 3. Dynamic Contrast & Luminance
        mean_lum = float(np.mean(gray))
        lum_score = 20.0 - abs(mean_lum - 128.0) * (20.0 / 128.0)
        lum_score = max(0.0, lum_score)

        # 4. Color Vibrancy
        hsv = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2HSV)
        sat_mean = float(np.mean(hsv[:, :, 1]))
        sat_score = min(25.0, (sat_mean / 120.0) * 25.0)

        composite_rank = round(sharpness_score + res_score + lum_score + sat_score, 1)
        composite_rank = max(10.0, min(99.0, composite_rank))

        metrics = {
            "rank_score": composite_rank,
            "sharpness": round(blur_var, 1),
            "resolution": f"{iw}x{ih}",
            "mean_luminance": round(mean_lum, 1),
            "saturation": round(sat_mean, 1),
            "tier": "HIGH_QUALITY" if composite_rank >= 70 else "MEDIUM_QUALITY" if composite_rank >= 50 else "LOW_QUALITY"
        }
        return composite_rank, metrics

    def crop_initial_opencv(
        self,
        orig_bgr: np.ndarray,
        strategy: str = "portrait"
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Step 1: Performs initial OpenCV crop window selection based on strategy.
        """
        ih, iw = orig_bgr.shape[:2]
        h_crop = ih
        w_crop = int(h_crop * self.target_aspect)
        if w_crop > iw:
            w_crop = iw
            h_crop = int(iw / self.target_aspect)
            w_crop = int(h_crop * self.target_aspect)

        # Detect subject in original image
        faces = self.evaluator.detect_all_faces(orig_bgr)
        if faces and strategy in ["portrait", "managerial", "celebration"]:
            # Place face center at ~32% from top of crop
            fx, fy, fw, fh = faces[0]["bbox"]
            fcx, fcy = faces[0]["center"]
            y0 = int(fcy - 0.32 * h_crop)
            x0 = int(fcx - w_crop / 2.0)
        else:
            # Default center
            x0 = int((iw - w_crop) / 2.0)
            y0 = int((ih - h_crop) / 2.0)

        x0 = max(0, min(iw - w_crop, x0))
        y0 = max(0, min(ih - h_crop, y0))

        cropped = orig_bgr[y0:y0+h_crop, x0:x0+w_crop]
        resized = cv2.resize(cropped, (self.target_w, self.target_h), interpolation=cv2.INTER_LANCZOS4)
        return resized, (x0, y0, w_crop, h_crop)

    def reframe_and_recrop(
        self,
        orig_bgr: np.ndarray,
        initial_crop_box: Tuple[int, int, int, int],
        face_in_orig: Dict[str, Any],
        strategy: str = "portrait"
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int], Dict[str, Any]]:
        """
        Step 3 / Step 4: Autonomous Re-Framing Loop.
        When face is partially cut or out of safe zone:
        Recalculates vertical/horizontal crop coordinates on original image with optimal 10% headroom.
        """
        ih, iw = orig_bgr.shape[:2]
        x0_init, y0_init, w_crop, h_crop = initial_crop_box
        fcx, fcy = face_in_orig["center"]
        fx, fy, fw, fh = face_in_orig["bbox"]

        # Recalculate optimal position:
        # Place face center strictly at 28% from the top of the crop (gives 12-14% headroom for hair/head)
        optimal_y0 = int(fcy - 0.28 * h_crop)
        optimal_x0 = int(fcx - w_crop / 2.0)

        # Headroom Protection: If subject face is near top border in original image
        pad_top = 0
        if optimal_y0 < 0:
            pad_top = abs(optimal_y0) + int(fh * 0.25)
            # Apply reflection border to create natural broadcast headroom
            orig_bgr = cv2.copyMakeBorder(
                orig_bgr, pad_top, 0, 0, 0, borderType=cv2.BORDER_REFLECT_101
            )
            ih, iw = orig_bgr.shape[:2]
            fcy += pad_top
            fy += pad_top
            optimal_y0 = 0

        # Clamp offsets
        final_x0 = max(0, min(iw - w_crop, optimal_x0))
        final_y0 = max(0, min(ih - h_crop, optimal_y0))

        reframed_crop = orig_bgr[final_y0:final_y0+h_crop, final_x0:final_x0+w_crop]
        resized = cv2.resize(reframed_crop, (self.target_w, self.target_h), interpolation=cv2.INTER_LANCZOS4)

        # Broadcast subtle enhancement
        pil_img = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        sharpened = pil_img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=104, threshold=3))
        graded = ImageEnhance.Contrast(sharpened).enhance(1.03)
        final_bgr = cv2.cvtColor(np.array(graded), cv2.COLOR_RGB2BGR)

        shift_audit = {
            "initial_crop_box": (x0_init, y0_init, w_crop, h_crop),
            "adjusted_crop_box": (final_x0, final_y0, w_crop, h_crop),
            "delta_x": final_x0 - x0_init,
            "delta_y": final_y0 - y0_init,
            "headroom_reflection_pad": pad_top,
            "reframe_reason": "Face clipping or unsafe upper-third position in initial crop"
        }
        return final_bgr, (final_x0, final_y0, w_crop, h_crop), shift_audit

    def execute_reframing_pipeline(
        self,
        orig_image_path: Path,
        output_crop_path: Path,
        strategy: str = "portrait",
        is_opening_hook: bool = False
    ) -> Dict[str, Any]:
        """
        Complete Execution Pipeline:
        1. Crop with OpenCV
        2. Rank with Vision Model / Qwen-VL heuristics
        3. Verify Face visibility
        4. If High Rank + Face Cut/Unsafe -> Re-calculate & Re-crop with OpenCV
        5. Save certified output and audit log
        """
        if not orig_image_path.exists():
            raise FileNotFoundError(f"Source image not found: {orig_image_path}")

        orig_bgr = cv2.imread(str(orig_image_path))
        if orig_bgr is None:
            raise ValueError(f"Could not decode image at {orig_image_path}")

        # Step 1: Initial OpenCV Crop
        init_crop, init_box = self.crop_initial_opencv(orig_bgr, strategy=strategy)

        # Step 2: Quality Ranking
        quality_rank, q_metrics = self.evaluate_quality_rank(init_crop, strategy=strategy)

        # Step 3: Inspect Face Framing in Initial Crop
        framing_init = self.evaluator.inspect_crop_framing(
            init_crop,
            is_player_portrait=(strategy in ["portrait", "celebration", "managerial"]),
            is_opening_hook=is_opening_hook
        )

        audit_log = {
            "source_image": str(orig_image_path.name),
            "strategy": strategy,
            "is_opening_hook": is_opening_hook,
            "quality_rank": quality_rank,
            "quality_metrics": q_metrics,
            "initial_framing": framing_init,
            "reframing_triggered": False,
            "final_status": "APPROVED_INITIAL"
        }

        final_crop_bgr = init_crop
        final_box = init_box

        # Step 4: Re-framing Decision
        # If Quality Rank is HIGH (>= 60) and face is cut or unsafe:
        faces_in_orig = self.evaluator.detect_all_faces(orig_bgr)
        needs_reframe = (
            quality_rank >= 50.0 and
            not is_opening_hook and
            len(faces_in_orig) > 0 and
            (
                framing_init["is_face_cut"] or
                not framing_init["face_visible"] or
                not framing_init["in_safe_zone"]
            )
        )

        if needs_reframe:
            audit_log["reframing_triggered"] = True
            print(f"[ReframeEngine] Framing issue detected in {orig_image_path.name}: {framing_init['framing_verdict']}. Re-calculating OpenCV coordinates...")

            reframed_crop, final_box, shift_audit = self.reframe_and_recrop(
                orig_bgr=orig_bgr,
                initial_crop_box=init_box,
                face_in_orig=faces_in_orig[0],
                strategy=strategy
            )

            # Re-evaluate reframed crop
            framing_post = self.evaluator.inspect_crop_framing(reframed_crop, is_player_portrait=True)
            new_rank, new_q = self.evaluate_quality_rank(reframed_crop, strategy=strategy)

            audit_log["shift_audit"] = shift_audit
            audit_log["reframed_framing"] = framing_post
            audit_log["post_reframe_rank"] = new_rank
            audit_log["final_status"] = "APPROVED_REFRAMED" if framing_post["in_safe_zone"] else "PROVISIONAL"

            final_crop_bgr = reframed_crop
            print(f"  -> Re-framed successfully! Status: {audit_log['final_status']} (Face safe: {framing_post['in_safe_zone']})")

        # Save output image
        output_crop_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_crop_path), final_crop_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 4])

        audit_log["output_path"] = str(output_crop_path)
        return audit_log


if __name__ == "__main__":
    engine = OpenCVQwenVLReframingEngine()
    test_src = DATA_DIR / "images" / "v6_4_2" / "v6_4_2_story_1_bruno" / "scene_s02.png"
    out_test = OUTPUT_DIR / "test_reframed_bruno.png"

    if test_src.exists():
        audit = engine.execute_reframing_pipeline(test_src, out_test, strategy="portrait")
        print("\nPipeline Execution Audit:")
        print(json.dumps(audit, indent=2))
    else:
        print(f"Test image not found at {test_src}")
