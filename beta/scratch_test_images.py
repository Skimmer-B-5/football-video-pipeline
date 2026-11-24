import sys
import json
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from pipeline.neural_instructions import StoryDossier
from beta.run_telegram_broadcast_service import source_story_shots

dossier = StoryDossier(
    story_id='calvin_bassey_fulham',
    main_headline='MAN UTD TARGET CALVIN BASSEY AS FULHAM OPEN CONTRACT TALKS',
    protagonist_name='Calvin Bassey',
    current_club='Fulham',
    pursuing_club='Manchester United',
    current_manager='Marco Silva',
    reported_base_fee='£30M',
    reported_bonuses='£5M',
    complication='Silva urges board to seal extension',
    headline_kicker='● BREAKING TRANSFER REPORT'
)

shots = source_story_shots(dossier, 'test_visual_check')
print("\nSOURCED SHOTS SUMMARY:")
for scene_id, shot_list in shots.items():
    print(f"[{scene_id}] ({len(shot_list)} shots): {shot_list}")
