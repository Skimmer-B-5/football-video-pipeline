import os
import sys
import time
from pathlib import Path
import torch
import soundfile as sf
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.jeff_stelling_synthesizer import get_base_model

def test_fabrizio():
    print("Testing Fabrizio Romano voice clone with Qwen3-TTS...")
    model = get_base_model()
    
    ref_wav = PROJECT_ROOT / "data" / "branding" / "voices" / "fabrizio_romano" / "fabrizio_ref.wav"
    ref_txt = (PROJECT_ROOT / "data" / "branding" / "voices" / "fabrizio_romano" / "fabrizio_ref.txt").read_text(encoding="utf-8").strip()
    
    prompt_cache = PROJECT_ROOT / "models" / "fabrizio_romano_prompt.pt"
    if prompt_cache.exists():
        print("Loading cached prompt...")
        prompt = torch.load(str(prompt_cache), weights_only=False)
    else:
        print("Creating voice clone prompt from reference...")
        prompt = model.create_voice_clone_prompt(
            ref_audio=str(ref_wav),
            ref_text=ref_txt,
            x_vector_only_mode=False
        )
        torch.save(prompt, str(prompt_cache))
        print("Prompt cached successfully!")
    
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
    raw_path = PROJECT_ROOT / "temp" / "raw_fabrizio_audition.wav"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(raw_path), wavs[0], sr)
    dur = len(wavs[0]) / sr
    print(f"Raw Fabrizio duration: {dur:.2f}s")
    
    # Broadcast vocal chain mastering
    out_master = PROJECT_ROOT / "temp" / "master_fabrizio_audition.mp3"
    filter_chain = (
        "highpass=f=90,"
        "lowpass=f=11000,"
        "equalizer=f=3200:t=q:w=1.2:g=2.5,"
        "compand=attacks=0.02:decays=0.15:points=-60/-60|-24/-16|-12/-8|0/-3,"
        "loudnorm=I=-14:TP=-1.0:LRA=7,"
        "aformat=sample_rates=48000:channel_layouts=stereo"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_path),
        "-af", filter_chain,
        "-c:a", "libmp3lame",
        str(out_master)
    ]
    subprocess.run(cmd, check=True)
    print(f"Mastered saved to: {out_master}")

if __name__ == "__main__":
    test_fabrizio()
