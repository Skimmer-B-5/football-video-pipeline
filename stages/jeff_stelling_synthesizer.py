"""
stages/jeff_stelling_synthesizer.py - Jeff Stelling Sky Sports Broadcast Voice Synthesizer.

Uses local Qwen3-TTS zero-shot voice cloning based on pristine television studio audio
(early-2000s Soccer Saturday style).
Captures:
- Brisk pacing, crisp consonants, lively British delivery
- Seasoned football journalist presenting breaking transfer news
- Conversational authority with occasional dry emphasis
- Zero crowd noise, zero stadium echo, zero exaggerated bass/rasp
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MODELS_DIR = PROJECT_ROOT / "models"
MODEL_BASE_PATH = MODELS_DIR / "qwen3_tts_base"
JEFF_VOICE_DIR = PROJECT_ROOT / "data" / "branding" / "voices" / "jeff_stelling"
PROMPT_CACHE_PATH = MODELS_DIR / "jeff_stelling_prompt.pt"

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

    print(f"[JeffStelling] Loading Qwen3-TTS Base model on {device} ({dtype})...")
    t0 = time.time()
    _MODEL_INSTANCE = Qwen3TTSModel.from_pretrained(
        str(MODEL_BASE_PATH),
        device_map=device,
        dtype=dtype,
    )
    print(f"[JeffStelling] Base model loaded in {time.time()-t0:.2f}s.")
    return _MODEL_INSTANCE


def get_jeff_stelling_prompt():
    """Load or build the cached VoiceClonePromptItem for Jeff Stelling."""
    global _CACHED_PROMPT
    if _CACHED_PROMPT is not None:
        return _CACHED_PROMPT

    import torch

    if PROMPT_CACHE_PATH.exists():
        try:
            print(f"[JeffStelling] Loading precomputed voice prompt from {PROMPT_CACHE_PATH.name}...")
            _CACHED_PROMPT = torch.load(str(PROMPT_CACHE_PATH), weights_only=False)
            return _CACHED_PROMPT
        except Exception as e:
            print(f"[JeffStelling] Prompt cache load error ({e}). Rebuilding...")

    model = get_base_model()

    ref_wav = JEFF_VOICE_DIR / "jeff_stelling_soccer_saturday.wav"
    ref_txt_file = JEFF_VOICE_DIR / "jeff_stelling_soccer_saturday.txt"

    if not ref_wav.exists() or not ref_txt_file.exists():
        raise FileNotFoundError(f"Missing Jeff Stelling reference audio: {ref_wav}")

    ref_text = ref_txt_file.read_text(encoding="utf-8").strip()
    print(f"[JeffStelling] Creating voice clone prompt from {ref_wav.name}...")
    print(f"  Reference text: \"{ref_text}\"")

    t0 = time.time()
    prompt_items = model.create_voice_clone_prompt(
        ref_audio=str(ref_wav),
        ref_text=ref_text,
        x_vector_only_mode=False
    )

    print(f"[JeffStelling] Voice clone prompt generated in {time.time()-t0:.2f}s.")
    try:
        torch.save(prompt_items, str(PROMPT_CACHE_PATH))
        print(f"[JeffStelling] Saved prompt cache to {PROMPT_CACHE_PATH.name}")
    except Exception as e:
        print(f"[JeffStelling] Warning: Could not save prompt cache: {e}")

    _CACHED_PROMPT = prompt_items
    return _CACHED_PROMPT


def master_jeff_audio(
    raw_wav_path: Path,
    final_output_path: Path,
    speed_factor: float = 1.08,
    target_lufs: float = -14.0,
    peak_db: float = -1.0
) -> Path:
    """
    Broadcast vocal chain for Jeff Stelling television desk delivery:
    - Highpass @ 90Hz (cuts sub-rumble without thinning male vocal)
    - Lowpass @ 11kHz (smooth high-end, zero digital hiss)
    - Presence EQ boost @ 3.2kHz (+2.5dB) for crisp British consonants and articulation
    - Compand for broadcast levelling and punch
    - Pacing speed multiplier (1.08x for lively brisk delivery)
    - ITU-R BS.1770-4 loudnorm to -14 LUFS, -1.0 dBTP ceiling
    - 48 kHz stereo output
    """
    final_output_path.parent.mkdir(parents=True, exist_ok=True)

    filter_chain = (
        f"highpass=f=90,"
        f"lowpass=f=11000,"
        f"equalizer=f=3200:t=q:w=1.2:g=2.5,"
        f"compand=attacks=0.02:decays=0.15:points=-60/-60|-24/-16|-12/-8|0/-3,"
        f"atempo={speed_factor},"
        f"loudnorm=I={target_lufs}:TP={peak_db}:LRA=7,"
        f"aformat=sample_rates=48000:channel_layouts=stereo"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_wav_path),
        "-af", filter_chain,
        "-c:a", "pcm_s16le" if final_output_path.suffix.lower() == ".wav" else "libmp3lame",
        str(final_output_path)
    ]

    subprocess.run(cmd, capture_output=True, check=True)
    return final_output_path


def synthesize_jeff_stelling_scene(
    text: str,
    output_wav_path: Path,
    scene_id: str = "scene_01",
    speed_factor: float = 1.08,
    master: bool = True
) -> Dict[str, Any]:
    """Synthesizes a single narration scene using Jeff Stelling cloned voice."""
    import soundfile as sf

    model = get_base_model()
    prompt = get_jeff_stelling_prompt()

    output_wav_path.parent.mkdir(parents=True, exist_ok=True)
    temp_raw = output_wav_path.parent / f"_raw_{output_wav_path.name}"

    t0 = time.time()
    wavs, sr = model.generate_voice_clone(
        text=text,
        language="English",
        voice_clone_prompt=prompt,
        non_streaming_mode=True,
        temperature=0.8,
        repetition_penalty=1.1,
    )
    synth_time = time.time() - t0

    audio_data = wavs[0]
    sf.write(str(temp_raw), audio_data, sr)

    if master:
        master_jeff_audio(temp_raw, output_wav_path, speed_factor=speed_factor)
        if temp_raw.exists():
            temp_raw.unlink()
    else:
        temp_raw.replace(output_wav_path)

    # Measure exact physical duration
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(output_wav_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    dur = float(res.stdout.strip())

    return {
        "audio_path": str(output_wav_path.resolve()),
        "audio_duration_sec": round(dur, 3),
        "synth_time_sec": round(synth_time, 2),
        "engine": "JeffStelling-Qwen3",
        "voice": "Jeff Stelling (Sky Sports Studio 1.08x)",
        "scene_id": scene_id
    }


def synthesize_jeff_stelling_script(
    scenes: List[Dict[str, Any]],
    output_dir: Path,
    speed_factor: float = 1.08
) -> List[Dict[str, Any]]:
    """Synthesizes all scenes in a Schema v2.0 script in order."""
    results = []
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[JeffStelling] Beginning synthesis of {len(scenes)} scenes...")
    for s in scenes:
        sid = s.get("scene_id", "s01")
        narration = s.get("narration", "")
        out_f = output_dir / f"scene_{sid}.wav"

        print(f"  [{sid}] Synthesizing: \"{narration[:50]}...\"")
        res = synthesize_jeff_stelling_scene(
            text=narration,
            output_wav_path=out_f,
            scene_id=sid,
            speed_factor=speed_factor
        )
        print(f"    -> Duration: {res['audio_duration_sec']}s (Generated in {res['synth_time_sec']}s)")
        results.append(res)

    return results


if __name__ == "__main__":
    test_line = "Endrick's future hangs in the balance as Milan readies a massive sixty million euro offer."
    out_test = PROJECT_ROOT / "temp" / "jeff_stelling_test" / "test_jeff_synth.wav"
    res = synthesize_jeff_stelling_scene(
        text=test_line,
        output_wav_path=out_test,
        scene_id="test_01",
        speed_factor=1.08
    )
    print("\nTest synthesis result:", res)

