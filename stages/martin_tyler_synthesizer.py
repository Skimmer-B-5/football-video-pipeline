"""
# PROVENANCE: Copied from stages/martin_tyler_synthesizer.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ - Safe experimental development environment.
"""

"""
Martin Tyler Legendary Commentator Voice Synthesizer using Qwen3-TTS Zero-Shot Cloning.
Delivers fast-paced, high-energy British football commentary delivery.
Includes broadcast vocal chain mastering (compand, EQ, atempo, loudness normalization).
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MODELS_DIR = PROJECT_ROOT / "models"
MODEL_BASE_PATH = MODELS_DIR / "qwen3_tts_base"
MARTIN_VOICE_DIR = PROJECT_ROOT / "data" / "branding" / "voices" / "martin_tyler"
PROMPT_CACHE_PATH = MODELS_DIR / "martin_tyler_prompt.pt"

_MODEL_INSTANCE = None
_CACHED_PROMPT = None

def get_base_model():
    """Singleton loader for Qwen3-TTS Base model on CUDA."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    import torch
    from qwen_tts import Qwen3TTSModel

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

    model_source = str(MODEL_BASE_PATH)
    print(f"[MartinTyler] Loading Qwen3-TTS Base model from {model_source} on {device} ({dtype})...")
    t0 = time.time()
    _MODEL_INSTANCE = Qwen3TTSModel.from_pretrained(
        model_source,
        device_map=device,
        dtype=dtype,
    )
    print(f"[MartinTyler] Model loaded in {time.time()-t0:.2f}s.")
    return _MODEL_INSTANCE

def get_martin_tyler_prompt():
    """Load or build the cached VoiceClonePromptItem for Martin Tyler."""
    global _CACHED_PROMPT
    if _CACHED_PROMPT is not None:
        return _CACHED_PROMPT

    import torch

    if PROMPT_CACHE_PATH.exists():
        try:
            print(f"[MartinTyler] Loading precomputed voice prompt from {PROMPT_CACHE_PATH.name}...")
            _CACHED_PROMPT = torch.load(str(PROMPT_CACHE_PATH), weights_only=False)
            return _CACHED_PROMPT
        except Exception as e:
            print(f"[MartinTyler] Prompt cache load error ({e}). Rebuilding...")

    model = get_base_model()
    
    # Priority reference audio: fast commentary
    ref_wav = MARTIN_VOICE_DIR / "martin_tyler_commentary_fast.wav"
    ref_txt_file = MARTIN_VOICE_DIR / "martin_tyler_commentary_fast.txt"
    
    if not ref_wav.exists() or not ref_txt_file.exists():
        raise FileNotFoundError(f"Missing Martin Tyler reference audio: {ref_wav}")

    ref_text = ref_txt_file.read_text(encoding="utf-8").strip()
    print(f"[MartinTyler] Creating voice clone prompt from {ref_wav.name}...")
    print(f"  Reference text: \"{ref_text}\"")

    t0 = time.time()
    prompt_items = model.create_voice_clone_prompt(
        ref_audio=str(ref_wav),
        ref_text=ref_text,
        x_vector_only_mode=False  # Enable ICL for true cadence and inflection reproduction
    )
    
    print(f"[MartinTyler] Voice clone prompt generated in {time.time()-t0:.2f}s.")
    try:
        torch.save(prompt_items, str(PROMPT_CACHE_PATH))
        print(f"[MartinTyler] Saved prompt cache to {PROMPT_CACHE_PATH.name}")
    except Exception as e:
        print(f"[MartinTyler] Warning: Could not save prompt cache: {e}")

    _CACHED_PROMPT = prompt_items
    return _CACHED_PROMPT

def master_commentator_audio(
    raw_wav_path: Path,
    final_output_path: Path,
    speed_factor: float = 1.14,
    target_lufs: float = -14.0,
    peak_db: float = -1.0
) -> Path:
    """
    Apply broadcast vocal chain mastering for fast-paced commentator delivery:
    1. atempo speedup (pitch-preserved fast commentator rhythm)
    2. highpass filter (80Hz rumble cut)
    3. presence EQ boost (3.2kHz clarity & British sibilance)
    4. broadcast compression (punchy upfront voice)
    5. EBU R128 loudness normalization
    """
    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # FFmpeg audio filter graph
    # 1. tempo speedup (e.g. 1.14x)
    # 2. highpass 80Hz
    # 3. 3200Hz bell EQ +2.5dB
    # 4. compand for broadcast energy
    # 5. loudnorm to -14 LUFS
    filter_chain = (
        f"atempo={speed_factor},"
        f"highpass=f=80,"
        f"equalizer=f=3200:t=q:w=1.2:g=2.5,"
        f"compand=attacks=0.02:decays=0.15:points=-70/-70|-45/-35|-20/-14|0/-8:soft-knee=6:gain=2,"
        f"loudnorm=I={target_lufs}:TP={peak_db}:LRA=7"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_wav_path),
        "-af", filter_chain,
        "-ar", "24000",
        "-ac", "1",
        str(final_output_path)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[MartinTyler] FFmpeg mastering warning: {res.stderr[:200]}")
        # fallback copy
        import shutil
        shutil.copy2(raw_wav_path, final_output_path)
    return final_output_path

def synthesize_martin_tyler(
    text: str,
    output_path: Optional[Path] = None,
    speed_factor: float = 1.14,
    temperature: float = 0.85,
    repetition_penalty: float = 1.1
) -> Tuple[Path, float]:
    """
    Synthesize speech in legendary Martin Tyler cloned commentator voice.
    
    Args:
        text: Script line or paragraph to synthesize.
        output_path: Target path for output (.wav or .mp3).
        speed_factor: Pacing multiplier (default 1.14 for fast-paced broadcast pace).
        temperature: Sampling randomness.
        repetition_penalty: Prevents loop artifacts.
        
    Returns:
        Tuple of (final_path, duration_seconds).
    """
    import soundfile as sf

    model = get_base_model()
    prompt = get_martin_tyler_prompt()

    print(f"[MartinTyler] Synthesizing commentary ({len(text.split())} words): \"{text[:65]}...\"")
    t0 = time.time()

    wavs, sr = model.generate_voice_clone(
        text=text,
        language="English",
        voice_clone_prompt=prompt,
        non_streaming_mode=True,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
    )

    audio_data = wavs[0]
    
    # Save raw synthesis
    temp_dir = PROJECT_ROOT / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    raw_wav = temp_dir / f"raw_martin_{int(time.time()*1000)}.wav"
    sf.write(str(raw_wav), audio_data, sr)

    if output_path is None:
        output_path = temp_dir / f"martin_tyler_{int(time.time()*1000)}.wav"
    output_path = Path(output_path)

    # Master with fast-paced broadcast chain
    mastered_path = master_commentator_audio(
        raw_wav_path=raw_wav,
        final_output_path=output_path,
        speed_factor=speed_factor
    )

    # Calculate final duration
    info = sf.info(str(mastered_path))
    duration = info.duration

    print(f"[MartinTyler] Generated & Mastered in {time.time()-t0:.2f}s | Final Duration: {duration:.2f}s | Speed: {speed_factor}x")
    return mastered_path, duration

if __name__ == "__main__":
    test_line = "Milan are ready to drop sixty million euros on Endrick! Can Carlo Ancelotti keep him on the bench forever? YES OR NO? Comment below!"
    out = PROJECT_ROOT / "scratch" / "test_martin_output.wav"
    synthesize_martin_tyler(test_line, output_path=out)
