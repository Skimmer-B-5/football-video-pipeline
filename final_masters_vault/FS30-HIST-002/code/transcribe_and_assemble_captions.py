"""
Transcribe each audio beat using Whisper with word-level timestamps and assemble
punchy MrBeast-style subtitle timeline into zidane_mrbeast_captions.json.
"""

import json
from pathlib import Path
import whisper
import torch

RUN_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\runs\zidane_headbutt_story")
AUDIO_DIR = RUN_DIR / "audio"

BEATS_METADATA = [
    ("beat_1", 0.0, 8.0),
    ("beat_2", 8.0, 16.5),
    ("beat_3", 16.5, 28.0),
    ("beat_4", 28.0, 39.5),
    ("beat_5", 39.5, 51.5),
    ("beat_6", 51.5, 56.0),
    ("outro_speech", 56.0, 60.0)
]

def run_transcription_and_assembly():
    print("=" * 70)
    print("  WHISPER WORD-LEVEL TRANSCRIPTION & MRBEAST TIMELINE ASSEMBLY")
    print("=" * 70)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Whisper base.en model on {device}...")
    model = whisper.load_model("base.en", device=device)

    all_beat_words = {}
    for bid, start_off, target_dur in BEATS_METADATA:
        timed_wav = AUDIO_DIR / f"{bid}_timed.wav"
        print(f"Transcribing {timed_wav.name}...")
        result = model.transcribe(
            str(timed_wav),
            language="en",
            word_timestamps=True,
            temperature=0.0
        )
        
        words = []
        for segment in result.get("segments", []):
            for w in segment.get("words", []):
                cleaned_word = w["word"].strip().upper().replace(",", "").replace(".", "").replace(";", "").replace(":", "")
                if cleaned_word:
                    words.append({
                        "word": cleaned_word,
                        "start": round(w["start"], 2),
                        "end": round(w["end"], 2)
                    })
        all_beat_words[bid] = words
        print(f"  -> Extracted {len(words)} words for {bid}")

    # Save raw whisper data
    with open(RUN_DIR / "zidane_whisper_by_beat.json", "w") as f:
        json.dump(all_beat_words, f, indent=2)

    # Assemble into 2-4 word punchy phrases
    all_phrases = []
    for bid, global_offset, target_dur in BEATS_METADATA:
        words = all_beat_words.get(bid, [])
        if not words:
            continue
        
        # Group words in chunks of 2 to 4 words
        chunk_size = 3
        chunks = []
        i = 0
        while i < len(words):
            remaining = len(words) - i
            if remaining == 4:
                chunks.append(words[i:i+2])
                chunks.append(words[i+2:i+4])
                break
            elif remaining <= 3:
                chunks.append(words[i:])
                break
            else:
                chunks.append(words[i:i+3])
                i += 3

        for chunk in chunks:
            p_words = []
            for w in chunk:
                w_start = round(global_offset + w["start"], 2)
                w_end = round(global_offset + w["end"], 2)
                if w_end <= w_start:
                    w_end = w_start + 0.15
                elif w_end - w_start < 0.10:
                    w_end = w_start + 0.12
                p_words.append({
                    "word": w["word"],
                    "start": w_start,
                    "end": w_end
                })
            
            p_start = p_words[0]["start"]
            p_end = p_words[-1]["end"]
            all_phrases.append({
                "beat": bid,
                "start": p_start,
                "end": p_end + 0.08,
                "words": p_words
            })

    # Smooth minor gaps between consecutive phrases in same beat
    for k in range(len(all_phrases) - 1):
        c_p = all_phrases[k]
        n_p = all_phrases[k + 1]
        if c_p["beat"] == n_p["beat"] and 0 < (n_p["start"] - c_p["end"]) < 0.25:
            c_p["end"] = n_p["start"]

    out_captions = RUN_DIR / "zidane_mrbeast_captions.json"
    with open(out_captions, "w") as f:
        json.dump(all_phrases, f, indent=2)

    print(f"\n✓ Successfully generated {len(all_phrases)} MrBeast subtitle bursts across 60.0s.")
    print(f"✓ Saved to {out_captions.name}")

if __name__ == "__main__":
    run_transcription_and_assembly()
