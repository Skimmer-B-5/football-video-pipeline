import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.image_sourcing import source_scene_image, reset_image_registry
from pipeline.neural_instructions import StoryDossier

def source_story_shots(dossier: StoryDossier, run_id: str) -> dict:
    reset_image_registry()
    run_dir = PROJECT_ROOT / "remotion" / "public" / "images" / f"story_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    shot_queries = {
        "S01": [
            (f"{dossier.current_club} stadium night", "stadium"),
            (f"{dossier.pursuing_club} stadium exterior", "stadium"),
            (f"{dossier.current_manager} manager touchline", "manager")
        ],
        "S02": [
            (f"{dossier.protagonist_name} match action celebration", "player"),
            (f"{dossier.protagonist_name} close up portrait", "player"),
            (f"{dossier.protagonist_name} training match", "player")
        ],
        "S03": [
            (f"{dossier.pursuing_club} stadium match", "stadium"),
            (f"{dossier.protagonist_name} presentation suit", "player"),
            (f"{dossier.current_club} football fans stadium", "fans"),
            (f"{dossier.protagonist_name} match action", "player")
        ],
        "S04": [
            (f"{dossier.protagonist_name} frustrated pitch", "player"),
            (f"{dossier.protagonist_name} training pitch", "player"),
            (f"{dossier.current_club} training ground", "training")
        ],
        "S05": [
            (f"{dossier.pursuing_club} stadium floodlights night", "stadium"),
            (f"{dossier.current_club} stadium pitch night", "stadium"),
            (f"{dossier.protagonist_name} walking pitch", "player")
        ]
    }
    
    remotion_shots = {}
    scene_counter = 1
    
    for sid, queries in shot_queries.items():
        remotion_shots[sid] = []
        for q_idx, (q_text, q_type) in enumerate(queries, 1):
            try:
                res = source_scene_image(
                    scene_id=scene_counter,
                    headline=dossier.main_headline,
                    scene_text=f"{dossier.protagonist_name} {dossier.current_club} {dossier.pursuing_club}",
                    visual_prompt=q_text,
                    source_name="Live Sports Desk",
                    search_entity=dossier.protagonist_name if q_type == "player" else dossier.current_club,
                    search_context=q_text
                )
                img_path = Path(res["chosen_image"])
                dest_file = run_dir / f"{sid}_shot{q_idx}_{img_path.name}"
                shutil.copy(img_path, dest_file)
                remotion_shots[sid].append(f"/images/story_{run_id}/{dest_file.name}")
                print(f"  [{sid} Shot {q_idx}] -> {dest_file.name}")
            except Exception as e:
                print(f"  [{sid} Shot {q_idx}] Fallback notice: {e}")
            scene_counter += 1
            
    return remotion_shots

# Test run
test_dossier = StoryDossier(
    story_id="calvin_bassey_manutd",
    protagonist_name="Calvin Bassey",
    current_club="Fulham",
    current_manager="Marco Silva",
    pursuing_club="Manchester United",
    reported_base_fee="€35M",
    reported_bonuses="€5M",
    reported_buyback="none",
    complication="Fulham pushing to extend contract until 2029",
    reporting_sources=["Sky Sports"],
    headline_kicker="● BREAKING TRANSFER REPORT",
    main_headline="MAN UTD MONITOR BASSEY AS FULHAM RUSH TO AGREE NEW DEAL",
    ticker_text="SKY SPORTS: MAN UTD TARGET FULHAM DEFENDER CALVIN BASSEY ✦"
)

shots = source_story_shots(test_dossier, "test_bassey")
print("\nGenerated Remotion Shots Map:")
import json
print(json.dumps(shots, indent=2))
