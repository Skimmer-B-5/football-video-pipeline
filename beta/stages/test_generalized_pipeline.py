import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.pipeline.neural_instructions import StoryDossier
from beta.pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline

def main():
    print("==================================================================")
    print("  TESTING GENERALIZED BROADCAST PIPELINE (BETA ARCHITECTURE)     ")
    print("==================================================================")

    # 1. Instantiate a verified Story Dossier
    dossier = StoryDossier(
        story_id="endrick_milan",
        protagonist_name="Endrick",
        current_club="Real Madrid",
        current_manager="Mourinho",
        pursuing_club="Milan",
        reported_base_fee="€60M",
        reported_bonuses="€10M",
        reported_buyback="eighty to eighty-five million",
        complication="left-leg muscle injury complicates matters",
        reporting_sources=["Cadena SER", "Corriere dello Sport"],
        headline_kicker="● TRANSFER WATCH",
        main_headline="MILAN PLOT ENDRICK MOVE AS MOURINHO RESISTS EXIT",
        ticker_text="CORRIERE DELLO SPORT: MILAN PREPARE €60M PROPOSAL FOR ENDRICK ✦ CADENA SER: MOURINHO RESISTS EXIT ✦ REAL MADRID: ADDUCTOR INJURY CONFIRMED ✦"
    )

    # 2. Map 16 public shot images
    shots = {
        "S01": [
            "/images/v7_1_6_5_shots/S01_shot1_bernabeu.png",
            "/images/v7_1_6_5_shots/S01_shot2_milan_facade.png",
            "/images/v7_1_6_5_shots/S01_shot3_mourinho.png",
        ],
        "S02": [
            "/images/v7_1_6_5_shots/S02_shot1_presentation.png",
            "/images/v7_1_6_5_shots/S02_shot2_action.png",
            "/images/v7_1_6_5_shots/S02_shot3_closeup.png",
        ],
        "S03": [
            "/images/v7_1_6_5_shots/S03_shot1_base60m.png",
            "/images/v7_1_6_5_shots/S03_shot2_bonuses.png",
            "/images/v7_1_6_5_shots/S03_shot3_buyback.png",
            "/images/v7_1_6_5_shots/S03_shot4_not_agreed.png",
        ],
        "S04": [
            "/images/v7_1_6_5_shots/S04_shot1_athletic.png",
            "/images/v7_1_6_5_shots/S04_shot2_medical_bulletin.png",
            "/images/v7_1_6_5_shots/S04_shot3_archival_training.png",
        ],
        "S05": [
            "/images/v7_1_6_5_shots/S05_shot1_exterior.png",
            "/images/v7_1_6_5_shots/S05_shot2_pitch.png",
            "/images/v7_1_6_5_shots/S05_shot3_anticipation.png",
        ]
    }

    # 3. Execute Generalized Pipeline
    pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id="run_v7_1_gen")
    
    # We test compilation of screenplay, voice, and props
    script_data = pipeline.generate_screenplay()
    assert len(script_data["scenes"]) == 6, "Expected 6 scenes (5 beats + outro)"
    print("✓ Screenplay validation passed")

    audio_data = pipeline.synthesize_voice(script_data)
    assert audio_data["total_frames"] > 0, "Expected positive total frames"
    print(f"✓ Audio assembly validation passed: {audio_data['total_frames']} frames")

    props_path = pipeline.compile_visual_props(script_data, audio_data, shots)
    assert props_path.exists(), f"Props file missing: {props_path}"
    print(f"✓ Visual props validation passed: {props_path}")

    print("\n==================================================================")
    print("  GENERALIZED BROADCAST PIPELINE ARCHITECTURE FULLY VALIDATED!   ")
    print("==================================================================")

if __name__ == "__main__":
    main()
