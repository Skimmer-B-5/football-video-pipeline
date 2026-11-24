"""
# BETA V6.4: REFRESH CONTACT SHEETS & MANIFEST
"""

import sys
import os
import json
import shutil
from pathlib import Path
import cv2
import numpy as np

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\beta")
sys.path.insert(0, str(PROJECT_ROOT))

from stages.image_procurement_engine import (
    DiagnosticContactSheetBuilder,
    OpenCVFocalFramingEngine
)

ARTIFACT_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
CONTACT_SHEETS_DIR = PROJECT_ROOT / "output" / "v6_4_contact_sheets"
MANIFEST_FILE = EVIDENCE_DIR / "v6_4_scene_image_manifest.json"

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    manifest = json.load(f)

framing = OpenCVFocalFramingEngine(target_w=1080, target_h=1920)

for st in manifest:
    s_id = st["story_id"]
    s_title = st["title"]
    contact_sheet_scenes = []

    for sc in st["scenes"]:
        img_rel = sc["selected_image_file"]
        img_path = PROJECT_ROOT / img_rel
        crop_bgr = cv2.imread(str(img_path))

        cm = sc["crop_metadata"]
        det = cm.get("detection", {})
        fx, fy, fw, fh = cm.get("final_subj_box", (0, 0, 0, 0))
        cy = fy + fh / 2.0
        cm["final_subj_center_y"] = int(cy)
        cm["in_safe_zone"] = (260 <= cy <= 1100) if det.get("is_face", False) else True

        contact_sheet_scenes.append({
            "scene_id": sc["scene_id"],
            "role": sc["role"],
            "subject_title": sc["subject_title"],
            "subject_name": sc["subject_name"],
            "event_context": sc["event_context"],
            "orig_bgr": crop_bgr,
            "final_bgr": crop_bgr,
            "crop_meta": cm,
            "metrics": sc["metrics"],
            "provenance": sc["provenance"],
            "rejections": sc.get("rejections", [])
        })

    cs_path = CONTACT_SHEETS_DIR / f"v6_4_contact_sheet_{s_id}.png"
    DiagnosticContactSheetBuilder.create_story_contact_sheet(
        story_title=s_title,
        scenes_data=contact_sheet_scenes,
        out_path=cs_path
    )
    artifact_cs = ARTIFACT_DIR / cs_path.name
    shutil.copyfile(cs_path, artifact_cs)
    print(f"Refreshed contact sheet -> {cs_path.name}")

with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("Manifest and contact sheets successfully updated!")
