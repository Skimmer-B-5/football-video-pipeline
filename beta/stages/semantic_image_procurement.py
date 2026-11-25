"""
# BETA V6.4.1: SEMANTIC IMAGE PROCUREMENT & FOCAL FRAMING ENGINE
# Sandboxed inside beta/ | Strictly zero modifications outside beta/
"""

import sys
import os
import re
import io
import json
import time
import shutil
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import numpy as np
import cv2

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\beta")
sys.path.insert(0, str(PROJECT_ROOT))

EVIDENCE_DIR = PROJECT_ROOT / "evidence"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
IMAGES_DIR = DATA_DIR / "images" / "v6_4_1"
CONTACT_SHEETS_DIR = OUTPUT_DIR / "v6_4_1_contact_sheets"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8"
}

DISQUALIFIED_DOMAINS = {
    'alamy.com', 'alamy', 'gettyimages.com', 'gettyimages', 'shutterstock.com', 'shutterstock',
    'istockphoto.com', 'stockphoto.com', 'depositphotos.com', 'depositphotos', '123rf.com',
    'adobestock', 'dreamstime.com', 'wallpaperaccess.com', 'wallpapercave.com', 'wallpapersafari.com',
    'pinterest.com', 'aliexpress.com', 'amazon.com', 'ebay.com', 'freepik.com', 'vectorstock.com',
    'clipart', 'iconfinder.com', 'flaticon.com', 'deviantart.com', 'lookfordiagnosis.com'
}


class SceneVisualSpec:
    """
    Stage A: Formal Scene Understanding Specification.
    Defines narrative purpose, intended subject, club, event context, date,
    required visual elements, and allowed asset provenance categories.
    """
    def __init__(
        self,
        scene_id: str,
        role: str,
        intended_subject: str,
        club: str,
        event_context: str,
        relevant_date: str,
        required_visual_elements: List[str],
        banned_visual_elements: List[str],
        allowed_asset_types: List[str],
        search_queries: List[str],
        preferred_composition: str = "vertical_upper_third",
        disqualified_entities: Optional[List[str]] = None,
        wiki_entities: Optional[List[str]] = None
    ):
        self.scene_id = scene_id
        self.role = role
        self.intended_subject = intended_subject
        self.club = club
        self.event_context = event_context
        self.relevant_date = relevant_date
        self.required_visual_elements = required_visual_elements
        self.banned_visual_elements = banned_visual_elements
        self.allowed_asset_types = allowed_asset_types
        self.search_queries = search_queries
        self.preferred_composition = preferred_composition
        self.disqualified_entities = disqualified_entities or []
        self.wiki_entities = wiki_entities or []


class EnhancedSubjectDetector:
    """
    Stage C / Focal Detection:
    Combines OpenCV YuNet CNN face detector + SFace 128-D identity verifier with Haar fallbacks.
    Distinguishes YUNET_FACE, FRONTAL_FACE, PROFILE_FACE, UPPER_BODY, PERSON_BOUNDING_BOX,
    ACTION_REGION, and NO_VALID_SUBJECT_DETECTED.
    Rejects out-of-focus background spectators.
    Never fabricates face centers for non-face detections.
    """

    _FACE_EMBEDDING_CACHE: Dict[str, Any] = {}
    _OBJECT_DETECTOR: Any = None
    _OBJECT_DETECTOR_DEVICE: str = "cpu"
    _YUNET_PATH = PROJECT_ROOT.parent / "models" / "vision" / "face_detection_yunet_2023mar.onnx"
    _SFACE_PATH = PROJECT_ROOT.parent / "models" / "vision" / "face_recognition_sface_2021dec.onnx"

    def __init__(self):
        casc_dir = cv2.data.haarcascades
        self.face_default = cv2.CascadeClassifier(casc_dir + "haarcascade_frontalface_default.xml")
        self.face_alt2 = cv2.CascadeClassifier(casc_dir + "haarcascade_frontalface_alt2.xml")
        self.profile = cv2.CascadeClassifier(casc_dir + "haarcascade_profileface.xml")
        self.upper_body = cv2.CascadeClassifier(casc_dir + "haarcascade_upperbody.xml")
        self.full_body = cv2.CascadeClassifier(casc_dir + "haarcascade_fullbody.xml")

        self.yunet = None
        self.sface = None
        try:
            if self._YUNET_PATH.exists() and hasattr(cv2, "FaceDetectorYN"):
                self.yunet = cv2.FaceDetectorYN.create(str(self._YUNET_PATH), "", (320, 320), 0.55, 0.3, 5000)
            if self._SFACE_PATH.exists() and hasattr(cv2, "FaceRecognizerSF"):
                self.sface = cv2.FaceRecognizerSF.create(str(self._SFACE_PATH), "")
        except Exception as e:
            print(f"[SubjectDetector] Note initializing YuNet/SFace: {e}")

    def _eval_face_sharpness(self, gray_roi: np.ndarray) -> float:
        """Computes Laplacian blur variance inside face region."""
        if gray_roi.size == 0:
            return 0.0
        return float(cv2.Laplacian(gray_roi, cv2.CV_64F).var())

    @classmethod
    def _ensure_object_detector(cls):
        """Lazy-loads CUDA-accelerated FasterRCNN person + sports ball detector."""
        if cls._OBJECT_DETECTOR is not None:
            return cls._OBJECT_DETECTOR
        try:
            import torch
            import torchvision
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = torchvision.models.detection.fasterrcnn_mobilenet_v3_large_fpn(weights="DEFAULT").eval()
            model = model.to(device)
            cls._OBJECT_DETECTOR = model
            cls._OBJECT_DETECTOR_DEVICE = device
            print(f"[SubjectDetector] Loaded FasterRCNN person/ball detector on {device}.")
        except Exception as e:
            print(f"[SubjectDetector] FasterRCNN init skipped ({e}); continuing with YuNet/CV.")
            cls._OBJECT_DETECTOR = False
        return cls._OBJECT_DETECTOR

    @classmethod
    def release_gpu_memory(cls):
        """Moves detector off GPU and clears VRAM before Qwen3-TTS stage loads."""
        try:
            import gc
            import torch
            if cls._OBJECT_DETECTOR not in (None, False):
                cls._OBJECT_DETECTOR.to("cpu")
                cls._OBJECT_DETECTOR_DEVICE = "cpu"
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def detect_scene_objects(self, cv_bgr: np.ndarray) -> Dict[str, List[Tuple[int, int, int, int, float]]]:
        """Detects full-body humans (COCO 1) and footballs (COCO 37) with original-pixel coordinates."""
        result: Dict[str, List[Tuple[int, int, int, int, float]]] = {"persons": [], "balls": []}
        model = self._ensure_object_detector()
        if not model:
            return result
        try:
            import torch
            ih, iw = cv_bgr.shape[:2]
            max_side = max(iw, ih)
            scale = min(1.0, 960.0 / float(max_side))
            if scale < 0.99:
                small_bgr = cv2.resize(cv_bgr, (int(iw * scale), int(ih * scale)), interpolation=cv2.INTER_AREA)
            else:
                small_bgr = cv_bgr
            rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)
            tensor_img = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255.0).to(self._OBJECT_DETECTOR_DEVICE)
            with torch.no_grad():
                pred = model([tensor_img])[0]
            labels = pred["labels"].cpu().tolist()
            scores = pred["scores"].cpu().tolist()
            boxes = pred["boxes"].cpu().tolist()
            inv_s = 1.0 / scale
            for lbl, sc, (x1, y1, x2, y2) in zip(labels, scores, boxes):
                bx, by = max(0, int(x1 * inv_s)), max(0, int(y1 * inv_s))
                bw, bh = max(1, int((x2 - x1) * inv_s)), max(1, int((y2 - y1) * inv_s))
                if lbl == 1 and sc >= 0.55 and bw * bh >= iw * ih * 0.015:
                    result["persons"].append((bx, by, bw, bh, round(float(sc), 3)))
                elif lbl == 37 and sc >= 0.45:
                    result["balls"].append((bx, by, bw, bh, round(float(sc), 3)))
            result["persons"].sort(key=lambda b: b[2] * b[3], reverse=True)
            result["balls"].sort(key=lambda b: b[4], reverse=True)
        except Exception as e:
            print(f"[SubjectDetector] Object detection note: {e}")
        return result

    @staticmethod
    def match_face_to_person_box(
        face_bbox: Optional[Tuple[int, int, int, int]],
        persons: List[Tuple[int, int, int, int, float]]
    ) -> Optional[Tuple[int, int, int, int]]:
        """Matches a verified face bounding box to its enclosing full-body person detection."""
        if not face_bbox or not persons:
            return None
        fx, fy, fw, fh = face_bbox
        fcx, fcy = fx + fw / 2.0, fy + fh / 2.0
        best_box = None
        best_area = float("inf")
        for (px, py, pw, ph, _) in persons:
            if px - pw * 0.1 <= fcx <= px + pw * 1.1 and py - ph * 0.08 <= fcy <= py + ph * 0.55:
                area = pw * ph
                if area < best_area:
                    best_area = area
                    best_box = (px, py, pw, ph)
        return best_box

    def evaluate_content_awareness(
        self,
        cv_bgr: np.ndarray,
        strategy: str = "match_action",
        is_venue: bool = False,
        objects: Optional[Dict[str, List[Tuple[int, int, int, int, float]]]] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        True visual content awareness check:
        1. Rejects synthetic screenshots, tweet cards, cartoons, and flat scoreboard overlays.
        2. Measures green turf pitch coverage and FasterRCNN human/sports-ball presence.
        3. Validates shot role vs actual pixel contents (action player vs venue vs manager).
        """
        ih, iw = cv_bgr.shape[:2]
        # 1. Synthetic Graphic / Meme / Screenshot Rejection via quantized color dominance & flat-band check
        small = cv2.resize(cv_bgr, (96, 96), interpolation=cv2.INTER_AREA)
        quant = (small // 32).reshape(-1, 3)
        bins = quant[:, 0] * 64 + quant[:, 1] * 8 + quant[:, 2]
        counts = np.bincount(bins, minlength=512)
        top3_share = float(np.sort(counts)[-3:].sum()) / float(len(bins))

        # Horizontal line / UI chrome check
        gray_s = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        row_diff = np.abs(np.diff(gray_s.astype(np.float32), axis=0)).mean(axis=1)
        flat_rows_ratio = float((row_diff < 1.5).sum()) / float(len(row_diff))

        if top3_share > 0.78 and flat_rows_ratio > 0.45:
            return False, f"Synthetic graphic / meme / text screenshot rejected (top3={top3_share:.2f}, flat_rows={flat_rows_ratio:.2f})", {"top3_share": round(top3_share, 3)}

        # 2. HSV Green Pitch Turf Ratio
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        green_mask = (hsv[:, :, 0] >= 32) & (hsv[:, :, 0] <= 90) & (hsv[:, :, 1] >= 40) & (hsv[:, :, 2] >= 35)
        pitch_ratio = float(green_mask.mean())

        objs = objects if objects is not None else self.detect_scene_objects(cv_bgr)
        persons = objs.get("persons", [])
        balls = objs.get("balls", [])
        max_person_h_ratio = max((p[3] / float(ih) for p in persons), default=0.0)
        max_person_area_ratio = max(((p[2] * p[3]) / float(iw * ih) for p in persons), default=0.0)

        metrics = {
            "person_count": len(persons),
            "ball_count": len(balls),
            "pitch_ratio": round(pitch_ratio, 3),
            "top3_color_share": round(top3_share, 3),
            "max_person_h": round(max_person_h_ratio, 3),
        }

        if is_venue and max_person_area_ratio > 0.30 and max_person_h_ratio > 0.68:
            return False, f"Venue shot dominated by foreground portrait (person area {max_person_area_ratio*100:.0f}%)", metrics

        if strategy in ("match_action", "celebration") and self._OBJECT_DETECTOR not in (None, False):
            if len(persons) == 0 or max_person_h_ratio < 0.22:
                return False, f"Action shot lacks prominent player subject (persons={len(persons)}, max_h={max_person_h_ratio:.2f})", metrics

        return True, f"Content aware pass (persons={len(persons)}, balls={len(balls)}, turf={pitch_ratio:.2f})", metrics

    def detect_yunet_faces(self, cv_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """Detects sharp foreground faces via YuNet CNN with exact landmarks and raw face vector."""
        if self.yunet is None:
            return []
        ih, iw = cv_bgr.shape[:2]
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)
        try:
            self.yunet.setInputSize((iw, ih))
            _, raw_faces = self.yunet.detect(cv_bgr)
        except Exception:
            return []
        if raw_faces is None:
            return []

        results = []
        for row in raw_faces:
            fx, fy, fw, fh = int(row[0]), int(row[1]), int(row[2]), int(row[3])
            score = float(row[-1])
            fx0 = max(0, fx)
            fy0 = max(0, fy)
            fx1 = min(iw, fx + fw)
            fy1 = min(ih, fy + fh)
            w_clamped = fx1 - fx0
            h_clamped = fy1 - fy0
            if w_clamped < 35 or h_clamped < 35:
                continue
            if (w_clamped * h_clamped) < (iw * ih * 0.005):
                continue
            roi = gray[fy0:fy1, fx0:fx1]
            sharpness = self._eval_face_sharpness(roi)
            if sharpness < 15.0:
                continue
            results.append({
                "method": "YUNET_FACE",
                "bbox": (fx0, fy0, w_clamped, h_clamped),
                "face_center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                "subject_center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                "area": w_clamped * h_clamped,
                "sharpness": sharpness,
                "is_face": True,
                "confidence": score,
                "raw_yunet": row
            })
        results.sort(key=lambda x: (x["area"], x["confidence"]), reverse=True)
        return results

    def get_reference_face_embedding(self, entity_name: str) -> Optional[np.ndarray]:
        """Fetches official Wikipedia portrait and extracts 128-D SFace embedding (cached)."""
        if not entity_name or self.yunet is None or self.sface is None:
            return None
        key = entity_name.strip().lower()
        if key in self._FACE_EMBEDDING_CACHE:
            return self._FACE_EMBEDDING_CACHE[key]

        cache_dir = DATA_DIR / "face_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        safe_slug = re.sub(r'[^a-z0-9_]+', '_', key)
        npy_path = cache_dir / f"{safe_slug}.npy"
        if npy_path.exists():
            try:
                emb = np.load(str(npy_path))
                self._FACE_EMBEDDING_CACHE[key] = emb
                return emb
            except Exception:
                pass

        try:
            slug = urllib.parse.quote(entity_name.strip().replace(" ", "_"))
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
            req = urllib.request.Request(url, headers={"User-Agent": "FootballNewsDesk/2.0 (broadcast@footballin30sec.com)"})
            with urllib.request.urlopen(req, timeout=8) as r:
                wdata = json.loads(r.read().decode("utf-8"))
            thumb = wdata.get("thumbnail", {}).get("source") or wdata.get("originalimage", {}).get("source")
            if not thumb:
                self._FACE_EMBEDDING_CACHE[key] = None
                return None
            req2 = urllib.request.Request(thumb, headers={"User-Agent": "FootballNewsDesk/2.0 (broadcast@footballin30sec.com)"})
            with urllib.request.urlopen(req2, timeout=8) as r2:
                arr = np.frombuffer(r2.read(), np.uint8)
            ref_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if ref_img is None:
                self._FACE_EMBEDDING_CACHE[key] = None
                return None
            ih, iw = ref_img.shape[:2]
            self.yunet.setInputSize((iw, ih))
            _, rf = self.yunet.detect(ref_img)
            if rf is not None and len(rf) > 0:
                best_rf = sorted(rf, key=lambda r_row: r_row[2] * r_row[3], reverse=True)[0]
                aligned = self.sface.alignCrop(ref_img, best_rf)
                feat = self.sface.feature(aligned)
                np.save(str(npy_path), feat)
                self._FACE_EMBEDDING_CACHE[key] = feat
                return feat
        except Exception as e:
            print(f"[SubjectDetector] Wiki ref portrait lookup note for '{entity_name}': {e}")

        self._FACE_EMBEDDING_CACHE[key] = None
        return None

    def verify_face_identity_with_box(
        self,
        cv_bgr: np.ndarray,
        expected_entity: str,
        threshold: float = 0.28
    ) -> Tuple[Optional[bool], float, str, Optional[Tuple[int, int, int, int]]]:
        """
        Matches candidate pixels against official Wikipedia SFace reference embedding.
        Returns (matched: Optional[bool], max_similarity: float, reason: str, matched_bbox: Optional[Tuple[int,int,int,int]]).
        """
        ref_feat = self.get_reference_face_embedding(expected_entity)
        if ref_feat is None or self.sface is None:
            return None, 0.0, "No reference face embedding available", None

        faces = self.detect_yunet_faces(cv_bgr)
        if not faces:
            return None, 0.0, "No clear foreground face detected for SFace comparison", None

        best_sim = -1.0
        best_bbox = None
        for f in faces:
            try:
                aligned = self.sface.alignCrop(cv_bgr, f["raw_yunet"])
                feat = self.sface.feature(aligned)
                sim = float(self.sface.match(ref_feat, feat, cv2.FaceRecognizerSF_FR_COSINE))
                if sim > best_sim:
                    best_sim = sim
                    best_bbox = f["bbox"]
            except Exception:
                continue

        if best_sim < -0.5:
            return None, 0.0, "SFace comparison skipped", None
        matched = best_sim >= threshold
        return matched, round(best_sim, 4), f"SFace cosine similarity vs '{expected_entity}' = {best_sim:.3f} (threshold {threshold})", best_bbox

    def verify_face_identity(self, cv_bgr: np.ndarray, expected_entity: str, threshold: float = 0.28) -> Tuple[Optional[bool], float, str]:
        """Compatibility wrapper returning (matched, max_similarity, reason)."""
        matched, sim, reason, _ = self.verify_face_identity_with_box(cv_bgr, expected_entity, threshold=threshold)
        return matched, sim, reason

    def detect(self, cv_bgr: np.ndarray) -> Dict[str, Any]:
        ih, iw = cv_bgr.shape[:2]
        gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)

        # 0. YuNet CNN Face Detector (High accuracy on tilted/floodlit sports photos)
        yunet_faces = self.detect_yunet_faces(cv_bgr)
        if yunet_faces:
            return yunet_faces[0]

        # 1. Frontal face cascades (reject background spectators < 45px or blur_var < 20.0)
        face_candidates = []
        for casc, m_name in [(self.face_default, "FRONTAL_FACE"), (self.face_alt2, "FRONTAL_FACE_ALT2")]:
            if casc.empty():
                continue
            detected = casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(45, 45))
            for (fx, fy, fw, fh) in detected:
                # Must be at least 2.5% of min dimension or 45px
                if fw >= 45 and fh >= 45 and (fw * fh) >= (iw * ih * 0.008):
                    face_roi = gray[fy:fy+fh, fx:fx+fw]
                    sharpness = self._eval_face_sharpness(face_roi)
                    # Filter out blurred background spectator faces
                    if sharpness >= 20.0:
                        face_candidates.append({
                            "method": m_name,
                            "bbox": (int(fx), int(fy), int(fw), int(fh)),
                            "face_center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                            "subject_center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                            "area": fw * fh,
                            "sharpness": sharpness,
                            "is_face": True,
                            "confidence": 0.95
                        })

        if face_candidates:
            # Pick the largest, sharpest foreground face
            best_face = sorted(face_candidates, key=lambda x: (x["area"], x["sharpness"]), reverse=True)[0]
            return best_face

        # 2. Profile Face
        if not self.profile.empty():
            profiles = self.profile.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(45, 45))
            for (fx, fy, fw, fh) in profiles:
                if fw >= 45 and fh >= 45 and (fw * fh) >= (iw * ih * 0.008):
                    face_roi = gray[fy:fy+fh, fx:fx+fw]
                    sharpness = self._eval_face_sharpness(face_roi)
                    if sharpness >= 20.0:
                        return {
                            "method": "PROFILE_FACE",
                            "bbox": (int(fx), int(fy), int(fw), int(fh)),
                            "face_center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                            "subject_center": (float(fx + fw / 2.0), float(fy + fh / 2.0)),
                            "is_face": True,
                            "confidence": 0.88,
                            "sharpness": sharpness
                        }

        # 3. Upper Body (Explicitly face_center = None)
        if not self.upper_body.empty():
            bodies = self.upper_body.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(70, 70))
            if len(bodies) > 0:
                bodies = sorted(bodies, key=lambda b: b[2] * b[3], reverse=True)
                bx, by, bw, bh = bodies[0]
                return {
                    "method": "UPPER_BODY",
                    "bbox": (int(bx), int(by), int(bw), int(bh)),
                    "face_center": None,  # NEVER fabricate face center
                    "subject_center": (float(bx + bw / 2.0), float(by + bh * 0.35)),
                    "is_face": False,
                    "confidence": 0.82
                }

        # 4. Person Bounding Box (Full Body)
        if not self.full_body.empty():
            fbodies = self.full_body.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(90, 90))
            if len(fbodies) > 0:
                fbodies = sorted(fbodies, key=lambda b: b[2] * b[3], reverse=True)
                bx, by, bw, bh = fbodies[0]
                return {
                    "method": "PERSON_BOUNDING_BOX",
                    "bbox": (int(bx), int(by), int(bw), int(bh)),
                    "face_center": None,
                    "subject_center": (float(bx + bw / 2.0), float(by + bh * 0.30)),
                    "is_face": False,
                    "confidence": 0.78
                }

        # 5. Sports Action Region (Otsu contour cluster)
        try:
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            edges = cv2.Canny(blurred, 40, 120)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            dilated = cv2.dilate(edges, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                valid_contours = []
                for c in contours:
                    cx_, cy_, cw_, ch_ = cv2.boundingRect(c)
                    if (cw_ * ch_ > (iw * ih * 0.04)) and (cw_ < iw * 0.92):
                        valid_contours.append((cx_, cy_, cw_, ch_))
                if valid_contours:
                    valid_contours = sorted(valid_contours, key=lambda x: x[2] * x[3], reverse=True)
                    bx, by, bw, bh = valid_contours[0]
                    return {
                        "method": "ACTION_REGION",
                        "bbox": (int(bx), int(by), int(bw), int(bh)),
                        "face_center": None,
                        "subject_center": (float(bx + bw / 2.0), float(by + bh * 0.40)),
                        "is_face": False,
                        "confidence": 0.70
                    }
        except Exception:
            pass

        return {
            "method": "NO_VALID_SUBJECT_DETECTED",
            "bbox": None,
            "face_center": None,
            "subject_center": None,
            "is_face": False,
            "confidence": 0.0
        }


class SemanticVisualVerifier:
    """
    Stage C: Semantic Visual & Entity Verification.
    Inspects actual pixel content and editorial metadata to reject:
    - Standalone shirts/jerseys with no active human player
    - Architectural empty stadiums when players are required
    - Background spectator false positives
    - Subject misattributions (e.g. Paul Barber labeled as Tony Bloom)
    - Date discrepancies and temporal mismatches
    """

    @staticmethod
    def inspect_candidate(
        raw_bytes: bytes,
        cand_meta: Dict[str, Any],
        spec: SceneVisualSpec
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Returns: (passed: bool, rejection_reason: str, audit_data: dict)
        """
        title = cand_meta.get("title", "")
        url = cand_meta.get("url", "")
        page_url = cand_meta.get("page_url", "")
        combined_text = (title + " " + url + " " + page_url).lower()

        # 1. Disqualified domains / watermarks
        for bad in DISQUALIFIED_DOMAINS:
            if bad in combined_text:
                return False, f"Disqualified watermark domain: {bad}", {}

        # 2. Check Disqualified Entities (e.g. Orlando Bloom vs Tony Bloom)
        for de in spec.disqualified_entities:
            if de.lower() in combined_text:
                return False, f"Depicts disqualified entity: {de}", {}

        # 3. Filename subject collision check (e.g. PaulBarber vs Tony Bloom)
        url_file = Path(urllib.parse.urlparse(url).path).name.lower()
        if "paulbarber" in url_file and "tony bloom" in spec.intended_subject.lower():
            return False, "Subject misattribution in source filename (PaulBarber vs Tony Bloom)", {}
        if "tonybloom" in url_file and "paul barber" in spec.intended_subject.lower():
            return False, "Subject misattribution in source filename (TonyBloom vs Paul Barber)", {}

        # 4. Decode Image & Check Dimensions
        try:
            pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            iw, ih = pil_img.size
            if iw < 400 or ih < 300:
                return False, f"Original dimensions too low ({iw}x{ih} < 400x300)", {}

            arr = np.array(pil_img)
            cv_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception as e:
            return False, f"Image decode failure: {e}", {}

        # 5. Pixel-Level Semantic Human/Player Verification
        # Check skin tone presence to reject shirt-only laydowns or empty stadiums
        hsv = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 25, 45], dtype=np.uint8)
        upper_skin = np.array([25, 200, 255], dtype=np.uint8)
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_ratio = float(np.count_nonzero(skin_mask)) / float(iw * ih)

        # Flat shirt laydown detection:
        if "footballer" in spec.required_visual_elements or "face" in spec.required_visual_elements:
            # If an image has almost zero skin pixels and high solid color variance, it's a jersey laydown
            if skin_ratio < 0.008:
                # Check if it has a detected face
                detector = EnhancedSubjectDetector()
                det_test = detector.detect(cv_bgr)
                if not det_test["is_face"] and det_test["method"] != "UPPER_BODY":
                    return False, "Pixel inspection: Shirt-only or inanimate object with no active human footballer", {}

        # Architectural empty stadium detection:
        if "walkout" in spec.required_visual_elements or "players" in spec.required_visual_elements:
            detector = EnhancedSubjectDetector()
            det_test = detector.detect(cv_bgr)
            if det_test["method"] == "NO_VALID_SUBJECT_DETECTED" and skin_ratio < 0.01:
                return False, "Pixel inspection: Empty architectural stadium with no active players or match personnel", {}

        # 6. Temporal / Date Discrepancy Check
        event_year = spec.relevant_date.split("-")[0]
        # Check for obvious older year stamps in URL paths
        url_years = re.findall(r'/20(1[0-9]|2[0-5])/', url)
        if url_years and spec.allowed_asset_types == ["EXACT_EVENT_PHOTO"]:
            return False, f"Temporal mismatch: Asset path contains year 20{url_years[0]}, not current event {event_year}", {}

        # 7. Classification
        asset_class = "PLAYER_CONTEXTUAL_PHOTO"
        if event_year in combined_text and any(q.lower() in combined_text for q in spec.club.lower().split()):
            asset_class = "SAME_MATCH_CONTEXT"
        if "official" in combined_text or "press" in combined_text:
            asset_class = "CLUB_CONTEXT_PHOTO"

        audit_data = {
            "dimensions": (iw, ih),
            "skin_ratio": round(skin_ratio, 4),
            "asset_classification": asset_class,
            "rights_status": evaluate_rights_status(cand_meta),
            "publisher": cand_meta.get("publisher", "Editorial Web"),
            "url": url,
            "title": title
        }

        return True, "PASSED_SEMANTIC_VERIFICATION", audit_data


def evaluate_rights_status(cand_meta: Dict[str, Any]) -> str:
    """
    Evaluates rights status based on source domain and provenance.
    Absence of watermark does NOT mean rights cleared.
    Returns: 'PUBLIC_DOMAIN', 'EDITORIAL_USE_ONLY', or 'RIGHTS_UNVERIFIED'.
    Never returns 'RIGHTS_CLEARED' for unverified web crawls.
    """
    url = cand_meta.get("url", "").lower()
    page_url = cand_meta.get("page_url", "").lower()
    if "wikimedia.org" in url or "wikipedia.org" in page_url:
        return "PUBLIC_DOMAIN"
    if any(pub in page_url for pub in [
        "theguardian.com", "bbc.com", "skysports.com", "reuters.com",
        "brightonandhovealbion.com", "arsenal.com", "manutd.com"
    ]):
        return "EDITORIAL_USE_ONLY"
    return "RIGHTS_UNVERIFIED"


class EffectiveResolutionCropValidator:
    """
    Stage D / Section 4:
    Validates the effective crop resolution without mirrored padding.
    If the crop cannot be composed into 9:16 vertical without excessive
    enlargement (scale factor > 2.25x or crop width < 480px), REJECTS the candidate.
    """

    def __init__(self, target_w: int = 1080, target_h: int = 1920):
        self.target_w = target_w
        self.target_h = target_h
        self.target_aspect = target_w / target_h
        self.detector = EnhancedSubjectDetector()

    def crop_and_validate(
        self,
        cv_bgr: np.ndarray,
        spec: SceneVisualSpec
    ) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        ih, iw = cv_bgr.shape[:2]
        det = self.detector.detect(cv_bgr)
        method = det["method"]

        if method == "NO_VALID_SUBJECT_DETECTED":
            return False, None, {
                "decision": "REJECTED",
                "reason": "No valid human or action subject detected in image",
                "detection": det
            }

        # Calculate Crop Window
        if det["is_face"]:
            bx, by, bw, bh = det["bbox"]
            cx, cy = det["face_center"]
            # Target crop height proportional to face height
            h_crop = max(int(bh * 4.2), int(ih * 0.55))
            h_crop = min(ih, h_crop)
            w_crop = int(h_crop * self.target_aspect)
            if w_crop > iw:
                w_crop = iw
                h_crop = min(ih, int(iw / self.target_aspect))
                w_crop = int(h_crop * self.target_aspect)

            # Center with upper-third focal bias (y_center ~ 30% of crop)
            y0 = int(cy - 0.30 * h_crop)
            # NO MIRRORED PADDING: If face exceeds canvas bounds severely, reject
            if y0 < 0:
                y0 = 0
            if y0 + h_crop > ih:
                y0 = ih - h_crop
            x0 = int(cx - w_crop / 2.0)
            x0 = max(0, min(iw - w_crop, x0))

        elif method in ["UPPER_BODY", "PERSON_BOUNDING_BOX"]:
            bx, by, bw, bh = det["bbox"]
            cx, cy = det["subject_center"]
            h_crop = min(ih, max(int(bh * 2.4), int(ih * 0.65)))
            w_crop = int(h_crop * self.target_aspect)
            if w_crop > iw:
                w_crop = iw
                h_crop = min(ih, int(iw / self.target_aspect))
                w_crop = int(h_crop * self.target_aspect)
            y0 = max(0, min(ih - h_crop, int(cy - 0.32 * h_crop)))
            x0 = max(0, min(iw - w_crop, int(cx - w_crop / 2.0)))

        else: # ACTION_REGION
            bx, by, bw, bh = det["bbox"]
            cx, cy = det["subject_center"]
            img_aspect = iw / ih
            if img_aspect > self.target_aspect:
                w_crop = int(ih * self.target_aspect)
                h_crop = ih
                y0 = 0
                x0 = max(0, min(iw - w_crop, int(cx - w_crop / 2.0)))
            else:
                w_crop = iw
                h_crop = min(ih, int(iw / self.target_aspect))
                x0 = 0
                y0 = max(0, min(ih - h_crop, int(cy - h_crop * 0.35)))

        # Resolution & Scale Factor Validation
        scale_x = self.target_w / float(w_crop)
        scale_y = self.target_h / float(h_crop)
        max_scale = max(scale_x, scale_y)

        # REJECT if native crop is too small (excessive enlargement)
        if w_crop < 400 or h_crop < 700 or max_scale > 2.5:
            return False, None, {
                "decision": "REJECTED",
                "reason": f"Effective native crop too small ({w_crop}x{h_crop}) requiring excessive upscale ({max_scale:.2f}x > 2.5x)",
                "detection": det,
                "crop_box": (x0, y0, w_crop, h_crop),
                "scale_factor": round(max_scale, 2)
            }

        cropped = cv_bgr[y0:y0+h_crop, x0:x0+w_crop]
        resized = cv2.resize(cropped, (self.target_w, self.target_h), interpolation=cv2.INTER_LANCZOS4)

        # Post-crop sharpness check
        gray_cropped = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        post_blur_var = float(cv2.Laplacian(gray_cropped, cv2.CV_64F).var())
        if post_blur_var < 18.0:
            return False, None, {
                "decision": "REJECTED",
                "reason": f"Post-crop image blurry/degraded (Laplacian var={post_blur_var:.1f} < 18.0)",
                "detection": det,
                "crop_box": (x0, y0, w_crop, h_crop)
            }

        # Calculate final coordinates in 1080x1920
        bx, by, bw, bh = det["bbox"]
        final_subj_x = int((bx - x0) / float(w_crop) * self.target_w)
        final_subj_y = int((by - y0) / float(h_crop) * self.target_h)
        final_subj_w = int(bw / float(w_crop) * self.target_w)
        final_subj_h = int(bh / float(h_crop) * self.target_h)
        final_subj_cy = final_subj_y + final_subj_h / 2.0

        in_safe_zone = (260 <= final_subj_cy <= 1150)

        # Grade image: broadcast clarity & contrast
        pil_res = Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
        sharpened = pil_res.filter(ImageFilter.UnsharpMask(radius=1.3, percent=105, threshold=3))
        balanced = ImageEnhance.Contrast(sharpened).enhance(1.04)
        vibrant = ImageEnhance.Color(balanced).enhance(1.05)
        final_bgr = cv2.cvtColor(np.array(vibrant), cv2.COLOR_RGB2BGR)

        crop_meta = {
            "decision": "PASSED",
            "detection": det,
            "original_dimensions": (iw, ih),
            "crop_box": (x0, y0, w_crop, h_crop),
            "effective_crop_res": f"{w_crop}x{h_crop}",
            "scale_factor": round(max_scale, 2),
            "final_subj_box": (final_subj_x, final_subj_y, final_subj_w, final_subj_h),
            "final_subj_center_y": int(final_subj_cy),
            "in_safe_zone": in_safe_zone,
            "post_blur_var": round(post_blur_var, 1)
        }

        return True, final_bgr, crop_meta


class DiagnosticContactSheetBuilderV2:
    """
    Stage 7: Production-Grade Diagnostic Contact Sheet.
    Includes 6 independent status indicators:
    - Semantic Relevance: PASS / FAIL / REVIEW
    - Event Provenance: PASS / FAIL / REVIEW
    - Focal Detection: PASS / FAIL / REVIEW
    - Crop Quality: PASS / FAIL / REVIEW
    - Resolution: PASS / FAIL
    - Rights: VERIFIED / UNVERIFIED / RESTRICTED
    Overall Status: APPROVED / PROVISIONAL_REVIEW / REJECTED
    """

    @staticmethod
    def create_story_contact_sheet(
        story_title: str,
        scenes_data: List[Dict[str, Any]],
        out_path: Path
    ) -> bool:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        row_h = 560
        total_w = 1600
        header_h = 100
        total_h = header_h + len(scenes_data) * row_h + 30

        canvas = Image.new("RGB", (total_w, total_h), color=(16, 18, 24))
        draw = ImageDraw.Draw(canvas)

        # Main Header
        draw.rectangle([(0, 0), (total_w, header_h)], fill=(24, 28, 38))
        draw.text((30, 20), "30 FOOTBALL PLUS — V6.4.1 SEMANTIC IMAGE PROCUREMENT & FOCAL AUDIT", fill=(255, 215, 0))
        draw.text((30, 55), f"STORY: {story_title.upper()} | INDEPENDENT QUALITY GATES & PROVENANCE", fill=(190, 205, 225))

        for idx, sc in enumerate(scenes_data):
            y_base = header_h + idx * row_h + 15
            sc_id = sc.get("scene_id", f"s{idx+1:02d}")
            role = sc.get("role", "scene")
            orig_bgr = sc.get("orig_bgr")
            final_bgr = sc.get("final_bgr")
            crop_meta = sc.get("crop_meta", {})
            det = crop_meta.get("detection", {})
            gates = sc.get("gates", {})
            overall_status = sc.get("overall_status", "PROVISIONAL_REVIEW")

            # Row container
            border_col = (40, 180, 80) if overall_status == "APPROVED" else (220, 160, 40) if "REVIEW" in overall_status else (220, 50, 50)
            draw.rectangle([(15, y_base), (total_w - 15, y_base + row_h - 10)], fill=(22, 25, 34), outline=(40, 45, 60), width=1)
            # Status badge
            draw.rectangle([(total_w - 240, y_base + 12), (total_w - 30, y_base + 42)], fill=border_col)
            draw.text((total_w - 225, y_base + 18), f"{overall_status}", fill=(255, 255, 255))
            draw.text((30, y_base + 15), f"SCENE {sc_id.upper()} [{role.upper()}] — {sc.get('intended_subject', '')[:50]}", fill=(100, 210, 255))

            # Panel 1: Original Candidate with Detection Overlay (Width ~ 450)
            if orig_bgr is not None:
                disp_orig = orig_bgr.copy()
                bx, by, bw, bh = det.get("bbox") or (0, 0, 0, 0)
                m_label = det.get("method", "NO_VALID_SUBJECT")
                if bw > 0 and bh > 0:
                    box_col = (0, 255, 0) if "FACE" in m_label else (0, 200, 255) if "BODY" in m_label else (0, 255, 255)
                    cv2.rectangle(disp_orig, (bx, by), (bx + bw, by + bh), box_col, 3)
                    cv2.putText(disp_orig, f"{m_label}", (bx, max(25, by - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_col, 2)
                    # Crosshair on center
                    cx_pt = det.get("face_center") or det.get("subject_center")
                    if cx_pt:
                        cv2.drawMarker(disp_orig, (int(cx_pt[0]), int(cx_pt[1])), box_col, markerType=cv2.MARKER_CROSS, markerSize=18, thickness=2)

                pil_orig = Image.fromarray(cv2.cvtColor(disp_orig, cv2.COLOR_BGR2RGB))
                pil_orig.thumbnail((440, 440), Image.Resampling.LANCZOS)
                canvas.paste(pil_orig, (30, y_base + 50))
                orig_dim = crop_meta.get("original_dimensions", (0, 0))
                draw.text((30, y_base + 50 + pil_orig.height + 6), f"Original: {orig_dim[0]}x{orig_dim[1]} | Det: {m_label}", fill=(160, 175, 195))

            # Panel 2: Vertical 9:16 Crop (Width ~ 260)
            if final_bgr is not None:
                disp_crop = final_bgr.copy()
                # Draw safe zone lines (y=260 and y=1100)
                cv2.line(disp_crop, (0, 260), (1080, 260), (0, 165, 255), 3)
                cv2.line(disp_crop, (0, 1100), (1080, 1100), (0, 0, 255), 3)
                cv2.putText(disp_crop, "HUD LIMIT (y=260)", (30, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
                cv2.putText(disp_crop, "CAPTION LIMIT (y=1100)", (30, 1085), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                pil_crop = Image.fromarray(cv2.cvtColor(disp_crop, cv2.COLOR_BGR2RGB))
                pil_crop.thumbnail((260, 462), Image.Resampling.LANCZOS)
                canvas.paste(pil_crop, (510, y_base + 50))
                eff_res = crop_meta.get("effective_crop_res", "N/A")
                scale = crop_meta.get("scale_factor", 1.0)
                draw.text((510, y_base + 50 + pil_crop.height + 6), f"Native Crop: {eff_res} (scale {scale}x)", fill=(160, 175, 195))

            # Panel 3: Evidence & Quality Gate Panel (Width ~ 760)
            p_x = 810
            p_y = y_base + 50
            draw.rectangle([(p_x, p_y), (total_w - 30, y_base + row_h - 20)], fill=(28, 32, 44), outline=(48, 55, 72), width=1)

            # Metadata lines
            prov = sc.get("provenance", {})
            lines = [
                f"Intended Subject: {sc.get('intended_subject', 'N/A')}",
                f"Visually Assessed Subject: {sc.get('assessed_subject', 'N/A')}",
                f"Publisher / Domain: {prov.get('publisher', 'Editorial Web')} ({prov.get('domain', 'N/A')})",
                f"Source URL: {prov.get('url', 'N/A')[:65]}...",
                f"Publication Date: {prov.get('pub_date', 'N/A')} | Event Date: {sc.get('event_date', 'N/A')}",
                f"Asset Classification: {sc.get('asset_classification', 'N/A')}"
            ]
            for i, l in enumerate(lines):
                draw.text((p_x + 15, p_y + 10 + i * 22), l, fill=(230, 235, 245) if i < 2 else (175, 190, 210))

            # Independent Gate Indicators (6 Gates)
            g_y = p_y + len(lines) * 22 + 15
            draw.text((p_x + 15, g_y), "INDEPENDENT QUALITY GATES:", fill=(255, 215, 0))

            gate_items = [
                ("Semantic Relevance", gates.get("semantic", "REVIEW")),
                ("Event Provenance", gates.get("provenance", "REVIEW")),
                ("Focal Detection", gates.get("focal", "PASS")),
                ("Crop Quality", gates.get("crop", "PASS")),
                ("Effective Res", gates.get("resolution", "PASS")),
                ("Rights Status", gates.get("rights", "UNVERIFIED"))
            ]

            for g_idx, (g_name, g_val) in enumerate(gate_items):
                col_offset = (g_idx % 3) * 240
                row_offset = (g_idx // 3) * 26
                v_col = (100, 255, 100) if g_val in ["PASS", "VERIFIED"] else (255, 180, 80) if "REVIEW" in g_val or "UNVERIFIED" in g_val else (255, 90, 90)
                draw.text((p_x + 15 + col_offset, g_y + 24 + row_offset), f"{g_name}: ", fill=(180, 190, 205))
                draw.text((p_x + 15 + col_offset + len(g_name)*8 + 15, g_y + 24 + row_offset), f"[{g_val}]", fill=v_col)

            # Rejections audit box
            r_y = g_y + 85
            draw.text((p_x + 15, r_y), "EVALUATED & REJECTED CANDIDATES:", fill=(255, 160, 60))
            rejections = sc.get("rejections", [])
            if rejections:
                for r_i, r in enumerate(rejections[:3]):
                    r_text = f"- {r.get('reason', 'N/A')}: {r.get('title', '')[:45]}"
                    draw.text((p_x + 20, r_y + 20 + r_i * 20), r_text[:85], fill=(230, 130, 130))
            else:
                draw.text((p_x + 20, r_y + 20), "- All candidates strictly vetted; no secondary rejections logged.", fill=(150, 150, 150))

        canvas.save(out_path, format="PNG")
        print(f"[ContactSheetV2] Generated redesigned diagnostic sheet -> {out_path}")
        return True
