import sys
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from pipeline.neural_instructions import StoryDossier
from beta.pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline

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
pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id='test_30s_check')
script = pipeline.generate_screenplay()
total_words = sum(len(sc['spoken_narration'].split()) for sc in script['scenes'])
print(f"TOTAL WORDS: {total_words}")
for sc in script['scenes']:
    words = len(sc['spoken_narration'].split())
    print(f"[{sc['scene_id']}] ({words}w): {sc['spoken_narration']}")
