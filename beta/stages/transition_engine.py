"""
beta/stages/transition_engine.py - Purposeful Editorial Transition Director.

Enforces:
1. Editorial Motivation: Transitions reflect narrative relationships (not random decorative wipes).
   - Camera Flash Cut: Rapid 2-frame white flash + shutter SFX for major news/transfer reveals.
   - Document Snap: Crisp slide-in with contract stamp SFX for explainer clause/tactical graphics.
   - Whip Pan: Directional lateral push for club-to-club or perspective shifts.
   - Record Stop Cut: Sudden audio brake & freeze for unexpected plot twists or contradictions.
   - Clean Hard Cut: Pure broadcast cut for dialogue momentum.
2. Timing & Sync: Transitions strictly bounded under 0.25s so they never cover faces or text.
"""

from typing import Dict, List, Any, Optional

TRANSITION_CATALOG = {
    "camera_flash": {
        "id": "camera_flash",
        "duration_sec": 0.08,
        "type": "flash_white",
        "sfx_cue": "camera_shutter",
        "description": "Rapid 2-frame white exposure flash for major transfer breaking reveals."
    },
    "document_snap": {
        "id": "document_snap",
        "duration_sec": 0.12,
        "type": "snap_up",
        "sfx_cue": "contract_stamp",
        "description": "Crisp upward snap into explainer contract & tactical cards."
    },
    "whip_pan": {
        "id": "whip_pan",
        "duration_sec": 0.15,
        "type": "lateral_push",
        "sfx_cue": "paper_slide",
        "description": "Directional motion-matched lateral pan for club-to-club switches."
    },
    "record_stop_cut": {
        "id": "record_stop_cut",
        "duration_sec": 0.10,
        "type": "freeze_cut",
        "sfx_cue": "record_stop",
        "description": "Hard freeze & brake for contradictory terms or plot twists."
    },
    "clean_hard_cut": {
        "id": "clean_hard_cut",
        "duration_sec": 0.0,
        "type": "cut",
        "sfx_cue": None,
        "description": "Clean, instantaneous broadcast cut for editorial pace."
    }
}

class TransitionDirector:
    """Selects purposeful transitions based on semantic relationships between scenes."""

    @staticmethod
    def plan_transitions_for_scenes(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determines the transition into each scene based on narrative beat and visual kind.
        """
        decorated = []
        for idx, sc in enumerate(scenes):
            sc_copy = dict(sc)
            v_kind = sc.get("visual", {}).get("kind", "")
            role = sc.get("role", "")
            narr = sc.get("narration", "").lower()

            if idx == 0:
                # Opening: Immediate punch-in, no transition delay
                trans = TRANSITION_CATALOG["clean_hard_cut"]
            elif "explainer" in v_kind:
                # Entering a contract or tactical explainer graphic
                trans = TRANSITION_CATALOG["document_snap"]
            elif "twist" in narr or "catch" in narr or "contradict" in narr or "refuse" in narr:
                trans = TRANSITION_CATALOG["record_stop_cut"]
            elif idx == 1 and ("accelerat" in narr or "formal" in narr or "bid" in narr):
                trans = TRANSITION_CATALOG["camera_flash"]
            elif "lateral" in sc.get("motion", {}).get("type", "") or "club" in role:
                trans = TRANSITION_CATALOG["whip_pan"]
            else:
                trans = TRANSITION_CATALOG["clean_hard_cut"]

            sc_copy["transition_in"] = trans
            decorated.append(sc_copy)

        return decorated

if __name__ == "__main__":
    test_scenes = [
        {"role": "hook", "narration": "Endrick to Milan? There's one detail that changes everything."},
        {"role": "situation", "narration": "Reports confirm formal negotiations have opened."},
        {"role": "clause", "visual": {"kind": "explainer_contract_card"}, "narration": "Madrid demand an 80 million buyback clause."},
        {"role": "tactical", "visual": {"kind": "explainer_tactical_card"}, "narration": "Milan offer immediate starting minutes."},
        {"role": "verdict", "narration": "Would you sell him or keep him? Tell us below."}
    ]
    planned = TransitionDirector.plan_transitions_for_scenes(test_scenes)
    for i, s in enumerate(planned):
        print(f"Scene {i+1}: Transition In -> {s['transition_in']['id']}")
