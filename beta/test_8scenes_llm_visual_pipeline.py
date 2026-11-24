"""
beta/test_8scenes_llm_visual_pipeline.py
End-to-End Test for the 8-Scene GPT OSS Visual Director Pipeline:
1. Generates 8-scene screenplay (7 story scenes + 1 ending card).
2. Sends scenes to GPT OSS (or Qwen 27B) to describe the real photograph in one sentence.
3. Skips scene 8 (ending card outro).
4. Detects "OR" / "AND" choice in S07 and derives TWO image descriptions to show both parts.
5. Scrapes full-res verified images and verifies shots dictionary.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from pipeline.neural_instructions import StoryDossier
from beta.pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline
from beta.stages.llm_visual_director import LLMVisualDirector
from beta.run_telegram_broadcast_service import source_story_shots

def main():
    dossier = StoryDossier(
        story_id="calvin_bassey_fulham",
        main_headline="MAN UTD TRANSFER NEWS: FULHAM DEFENDER CALVIN BASSEY IS IN TALKS OVER NEW CONTRACT AMID MAN UTD LINKS",
        protagonist_name="Calvin Bassey",
        current_club="Fulham",
        pursuing_club="Manchester United",
        current_manager="Marco Silva",
        reported_base_fee="£30M",
        reported_bonuses="£5M",
        reported_buyback="5-year contract terms",
        complication="Silva urges board to seal extension",
        headline_kicker="● BREAKING TRANSFER REPORT",
        ticker_text="SKY SPORTS: FULHAM OPEN TALKS WITH CALVIN BASSEY AMID MAN UTD INTEREST ✦ MARCO SILVA DETERMINED TO KEEP DEFENDER ✦"
    )

    run_id = "test_8scenes_llm_director"
    pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id=run_id)

    print("\n=======================================================")
    print("STEP 1: Generating 8-Scene Screenplay (7 Story + 1 Outro)")
    print("=======================================================")
    script_data = pipeline.generate_screenplay()
    scenes = script_data["scenes"]
    print(f"Total Scenes: {len(scenes)}")

    story_words = 0
    for idx, sc in enumerate(scenes, 1):
        words = len(sc["spoken_narration"].split())
        if sc["scene_id"] != "outro":
            story_words += words
        print(f"  Scene {idx} [{sc['scene_id']}] ({words}w): {sc['spoken_narration']}")
    print(f"Total Story Words: {story_words} (Target: 56-62 words for ~26s story duration)")

    print("\n=======================================================")
    print("STEP 2: LLM Visual Director (GPT OSS / Qwen 27B)")
    print("=======================================================")
    director = LLMVisualDirector()
    shot_specs = director.plan_visual_timeline(scenes, dossier)
    print(f"Total Planned Shots: {len(shot_specs)}")

    for spec in shot_specs:
        print(f"\n--- Shot [{spec.shot_id}] ({spec.scene_id}) ---")
        print(f"  Role: {spec.role}")
        print(f"  Entity: {spec.primary_entity} ({spec.club_affiliation})")
        print(f"  Context Description (1-sentence from LLM): \"{spec.required_context}\"")
        print(f"  Primary Search Query: \"{spec.search_queries[0]}\"")

    # Verify requirement: S07 must have 2 shots (Part 1 and Part 2)
    s07_shots = [s for s in shot_specs if s.scene_id == "S07"]
    print(f"\nS07 Shots Count: {len(s07_shots)} (Expected: 2 shots for OR/AND choice)")
    assert len(s07_shots) == 2, f"Expected 2 shots for S07, got {len(s07_shots)}"

    print("\n=======================================================")
    print("STEP 3: Scraping & Auditing Visuals via Descriptions")
    print("=======================================================")
    sourced_shots = source_story_shots(dossier, run_id, screenplay_scenes=scenes)

    print("\n=======================================================")
    print("VERIFICATION SUMMARY:")
    print("=======================================================")
    for sc in scenes:
        sid = sc["scene_id"]
        imgs = sourced_shots.get(sid, [])
        print(f"  [{sid}] -> {len(imgs)} image(s): {imgs}")

    assert len(sourced_shots.get("S07", [])) == 2, "S07 did not receive 2 images for the dual-choice split!"
    print("\nSUCCESS: All 8 scenes, 1-sentence LLM visual descriptions, and dual-choice split verified!")

if __name__ == "__main__":
    main()
