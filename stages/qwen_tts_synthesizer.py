"""
Qwen3-TTS Speech Synthesizer for High-Retention Football Shorts.
Utilizes Alibaba's Qwen3-TTS (0.6B CustomVoice) with natural language style instructions
for punchy, dramatic British news reader cadence.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MODELS_DIR = PROJECT_ROOT / "models"
MODEL_LOCAL_PATH = MODELS_DIR / "qwen3_tts_customvoice"

_MODEL_INSTANCE = None

def get_qwen3_tts_model():
    """Singleton loader for Qwen3-TTS model."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    import torch
    from qwen_tts import Qwen3TTSModel

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

    model_source = str(MODEL_LOCAL_PATH) if MODEL_LOCAL_PATH.exists() else "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
    print(f"[Qwen3TTS] Loading model from {model_source} on {device} ({dtype})...")
    
    t0 = time.time()
    _MODEL_INSTANCE = Qwen3TTSModel.from_pretrained(
        model_source,
        device_map=device,
        dtype=dtype,
    )
    print(f"[Qwen3TTS] Model loaded successfully in {time.time()-t0:.2f}s.")
    return _MODEL_INSTANCE

def synthesize_qwen3(
    text: str,
    output_path: Optional[Path] = None,
    speaker: str = "Ryan",
    instruct: Optional[str] = None,
    language: str = "English",
    normalize_db: float = -1.0
) -> Tuple[Path, float]:
    """
    Synthesize speech using Qwen3-TTS with dynamic instruction styling.
    
    Args:
        text: Monologue or sentence to synthesize.
        output_path: Target path to save audio (.wav).
        speaker: Voice identity (default "Ryan", dynamic rhythm).
        instruct: Style guidance prompt for expressive tone.
        language: Synthesis language.
        normalize_db: Target peak normalization in dB.
        
    Returns:
        Tuple of (output_path, duration_seconds).
    """
    import soundfile as sf

    if instruct is None:
        instruct = "Speak in an urgent, dramatic sports breaking news anchor tone with punchy, high-energy British cadence."

    model = get_qwen3_tts_model()

    print(f"[Qwen3TTS] Synthesizing ({len(text.split())} words): \"{text[:60]}...\"")
    t0 = time.time()

    wavs, sr = model.generate_custom_voice(
        text=text,
        language=language,
        speaker=speaker,
        instruct=instruct,
    )

    audio_data = wavs[0]
    
    # Peak normalization to target dB
    if normalize_db is not None and len(audio_data) > 0:
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            target_amplitude = 10.0 ** (normalize_db / 20.0)
            audio_data = audio_data * (target_amplitude / max_val)

    if output_path is None:
        output_path = PROJECT_ROOT / "temp" / f"qwen3_{int(time.time()*1000)}.wav"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sf.write(str(output_path), audio_data, sr)
    duration = len(audio_data) / float(sr)

    print(f"[Qwen3TTS] Generated in {time.time()-t0:.2f}s | Duration: {duration:.2f}s | Saved to {output_path.name}")
    return output_path, duration

if __name__ == "__main__":
    print("Testing Qwen3-TTS synthesizer module...")
    test_out = PROJECT_ROOT / "scratch" / "test_qwen3_output.wav"
    path, dur = synthesize_qwen3(
        text="Milan are about to unleash a sixty million euro bomb on Real Madrid!",
        output_path=test_out
    )
    print(f"Test completed: {path} ({dur:.2f}s)")
