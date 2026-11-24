import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "beta"))

from stages.qwen_tts_synthesizer import synthesize_qwen3

test_text = "Milan have made their move, but Mourinho wants him to stay."
test_out = Path("beta/workspaces/endrick_milan/run_v7_1/voice/test_s01.wav")

print("Testing Qwen3-TTS synthesis...")
t0 = time.time()
try:
    out, dur = synthesize_qwen3(
        text=test_text,
        output_path=test_out,
        speaker="Ryan",
        instruct="A mature British male sports correspondent delivering breaking football transfer news. Measured, authoritative, calm baritone with clear British pronunciation.",
        language="English"
    )
    print(f"Success! Generated: {out} ({dur:.2f}s) in {time.time()-t0:.2f}s")
except Exception as e:
    print(f"Failed with exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
