import sys
import json
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from stages.groq_client import call_groq_chat

test_scenes = [
    {
        "scene_id": "S01",
        "spoken_narration": "Fulham face a massive battle to keep their star defender from Premier League rivals.",
        "is_choice": False
    },
    {
        "scene_id": "S02",
        "spoken_narration": "And — Manchester United are actively circling around Calvin Bassey.",
        "is_choice": False
    },
    {
        "scene_id": "S07",
        "spoken_narration": "So — will Marco Silva keep his defensive anchor, or will Manchester United force the move?",
        "is_choice": True
    }
]

for sc in test_scenes:
    sid = sc["scene_id"]
    narration = sc["spoken_narration"]
    is_choice = sc["is_choice"]
    
    if is_choice:
        sys_prompt = "You are the Visual Director for a top-tier football television news channel. Output strict JSON only."
        user_prompt = f"""This football news scene presents an "OR" / "AND" choice between two sides:
Spoken Narration: "{narration}"
Protagonist: "Calvin Bassey"
Current Club: "Fulham"
Pursuing Club: "Manchester United"
Manager: "Marco Silva"

Describe TWO distinct real-world photographs to visually corroborate each part of the choice:
1. Part 1 (First part before the or/and): Describe in exactly one sentence the photo for Part 1.
2. Part 2 (Second part after the or/and): Describe in exactly one sentence the photo for Part 2.

Output JSON schema:
{{
  "part1_description": "one sentence describing real photograph for part 1",
  "part1_query": "concise search query for part 1",
  "part1_entity": "primary entity for part 1",
  "part2_description": "one sentence describing real photograph for part 2",
  "part2_query": "concise search query for part 2",
  "part2_entity": "primary entity for part 2"
}}"""
    else:
        sys_prompt = "You are the Visual Director for a top-tier football television news channel. Output strict JSON only."
        user_prompt = f"""Here is a scene from our breaking football transfer news broadcast:
Scene ID: {sid}
Spoken Narration: "{narration}"
Protagonist: "Calvin Bassey"
Current Club: "Fulham"
Pursuing Club: "Manchester United"
Manager: "Marco Silva"

For a football channel, describe in EXACTLY ONE sentence the real-world photograph that should be shown here to visually corroborate this scene.
Must be an authentic football photograph (match action, training, stadium under floodlights, or press conference). NO illustrations, NO empty benches or sidewalks.

Output JSON schema:
{{
  "image_description": "one sentence describing the real photograph",
  "search_query": "concise search query to find this photo",
  "primary_entity": "name of player, manager, or club stadium"
}}"""

    raw = call_groq_chat(
        system_prompt=sys_prompt,
        user_prompt=user_prompt,
        preferred_model="openai/gpt-oss-120b",
        fallback_model="qwen/qwen3.8-27b",
        temperature=0.2
    )
    print(f"\n--- SCENE {sid} ---")
    print(raw)
