"""
beta/stages/execute_v7_1_2_update_and_dispatch.py
Executes the full V7.1.2 update and Telegram dispatch sequence.
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.story_workspace_manager import StoryWorkspace
from stages.approval_state_machine import ApprovalStateMachine, PipelineState
from stages.telegram_editorial_workflow import TelegramEditorialWorkflow
from stages.dual_script_architecture import DualScriptDirector
from stages.reporter_voice_audition import AUDITION_PASSAGE

def main():
    ws = StoryWorkspace("endrick_milan", "run_v7_1")
    workflow = TelegramEditorialWorkflow(ws)

    print("=== Step 1: Invalidate previous state for v7.1.2 ===")
    workflow.state_machine.invalidate_downstream_on_script_change("v7.1.2", "editorial_age_injury_correction")

    print("=== Step 2: Dispatch Gate 1 (Dual Scripts) to Telegram ===")
    res_g1 = workflow.dispatch_gate1_scripts_for_review()
    print("Gate 1 Result:", res_g1)

    print("=== Step 3: Dispatch Gate 2 (Clean Scene Contact Sheet V7.1.2) to Telegram ===")
    chart_path = ws.telegram_dir / "clean_scene_chart_master_v7_1_2.jpg"
    if not chart_path.exists():
        raise FileNotFoundError(f"Contact sheet not found at: {chart_path}")
    res_g2 = workflow.dispatch_gate2_visuals_for_review(chart_path, update_state_machine=False)
    print("Gate 2 Result:", res_g2)

    print("=== Step 4: Dispatch Gate 3 (3 Voice Auditions V7.1.2) to Telegram ===")
    audition_files = [
        {
            "id": "VOICE_A",
            "name": "Correspondent Newsdesk",
            "profile": "Mature British male sports correspondent, measured pacing, calm authoritative broadcast baritone, clear consonants, restrained emphasis.",
            "file_path": str(ws.voice_dir / "VOICE_A_mastered.wav"),
            "duration_sec": 29.2,
            "script_passage": AUDITION_PASSAGE
        },
        {
            "id": "VOICE_B",
            "name": "Transfer Insider Specialist",
            "profile": "Experienced British transfer specialist, crisp articulation, dynamic pitch contours, subtle investigative intrigue, warm textured tenor.",
            "file_path": str(ws.voice_dir / "VOICE_B_mastered.wav"),
            "duration_sec": 30.3,
            "script_passage": AUDITION_PASSAGE
        },
        {
            "id": "VOICE_C",
            "name": "Senior Sports Anchor",
            "profile": "Senior British sports desk anchor, rich seasoned baritone, deliberate broadcast rhythm, natural pauses, professional broadcast gravitas.",
            "file_path": str(ws.voice_dir / "VOICE_C_mastered.wav"),
            "duration_sec": 34.2,
            "script_passage": AUDITION_PASSAGE
        }
    ]
    res_g3 = workflow.dispatch_gate3_voice_auditions(audition_files, update_state_machine=False)
    print("Gate 3 Result:", res_g3)

    return {
        "gate_1": res_g1,
        "gate_2": res_g2,
        "gate_3": res_g3
    }

if __name__ == "__main__":
    main()
