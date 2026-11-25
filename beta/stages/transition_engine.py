"""
beta/stages/transition_engine.py - Purposeful Editorial Transition Director (V2.5).

Enforces:
1. Narrative Motivation: Transitions match editorial story beats:
   - cross_fade_in: Clean dark-navy studio fade-in on S01 opening.
   - camera_flash: Crisp 6-frame exposure peak flash + scale punch on protagonist reveal (S02).
   - whip_pan: Cubic-bezier directional horizontal push for club-to-club / duel switches (S03, S07).
   - document_snap: Vertical card snap-in for reported fee/contract & boardroom stance beats (S04, S05).
   - shutter_wipe: Angled geometric clip-path sweep for tactical shifts.
   - cross_dissolve: Smooth broadcast crossfade for status continuity beats.
2. Timing Discipline: Bounded cleanly under 0.28s (<= 8 frames @ 30fps) using GPU transforms only.
"""

from typing import Dict, List, Any

TRANSITION_CATALOG = {
    "cross_fade_in": {
        "id": "cross_fade_in",
        "duration_sec": 0.20,
        "type": "cross_fade_in",
        "sfx_cue": None,
        "description": "Clean opening studio reveal fade-in."
    },
    "camera_flash": {
        "id": "camera_flash",
        "duration_sec": 0.20,
        "type": "camera_flash",
        "sfx_cue": "camera_shutter",
        "description": "Brief exposure peak glint + crisp scale punch for protagonist identity reveal."
    },
    "document_snap": {
        "id": "document_snap",
        "duration_sec": 0.24,
        "type": "document_snap",
        "sfx_cue": "contract_stamp",
        "description": "Crisp upward snap for financial packages, clauses, and managerial stances."
    },
    "whip_pan": {
        "id": "whip_pan",
        "duration_sec": 0.26,
        "type": "whip_pan",
        "sfx_cue": "paper_slide",
        "description": "Directional cubic-bezier lateral sweep for club switches and split verdicts."
    },
    "shutter_wipe": {
        "id": "shutter_wipe",
        "duration_sec": 0.26,
        "type": "shutter_wipe",
        "sfx_cue": None,
        "description": "Angled geometric broadcast clip-path wipe."
    },
    "cross_dissolve": {
        "id": "cross_dissolve",
        "duration_sec": 0.24,
        "type": "cross_dissolve",
        "sfx_cue": None,
        "description": "Smooth editorial opacity cross-dissolve."
    },
    "record_stop_cut": {
        "id": "record_stop_cut",
        "duration_sec": 0.16,
        "type": "camera_flash",
        "sfx_cue": "record_stop",
        "description": "Crisp impact accent for sudden plot twists or contradictions."
    },
    "clean_hard_cut": {
        "id": "clean_hard_cut",
        "duration_sec": 0.14,
        "type": "cross_dissolve",
        "sfx_cue": None,
        "description": "Ultra-brisk broadcast transition preserving tempo."
    }
}


class TransitionDirector:
    """Selects purposeful transitions based on scene narrative roles & screenplay hints."""

    @staticmethod
    def plan_transitions_for_scenes(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        decorated = []
        for idx, sc in enumerate(scenes):
            sc_copy = dict(sc)
            sid = str(sc.get("scene_id", "")).upper()
            hint = (sc.get("transition_hint") or "").strip().lower()
            v_kind = (sc.get("visual") or {}).get("kind", "")
            narr = (sc.get("narration") or "").lower()

            if sid == "OUTRO":
                trans = TRANSITION_CATALOG["cross_dissolve"]
            elif hint and hint in TRANSITION_CATALOG:
                trans = TRANSITION_CATALOG[hint]
            elif idx == 0:
                trans = TRANSITION_CATALOG["cross_fade_in"]
            elif sid == "S02":
                trans = TRANSITION_CATALOG["camera_flash"]
            elif sid in ("S03", "S07") or sc.get("motion", {}).get("type") == "split_duel":
                trans = TRANSITION_CATALOG["whip_pan"]
            elif "explainer" in v_kind or "fee" in v_kind or sid in ("S04",):
                trans = TRANSITION_CATALOG["document_snap"]
            elif sid == "S05" or "refuse" in narr or "reject" in narr or "order" in narr:
                trans = TRANSITION_CATALOG["shutter_wipe"]
            else:
                trans = TRANSITION_CATALOG["cross_dissolve"]

            sc_copy["transition_in"] = trans
            decorated.append(sc_copy)

        return decorated
