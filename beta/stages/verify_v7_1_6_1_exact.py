import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "beta"))

from stages.dual_script_architecture import expand_spoken_tokens

beats = [
    {
        "id": "S01",
        "dialogue": "Milan are plotting a January approach, but reports say Mourinho resists.",
        "commas": 1,
        "terminals": 1,
    },
    {
        "id": "S02",
        "dialogue": "Italian reports put Milan's proposed package at sixty million euros, plus ten million in potential bonuses.",
        "commas": 1,
        "terminals": 1,
    },
    {
        "id": "S03",
        "dialogue": "Madrid discussed eighty to eighty-five million repurchase terms, but nothing is agreed.",
        "commas": 1,
        "terminals": 1,
    },
    {
        "id": "S04",
        "dialogue": "Now a left-adductor injury adds another complication, with no official return date.",
        "commas": 0,  # Explicit mandate: 1 terminal punctuation mark only -> 0.32s
        "terminals": 1,
    },
    {
        "id": "S05",
        "dialogue": "Will Mourinho keep the Brazilian or will Milan force a compromise?",
        "commas": 0,  # Explicit mandate: 1 terminal punctuation mark only -> 0.32s
        "terminals": 1,
    }
]

wpm = 138.0
current_time = 0.0
total_words = 0
total_tokens = 0

print("--- VERIFYING V7.1.6.1 TIMING & TOKENS ---")
for b in beats:
    text = b["dialogue"]
    words = len(text.split())
    tokens = expand_spoken_tokens(text)
    tok_len = len(tokens)
    speech_sec = (tok_len / wpm) * 60.0
    pause_sec = (b["commas"] * 0.18) + (b["terminals"] * 0.32)
    dur = round(speech_sec + pause_sec, 2)
    start_t = round(current_time, 2)
    end_t = round(current_time + dur, 2)
    current_time = end_t
    total_words += words
    total_tokens += tok_len
    print(f"Beat {b['id']}: {words} words | {tok_len} tokens | pause={pause_sec:.2f}s | dur={dur:.2f}s | timeline={start_t:.2f}s - {end_t:.2f}s")
    print(f"  Text: \"{text}\"")
    print(f"  Tokens: {tokens}")

print(f"\nTOTALS:")
print(f"Total Written Words: {total_words}")
print(f"Total Spoken Tokens: {total_tokens}")
print(f"Total Timeline Duration: {round(current_time, 2)}s")
