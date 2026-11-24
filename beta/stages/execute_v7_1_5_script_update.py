"""
beta/stages/execute_v7_1_5_script_update.py
Generates the V7.1.5 synchronized dual scripts and updates the story workspace.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.dual_script_architecture import DualScriptDirector
from stages.story_workspace_manager import StoryWorkspace

def run_update():
    ws = StoryWorkspace("endrick_milan", "run_v7_1")
    director = DualScriptDirector()
    script_a, script_b = director.generate_endrick_dual_scripts(
        story_id=ws.story_id,
        run_id=ws.run_id,
        script_version="v7.1.5"
    )

    print(f"Script A Total Words: {script_a['metadata']['total_spoken_words']}")
    print(f"Script A Total Duration: {script_a['metadata']['total_duration_sec']}s")
    for beat in script_a['beats']:
        print(f"[{beat['beat_id']}] {beat['start_time_sec']}s - {beat['end_time_sec']}s ({beat['estimated_duration_sec']}s, {beat['word_count']} words): \"{beat['spoken_dialogue']}\"")

    out_a = ws.scripts_dir / "dialogue_script.json"
    out_b = ws.scripts_dir / "image_key_script.json"

    out_a.write_text(json.dumps(script_a, indent=2), encoding="utf-8")
    out_b.write_text(json.dumps(script_b, indent=2), encoding="utf-8")
    print(f"Successfully saved {out_a} and {out_b}")

if __name__ == "__main__":
    run_update()
