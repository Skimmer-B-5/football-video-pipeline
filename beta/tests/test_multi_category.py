"""
beta/tests/test_multi_category.py - Multi-Category Retention, Sound & Editorial Verification Suite.

Tests 5 distinct story types:
1. Major Transfer Rumour (Endrick to Milan)
2. Controversial Decision (Premier League VAR handball penalty overturn)
3. Tactical Analysis (High-press breakdown & midfield overload)
4. Managerial Crisis (Manager facing sack after 4 straight losses)
5. Humorous/Bizarre Story (Absurd contract clause on player weight)
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.hook_engine import CuriosityHookEngine
from stages.sfx_manager import SFXDirector
from stages.transition_engine import TransitionDirector

def run_tests():
    test_cases = [
        {
            "id": "transfer_rumour",
            "category": "transfer_rumour",
            "headline": "Milan Agree €60M Terms for Endrick with Buy-Back Clause",
            "text": "A severe lack of playing time amid fierce competition looks set to edge Endrick towards the exit door at Real Madrid. AC Milan have emerged as strong contenders to sign the Brazilian teenager on loan with a potential buy-back clause, offering immediate starting minutes at San Siro while Madrid demand guaranteed development."
        },
        {
            "id": "controversial_var",
            "category": "controversy_var",
            "headline": "Premier League In Chaos After Disallowed Injury Time Penalty",
            "text": "A controversial VAR review in the ninety-fourth minute overturned a clear handball penalty at the Emirates Stadium, sparking furious protests from the bench and widespread outrage across the league as referees refused to consult the pitchside monitor."
        },
        {
            "id": "tactical_analysis",
            "category": "tactical_analysis",
            "headline": "How Manchester City Overloaded Midfield to Destroy Arsenal High Press",
            "text": "Tactical analysis reveals how Pep Guardiola inverted his full-backs into central midfield to create a numerical four-versus-three overload, completely neutralizing Arsenal pressing traps and isolating defenders in wide channels throughout ninety minutes."
        },
        {
            "id": "managerial_crisis",
            "category": "managerial_crisis",
            "headline": "Manager Facing Sack After Fourth Straight Defeat Sparks Crisis Meeting",
            "text": "Pressure reaches boiling point at Old Trafford following a disastrous four-game losing streak. The board held an emergency midnight crisis meeting to discuss an immediate dismissal, with players reportedly stunned by tactical chaos in the dressing room."
        },
        {
            "id": "bizarre_humour",
            "category": "bizarre_humour",
            "headline": "Bizarre Contract Clause Refuses Player Bonus If Weight Exceeds Eighty Kilos",
            "text": "An absurd leaked contract reveals a bizarre dietary clause penalizing the striker ten thousand pounds per match if weekly weigh-ins exceed eighty kilograms, leaving fans and teammates in stitches as the club chef faces an impossible ultimatum."
        }
    ]

    print("=" * 80)
    print("MULTI-CATEGORY RETENTION, SOUND & EDITORIAL VERIFICATION MATRIX")
    print("=" * 80)

    results = []
    for tc in test_cases:
        cat = tc["category"]
        head = tc["headline"]
        txt = tc["text"]

        # 1. Script & Narrative
        script_plan = CuriosityHookEngine.compose_full_narrative(head, txt, [{"publisher": "BBC Sport"}], "REPORTED")
        scenes = script_plan["scenes"]
        hook = script_plan["selected_hook"]

        # 2. Transition Director
        scenes_with_trans = TransitionDirector.plan_transitions_for_scenes(scenes)

        # 3. SFX Director
        sfx_dir = SFXDirector()
        scenes_final, music_plan = sfx_dir.design_soundtrack_for_story(scenes_with_trans, cat, head)

        # Extract assigned cues
        assigned_sfx = [s["sound_design"]["sfx"]["sfx_id"] for s in scenes_final if s.get("sound_design", {}).get("sfx")]
        trans_list = [s["transition_in"]["id"] for s in scenes_final]

        print(f"\n[CATEGORY: {cat.upper()}]")
        print(f"  • Headline: {head}")
        print(f"  • Hook Archetype: {hook['archetype']} (Score: {hook['scores']['composite']})")
        print(f"  • Hook Spoken: \"{hook['spoken_text']}\"")
        print(f"  • Music Bed: {music_plan['mood']} ({Path(music_plan['file_path']).name})")
        print(f"  • Assigned SFX: {assigned_sfx}")
        print(f"  • Transitions: {trans_list}")

        results.append({
            "category": cat,
            "headline": head,
            "hook_archetype": hook["archetype"],
            "hook_score": hook["scores"]["composite"],
            "hook_spoken": hook["spoken_text"],
            "music_bed": Path(music_plan["file_path"]).name,
            "assigned_sfx": assigned_sfx,
            "transitions": trans_list
        })

    evidence_path = PROJECT_ROOT / "evidence" / "multi_category_test_results.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Saved test matrix results to: {evidence_path.name}")

if __name__ == "__main__":
    run_tests()
