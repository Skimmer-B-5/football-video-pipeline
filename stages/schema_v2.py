"""
# PROVENANCE: Copied from stages/schema_v2.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Structured Scene Plan Schema v2.0 & Invariant Validator.
Enforces the strict data contract between Script Generation, Visual Planning, TTS, and FFmpeg Assembly.
"""

import re
from typing import Dict, List, Any, Tuple

VALID_ROLES = {
    "hook", "evidence_context", "player_context", "deal_mechanics",
    "tactical_fit", "risk_obstacle", "analysis", "debate", "outro"
}

VALID_VISUAL_KINDS = {
    "player_photo", "manager_photo", "club_photo", "match_action",
    "licensed_match_clip", "training_photo", "press_conference",
    "tactical_diagram", "stat_card", "transfer_flow_graphic",
    "contract_or_clause_graphic", "timeline", "league_table_or_ranking",
    "quote_card", "generic_atmosphere"
}

VALID_BADGES = {
    "REPORTED", "RUMOUR", "CONFIRMED", "ANALYSIS", "TACTICS",
    "FINANCIAL", "CRISIS", "DEBATE", "UPDATE"
}

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace for verbatim invariant check."""
    return re.sub(r'\s+', ' ', text).strip()

def validate_scene_plan_v2(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate structured scene plan against Schema v2.0 invariants.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    # 1. Top-level structure
    required_top = ["story", "editorial_brief", "full_script", "scenes", "ending_question"]
    for field in required_top:
        if field not in data:
            errors.append(f"Missing required top-level field: '{field}'")

    if errors:
        return False, errors

    full_script = normalize_whitespace(data.get("full_script", ""))
    if not full_script:
        errors.append("full_script cannot be empty.")

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list) or len(scenes) < 4 or len(scenes) > 12:
        errors.append(f"Scene count must be dynamic between 4 and 12 scenes (found {len(scenes)}).")

    # Invariant 1: Concatenation of scene narrations must match full_script verbatim
    scene_narrations = []
    seen_scene_ids = set()

    for idx, sc in enumerate(scenes):
        s_id = sc.get("scene_id", f"s{idx+1:02d}")
        if s_id in seen_scene_ids:
            errors.append(f"Duplicate scene_id: '{s_id}'")
        seen_scene_ids.add(s_id)

        narration = normalize_whitespace(sc.get("narration", ""))
        if not narration:
            errors.append(f"Scene {s_id} has empty narration.")
        scene_narrations.append(narration)

        # On-screen metadata validation
        on_screen = sc.get("on_screen", {})
        if not on_screen or not isinstance(on_screen, dict):
            errors.append(f"Scene {s_id} is missing 'on_screen' metadata object.")
        else:
            headline = on_screen.get("headline", "").strip()
            if not headline:
                errors.append(f"Scene {s_id} is missing written on_screen headline.")
            elif len(headline) > 45:
                errors.append(f"Scene {s_id} on_screen headline too long ({len(headline)} chars). Max 45.")

            badge = on_screen.get("status_badge", "").upper().strip()
            if badge and badge not in VALID_BADGES:
                errors.append(f"Scene {s_id} has invalid status_badge: '{badge}'. Must be one of {VALID_BADGES}.")
            if badge == "BREAKING EXCLUSIVE":
                errors.append(f"Scene {s_id} violates rule: 'BREAKING EXCLUSIVE' badge is prohibited.")

        # Visual metadata validation
        visual = sc.get("visual", {})
        if not visual or not isinstance(visual, dict):
            errors.append(f"Scene {s_id} is missing 'visual' metadata object.")
        else:
            kind = visual.get("kind", "").strip()
            if kind not in VALID_VISUAL_KINDS:
                errors.append(f"Scene {s_id} has invalid visual.kind: '{kind}'. Must be in {VALID_VISUAL_KINDS}.")
            must_explain = visual.get("must_explain", "").strip()
            if not must_explain:
                errors.append(f"Scene {s_id} must have a non-empty 'must_explain' visual intent description.")

        # Motion metadata validation
        motion = sc.get("motion", {})
        if not motion or not isinstance(motion, dict):
            errors.append(f"Scene {s_id} is missing 'motion' metadata object.")

    # Check narration match
    joined_narration = normalize_whitespace(" ".join(scene_narrations))
    if full_script and joined_narration != full_script:
        # Check minor punctuation differences vs lost words
        clean_joined = re.sub(r'[^\w\s]', '', joined_narration).lower()
        clean_full = re.sub(r'[^\w\s]', '', full_script).lower()
        if clean_joined != clean_full:
            errors.append("Invariant violated: Concatenated scene narrations do not match full_script verbatim.")

    # Ending question check
    ending_q = data.get("ending_question", "").strip()
    if not ending_q:
        errors.append("Missing required context-specific 'ending_question'.")
    elif not ending_q.endswith("?"):
        errors.append("ending_question must end with a question mark.")

    is_valid = (len(errors) == 0)
    return is_valid, errors
