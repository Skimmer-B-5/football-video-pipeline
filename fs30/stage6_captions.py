"""
Stage 6: captions
Generates word-level timings and paper-style caption cards for each scene.
Preserves original script words (never phonetic spellings).
Formats subtitle cards in the lower-third safe area (160px from bottom, 80px from sides),
displaying 3 to 5 words visible at a time with the active word highlighted in accent1.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

def compute_word_timings(narration: str, total_duration: float, silence_margin: float = 0.3) -> List[Dict[str, Any]]:
    """
    Computes proportional word-level timestamps for the narration text.
    Active voice duration = total_duration - silence_margin.
    """
    words = [w for w in narration.split() if w.strip()]
    if not words:
        return []

    active_dur = max(0.5, total_duration - silence_margin)

    # Calculate proportional weights (character length + punctuation pause)
    weights = []
    for w in words:
        wt = len(w)
        if w.endswith((".", ",", "!", "?")):
            wt += 2
        weights.append(max(2, wt))

    total_weight = sum(weights)
    time_per_weight = active_dur / float(total_weight)

    timings = []
    current_time = 0.0
    for w, wt in zip(words, weights):
        w_dur = wt * time_per_weight
        timings.append({
            "word": w,
            "start": round(current_time, 3),
            "end": round(current_time + w_dur, 3)
        })
        current_time += w_dur

    return timings

def generate_scene_ass_subtitles(
    scene_id: int,
    narration: str,
    total_duration: float,
    palette: Dict[str, str],
    out_ass: Path
) -> Path:
    """
    Generates an ASS subtitle file formatted as a paper-style lower-third card:
    - Safe area: MarginV=160, MarginL=80, MarginR=80
    - 3 to 5 words per line
    - Active word highlighted in accent1
    """
    timings = compute_word_timings(narration, total_duration)
    if not timings:
        return out_ass

    # Accent color in ASS hex format (&H00BBGGRR)
    def hex_to_ass_color(h):
        h = h.lstrip('#')
        r, g, b = h[0:2], h[2:4], h[4:6]
        return f"&H00{b}{g}{r}"

    accent1_ass = hex_to_ass_color(palette.get("accent1", "#C8102E"))
    paper_ass = hex_to_ass_color(palette.get("paper", "#F4EFE6"))

    header = f"""[Script Info]
Title: FS30 Paper-Cut Subtitles - Scene {scene_id}
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: PaperSub,Arial,54,{paper_ass},&H000000FF,&H000A0A0A,&H90000000,-1,0,0,0,100,100,0,0,1,4.0,3.0,2,80,80,180,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def fmt_time(t):
        m = int(t // 60)
        s = int(t % 60)
        cs = int((t - int(t)) * 100)
        return f"0:{m:02d}:{s:02d}.{cs:02d}"

    # Group words into 3 to 5 word chunks (e.g., 4 words)
    chunk_size = 4
    events = []
    for chunk_start in range(0, len(timings), chunk_size):
        chunk = timings[chunk_start:chunk_start + chunk_size]
        for w_idx, active_item in enumerate(chunk):
            w_start = active_item["start"]
            w_end = active_item["end"]
            
            # Format chunk text with active word highlighted
            line_parts = []
            for item in chunk:
                w_str = item["word"].upper()
                if item == active_item:
                    line_parts.append(f"{{\\c{accent1_ass}}}{w_str}{{\\r}}")
                else:
                    line_parts.append(w_str)
            line_text = " ".join(line_parts)

            start_str = fmt_time(w_start)
            end_str = fmt_time(w_end)
            events.append(f"Dialogue: 0,{start_str},{end_str},PaperSub,,0,0,0,,{line_text}")

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

    return out_ass

def generate_all_captions(
    plan_data: Dict[str, Any],
    run_dir: Path,
    log_func=print
) -> Dict[int, Path]:
    """Generates ASS subtitle files for every scene."""
    run_dir = Path(run_dir)
    render_dir = run_dir / "render"
    render_dir.mkdir(parents=True, exist_ok=True)

    palette = plan_data.get("palette", {})
    caption_files = {}

    log_func(f"[Stage 6: captions] Generating word-level subtitle cards for {len(plan_data.get('scenes', []))} scenes...")

    for sc in plan_data.get("scenes", []):
        s_id = sc.get("id")
        narr = sc.get("narration", "")
        dur = sc.get("est_seconds", 4.0)

        ass_file = render_dir / f"scene_{s_id}_captions.ass"
        generate_scene_ass_subtitles(s_id, narr, dur, palette, ass_file)
        caption_files[s_id] = ass_file

    log_func(f"[Stage 6: captions] ✓ All {len(caption_files)} caption track(s) ready.")
    return caption_files
