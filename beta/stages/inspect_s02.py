import soundfile as sf
import numpy as np

data, sr = sf.read('beta/workspaces/endrick_milan/run_v7_1/voice/test_vocal_transitions/beat_S02_master.wav')
if data.ndim == 2:
    data = np.mean(data, axis=1)

win = int(0.02 * sr)
rms = [np.sqrt(np.mean(data[i:i+win]**2)) for i in range(0, len(data)-win, win)]
times = [i * 0.02 for i in range(len(rms))]

print("S02 RMS over first 1.5s:")
for t, r in zip(times[:75], rms[:75]):
    if r > 0.02:
        bar = "#" * int(r * 100)
        print(f"{t:4.2f}s: {bar}")
    else:
        print(f"{t:4.2f}s: (pause)")
