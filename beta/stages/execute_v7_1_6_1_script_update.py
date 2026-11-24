import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "beta"))

from stages.story_workspace_manager import StoryWorkspace
from stages.dual_script_architecture import DualScriptDirector
from stages.approval_state_machine import ApprovalStateMachine, PipelineState

ws = StoryWorkspace("endrick_milan", "run_v7_1")
director = DualScriptDirector()

script_a, script_b = director.generate_endrick_dual_scripts(
    story_id=ws.story_id,
    run_id=ws.run_id,
    script_version="v7.1.6.1"
)

out_a = ws.scripts_dir / "dialogue_script.json"
out_b = ws.scripts_dir / "image_key_script.json"

out_a.write_text(json.dumps(script_a, indent=2), encoding="utf-8")
out_b.write_text(json.dumps(script_b, indent=2), encoding="utf-8")

print(f"Saved Script A: {out_a}")
print(f"Saved Script B: {out_b}")
print("Metadata Script A:", json.dumps(script_a["metadata"], indent=2))

for b in script_a["beats"]:
    print(f"  {b['beat_id']} [{b['start_time_sec']}s - {b['end_time_sec']}s] ({b['estimated_duration_sec']}s | {b['written_word_count']}w / {b['spoken_token_count']}t): \"{b['spoken_dialogue']}\"")

# Update state machine to reflect v7.1.6.1 while maintaining SCRIPT_REVIEW_PENDING
state_file = ws.state_dir / "approval_state.json"
sm = ApprovalStateMachine(state_file, ws.story_id, ws.run_id)
state_data = json.loads(state_file.read_text(encoding="utf-8"))
state_data["script_version"] = "v7.1.6.1"
state_data["last_transition_reason"] = "Updated to v7.1.6.1 with reconciled pause calculation (29.97s total duration)"
state_file.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
print(f"Updated state file: {state_file}")
