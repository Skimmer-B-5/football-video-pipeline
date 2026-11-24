import os
import sys
import subprocess
from pathlib import Path
import soundfile as sf
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

test_dir = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1" / "voice" / "test_vocal_transitions"

beats = ["S01", "S02", "S03", "S04", "S05", "outro"]

total_dur = 0.0
print("=== BEAT-BY-BEAT WITH EM-DASH VOCAL PACING ===")
for sid in beats:
    p = test_dir / f"beat_{sid}_master.wav"
    data, sr = sf.read(str(p))
    dur = len(data) / sr
    total_dur += dur
    
    # Check start silence (pause before speech)
    if data.ndim == 2:
        mono = np.mean(data, axis=1)
    else:
        mono = data
        
    lead_silence = 0
    for idx, sample in enumerate(mono):
        if abs(sample) > 0.01:
            lead_silence = idx / sr
            break
            
    print(f"Beat [{sid}]: {dur:.2f}s (lead-in: {lead_silence*1000:.1f}ms)")

print(f"Total Combined Duration: {total_dur:.2f}s")
