import os
import sys
import time
from pathlib import Path
import torch
import soundfile as sf
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.stages.martin_tyler_synthesizer import get_base_model, get_martin_tyler_prompt, master_commentator_audio

def test_martin():
    print("Testing Martin Tyler voice clone with Qwen3-TTS...")
    model = get_base_model()
    prompt = get_martin_tyler_prompt()
    
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
    raw_path = PROJECT_ROOT / "temp" / "raw_martin_audition.wav"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(raw_path), wavs[0], sr)
    dur = len(wavs[0]) / sr
    print(f"Raw Martin Tyler duration: {dur:.2f}s")
    
    out_master = PROJECT_ROOT / "temp" / "master_martin_audition.mp3"
    master_commentator_audio(raw_path, out_master)
    print(f"Mastered saved to: {out_master}")

if __name__ == "__main__":
    test_martin()
