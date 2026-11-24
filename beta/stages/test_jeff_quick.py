import os
import sys
import time
from pathlib import Path
import torch
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.jeff_stelling_synthesizer import get_base_model, get_jeff_stelling_prompt

def test():
    print("Testing Jeff Stelling voice clone with Qwen3-TTS...")
    model = get_base_model()
    prompt = get_jeff_stelling_prompt()
    
    text = "Milan have made their move, but Mourinho wants him to stay. Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses."
    print(f"Synthesizing test passage: {text}")
    t0 = time.time()
    wavs, sr = model.generate_voice_clone(
        text=text,
        language="English",
        voice_clone_prompt=prompt,
        non_streaming_mode=True,
        temperature=0.7,
        repetition_penalty=1.1,
    )
    print(f"Synthesis finished in {time.time()-t0:.2f}s!")
    out_path = PROJECT_ROOT / "temp" / "test_jeff_audition.wav"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), wavs[0], sr)
    dur = len(wavs[0]) / sr
    print(f"Saved to {out_path} (duration: {dur:.2f}s)")

if __name__ == "__main__":
    test()
