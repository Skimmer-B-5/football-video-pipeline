import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "beta"))

from stages.dual_script_architecture import expand_spoken_tokens

def calc(tokens_count, commas, periods, wpm=138.0):
    speech = (tokens_count / wpm) * 60.0
    pauses = (commas * 0.18) + (periods * 0.32)
    return round(speech + pauses, 2)

# S02: "Italian reports put Milan's proposed package at sixty million euros, plus ten million in potential bonuses."
# 16 tokens, 1 comma, 1 period -> pause 0.50s
s02_tok = 16
s02_dur = calc(16, 1, 1) # 7.46s

# S03: "Madrid discussed eighty to eighty-five million repurchase terms, but nothing is agreed."
# 13 tokens, 1 comma, 1 period -> pause 0.50s
s03_tok = 13
s03_dur = calc(13, 1, 1) # 6.15s

# S04: "Now a left-adductor injury adds another complication, with no official return date."
# User says: S04 and S05 have one terminal punctuation mark each and therefore receive 0.32 seconds, not 0.50 seconds.
# So commas=0, periods=1 -> pause 0.32s
# Tokens: 13 tokens (Now a left adductor injury adds another complication with no official return date)
s04_tok = 13
s04_dur = calc(13, 0, 1) # 5.97s

# S05: "Will Mourinho keep the Brazilian, or will Milan force a compromise?"
# commas=0, periods=1 -> pause 0.32s
# Tokens: 11 tokens
s05_tok = 11
s05_dur = calc(11, 0, 1) # 5.10s

print(f"S02: {s02_tok} tok, {s02_dur}s")
print(f"S03: {s03_tok} tok, {s03_dur}s")
print(f"S04: {s04_tok} tok, {s04_dur}s")
print(f"S05: {s05_tok} tok, {s05_dur}s")
subtotal_tok = s02_tok + s03_tok + s04_tok + s05_tok
subtotal_dur = s02_dur + s03_dur + s04_dur + s05_dur
print(f"Subtotal S02-S05: {subtotal_tok} tokens, {subtotal_dur}s")

# Target total duration: ~29.97s (64 tokens total: 64/138*60 + 2.14 = 29.966s = 29.97s)
needed_s01_tok = 64 - subtotal_tok
print(f"Needed S01 tokens for 64 tokens total: {needed_s01_tok}")
s01_dur = calc(needed_s01_tok, 1, 1) # 1 comma, 1 period
print(f"S01 with {needed_s01_tok} tokens: {s01_dur}s")
print(f"Total tokens: {needed_s01_tok + subtotal_tok}")
print(f"Total duration: {round(s01_dur + s02_dur + s03_dur + s04_dur + s05_dur, 2)}s")
