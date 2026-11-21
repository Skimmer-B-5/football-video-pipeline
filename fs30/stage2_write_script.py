"""
Stage 2: write_script
Loads prompts/script.md as system prompt.
Calls GPT-OSS 120B with formatted story details.
Performs strict deterministic code validation and automated retry with feedback.
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from fs30.config import PROJECT_ROOT, load_config
from fs30.llm import call_llm_json

PROMPT_SCRIPT_PATH = PROJECT_ROOT / "prompts" / "script.md"

def count_words(text: str) -> int:
    """Deterministic word count based on whitespace separation."""
    return len([w for w in text.split() if w.strip()])

def split_sentences(text: str) -> List[str]:
    """Splits text into sentences by terminal punctuation."""
    raw_sentences = re.split(r"[.!?]+", text)
    return [s.strip() for s in raw_sentences if s.strip()]

def contains_emojis(text: str) -> bool:
    """Checks for emoji characters."""
    for char in text:
        if unicodedata.category(char) in ("So", "Cn"):
            return True
        # Explicit emoji code ranges
        if ord(char) > 0x1F000:
            return True
    return False

def validate_script(
    script_data: Dict[str, Any],
    source_name: str,
    words_min: int = 70,
    words_max: int = 85,
    max_sentence_len: int = 16
) -> Tuple[bool, List[str]]:
    """
    Validates script strictly against all brief rules.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    # 1. Schema check
    required_top = ["title", "certainty", "beats", "pronunciation_hints", "word_count"]
    for k in required_top:
        if k not in script_data:
            errors.append(f"Missing required key: '{k}'")

    beats = script_data.get("beats", [])
    if not isinstance(beats, list) or len(beats) != 5:
        errors.append(f"Expected exactly 5 beats, got {len(beats) if isinstance(beats, list) else 'invalid type'}")
        return False, errors

    expected_beats = ["hook", "context", "source", "detail", "outlook"]
    actual_beats = [b.get("beat") for b in beats if isinstance(b, dict)]
    if actual_beats != expected_beats:
        errors.append(f"Beats order mismatch: expected {expected_beats}, got {actual_beats}")

    # 2. Word count check
    total_words = 0
    full_narration_parts = []
    for i, b in enumerate(beats):
        narr = b.get("narration", "")
        if not isinstance(narr, str) or not narr.strip():
            errors.append(f"Beat {i+1} ('{b.get('beat')}') has empty or invalid narration.")
            continue
        total_words += count_words(narr)
        full_narration_parts.append(narr)

    full_narration = " ".join(full_narration_parts)

    reported_wc = script_data.get("word_count", 0)
    if total_words != reported_wc:
        errors.append(f"Reported word_count ({reported_wc}) does not match actual count ({total_words})")

    if not (words_min <= total_words <= words_max):
        errors.append(f"Total narration word count ({total_words}) must be between {words_min} and {words_max}")

    # 3. Disallowed characters check: digits, currency symbols, emojis, hashtags, brackets, quotation marks
    if re.search(r"\d", full_narration):
        digits = re.findall(r"\d+", full_narration)
        errors.append(f"Narration contains digits ({digits}); must spell numbers in words")

    if re.search(r"[$€£¥]", full_narration):
        symbols = re.findall(r"[$€£¥]", full_narration)
        errors.append(f"Narration contains currency symbols ({symbols}); must write money in words")

    if contains_emojis(full_narration):
        errors.append("Narration contains emojis; emojis are strictly prohibited")

    if "#" in full_narration:
        errors.append("Narration contains hashtags (#); hashtags are prohibited")

    if re.search(r"[\(\)\[\]\{\}]", full_narration):
        errors.append("Narration contains brackets or parentheses; brackets are prohibited")

    if re.search(r"[\"“”]", full_narration):
        errors.append("Narration contains quotation marks; quotes are prohibited")

    # 4. Sentence length check (max 16 words per sentence within each beat)
    for b in beats:
        narr = b.get("narration", "")
        sentences = split_sentences(narr)
        if not sentences and narr.strip():
            sentences = [narr.strip()]
        for s in sentences:
            s_words = count_words(s)
            if s_words > max_sentence_len:
                errors.append(f"In beat '{b.get('beat')}', sentence exceeds {max_sentence_len} words ({s_words} words): '{s}'")

    # 5. Source name appears in the 'source' beat
    source_beat = next((b for b in beats if b.get("beat") == "source"), None)
    if source_beat:
        s_narr = source_beat.get("narration", "").lower()
        # Clean source name tokens
        src_tokens = [tok.lower() for tok in re.split(r"\W+", source_name) if len(tok) > 2]
        matched = any(tok in s_narr for tok in src_tokens) if src_tokens else (source_name.lower() in s_narr)
        if not matched:
            errors.append(f"Source name '{source_name}' does not appear in the 'source' beat narration: '{source_beat.get('narration')}'")
    else:
        errors.append("Missing 'source' beat")

    return len(errors) == 0, errors

def write_script(
    story_data: Dict[str, Any],
    run_dir: Path,
    config: Optional[Dict[str, Any]] = None,
    llm_func=None,
    log_func=print
) -> Dict[str, Any]:
    """
    Executes Stage 2: Loads system prompt, formats user input, calls LLM,
    validates rules strictly, and retries on failure up to 2 times.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    out_file = run_dir / "script.json"
    report_file = run_dir / "report.json"

    if config is None:
        config = load_config()

    script_cfg = config.get("script", {})
    words_min = script_cfg.get("words_min", 70)
    words_max = script_cfg.get("words_max", 85)
    max_sentence_len = script_cfg.get("max_sentence_words", 16)
    llm_cfg = config.get("llm", {})
    val_retries = llm_cfg.get("validation_retries", 2)

    with open(PROMPT_SCRIPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()

    source_name = story_data.get("source_name", "The Guardian")
    base_user_message = (
        f"SOURCE NAME: {source_name}\n"
        f"PUBLISHED: {story_data.get('date', 'Today')}\n"
        f"HEADLINE: {story_data.get('headline', '')}\n"
        f"ARTICLE TEXT:\n{story_data.get('article_text', '')}"
    )

    current_user_message = base_user_message
    caller = llm_func or call_llm_json

    validation_history = []
    final_script = None

    for attempt in range(val_retries + 1):
        log_func(f"[Stage 2: write_script] Generating script with GPT-OSS 120B (attempt {attempt + 1}/{val_retries + 1})...")
        script_candidate = caller(system_prompt, current_user_message, log_func=log_func)

        # Validate strictly in code
        is_valid, errors = validate_script(
            script_candidate,
            source_name=source_name,
            words_min=words_min,
            words_max=words_max,
            max_sentence_len=max_sentence_len
        )

        if is_valid:
            log_func(f"[Stage 2: write_script] ✓ Script passed all validation checks ({script_candidate.get('word_count')} words)!")
            final_script = script_candidate
            break
        else:
            log_func(f"[Stage 2: write_script] ⚠ Validation failed with {len(errors)} error(s):")
            for err in errors:
                log_func(f"    - {err}")
            validation_history.append({"attempt": attempt + 1, "errors": errors})
            
            # Prepare retry prompt appending the exact validation error
            error_bullets = "\n".join(f"- {e}" for e in errors)
            current_user_message = (
                f"{base_user_message}\n\n"
                f"CRITICAL: Your previous output failed validation with the following errors:\n"
                f"{error_bullets}\n"
                f"You MUST fix every error. Ensure exactly 5 beats, no digits, no currency symbols, no quotes, "
                f"no sentence over 16 words, word_count exactly between {words_min} and {words_max}, and source name '{source_name}' in the source beat."
            )

    if not final_script:
        error_summary = {
            "stage": "write_script",
            "status": "FAILED",
            "validation_errors": validation_history
        }
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(error_summary, f, indent=2)
        raise ValueError(f"Stage 2 failed validation after {val_retries + 1} attempts. See {report_file.name}")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_script, f, indent=2)

    return final_script
