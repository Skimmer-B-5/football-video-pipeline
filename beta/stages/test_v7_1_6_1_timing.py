import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "beta"))

from stages.dual_script_architecture import expand_spoken_tokens, calculate_spoken_duration

# Proposed S02:
s02 = "Italian reports put Milan's proposed package at sixty million euros, plus ten million in potential bonuses."
# Proposed S04:
s04_with_comma = "Now a left-adductor injury adds another complication, with no official return date."
s04_no_comma = "Now a left-adductor injury adds another complication with no official return date."
# Proposed S03:
s03 = "Madrid discussed eighty to eighty-five million repurchase terms, but nothing is agreed."
# Proposed S05:
s05_with_comma = "Will Mourinho keep the Brazilian, or will Milan force a compromise?"
s05_no_comma = "Will Mourinho keep the Brazilian or will Milan force a compromise?"

print("S02:", calculate_spoken_duration(s02))
print("S03:", calculate_spoken_duration(s03))
print("S04 (no comma):", calculate_spoken_duration(s04_no_comma))
print("S05 (no comma):", calculate_spoken_duration(s05_no_comma))

# Check S01 options:
s01_candidates = [
    "Milan are plotting a January approach, but reports say José Mourinho refuses to let him leave.",
    "Milan are plotting a January approach, but reports say José Mourinho resists an exit.",
    "Milan are plotting a January approach, but reporting indicates José Mourinho resists an exit.",
    "Milan are plotting a January approach, but reports say Mourinho refuses to let him leave.",
    "Milan are plotting a January approach, but current reporting says José Mourinho resists an exit.",
    "Milan are plotting a January approach, but reports suggest José Mourinho resists an exit.",
]

for c in s01_candidates:
    w, t, d = calculate_spoken_duration(c)
    print(f"S01 cand ({t} tokens, {d}s): {c}")
