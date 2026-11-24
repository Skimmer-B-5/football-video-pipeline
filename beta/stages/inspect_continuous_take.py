import os
import sys
from pathlib import Path
import soundfile as sf
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

wav_path = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1" / "voice" / "test_vocal_transitions" / "full_continuous_take_master.wav"

data, sr = sf.read(str(wav_path))
if data.ndim == 2:
    mono = np.mean(data, axis=1)
else:
    mono = data

total_duration = len(mono) / sr
print(f"Total duration: {total_duration:.2f}s")

# Let's find pauses (where RMS < 0.01 for > 0.25s)
frame_len = int(0.02 * sr) # 20ms
rms = [np.sqrt(np.mean(mono[i:i+frame_len]**2)) for i in range(0, len(mono)-frame_len, frame_len)]
times = [i * 0.02 for i in range(len(rms))]

threshold = 0.015
pauses = []
in_pause = False
pause_start = 0

for t, r in zip(times, rms):
    if r < threshold:
        if not in_pause:
            in_pause = True
            pause_start = t
    else:
        if in_pause:
            in_pause = False
            dur = t - pause_start
            if dur >= 0.20:
                pauses.append((round(pause_start, 2), round(t, 2), round(dur, 2)))

print(f"Found {len(pauses)} pauses:")
for idx, (s, e, d) in enumerate(pauses):
    print(f"  Pause {idx+1}: {s:.2f}s - {e:.2f}s ({d:.2f}s)")
