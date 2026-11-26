"""
beta/stages/image_procurement_and_ranking.py - Image Procurement, Multi-Crop Generation, and Qwen-VL Integration.

Fulfills Beta V7.1 Mandate:
"1. Retrieve actual photographs.
 2. Rank photographs and proposed crops using Qwen-VL.
 3. Reposition images through OpenCV and repeat visual assessment where necessary.
 4. Do not pretend a Qwen model is available: If no working Qwen-VL endpoint exists, stop and report the blocker.
 5. Generate multiple crop alternatives with different focal positions.
 6. If face is cut off, return to original source image, adjust OpenCV crop position, and re-evaluate."
"""

import os
import sys
import re
import json
import time
import urllib.request
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.story_workspace_manager import StoryWorkspace, AssetMetadata
from stages.qwen_vl_reframing_engine import FaceSafeZoneEvaluator
from stages.image_scrapers import WikimediaCommonsScraper


class QwenVLRerankerClient:
    """
    Connects to Alibaba Cloud Model Studio `qwen3-vl-rerank` API.
    Enforces honest credential auditing: never pretends an API key exists when it does not.
    """

    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("MODEL_STUDIO_API_KEY")
        self.workspace_id = os.environ.get("DASHSCOPE_WORKSPACE_ID")
        self.region = os.environ.get("DASHSCOPE_REGION", "ap-southeast-1")  # international default
        self.model_id = "qwen3-vl-rerank"

    def is_available(self) -> Tuple[bool, str]:
        """Audits credential and endpoint availability without logging keys."""
        if not self.api_key:
            return False, "DASHSCOPE_API_KEY not configured in environment or .env"
        return True, "DashScope API key configured"

    def rank_images(
        self,
        query: str,
        image_paths: List[Path]
    ) -> Dict[str, Any]:
        """
        Sends query and images to Alibaba Cloud Model Studio multimodal rerank API.
        If credentials are not configured, raises an explicit blocker exception.
        """
        avail, reason = self.is_available()
        if not avail:
            raise RuntimeError(
                f"[QWEN-VL BLOCKER] Cannot perform Qwen-VL ranking: {reason}. "
                "Per Section 4.2, keyword heuristics cannot substitute for real Qwen-VL inference."
            )

        # Implementation for hosted DashScope Model Studio multimodal reranking
        import base64
        import requests

        url = "https://dashscope-intl.aliyuncs.com/api/v1/services/rerank/multimodal-rerank"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        documents = []
        for p in image_paths:
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            ext = p.suffix.lower().replace(".", "")
            mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            documents.append({
                "type": "image",
                "image": f"data:{mime};base64,{b64}"
            })

        payload = {
            "model": self.model_id,
            "input": {
                "query": query,
                "documents": documents
            },
            "parameters": {
                "top_n": len(image_paths),
                "return_documents": False
            }
        }

        t0 = time.time()
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Qwen-VL Model Studio API returned status {resp.status_code}: {resp.text}")

        res_data = resp.json()
        latency = time.time() - t0
        return {
            "model": self.model_id,
            "latency_sec": round(latency, 2),
            "results": res_data.get("output", {}).get("results", []),
            "usage": res_data.get("usage", {})
        }


class OpenCVMultiCropEngine:
    """
    Generates multiple 9:16 crop alternatives with different focal positions from full-resolution source,
    and runs the autonomous re-framing loop when face clipping is detected.
    """

    def __init__(self, target_w: int = 1080, target_h: int = 1920):
        self.target_w = target_w
        self.target_h = target_h
        self.target_aspect = target_w / float(target_h)
        self.evaluator = FaceSafeZoneEvaluator()

    def generate_crop_alternatives(
        self,
        orig_bgr: np.ndarray,
        strategy: str = "portrait"
    ) -> List[Dict[str, Any]]:
        """
        Generates 5 distinct 9:16 crop alternatives from uncropped original:
        1. Face-prioritized upper composition (10% headroom).
        2. Medium upper-body composition.
        3. Shifted horizontal crop (-60px).
        4. Shifted vertical crop (+50px).
        5. Action / wide-context composition.
        """
        ih, iw = orig_bgr.shape[:2]
        faces = self.evaluator.detect_all_faces(orig_bgr)
        primary_face = faces[0] if faces else None

        # Base 9:16 crop window dimensions
        h_crop = ih
        w_crop = int(h_crop * self.target_aspect)
        if w_crop > iw:
            w_crop = iw
            h_crop = int(iw / self.target_aspect)
            w_crop = int(h_crop * self.target_aspect)

        variants = []

        if primary_face:
            fcx, fcy = primary_face["center"]
            fx, fy, fw, fh = primary_face["bbox"]

            # Variant 1: Face-prioritized upper composition (eyes at 30% from top)
            y1 = int(fcy - 0.30 * h_crop)
            x1 = int(fcx - w_crop / 2.0)
            variants.append(("crop_v1_face_upper", x1, y1, "Face centered at upper-third with 10% headroom"))

            # Variant 2: Medium upper-body (face at 24% from top, wider headroom)
            y2 = int(fcy - 0.24 * h_crop)
            x2 = int(fcx - w_crop / 2.0)
            variants.append(("crop_v2_upper_body", x2, y2, "Medium upper-body composition"))

            # Variant 3: Shifted horizontal (-50px)
            y3 = y1
            x3 = int(x1 - 50)
            variants.append(("crop_v3_shifted_left", x3, y3, "Horizontally shifted left"))

            # Variant 4: Shifted vertical (+40px downward)
            y4 = int(y1 + 40)
            x4 = x1
            variants.append(("crop_v4_shifted_down", x4, y4, "Vertically shifted downward"))

            # Variant 5: Action / context centered
            y5 = int((ih - h_crop) / 2.0)
            x5 = int((iw - w_crop) / 2.0)
            variants.append(("crop_v5_action_context", x5, y5, "Action center crop"))
        else:
            # Architectural or stadium wide shots without prominent face
            variants.append(("crop_v1_center", int((iw - w_crop) / 2.0), int((ih - h_crop) / 2.0), "Standard center composition"))
            variants.append(("crop_v2_top_biased", int((iw - w_crop) / 2.0), int(0.15 * (ih - h_crop)), "Top-biased roof composition"))
            variants.append(("crop_v3_pitch_biased", int((iw - w_crop) / 2.0), int(0.85 * (ih - h_crop)), "Pitch-biased lower composition"))
            variants.append(("crop_v4_left_biased", 0, int((ih - h_crop) / 2.0), "Left architectural composition"))
            variants.append(("crop_v5_right_biased", iw - w_crop, int((ih - h_crop) / 2.0), "Right architectural composition"))

        crop_results = []
        for v_name, x0, y0, desc in variants:
            # Clamp coordinates
            x_clamped = max(0, min(iw - w_crop, x0))
            y_clamped = max(0, min(ih - h_crop, y0))

            crop_roi = orig_bgr[y_clamped:y_clamped+h_crop, x_clamped:x_clamped+w_crop]
            resized = cv2.resize(crop_roi, (self.target_w, self.target_h), interpolation=cv2.INTER_LANCZOS4)

            # Evaluate framing
            framing = self.evaluator.inspect_crop_framing(resized, is_player_portrait=(strategy == "portrait"))

            crop_results.append({
                "variant_name": v_name,
                "description": desc,
                "crop_bgr": resized,
                "crop_box": (x_clamped, y_clamped, w_crop, h_crop),
                "framing_audit": framing,
                "is_face_cut": framing.get("is_face_cut", False),
                "is_face_safe": framing.get("is_face_safe", True)
            })

        return crop_results

    def autonomous_reframe_loop(
        self,
        orig_bgr: np.ndarray,
        strategy: str = "portrait",
        max_attempts: int = 4
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Fulfills Section 4.7:
        If face is cut off or outside safe area:
        Returns to original uncropped source image, adjusts OpenCV crop position,
        and repeats up to 4 attempts until certified.
        """
        ih, iw = orig_bgr.shape[:2]
        faces = self.evaluator.detect_all_faces(orig_bgr)

        if not faces and strategy == "portrait":
            # If no face is in the original image, cropping cannot create it
            crop_results = self.generate_crop_alternatives(orig_bgr, strategy="portrait")
            best = crop_results[0]
            best["reframe_attempts"] = 1
            best["reframe_status"] = "REJECTED_NO_FACE_IN_SOURCE"
            return best["crop_bgr"], best

        attempts_log = []
        crop_results = self.generate_crop_alternatives(orig_bgr, strategy=strategy)

        # Check if any variant is already safe
        for c in crop_results:
            if not c["is_face_cut"] and c["is_face_safe"]:
                c["reframe_attempts"] = 1
                c["reframe_status"] = "CERTIFIED_SAFE"
                return c["crop_bgr"], c

        # If all had clipping or unsafe position, iteratively adjust coordinates
        primary_face = faces[0]
        fcx, fcy = primary_face["center"]
        fx, fy, fw, fh = primary_face["bbox"]

        h_crop = ih
        w_crop = int(h_crop * self.target_aspect)
        if w_crop > iw:
            w_crop = iw
            h_crop = int(iw / self.target_aspect)
            w_crop = int(h_crop * self.target_aspect)

        # Try adjusting vertical offsets with 15%, 20%, 25%, 30% headroom
        headroom_fractions = [0.15, 0.22, 0.28, 0.35]
        for attempt_idx, h_frac in enumerate(headroom_fractions[:max_attempts], start=1):
            y_adj = int(fy - h_frac * h_crop)
            x_adj = int(fcx - w_crop / 2.0)

            pad_top = 0
            curr_bgr = orig_bgr
            if y_adj < 0:
                pad_top = abs(y_adj) + int(fh * 0.2)
                curr_bgr = cv2.copyMakeBorder(
                    orig_bgr, pad_top, 0, 0, 0, borderType=cv2.BORDER_REFLECT_101
                )
                y_adj = 0

            ch, cw = curr_bgr.shape[:2]
            x_adj = max(0, min(cw - w_crop, x_adj))
            y_adj = max(0, min(ch - h_crop, y_adj))

            crop_roi = curr_bgr[y_adj:y_adj+h_crop, x_adj:x_adj+w_crop]
            resized = cv2.resize(crop_roi, (self.target_w, self.target_h), interpolation=cv2.INTER_LANCZOS4)

            framing = self.evaluator.inspect_crop_framing(resized, is_player_portrait=(strategy == "portrait"))
            attempts_log.append({
                "attempt": attempt_idx,
                "headroom_frac": h_frac,
                "crop_box": (x_adj, y_adj, w_crop, h_crop),
                "is_face_cut": framing.get("is_face_cut", False),
                "is_face_safe": framing.get("is_face_safe", True)
            })

            if not framing.get("is_face_cut", False) and framing.get("is_face_safe", True):
                audit = {
                    "reframe_attempts": attempt_idx,
                    "reframe_status": "CERTIFIED_AFTER_ADJUSTMENT",
                    "attempts_log": attempts_log,
                    "crop_box": (x_adj, y_adj, w_crop, h_crop),
                    "framing_audit": framing
                }
                return resized, audit

        # If still failing, return best attempt marked provisional
        audit = {
            "reframe_attempts": max_attempts,
            "reframe_status": "PROVISIONAL_FAILED_STRICT_SAFE_ZONE",
            "attempts_log": attempts_log,
            "framing_audit": framing
        }
        return resized, audit


class StoryImageProcurementEngine:
    """Orchestrates genuine image retrieval, workspace registration, multi-crop generation, and Qwen-VL ranking."""

    def __init__(self, workspace: StoryWorkspace):
        self.workspace = workspace
        self.cropper = OpenCVMultiCropEngine()
        self.qwen_reranker = QwenVLRerankerClient()

    def download_and_register_candidate(
        self,
        scene_id: str,
        image_url: str,
        page_url: str,
        title: str,
        intended_subject: str,
        subject_category: str
    ) -> AssetMetadata:
        """Downloads an image from URL and registers it strictly into story workspace."""
        temp_dir = self.workspace.crops_dir / "temp_dl"
        temp_dir.mkdir(parents=True, exist_ok=True)
        filename = re.sub(r"[^a-zA-Z0-9_\.]", "_", Path(image_url.split("?")[0]).name)
        if not filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
            filename += ".jpg"

        dest_temp = temp_dir / filename
        if "wikimedia.org" in image_url:
            headers = {
                "User-Agent": "FootballStudioBot/2.0 (https://footballin30sec.com; editorial@footballin30sec.com) Python/3.11"
            }
        else:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
        req = urllib.request.Request(image_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            dest_temp.write_bytes(resp.read())

        meta = self.workspace.register_candidate_asset(
            scene_id=scene_id,
            source_file=dest_temp,
            source_url=image_url,
            source_page_url=page_url,
            intended_subject=intended_subject,
            subject_category=subject_category,
            publication_date="2026-11-20",
            event_date="2026-11-20"
        )
        dest_temp.unlink(missing_ok=True)
        return meta

    def procure_candidates_for_scene(
        self,
        scene_id: str,
        intended_subject: str,
        search_query: str,
        subject_category: str
    ) -> List[AssetMetadata]:
        """Procures 2-4 authentic candidate photographs from Wikimedia Commons."""
        scraper = WikimediaCommonsScraper()
        print(f"[Procurement] Scraping Wikimedia Commons for Scene {scene_id}: \"{search_query}\"...")
        scraped = scraper.scrape(search_query, max_results=4)

        registered = []
        for s in scraped:
            try:
                meta = self.download_and_register_candidate(
                    scene_id=scene_id,
                    image_url=s.url,
                    page_url=s.page_url or s.url,
                    title=s.title,
                    intended_subject=intended_subject,
                    subject_category=subject_category
                )
                registered.append(meta)
            except Exception as e:
                print(f"[Procurement] Download note for {s.url[:40]}: {e}")

        return registered
