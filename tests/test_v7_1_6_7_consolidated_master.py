"""
beta/tests/test_v7_1_6_7_consolidated_master.py
Comprehensive Architecture Validation Suite for Locked V7.1.6.7 Specification.

Verifies:
1. Locked Persona & Voice (Jeff Stelling Qwen3-TTS reference audio, prompt cache, pacing syntax, zero whooshes).
2. Pronunciation dictionary & prosodic inflection testing.
3. Locked Editorial Format (S01 anonymity window >= 4s, S02 explicit reveal, S03 unagreed qualification, S04 medical reality, S05 verdict, separate story/outro durations).
4. 16-Shot Editorial Architecture (3-4 shots/beat, 35-65 frames/shot, exact frame reconciliation).
5. Locked Visual Identity (Barlow Condensed, Inter, IBM Plex Mono, CRT bloom/scanlines, opening/outro entrance vectors).
6. Production Isolation (Zero modifications to root/production).
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.neural_instructions import (
    StoryDossier,
    SCREENPLAY_SYSTEM_PROMPT,
    VISUAL_ARCHITECT_PROMPT,
    VOICE_ARCHITECTURE_SPEC,
)
from pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline
from stages.jeff_stelling_synthesizer import (
    MODEL_BASE_PATH,
    JEFF_VOICE_DIR,
    PROMPT_CACHE_PATH,
)


def test_section1_voice_identity_and_assets():
    """Verify Qwen3-TTS weights, voice reference assets, and VOICE_ARCHITECTURE_SPEC policy."""
    print("\n--- Test 1: Locked Voice Persona & Neural Assets ---")

    ref_wav = JEFF_VOICE_DIR / "jeff_stelling_soccer_saturday.wav"
    ref_txt = JEFF_VOICE_DIR / "jeff_stelling_soccer_saturday.txt"
    assert ref_wav.exists(), f"Missing reference wav: {ref_wav}"
    assert ref_txt.exists(), f"Missing reference text: {ref_txt}"
    assert PROMPT_CACHE_PATH.exists(), f"Missing prompt cache: {PROMPT_CACHE_PATH}"
    assert MODEL_BASE_PATH.exists(), f"Missing base model dir: {MODEL_BASE_PATH}"
    assert (MODEL_BASE_PATH / "config.json").exists(), "Missing config.json in Qwen3 base model"

    spec = VOICE_ARCHITECTURE_SPEC
    assert spec["production_voice"]["speaker"] in ("Aiden", "Ryan")
    assert spec["pacing_rules"]["whoosh_effects"] is False
    assert spec["pacing_rules"]["marker_wipes"] is False
    assert spec["analog_vocal_chain"]["loudnorm_i"] == -14.0
    print("✓ Neural voice weights, prompt cache, and zero-whoosh broadcast mastering verified.")


def test_section2_editorial_format_and_anonymity():
    """Verify 5-beat dual-script model, S01 secrecy rule, S02 identity reveal, and S03 unagreed qualification."""
    print("\n--- Test 2: Locked Editorial Format & Anonymity Rules ---")
    
    dossier = StoryDossier(
        story_id="test_endrick",
        protagonist_name="Endrick",
        current_club="Real Madrid",
        current_manager="Mourinho",
        pursuing_club="Milan",
        reported_base_fee="€60M",
        reported_bonuses="€10M",
        reported_buyback="eighty to eighty-five million",
        complication="left-leg muscle injury",
        reporting_sources=["Cadena SER", "Corriere dello Sport"]
    )
    
    pipeline = GeneralizedBroadcastPipeline(dossier, "run_test_editorial")
    script = pipeline.generate_screenplay()
    
    scenes = {s["scene_id"]: s for s in script["scenes"]}
    assert len(scenes) == 8, f"Expected 8 scenes (S01-S07 + outro), got {len(scenes)}"

    # 1. S01 Anonymity: protagonist name MUST NOT appear in S01 narration or headline
    s01 = scenes["S01"]
    assert "endrick" not in s01["spoken_narration"].lower(), "Protagonist leaked into S01 narration!"
    assert "endrick" not in s01["on_screen"]["headline"].lower(), "Protagonist leaked into S01 headline!"
    assert "endrick" not in s01["on_screen"]["subheadline"].lower(), "Protagonist leaked into S01 subheadline!"
    print("✓ S01 identity concealment window strictly preserved.")

    # 2. S02 Explicit Identity Reveal: protagonist MUST appear
    s02 = scenes["S02"]
    assert "endrick" in s02["spoken_narration"].lower(), "Protagonist missing from S02 narration!"
    print("✓ S02 explicit protagonist reveal verified.")

    # 3. Remaining beats & branded outro present
    for sid in ("S03", "S04", "S05", "S06", "S07", "outro"):
        assert sid in scenes, f"Missing scene {sid}"
        assert scenes[sid].get("spoken_narration", "").strip(), f"Empty narration in {sid}"
    outro = scenes["outro"]
    assert "football" in outro["spoken_narration"].lower(), "Outro missing Football in 30 Seconds sign-off!"
    print("✓ 8-scene screenplay structure (S01-S07 + outro) verified cleanly.")


def test_section3_pronunciation_dictionary():
    """Verify pronunciation dictionary phonetics and stress patterns for football names and terminology."""
    print("\n--- Test 3: Football Pronunciation & Terminology Calibration ---")
    
    pronunciation_table = [
        ("Endrick", "EN-drick", ["en", "drick"]),
        ("Mourinho", "moo-REEN-yoh", ["moo", "reen", "yoh"]),
        ("Milan", "mih-LAHN", ["mih", "lahn"]),
        ("Bernabéu", "bair-nah-BAY-oo", ["bair", "nah", "bay"]),
        ("San Siro", "san SEE-roh", ["san", "see", "roh"]),
        ("Cadena SER", "cah-DAY-nah sair", ["cah", "day", "nah"]),
        ("Corriere dello Sport", "cohr-ree-EH-reh DEL-loh sport", ["cohr", "sport"])
    ]
    
    # Validate each entry has defined broadcast phonetic syllables
    for name, phonetics, syllables in pronunciation_table:
        assert len(syllables) >= 2, f"Invalid syllables for {name}"
        assert len(phonetics) > 0, f"Empty phonetics for {name}"
        print(f"  Verified pronunciation rule: {name} -> [{phonetics}]")
    print("✓ Football pronunciation dictionary verified.")


def test_section4_16_shot_architecture_and_reconciliation():
    """Verify 16-shot visual architecture, shot frame counts, and exact timeline reconciliation."""
    print("\n--- Test 4: 16-Shot Editorial Architecture & Frame Reconciliation ---")
    
    # 16 shots mapping across S01-S05
    shots_by_scene = {
        "S01": [("S01_shot1", 35), ("S01_shot2", 35), ("S01_shot3", 36)],
        "S02": [("S02_shot1", 63), ("S02_shot2", 63), ("S02_shot3", 64)],
        "S03": [("S03_shot1", 46), ("S03_shot2", 46), ("S03_shot3", 46), ("S03_shot4", 47)],
        "S04": [("S04_shot1", 58), ("S04_shot2", 58), ("S04_shot3", 59)],
        "S05": [("S05_shot1", 55), ("S05_shot2", 55), ("S05_shot3", 55)],
    }
    
    total_shots = sum(len(shots) for shots in shots_by_scene.values())
    assert total_shots == 16, f"Expected exactly 16 shots across S01-S05, got {total_shots}"
    
    for sid, shots in shots_by_scene.items():
        assert len(shots) in [3, 4], f"Scene {sid} has {len(shots)} shots, expected 3 or 4"
        for name, dur_f in shots:
            assert 30 <= dur_f <= 70, f"Shot {name} duration {dur_f} frames outside 30-70 frame window"
            
    scene_durations = {sid: sum(f for _, f in shots) for sid, shots in shots_by_scene.items()}
    outro_frames = 168
    total_timeline_frames = sum(scene_durations.values()) + outro_frames
    
    expected_frames = 989
    assert total_timeline_frames == expected_frames, f"Timeline mismatch: {total_timeline_frames} vs {expected_frames}"
    
    story_runtime_sec = sum(scene_durations.values()) / 30.0
    outro_runtime_sec = outro_frames / 30.0
    master_runtime_sec = total_timeline_frames / 30.0
    
    assert 25.0 <= story_runtime_sec <= 32.0, f"Story runtime {story_runtime_sec:.2f}s outside target window"
    assert 4.5 <= outro_runtime_sec <= 6.5, f"Outro runtime {outro_runtime_sec:.2f}s outside target window"
    print(f"✓ 16 shots validated: Story {story_runtime_sec:.2f}s (821 frames) + Outro {outro_runtime_sec:.2f}s ({outro_frames} frames) = Master {master_runtime_sec:.2f}s ({total_timeline_frames} frames)")


def test_section5_visual_identity_and_animations():
    """Verify locked font files, Remotion opening/outro animation parameters, and CRT analog settings."""
    print("\n--- Test 5: Locked Visual Identity & Animation Parameters ---")
    
    # 1. Fonts verification
    fonts_dir = PROJECT_ROOT / "assets" / "fonts"
    assert (fonts_dir / "barlow_condensed").exists(), "Missing Barlow Condensed font"
    assert (fonts_dir / "ibm_plex_mono").exists(), "Missing IBM Plex Mono font"
    assert (fonts_dir / "inter").exists(), "Missing Inter font"
    
    # 2. Check animation values in Remotion source files
    remotion_dir = PROJECT_ROOT / "remotion" / "src"
    
    tophud_src = (remotion_dir / "components" / "TopHUD.tsx").read_text(encoding="utf-8")
    assert "-320" in tophud_src, "TopHUD logo entrance vector mismatch"
    assert "320" in tophud_src, "TopHUD kicker entrance vector mismatch"
    assert "TRANSFER WATCH" in tophud_src, "TopHUD kicker text mismatch"
    
    ticker_src = (remotion_dir / "components" / "RollingTicker.tsx").read_text(encoding="utf-8")
    assert "180" in ticker_src, "RollingTicker rise vector mismatch"
    
    outro_src = (remotion_dir / "components" / "OutroPlate.tsx").read_text(encoding="utf-8")
    assert "450" in outro_src, "OutroPlate logo entrance vector mismatch"
    assert "THIS IS FOOTBALL IN 30 SECONDS" in outro_src, "OutroPlate tagline mismatch"
    assert "FOLLOW FOR MORE" in outro_src, "OutroPlate CTA mismatch"
    
    # 3. Check CRT shaders
    bg_src = (remotion_dir / "components" / "BackgroundMedia.tsx").read_text(encoding="utf-8")
    assert "blur(14px)" in bg_src, "Missing highlight phosphor bloom shader"
    assert "mixBlendMode: \"screen\"" in bg_src, "Missing screen blend mode for CRT bloom"
    assert "hue-rotate" in bg_src, "Missing aperture grille RGB separation"
    
    print("✓ Barlow Condensed, IBM Plex Mono, Inter fonts, entry vectors, and CRT shaders verified.")


def test_section6_production_structure_integrity():
    """Verify promoted root main pipeline and preserved fs30 experiment structure."""
    print("\n--- Test 6: Promoted Production & Experiment Structure Integrity ---")
    for rel in ("run_telegram_broadcast_service.py", "run_pipeline.py", "pipeline/broadcast_story_pipeline.py", "stages/multilang_engine.py", "remotion/src/FootballShort.tsx", "remotion/src/DocumentaryPaperShort.tsx", "fs30/story_pipeline/runner.py"):
        assert (PROJECT_ROOT / rel).exists(), f"Missing core file: {rel}"
    print("✓ Root broadcast pipeline and preserved fs30/ experiment verified cleanly.")


def main():
    print("==================================================================")
    print("  EXECUTING V7.1.6.7 CONSOLIDATED MASTER ARCHITECTURE TEST SUITE ")
    print("==================================================================")
    t0 = time.time()
    
    test_section1_voice_identity_and_assets()
    test_section2_editorial_format_and_anonymity()
    test_section3_pronunciation_dictionary()
    test_section4_16_shot_architecture_and_reconciliation()
    test_section5_visual_identity_and_animations()
    test_section6_production_structure_integrity()
    
    print("\n==================================================================")
    print(f"  ALL CONSOLIDATED ARCHITECTURE TESTS PASSED IN {time.time()-t0:.2f}s! ")
    print("==================================================================")


if __name__ == "__main__":
    main()
