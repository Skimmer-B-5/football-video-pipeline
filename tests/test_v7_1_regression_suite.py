"""
beta/tests/test_v7_1_regression_suite.py - Exhaustive Regression Tests for Beta V7.1.

Verifies:
1. Cross-Story Asset Contamination Protection (Deliberate V7 contamination failure reproduction and blocking).
2. Story Workspace Isolation & SHA-256 Hash Validation.
3. Strict Approval State Machine Gate Transitions & Invalidation.
4. Dual Script Synchronization & Secrecy Rules.
5. Remotion Renderer InputProps Validation (Unapproved or mismatching assets blocked).
"""

import os
import sys
import json
import time
import shutil
import hashlib
import re
from contextlib import contextmanager

@contextmanager
def raises(expected_exception, match=None):
    try:
        yield
    except expected_exception as e:
        if match and not re.search(match, str(e)):
            raise AssertionError(f"Pattern '{match}' does not match exception message: '{str(e)}'")
        return
    except Exception as e:
        raise AssertionError(f"Expected {expected_exception.__name__}, but caught {type(e).__name__}: {e}")
    raise AssertionError(f"Expected {expected_exception.__name__} but no exception was raised")
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.story_workspace_manager import StoryWorkspace, AssetMetadata, ContaminationError
from stages.approval_state_machine import ApprovalStateMachine, PipelineState
from stages.dual_script_architecture import DualScriptDirector
from stages.reporter_voice_audition import AUDITION_PASSAGE, VOICE_CANDIDATES
from stages.remotion_renderer import prepare_remotion_props


def test_story_isolation_rejects_bruno_in_endrick_workspace():
    """
    Directly reproduces the V7 failure:
    Injecting a Bruno Fernandes image into an Endrick workspace must be blocked.
    """
    ws_endrick = StoryWorkspace("test_endrick_milan", "run_test_01")
    
    # Create fake Bruno asset with story_id="bruno_fernandes"
    dummy_img = ws_endrick.candidates_dir / "bruno_photo.png"
    dummy_img.write_bytes(b"FAKE_BRUNO_FERNANDES_IMAGE_BYTES_12345")
    actual_sha = hashlib.sha256(dummy_img.read_bytes()).hexdigest()

    contaminated_asset = AssetMetadata(
        story_id="bruno_fernandes",  # MISMATCH!
        run_id="run_test_01",
        script_version="v7.1",
        scene_id="S02",
        asset_id="bruno_fernandes_S02_leak",
        candidate_id="cand_bruno_01",
        source_url="https://example.com/bruno.jpg",
        source_page_url="https://example.com/bruno",
        original_filename="bruno_photo.png",
        sha256=actual_sha,
        publication_date="2026-11-20",
        event_date="2026-11-20",
        approval_status="APPROVED",
        subject_category="portrait",
        intended_subject="Bruno Fernandes",
        relative_path="assets/candidates/bruno_photo.png"
    )

    with raises(ContaminationError, match=r"\[STORY CONTAMINATION\]"):
        ws_endrick.validate_asset(contaminated_asset, expected_scene_id="S02")


def test_story_isolation_rejects_pochettino_in_unrelated_story():
    """
    Directly reproduces V7 Pochettino contamination in Scene S04:
    Mauricio Pochettino portrait from previous session must be blocked.
    """
    ws = StoryWorkspace("test_endrick_milan", "run_test_02")
    dummy_img = ws.candidates_dir / "pochettino.png"
    dummy_img.write_bytes(b"FAKE_POCHETTINO_MANAGER_PHOTO")
    sha = hashlib.sha256(dummy_img.read_bytes()).hexdigest()

    pochettino_asset = AssetMetadata(
        story_id="v6_4_2_story_1_bruno",  # Outdated story ID!
        run_id="run_previous_session",
        script_version="v6.4.2",
        scene_id="S04",
        asset_id="pochettino_manager_portrait",
        candidate_id="cand_poch_01",
        source_url="https://example.com/poch.jpg",
        source_page_url="https://example.com/poch",
        original_filename="pochettino.png",
        sha256=sha,
        publication_date="2026-10-15",
        event_date="2026-10-15",
        approval_status="APPROVED",
        subject_category="managerial",
        intended_subject="Mauricio Pochettino",
        relative_path="assets/candidates/pochettino.png"
    )

    with raises(ContaminationError, match=r"\[STORY CONTAMINATION\]"):
        ws.validate_asset(pochettino_asset, expected_scene_id="S04")


def test_sha256_mismatch_blocks_asset():
    """
    Verifies that if an image file is altered or swapped on disk,
    hash validation fails and blocks the operation.
    """
    ws = StoryWorkspace("test_endrick_milan", "run_test_03")
    img_file = ws.candidates_dir / "endrick_action.png"
    img_file.write_bytes(b"GENUINE_ENDRICK_RAW_BYTES")

    tampered_asset = AssetMetadata(
        story_id="test_endrick_milan",
        run_id="run_test_03",
        script_version="v7.1",
        scene_id="S03",
        asset_id="endrick_s03",
        candidate_id="cand_s03",
        source_url="https://example.com/endrick.jpg",
        source_page_url="https://example.com/endrick",
        original_filename="endrick_action.png",
        sha256="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",  # FAKE HASH
        publication_date="2026-11-20",
        event_date="2026-11-20",
        approval_status="APPROVED",
        subject_category="match_action",
        intended_subject="Endrick",
        relative_path="assets/candidates/endrick_action.png"
    )

    with raises(ContaminationError, match=r"\[HASH INTEGRITY FAILURE\]"):
        ws.validate_asset(tampered_asset, expected_scene_id="S03")


def test_missing_asset_in_manifest_blocks_resolution():
    """Unapproved scene or missing manifest entry raises ContaminationError."""
    ws = StoryWorkspace("test_endrick_milan", "run_test_04")
    with raises(ContaminationError, match=r"Scene 'S05' has no approved asset in manifest"):
        ws.resolve_scene_asset("S05")


def test_approval_state_machine_sequential_gates():
    """Verifies that approval states advance strictly in sequence."""
    ws = StoryWorkspace("test_endrick_milan", f"run_test_05_{int(time.time()*1000)}")
    sm = ApprovalStateMachine(ws.state_dir / "approval_state.json", ws.story_id, ws.run_id)

    assert sm.current_state == PipelineState.STORY_SELECTED

    # Valid step
    sm.transition_to(PipelineState.DUAL_SCRIPT_GENERATED, "author", "Script drafted")
    assert sm.current_state == PipelineState.DUAL_SCRIPT_GENERATED

    # Invalid jump directly to RENDER_READY must fail!
    with raises(ValueError, match=r"\[INVALID STATE TRANSITION\]"):
        sm.transition_to(PipelineState.RENDER_READY, "hacker", "Attempted render bypass")

    # Correct sequential progression
    sm.transition_to(PipelineState.SCRIPT_REVIEW_PENDING, "telegram", "Dispatched to phone")
    sm.transition_to(PipelineState.SCRIPT_APPROVED, "owner_phone", "Approved by user")
    assert sm.script_approved_by == "owner_phone"

    sm.transition_to(PipelineState.IMAGE_PROCUREMENT, "agent", "Procuring assets")
    sm.transition_to(PipelineState.QWEN_VL_RANKING, "agent", "Ranking candidates")
    sm.transition_to(PipelineState.OPENCV_CROP_OPTIMISATION, "agent", "Cropping 9:16")
    sm.transition_to(PipelineState.VISUAL_REVIEW_PENDING, "telegram", "Dispatched contact sheet")
    sm.transition_to(PipelineState.VISUALS_APPROVED, "owner_phone", "Visuals approved by user")
    assert sm.visuals_approved_by == "owner_phone"

    sm.transition_to(PipelineState.VOICE_AUDITION_PENDING, "telegram", "Dispatched auditions")
    sm.transition_to(PipelineState.VOICE_APPROVED, "owner_phone", "Voice Candidate A approved")
    assert sm.voice_approved_by == "owner_phone"

    sm.transition_to(PipelineState.RENDER_READY, "system", "All gates cleared")
    assert sm.assert_render_permitted() is True


def test_script_invalidation_resets_downstream_approvals():
    """Modifying the script invalidates visual, voice, and render readiness."""
    ws = StoryWorkspace("test_endrick_milan", f"run_test_06_{int(time.time()*1000)}")
    sm = ApprovalStateMachine(ws.state_dir / "approval_state.json", ws.story_id, ws.run_id)

    sm.transition_to(PipelineState.DUAL_SCRIPT_GENERATED, "author", "Draft")
    sm.transition_to(PipelineState.SCRIPT_REVIEW_PENDING, "telegram", "Sent")
    sm.transition_to(PipelineState.SCRIPT_APPROVED, "owner", "Approved")

    # Invalidate due to editorial change
    sm.invalidate_downstream_on_script_change(new_script_version="v7.2", actor="editor")

    assert sm.current_state == PipelineState.DUAL_SCRIPT_GENERATED
    assert sm.script_approved_by is None
    assert sm.visuals_approved_by is None
    assert sm.voice_approved_by is None

    with raises(ValueError, match=r"\[RENDER BLOCKED\]"):
        sm.assert_render_permitted()


def test_dual_script_synchronization_and_secrecy():
    """Verifies that Script A and Script B share identical beat IDs and follow 4s secrecy."""
    director = DualScriptDirector()
    script_a, script_b = director.generate_endrick_dual_scripts()

    beats_a = script_a["beats"]
    beats_b = script_b["image_beats"]

    assert len(beats_a) == len(beats_b) == 5

    # Check Beat IDs align
    for idx in range(5):
        assert beats_a[idx]["beat_id"] == beats_b[idx]["beat_id"]
        assert beats_a[idx]["estimated_duration_sec"] == beats_b[idx]["allocated_duration_sec"]

    # Beat S01 must enforce opening secrecy
    s01_a = beats_a[0]
    s01_b = beats_b[0]
    assert s01_a["secrecy_requirements"]["player_name_hidden"] is True
    assert "Endrick" not in s01_a["spoken_dialogue"]
    assert "CONCEALED" in s01_b["face_visibility_requirement"]

    # Beat S02 reveals Endrick explicitly in spoken dialogue
    s02_a = beats_a[1]
    s02_b = beats_b[1]
    assert "Endrick" in s02_a["spoken_dialogue"], "Endrick must be explicitly named in S02 spoken dialogue"
    assert "nineteen" not in s02_a["spoken_dialogue"]
    assert "MANDATORY" in s02_b["face_visibility_requirement"]

    # Beat S04 includes Nov 23 official left-leg muscle injury and no official return date per V7.1.6.3
    s04_a = beats_a[3]
    assert "left-leg muscle injury" in s04_a["spoken_dialogue"] or "left-adductor injury" in s04_a["spoken_dialogue"]
    assert "no official return date" in s04_a["spoken_dialogue"] or "recovery timetable" in s04_a["spoken_dialogue"]


def test_voice_audition_passages_are_identical():
    """All 3 voice candidates must speak the exact same audition passage conforming to V7.1.2."""
    assert len(VOICE_CANDIDATES) == 3
    # Check all candidates have distinct IDs and identical passage requirement
    ids = [c["id"] for c in VOICE_CANDIDATES]
    assert len(set(ids)) == 3
    # V7.1.2 word count must be between 55 and 65 words
    assert 55 <= len(AUDITION_PASSAGE.split()) <= 65
    assert "sixty-million-euro" in AUDITION_PASSAGE
    # Endrick age verified as 20
    assert "twenty-year-old" in AUDITION_PASSAGE
    assert "nineteen" not in AUDITION_PASSAGE
    # Nov 23 right-thigh injury included
    assert "right-thigh injury" in AUDITION_PASSAGE
    # Conflicting minutes and cliches absent
    assert "one hundred and fifty-five minutes" not in AUDITION_PASSAGE
    assert "Tell us below" not in AUDITION_PASSAGE


def test_remotion_props_with_workspace_enforces_manifest():
    """Remotion input props must resolve only approved workspace assets."""
    ws = StoryWorkspace("test_endrick_milan", "run_test_07")
    
    # Approved S01 asset
    img_file = ws.approved_dir / "S01_approved.png"
    img_file.write_bytes(b"APPROVED_S01_PIXELS")
    sha = hashlib.sha256(img_file.read_bytes()).hexdigest()

    meta = AssetMetadata(
        story_id="test_endrick_milan",
        run_id="run_test_07",
        script_version="v7.1",
        scene_id="S01",
        asset_id="test_endrick_milan_S01_approved",
        candidate_id="cand_s01",
        source_url="https://example.com/s01.jpg",
        source_page_url="https://example.com",
        original_filename="S01_approved.png",
        sha256=sha,
        publication_date="2026-11-20",
        event_date="2026-11-20",
        approval_status="APPROVED",
        subject_category="atmosphere",
        intended_subject="Bernabeu",
        relative_path="assets/approved/S01_approved.png"
    )
    ws.update_visual_manifest("S01", meta)

    script_data = {
        "story": {"headline": "ENDRICK MILAN"},
        "scenes": [
            {"scene_id": "S01", "role": "hook", "narration": "A sixty million transfer.", "duration_sec": 5.0}
        ]
    }

    props = prepare_remotion_props(script_data, ws.base_dir, fps=30.0, workspace=ws)
    assert props["story_id"] == "football_short"
    assert len(props["scenes"]) == 1
    assert props["scenes"][0]["scene_id"] == "S01"
    assert props["scenes"][0]["image_path"].startswith("data:image/png;base64,")


def test_remotion_props_blocks_unapproved_scene_in_workspace():
    """If a scene has no approved asset in workspace manifest, Remotion props creation fails."""
    ws = StoryWorkspace("test_endrick_milan", "run_test_08")
    script_data = {
        "story": {"headline": "ENDRICK MILAN"},
        "scenes": [
            {"scene_id": "S02", "role": "reveal", "narration": "That player is Endrick.", "duration_sec": 5.0}
        ]
    }
    with raises(ContaminationError, match=r"Scene 'S02' has no approved asset in manifest"):
        prepare_remotion_props(script_data, ws.base_dir, fps=30.0, workspace=ws)


def test_timing_engine_rejects_single_pause_when_comma_and_period_present():
    """
    Regression test for Beta V7.1.6.2:
    A sentence containing both a comma and a period (e.g. S04:
    'Now a left-adductor injury adds another complication, with no official return date.')
    MUST receive a pause allowance of 0.50s (0.18s comma + 0.32s period), NOT 0.32s.
    The timing engine must calculate 6.15s duration and reject an allowance of 0.32 seconds (5.97s).
    """
    from stages.dual_script_architecture import calculate_spoken_duration, expand_spoken_tokens

    s04_text = "Now a left-adductor injury adds another complication, with no official return date."
    w_cnt, t_cnt, duration = calculate_spoken_duration(s04_text, wpm=138.0)

    # 13 spoken tokens: speech = 13/138*60 = 5.6522s
    speech_sec = (t_cnt / 138.0) * 60.0

    # If pause was incorrectly 0.32s (terminal period only, ignoring comma):
    incorrect_duration = round(speech_sec + 0.32, 2)
    assert incorrect_duration == 5.97, f"Expected incorrect duration to equal 5.97s, got {incorrect_duration}"

    # Correct pause is 0.50s (0.18s comma + 0.32s period):
    correct_duration = round(speech_sec + 0.50, 2)
    assert correct_duration == 6.15, f"Expected correct duration to equal 6.15s, got {correct_duration}"

    # Verification:
    assert duration == 6.15, f"Expected timing engine duration 6.15s, got {duration}s"
    assert duration != 5.97, "Timing engine incorrectly allowed 0.32s pause for sentence with both comma and period"


def test_s05_displayed_duration_and_unrounded_master_duration():
    """
    Regression test for Beta V7.1.6.3:
    1. S05 displayed duration must be exactly 5.10s (exact: 11 / 138 * 60 + 0.32 = 5.1026087s).
    2. Master cumulative duration must derive from unrounded summation, yielding 30.15s.
    3. Summing rounded display durations (5.28 + 7.46 + 6.15 + 6.15 + 5.10 = 30.14) produces
       a 1-cent truncation error. The system MUST NOT calculate cumulative time by summing
       rounded display values.
    """
    from stages.dual_script_architecture import DualScriptDirector, calculate_spoken_duration_exact

    director = DualScriptDirector()
    script_a, script_b = director.generate_endrick_dual_scripts()

    beats_a = script_a["beats"]
    s05_a = beats_a[4]

    # Verify S05 exact calculation
    w_cnt, t_cnt, exact_dur, disp_dur = calculate_spoken_duration_exact(s05_a["spoken_dialogue"])
    assert w_cnt == 11, f"Expected 11 written words in S05, got {w_cnt}"
    assert t_cnt == 11, f"Expected 11 spoken tokens in S05, got {t_cnt}"
    assert round(exact_dur, 7) == round(11 / 138.0 * 60.0 + 0.32, 7)
    assert disp_dur == 5.10, f"Expected S05 displayed duration to be 5.10s, got {disp_dur}s"
    assert s05_a["estimated_duration_sec"] == 5.10

    # Verify S05 cumulative boundaries and master duration
    assert s05_a["start_time_sec"] == 25.04
    assert s05_a["end_time_sec"] == 30.15
    assert script_a["metadata"]["total_duration_sec"] == 30.15
    assert script_b["metadata"]["total_duration_sec"] == 30.15

    # Verify that summing rounded values does NOT equal master duration
    rounded_sum = round(sum(b["estimated_duration_sec"] for b in beats_a), 2)
    assert rounded_sum == 30.14, f"Sum of rounded display values must equal 30.14, got {rounded_sum}"
    assert script_a["metadata"]["total_duration_sec"] != rounded_sum, (
        "Master duration must derive from unrounded values (30.15s), not rounded sum (30.14s)"
    )


def test_v7_1_6_3_evidence_dossier_reconciliation():
    """
    Verifies that evidence_dossier.json contains all 6 verified sources,
    with exact publication dates, URLs, domains, and claims.
    """
    ws = StoryWorkspace("endrick_milan", "run_v7_1")
    dossier_file = ws.manifests_dir / "evidence_dossier.json"
    assert dossier_file.exists(), "evidence_dossier.json must exist in manifests directory"

    dossier = json.loads(dossier_file.read_text(encoding="utf-8"))
    assert dossier["version"] == "v7.1.6.3"
    assert dossier["player_profile"]["verified_age_as_of_2026_11_24"] == 20

    sources = {s["source_id"]: s for s in dossier["sources"]}
    assert len(sources) == 6, f"Expected 6 sources in dossier, found {len(sources)}"

    # 1. Cadena SER Nov 23 - formal offer
    assert "src_cadena_ser_nov23" in sources
    ser_23 = sources["src_cadena_ser_nov23"]
    assert ser_23["publication_date"] == "2026-11-23"
    assert "70-millones" in ser_23["url"]

    # 2. Cadena SER Nov 24 - willing to offer / Mourinho opposes
    assert "src_cadena_ser_nov24" in sources
    ser_24 = sources["src_cadena_ser_nov24"]
    assert ser_24["publication_date"] == "2026-11-24"
    assert "setenta-kilos" in ser_24["url"]

    # 3. Corriere dello Sport Nov 16
    assert "src_corriere_dello_sport_nov16" in sources
    corriere = sources["src_corriere_dello_sport_nov16"]
    assert corriere["publication_date"] == "2026-11-16"
    assert "16-152628185" in corriere["url"]

    # 4. TNT Sports Brazil (MilanReports Nov 18)
    assert "src_tnt_sports_milanreports_nov18" in sources
    tnt = sources["src_tnt_sports_milanreports_nov18"]
    assert tnt["publication_date"] == "2026-11-18"
    assert "milan-prepare-70m-offer-endrick" in tnt["url"]

    # 5. Real Madrid Medical Bulletin Nov 23
    assert "src_official_rm_medical_nov23" in sources
    med = sources["src_official_rm_medical_nov23"]
    assert med["publication_date"] == "2026-11-23"
    assert "parte-medico-de-endrick-23-11-2026" in med["url"]

    # 6. Real Madrid Training Report Nov 23 (indoor)
    assert "src_official_rm_training_nov23" in sources
    train = sources["src_official_rm_training_nov23"]
    assert train["publication_date"] == "2026-11-23"
    assert "el-equipo-se-esta-entrenando-23-11-2026" in train["url"]


def test_image_rights_status_pending_across_all_beats():
    """
    Verifies that all 5 beats in the image key script maintain rights_status
    as PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION, without premature clearance claims.
    """
    ws = StoryWorkspace("endrick_milan", "run_v7_1")
    key_file = ws.scripts_dir / "image_key_script.json"
    assert key_file.exists(), "image_key_script.json must exist"

    key_data = json.loads(key_file.read_text(encoding="utf-8"))
    beats = key_data["image_beats"]
    assert len(beats) == 5

    for b in beats:
        assert b["rights_status"] == "PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION", (
            f"Beat {b['beat_id']} rights status must be PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION, got {b['rights_status']}"
        )



if __name__ == "__main__":
    import inspect
    tests = [
        obj for name, obj in inspect.getmembers(sys.modules[__name__])
        if inspect.isfunction(obj) and name.startswith("test_")
    ]
    print(f"=== RUNNING BETA V7.1 REGRESSION TEST SUITE ({len(tests)} TESTS) ===")
    passed = 0
    for t in tests:
        t0 = time.time()
        t()
        elapsed = round(time.time() - t0, 3)
        print(f"  [PASS] {t.__name__} ({elapsed}s)")
        passed += 1
    print(f"\nSUCCESS: All {passed} regression tests passed cleanly.\n")
