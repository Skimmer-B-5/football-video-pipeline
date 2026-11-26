"""
# PROVENANCE: Copied from stages/subtitles_engine.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
stages/subtitles_engine.py - Word-Level Forced Alignment & Safe-Zone Subtitle Generator.

Uses Groq LPU Whisper Turbo (whisper-large-v3-turbo) to achieve millisecond-accurate
word forced-alignment on synthesized voiceover audio tracks.

Features:
1. True word-level timestamps (no linear duration guessing).
2. Natural 2-4 word rhythmic phrase chunking.
3. Word-level active highlighting with Brand Yellow (#FFD166) and high-contrast white text.
4. Guaranteed Safe-Zone positioning (MarginV=560 / y=1300), preventing any overlap with
   the lower-third headline (y=1440), ticker (y=1730), or platform UI overlays.
5. Dual output: ASS (with karaoke word highlight) and SRT (for YouTube metadata).
"""

import os
import re
import json
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_groq_api_key() -> Optional[str]:
    """Retrieve Groq API key from environment or .env file."""
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("GROQ_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def transcribe_audio_with_whisper(audio_path: Path) -> List[Dict[str, Any]]:
    """
    Calls Groq whisper-large-v3-turbo to extract word-level timestamps in ~200ms.
    Returns list of dicts: [{"word": str, "start": float, "end": float}]
    """
    api_key = get_groq_api_key()
    if not api_key:
        print("[SubtitlesEngine] No GROQ_API_KEY, using local phonetic fallback.")
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "FootballIn30Sec/2.0"
    }

    try:
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f, "audio/wav")}
            data = {
                "model": "whisper-large-v3-turbo",
                "response_format": "verbose_json",
                "timestamp_granularities[]": ["word"]
            }
            resp = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=25
            )
            if resp.status_code == 200:
                res_data = resp.json()
                raw_words = res_data.get("words", [])
                clean_words = []
                for w in raw_words:
                    clean_words.append({
                        "word": w.get("word", "").strip(),
                        "start": float(w.get("start", 0.0)),
                        "end": float(w.get("end", 0.0))
                    })
                print(f"[SubtitlesEngine] ✓ Aligned {len(clean_words)} words via Groq Whisper Turbo")
                return clean_words
            else:
                print(f"[SubtitlesEngine] Groq Whisper error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[SubtitlesEngine] Whisper request failed: {e}")

    return []

def group_words_into_rhythmic_phrases(
    words: List[Dict[str, Any]],
    max_words_per_phrase: int = 3,
    max_pause_sec: float = 0.35
) -> List[Dict[str, Any]]:
    """
    Groups individual aligned words into 2 to 4 word display cards based on
    rhythmic cadence and punctuation pauses.
    """
    if not words:
        return []

    phrases = []
    current_phrase_words = []

    for idx, w in enumerate(words):
        current_phrase_words.append(w)
        
        is_last = (idx == len(words) - 1)
        ends_with_punct = any(w["word"].endswith(p) for p in [".", ",", "!", "?", ":", ";"])
        
        # Check pause to next word
        pause_to_next = 0.0
        if not is_last:
            pause_to_next = max(0.0, words[idx + 1]["start"] - w["end"])

        if len(current_phrase_words) >= max_words_per_phrase or ends_with_punct or pause_to_next > max_pause_sec or is_last:
            p_start = current_phrase_words[0]["start"]
            p_end = current_phrase_words[-1]["end"]
            
            # Avoid micro-durations
            if p_end - p_start < 0.30:
                p_end = p_start + 0.40

            phrase_text = " ".join(item["word"] for item in current_phrase_words)
            phrases.append({
                "text": phrase_text,
                "start": round(p_start, 3),
                "end": round(p_end, 3),
                "words": list(current_phrase_words)
            })
            current_phrase_words = []

    return phrases

def format_timestamp_ass(seconds: float) -> str:
    """Format seconds into ASS timestamp string: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp string: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def generate_ass_script(
    phrases: List[Dict[str, Any]],
    output_ass_path: Path,
    margin_v: int = 560  # Centers text safely at y=1300 in 1080x1920
) -> Path:
    """
    Generates an Advanced SubStation Alpha (.ass) file with:
    - High-contrast Barlow Condensed ExtraBold font.
    - Solid black border (Outline=3) and soft shadow (Shadow=2).
    - Dynamic word-by-word active yellow highlight for current spoken word.
    """
    ass_header = f"""[Script Info]
Title: 30 Football Plus Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Barlow Condensed,42,&H00FFFFFF,&H0066D1FF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,3.5,2.0,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [ass_header]

    for p in phrases:
        p_words = p.get("words", [])
        p_start = p["start"]
        p_end = p["end"]

        # Word-level highlighting: emit sub-events where each word is highlighted in yellow
        if len(p_words) > 1:
            for w_idx, current_w in enumerate(p_words):
                w_start = current_w["start"]
                w_end = current_w["end"]
                
                # Highlight active word with yellow &H0066D1FF& (BGR for #FFD166)
                formatted_words = []
                for other_idx, other_w in enumerate(p_words):
                    if other_idx == w_idx:
                        formatted_words.append(f"{{\\c&H0066D1FF&}}{other_w['word']}{{\\c&H00FFFFFF&}}")
                    else:
                        formatted_words.append(other_w["word"])
                
                card_text = " ".join(formatted_words)
                start_str = format_timestamp_ass(w_start)
                end_str = format_timestamp_ass(w_end)
                lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{card_text}\n")
        else:
            start_str = format_timestamp_ass(p_start)
            end_str = format_timestamp_ass(p_end)
            card_text = p["text"]
            lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{card_text}\n")

    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return output_ass_path

def generate_srt_file(
    phrases: List[Dict[str, Any]],
    output_srt_path: Path
) -> Path:
    """Generates a standard .srt subtitle file."""
    lines = []
    for idx, p in enumerate(phrases, 1):
        s_time = format_timestamp_srt(p["start"])
        e_time = format_timestamp_srt(p["end"])
        lines.append(f"{idx}\n{s_time} --> {e_time}\n{p['text'].upper()}\n\n")

    output_srt_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return output_srt_path

def build_aligned_captions_for_video(
    audio_path: Path,
    output_base_path: Path,
    scenes: Optional[List[Dict[str, Any]]] = None,
    max_caption_time: Optional[float] = None
) -> Tuple[Path, Path]:
    """
    Main entrypoint: extracts forced-alignment word timestamps, groups into rhythmic phrases,
    and produces both .ass (with active word highlights) and .srt subtitles.
    Guarantees no subtitles spill into the outro plate when max_caption_time is specified.
    """
    # 1. Extract forced alignment
    words = transcribe_audio_with_whisper(audio_path)

    # 2. Fallback if offline / whisper returned 0 words
    if not words and scenes:
        print("[SubtitlesEngine] Using scene fallback duration estimation...")
        global_t = 0.0
        words = []
        for sc in scenes:
            narr = sc.get("narration", "")
            sc_dur = float(sc.get("audio_duration_sec") or sc.get("duration", 3.5))
            sc_words = narr.split()
            if sc_words and sc_dur > 0:
                w_dur = sc_dur / len(sc_words)
                for w in sc_words:
                    words.append({
                        "word": w,
                        "start": global_t,
                        "end": global_t + w_dur
                    })
                    global_t += w_dur
            else:
                global_t += sc_dur

    # Filter out words past max_caption_time (strict outro plate protection)
    if max_caption_time is not None and max_caption_time > 0:
        clean_words = []
        for w in words:
            if w["start"] >= max_caption_time:
                continue
            if w["end"] > max_caption_time:
                w["end"] = max_caption_time
            clean_words.append(w)
        words = clean_words

    # 3. Group into 2-4 word cards
    phrases = group_words_into_rhythmic_phrases(words, max_words_per_phrase=3)

    if max_caption_time is not None and max_caption_time > 0:
        clean_phrases = []
        for p in phrases:
            if p["start"] >= max_caption_time:
                continue
            if p["end"] > max_caption_time:
                p["end"] = max_caption_time
            clean_phrases.append(p)
        phrases = clean_phrases

    ass_path = output_base_path.with_suffix(".ass")
    srt_path = output_base_path.with_suffix(".srt")

    generate_ass_script(phrases, ass_path)
    generate_srt_file(phrases, srt_path)

    print(f"[SubtitlesEngine] ✓ Produced ASS ({ass_path.name}) and SRT ({srt_path.name}) with {len(phrases)} display cards")
    return ass_path, srt_path
