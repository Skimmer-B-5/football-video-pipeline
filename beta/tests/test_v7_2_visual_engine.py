import sys
import shutil
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from pipeline.neural_instructions import StoryDossier
from stages.editorial_visual_architect import EditorialVisualArchitect
from stages.vision_framing_inspector import VisionFramingInspector

def test_v7_2_visual_pipeline():
    dossier = StoryDossier(
        story_id="calvin_bassey_fulham",
        protagonist_name="Calvin Bassey",
        current_club="Fulham",
        current_manager="Marco Silva",
        pursuing_club="Manchester United",
        reported_base_fee="£30 million",
        reported_bonuses="performance incentives",
        complication="medical pending and Fulham board resistance",
        main_headline="Fulham defender Calvin Bassey is in talks over new contract amid Man Utd links",
        headline_kicker="BREAKING TRANSFER REPORT"
    )

    run_id = "test_v7_2_bassey"
    run_dir = BETA_ROOT / "remotion" / "public" / "images" / f"story_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    architect = EditorialVisualArchitect()
    inspector = VisionFramingInspector()
    shot_specs = architect.plan_16_shots(dossier)

    print(f"Testing 16-Shot Editorial Visual Engine for: {dossier.protagonist_name}\n")
    results = {}

    for idx, spec in enumerate(shot_specs, 1):
        dest_filename = f"{spec.shot_id}_{idx}.png"
        dest_file = run_dir / dest_filename
        print(f"--- Shot {idx}/16: [{spec.shot_id}] {spec.primary_entity} ({spec.role}) ---")
        ok = inspector.audit_and_produce_shot(spec, dest_file)
        results[spec.shot_id] = ok
        if not ok:
            print(f"FAILED on shot {spec.shot_id}")

    print("\n--- SUMMARY OF 16 SHOTS ---")
    for sid, ok in results.items():
        print(f"[{sid}] {'✅ PRODUCED' if ok else '❌ FAILED'}")

if __name__ == "__main__":
    test_v7_2_visual_pipeline()
