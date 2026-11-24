import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "beta"))

from stages.dual_script_architecture import expand_spoken_tokens, calculate_spoken_duration

cands = [
    "Italian reports put Milan's package for Endrick at sixty million euros, plus ten in potential bonuses.",
    "Italian reports put Milan's proposed Endrick package at sixty million euros, plus ten in potential bonuses.",
    "Italian reports link Endrick to Milan's proposed package of sixty million euros, plus ten in bonuses.",
    "Italian reports connect Endrick to Milan's proposed sixty million euros, plus ten in potential bonuses."
]

for c in cands:
    toks = expand_spoken_tokens(c)
    words = c.split()
    print(f"words={len(words)}, tokens={len(toks)}: {c}")

s01 = "Milan are plotting a January approach, but reports say Mourinho resists."
s02 = "Italian reports put Milan's package for Endrick at sixty million euros, plus ten in potential bonuses."
s03 = "Madrid discussed eighty to eighty-five million repurchase terms, but nothing is agreed."
s04 = "Now a left-adductor injury adds another complication, with no official return date."
s05 = "Will Mourinho keep the Brazilian or will Milan force a compromise?"

print("\n--- BEAT BREAKDOWN ---")
full_script = [("S01", s01, 1, 1), ("S02", s02, 1, 1), ("S03", s03, 1, 1), ("S04", s04, 1, 1), ("S05", s05, 0, 1)]

total_w = 0
total_t = 0
total_p = 0.0
curr_time = 0.0

for sid, text, commas, terminals in full_script:
    words = len(text.split())
    tokens = expand_spoken_tokens(text)
    t_cnt = len(tokens)
    speech = (t_cnt / 138.0) * 60.0
    pause = (commas * 0.18) + (terminals * 0.32)
    dur = round(speech + pause, 2)
    start_t = round(curr_time, 2)
    end_t = round(curr_time + dur, 2)
    curr_time = end_t
    total_w += words
    total_t += t_cnt
    total_p += pause
    print(f"{sid}: {words}w | {t_cnt}t | pause={pause:.2f}s | dur={dur:.2f}s | [{start_t:.2f}s - {end_t:.2f}s]")
    print(f"     \"{text}\"")

print(f"\nTOTALS:")
print(f"Written words: {total_w} (Expected: 62)")
print(f"Spoken tokens: {total_t} (Expected: 64)")
print(f"Speech time: {(total_t / 138.0 * 60):.2f}s (Expected: 27.83s)")
print(f"Total pauses: {total_p:.2f}s (Expected: 2.32s)")
print(f"Total duration: {curr_time:.2f}s (Expected: 30.15s)")
