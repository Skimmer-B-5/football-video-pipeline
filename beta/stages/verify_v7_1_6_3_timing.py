import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "beta"))

from stages.dual_script_architecture import expand_spoken_tokens

beats = [
    ("S01", "Milan have made their move, but Mourinho wants him to stay.", 1, 1),
    ("S02", "Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.", 1, 1),
    ("S03", "Reports cite eighty to eighty-five million repurchase figures, but nothing is agreed.", 1, 1),
    ("S04", "Now a left-leg muscle injury complicates matters, with no official return date.", 1, 1),
    ("S05", "Will Mourinho keep the Brazilian or will Milan force a compromise?", 0, 1)
]

wpm = 138.0
unrounded_curr = 0.0
total_w = 0
total_t = 0
total_pause = 0.0

print("--- VERIFYING V7.1.6.3 TIMINGS & UNROUNDED BOUNDARIES ---")
for sid, text, commas, terminals in beats:
    words = len(text.split())
    tokens = expand_spoken_tokens(text)
    t_cnt = len(tokens)
    speech = (t_cnt / wpm) * 60.0
    pause = (commas * 0.18) + (terminals * 0.32)
    unrounded_dur = speech + pause
    disp_dur = round(unrounded_dur, 2)
    
    start_disp = round(unrounded_curr, 2)
    unrounded_curr += unrounded_dur
    end_disp = round(unrounded_curr, 2)
    
    total_w += words
    total_t += t_cnt
    total_pause += pause
    
    print(f"{sid}: {words}w | {t_cnt}t | pause={pause:.2f}s | disp_dur={disp_dur:.2f}s | timeline=[{start_disp:.2f}s - {end_disp:.2f}s]")
    print(f"     \"{text}\"")
    print(f"     tokens={tokens}")

print(f"\nTOTALS:")
print(f"Total written words: {total_w} (Expected: 62)")
print(f"Total spoken tokens: {total_t} (Expected: 64)")
print(f"Total speech time: {(total_t / wpm * 60):.4f}s (Expected: 27.8261s -> 27.83s)")
print(f"Total pauses: {total_pause:.2f}s (Expected: 2.32s)")
print(f"Unrounded master duration: {unrounded_curr:.7f}s")
print(f"Displayed master duration: {round(unrounded_curr, 2):.2f}s (Expected: 30.15s)")
