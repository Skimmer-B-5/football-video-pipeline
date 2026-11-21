"""
Stage 3: plan_frames
Loads prompts/frames.md as system prompt.
Calls GPT-OSS 120B with the script JSON.
Performs strict deterministic code validation, sanitizes unknown animations,
retries on failure, and prints a readable plan for --dry-run.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

from fs30.config import PROJECT_ROOT, load_config
from fs30.llm import call_llm_json
from fs30.models import (
    ALLOWED_ENTER, ALLOWED_IDLE, ALLOWED_EXIT,
    ALLOWED_TRANSITIONS, ALLOWED_CAMERA_MOVES,
    ALLOWED_CAMERA_INTENSITIES, ALLOWED_PAPER_SHAPES,
    ALLOWED_LAYER_ROLES
)

PROMPT_FRAMES_PATH = PROJECT_ROOT / "prompts" / "frames.md"

def count_words(text: str) -> int:
    return len([w for w in text.split() if w.strip()])

def sanitize_and_log_animations(plan: Dict[str, Any], log_func=print) -> Tuple[Dict[str, Any], List[str]]:
    """
    If unknown enter/idle/exit/transition names exist in the plan:
    replaces with 'none' or 'cut' and logs it, without failing validation.
    """
    sanitized_warnings = []
    scenes = plan.get("scenes", [])

    for s_idx, scene in enumerate(scenes):
        # Sanitize transition
        trans = scene.get("transition_out", "cut")
        if trans not in ALLOWED_TRANSITIONS:
            sanitized_warnings.append(f"Scene {scene.get('id', s_idx+1)}: unknown transition_out '{trans}' replaced with 'cut'")
            scene["transition_out"] = "cut"

        # Sanitize camera move
        cam = scene.get("camera", {})
        if isinstance(cam, dict):
            move = cam.get("move", "push_in")
            if move not in ALLOWED_CAMERA_MOVES:
                sanitized_warnings.append(f"Scene {scene.get('id', s_idx+1)}: unknown camera move '{move}' replaced with 'push_in'")
                cam["move"] = "push_in"
            intensity = cam.get("intensity", "low")
            if intensity not in ALLOWED_CAMERA_INTENSITIES:
                cam["intensity"] = "low"

        # Sanitize layers
        for l_idx, layer in enumerate(scene.get("layers", [])):
            enter = layer.get("enter", "none")
            if enter not in ALLOWED_ENTER:
                sanitized_warnings.append(f"Scene {scene.get('id')}, layer {l_idx}: unknown enter '{enter}' replaced with 'none'")
                layer["enter"] = "none"

            idle = layer.get("idle", "none")
            if idle not in ALLOWED_IDLE:
                sanitized_warnings.append(f"Scene {scene.get('id')}, layer {l_idx}: unknown idle '{idle}' replaced with 'none'")
                layer["idle"] = "none"

            exit_anim = layer.get("exit", "none")
            if exit_anim not in ALLOWED_EXIT:
                sanitized_warnings.append(f"Scene {scene.get('id')}, layer {l_idx}: unknown exit '{exit_anim}' replaced with 'none'")
                layer["exit"] = "none"

    return plan, sanitized_warnings

def validate_plan(plan: Dict[str, Any], script_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates plan strictly against all Part 1 & Part 3 rules.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    # 1. Palette check
    palette = plan.get("palette", {})
    if not isinstance(palette, dict):
        errors.append("Missing or invalid 'palette' object")
        palette_colors = set()
    else:
        palette_colors = set(palette.keys()) | set(palette.values())
        for acc in ["accent1", "accent2", "accent3", "paper"]:
            if acc not in palette:
                errors.append(f"Palette missing required key: '{acc}'")

    # 2. Assets check
    assets = plan.get("assets", [])
    if not isinstance(assets, list) or len(assets) == 0:
        errors.append("Assets list is empty or invalid")
    else:
        for idx, a in enumerate(assets):
            a_id = a.get("id", f"asset_{idx}")
            if not a.get("search_query"):
                errors.append(f"Asset '{a_id}' is missing required 'search_query'")
            if not a.get("fallback_query"):
                errors.append(f"Asset '{a_id}' is missing required 'fallback_query'")

    # 3. Scenes count check (6 to 9)
    scenes = plan.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append("Scenes field is not a list")
        return False, errors

    if not (6 <= len(scenes) <= 9):
        errors.append(f"Expected 6 to 9 scenes, got {len(scenes)}")

    # 4. Narration continuity check: concatenated scene narrations must equal script narration exactly
    script_beats = script_data.get("beats", [])
    script_words = [w for b in script_beats for w in b.get("narration", "").split() if w]
    scene_words = [w for s in scenes for w in s.get("narration", "").split() if w]

    script_joined = " ".join(script_words).lower()
    scene_joined = " ".join(scene_words).lower()

    if script_joined != scene_joined:
        errors.append(
            f"Narration mismatch: scene narrations concatenated do not match script narration.\n"
            f"Script ({len(script_words)} words): '{' '.join(script_words)[:80]}...'\n"
            f"Scenes ({len(scene_words)} words): '{' '.join(scene_words)[:80]}...'"
        )

    # 5. Scene-by-scene validation
    for i, sc in enumerate(scenes):
        s_id = sc.get("id", i + 1)
        layers = sc.get("layers", [])

        # Check layers count (2 to 5)
        if not (2 <= len(layers) <= 5):
            errors.append(f"Scene {s_id}: expected 2 to 5 layers, got {len(layers)}")

        # Check ordered by z
        z_vals = [l.get("z", 0) for l in layers if isinstance(l, dict)]
        if z_vals != sorted(z_vals):
            errors.append(f"Scene {s_id}: layers are not ordered by z ({z_vals})")

        # Check at most ONE subject layer per scene
        subject_count = sum(1 for l in layers if l.get("role") == "subject")
        if subject_count > 1:
            errors.append(f"Scene {s_id}: has {subject_count} subject layers (maximum allowed is 1)")

        # Check text_card max 6 words
        for l in layers:
            if l.get("role") == "text_card":
                card_text = l.get("text", "")
                if count_words(card_text) > 6:
                    errors.append(f"Scene {s_id}: text_card exceeds 6 words ({count_words(card_text)} words): '{card_text}'")

        # Check colours come from palette
        for l in layers:
            c = l.get("color")
            if c:
                if c not in ["accent1", "accent2", "accent3", "paper"] and c not in palette.values():
                    errors.append(f"Scene {s_id}: color '{c}' is not from the palette ({list(palette_colors)})")

        # Check at most 2 layers entering at the same enter_delay
        delays = [l.get("enter_delay", 0.0) for l in layers if l.get("enter") != "none"]
        delay_counts = Counter(delays)
        for d, count in delay_counts.items():
            if count > 2:
                errors.append(f"Scene {s_id}: {count} layers enter at the same enter_delay {d}s (maximum allowed is 2)")

        # Check adjacent scene camera and transition rules
        if i > 0:
            prev_cam = scenes[i - 1].get("camera", {}).get("move")
            curr_cam = sc.get("camera", {}).get("move")
            if curr_cam and curr_cam == prev_cam:
                errors.append(f"Scene {s_id}: shares camera move '{curr_cam}' with adjacent Scene {scenes[i-1].get('id', i)}")

            prev_trans = scenes[i - 1].get("transition_out")
            curr_trans = sc.get("transition_out")
            if curr_trans and curr_trans == prev_trans:
                errors.append(f"Scene {s_id}: shares transition_out '{curr_trans}' with adjacent Scene {scenes[i-1].get('id', i)}")

    return len(errors) == 0, errors

def print_readable_plan(plan: Dict[str, Any], script_data: Dict[str, Any]):
    """Prints a beautiful, formatted dry-run plan."""
    print("\n" + "=" * 80)
    print("  FS 30 — DRY-RUN STORYBOARD & FRAME PLAN")
    print(f"  Title: {script_data.get('title', 'Untitled')} | Certainty: {script_data.get('certainty', 'N/A').upper()}")
    print("=" * 80)

    pal = plan.get("palette", {})
    print(f"\n🎨 PALETTE: accent1={pal.get('accent1')} | accent2={pal.get('accent2')} | accent3={pal.get('accent3')} | paper={pal.get('paper')}")

    print("\n📦 ASSETS TO FETCH:")
    for a in plan.get("assets", []):
        print(f"  • [{a.get('id')}] ({a.get('type')}) Query: \"{a.get('search_query')}\" | Fallback: \"{a.get('fallback_query')}\" (Alt: {a.get('subject_alt')})")

    print("\n🎬 SCENES BREAKDOWN:")
    for sc in plan.get("scenes", []):
        sid = sc.get("id")
        beat = sc.get("beat", "").upper()
        cam = sc.get("camera", {})
        trans = sc.get("transition_out", "")
        est = sc.get("est_seconds", 0.0)
        print(f"\n┌─ [SCENE {sid} | {beat} | {est}s] ──────────────────────────────────────────")
        print(f"│ 🎙 Spoken: \"{sc.get('narration', '')}\"")
        print(f"│ 🎥 Camera: {cam.get('move')} ({cam.get('intensity')}) ➔ Transition Out: {trans}")
        print("│ 📑 Layers (Back to Front):")
        for l in sc.get("layers", []):
            role = l.get("role")
            z = l.get("z")
            enter = l.get("enter", "none")
            delay = l.get("enter_delay", 0.0)
            idle = l.get("idle", "none")
            
            detail = ""
            if role == "background":
                detail = f"Asset={l.get('asset')}"
            elif role == "subject":
                detail = f"Asset={l.get('asset')}"
            elif role == "paper_shape":
                detail = f"Shape={l.get('shape')}, Color={l.get('color')}"
            elif role == "text_card":
                detail = f"Card Text=\"{l.get('text')}\""
            elif role == "foreground":
                detail = f"Shape={l.get('shape')}"
                
            print(f"│    z={z} | {role:<12} | {detail:<32} | Enter: {enter} (+{delay}s) | Idle: {idle}")
        print("└────────────────────────────────────────────────────────────────────────")
    print("=" * 80 + "\n")

def plan_frames(
    script_data: Dict[str, Any],
    run_dir: Path,
    config: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    llm_func=None,
    log_func=print
) -> Dict[str, Any]:
    """
    Executes Stage 3: Loads prompts/frames.md, calls LLM,
    validates rules strictly, sanitizes unknown animations, and saves plan.json.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    out_file = run_dir / "plan.json"
    report_file = run_dir / "report.json"

    if config is None:
        config = load_config()

    llm_cfg = config.get("llm", {})
    val_retries = llm_cfg.get("validation_retries", 2)

    with open(PROMPT_FRAMES_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()

    base_user_message = f"SCRIPT JSON:\n{json.dumps(script_data, indent=2)}"
    current_user_message = base_user_message
    caller = llm_func or call_llm_json

    validation_history = []
    final_plan = None

    for attempt in range(val_retries + 1):
        log_func(f"[Stage 3: plan_frames] Planning scenes with GPT-OSS 120B (attempt {attempt + 1}/{val_retries + 1})...")
        plan_candidate = caller(system_prompt, current_user_message, log_func=log_func)

        # 1. Sanitize animations (brief specifies: if unknown, replace with none/cut and log it, do not fail)
        plan_candidate, warnings = sanitize_and_log_animations(plan_candidate, log_func=log_func)
        for w in warnings:
            log_func(f"[Stage 3: plan_frames] ℹ {w}")

        # 2. Strict validation
        is_valid, errors = validate_plan(plan_candidate, script_data)

        if is_valid:
            log_func(f"[Stage 3: plan_frames] ✓ Plan passed all validation checks ({len(plan_candidate.get('scenes', []))} scenes)!")
            final_plan = plan_candidate
            break
        else:
            log_func(f"[Stage 3: plan_frames] ⚠ Plan validation failed with {len(errors)} error(s):")
            for err in errors:
                log_func(f"    - {err}")
            validation_history.append({"attempt": attempt + 1, "errors": errors})

            # Prepare retry prompt appending the exact validation error
            error_bullets = "\n".join(f"- {e}" for e in errors)
            current_user_message = (
                f"{base_user_message}\n\n"
                f"CRITICAL: Your previous frame plan failed validation with the following errors:\n"
                f"{error_bullets}\n"
                f"You MUST fix every error. Ensure 6 to 9 scenes, exact narration matching script text, "
                f"no adjacent duplicate camera moves or transitions, at most one subject per scene, and max 6 words per text_card."
            )

    if not final_plan:
        error_summary = {
            "stage": "plan_frames",
            "status": "FAILED",
            "validation_errors": validation_history
        }
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(error_summary, f, indent=2)
        raise ValueError(f"Stage 3 failed validation after {val_retries + 1} attempts. See {report_file.name}")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_plan, f, indent=2)

    if dry_run:
        print_readable_plan(final_plan, script_data)

    return final_plan
