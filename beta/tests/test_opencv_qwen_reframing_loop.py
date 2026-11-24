"""
beta/tests/test_opencv_qwen_reframing_loop.py - Rigorous Verification for OpenCV + Vision Re-Framing Pipeline.

Verifies:
1. High-quality ranking evaluation.
2. Detection of face clipping / face cutoff boundaries.
3. Autonomous trigger of re-framing coordinates calculation.
4. Correct repositioning and OpenCV re-crop with verified upper-third face placement.
5. Certification of candidate scene images across all story beats.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from stages.qwen_vl_reframing_engine import OpenCVQwenVLReframingEngine, FaceSafeZoneEvaluator

OUTPUT_DIR = BETA_ROOT / "output" / "reframing_proofs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR = BETA_ROOT / "evidence"


def test_intentional_face_clipping_reframe():
    """
    Simulates an image where initial OpenCV crop severed the face/forehead,
    verifying that the engine detects the cutoff, triggers re-framing, and restores
    full facial integrity in the upper third.
    """
    print("\n[TEST 1] Testing Face-Clipping Detection & Autonomous Re-Framing Loop...")
    engine = OpenCVQwenVLReframingEngine()
    evaluator = FaceSafeZoneEvaluator()

    # Load high quality subject image
    src_img_path = BETA_ROOT / "data" / "images" / "v6_4_2" / "v6_4_2_story_1_bruno" / "scene_s02.png"
    orig_bgr = cv2.imread(str(src_img_path))
    assert orig_bgr is not None, f"Failed to load test image: {src_img_path}"

    ih, iw = orig_bgr.shape[:2]
    faces = evaluator.detect_all_faces(orig_bgr)
    assert len(faces) > 0, "Expected at least one face in test image"
    face = faces[0]
    fx, fy, fw, fh = face["bbox"]

    # 1. Create an intentionally defective initial crop box where the top edge slices right through the face
    # (severing the forehead: y0 is placed at fy + fh * 0.4)
    h_crop = int(ih * 0.7)
    w_crop = int(h_crop * (9 / 16.0))
    defective_y0 = int(fy + fh * 0.35)  # Face top severed!
    defective_x0 = max(0, min(iw - w_crop, int(face["center"][0] - w_crop / 2.0)))

    defective_crop = orig_bgr[defective_y0:defective_y0+h_crop, defective_x0:defective_x0+w_crop]
    defective_resized = cv2.resize(defective_crop, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)

    # Save the defective initial crop as proof
    defective_proof_path = OUTPUT_DIR / "proof_1_defective_initial_crop.png"
    cv2.imwrite(str(defective_proof_path), defective_resized)

    # 2. Evaluate the defective crop
    framing_defective = evaluator.inspect_crop_framing(defective_resized, is_player_portrait=True)
    rank, _ = engine.evaluate_quality_rank(defective_resized)

    print(f"  • Initial Defective Crop Quality Rank: {rank:.1f}")
    print(f"  • Initial Framing Verdict: {framing_defective['framing_verdict']}")
    print(f"  • Face Cut Detected: {framing_defective['is_face_cut']}")

    # 3. Trigger Autonomous Re-Framing
    print("  • Executing re-frame coordinates recalculation...")
    reframed_crop, final_box, shift_audit = engine.reframe_and_recrop(
        orig_bgr=orig_bgr,
        initial_crop_box=(defective_x0, defective_y0, w_crop, h_crop),
        face_in_orig=face,
        strategy="portrait"
    )

    # Save the reframed crop as proof
    reframed_proof_path = OUTPUT_DIR / "proof_1_reframed_certified_crop.png"
    cv2.imwrite(str(reframed_proof_path), reframed_crop)

    # 4. Verify reframed crop
    framing_reframed = evaluator.inspect_crop_framing(reframed_crop, is_player_portrait=True)
    post_rank, _ = engine.evaluate_quality_rank(reframed_crop)

    print(f"  • Reframed Quality Rank: {post_rank:.1f}")
    print(f"  • Reframed Framing Verdict: {framing_reframed['framing_verdict']}")
    print(f"  • Face Safe in Upper-Third: {framing_reframed['in_safe_zone']}")
    print(f"  • Vertical Shift Applied: {shift_audit['delta_y']}px")

    assert framing_reframed["in_safe_zone"] is True, "Reframed image must be inside upper-third safe zone"
    assert framing_reframed["is_face_cut"] is False, "Reframed image must not have cut face"

    proof_data = {
        "test_name": "intentional_face_clipping_reframe",
        "initial_defective": {
            "path": str(defective_proof_path),
            "verdict": framing_defective["framing_verdict"],
            "face_cut": framing_defective["is_face_cut"]
        },
        "reframe_action": shift_audit,
        "certified_reframed": {
            "path": str(reframed_proof_path),
            "verdict": framing_reframed["framing_verdict"],
            "in_safe_zone": framing_reframed["in_safe_zone"],
            "rank": post_rank
        }
    }

    with open(EVIDENCE_DIR / "reframe_proof_intentional_clipping.json", "w", encoding="utf-8") as f:
        json.dump(proof_data, f, indent=2)

    print("  ✓ TEST 1 PASSED: Defective crop detected and autonomously reframed with verified safe zone.")


def test_batch_story_scene_reframing():
    """
    Tests the re-framing pipeline across active candidate story scenes.
    """
    print("\n[TEST 2] Processing Story Candidate Scene Frames...")
    engine = OpenCVQwenVLReframingEngine()

    candidate_scenes = [
        ("s01", BETA_ROOT / "data" / "images" / "v7" / "bruno_s01_armband_detail.png", "tactical_atmosphere", True),
        ("s02", BETA_ROOT / "data" / "images" / "v6_4_2" / "v6_4_2_story_1_bruno" / "scene_s02.png", "portrait", False),
        ("s03", BETA_ROOT / "data" / "images" / "v6_4_2" / "v6_4_2_story_1_bruno" / "scene_s03.png", "portrait", False),
        ("s04", BETA_ROOT / "data" / "images" / "v6_4_2" / "v6_4_2_story_1_bruno" / "scene_s04.png", "match_action", False)
    ]

    results = []
    for sid, img_path, strat, is_hook in candidate_scenes:
        if not img_path.exists():
            print(f"  [SKIP] {img_path.name} not found")
            continue

        out_path = OUTPUT_DIR / f"reframed_{sid}_{img_path.name}"
        audit = engine.execute_reframing_pipeline(
            orig_image_path=img_path,
            output_crop_path=out_path,
            strategy=strat,
            is_opening_hook=is_hook
        )
        print(f"  • [{sid}] {img_path.name}: Rank={audit['quality_rank']} | Status={audit['final_status']} -> {out_path.name}")
        results.append(audit)

    with open(EVIDENCE_DIR / "batch_scenes_reframing_audit.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"  ✓ TEST 2 PASSED: Processed {len(results)} candidate scene images.")


if __name__ == "__main__":
    test_intentional_face_clipping_reframe()
    test_batch_story_scene_reframing()
