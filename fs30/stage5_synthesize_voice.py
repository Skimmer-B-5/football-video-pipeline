"""
Stage 5: synthesize_voice
Runs Qwen3-TTS voice model per scene with calm, deep storytelling instructions.
Measures real duration, appends 0.3s silence, updates plan.json with exact est_seconds.
Applies pronunciation_hints before TTS only.
Ensures Qwen3-TTS model is unloaded immediately from GPU memory after completion.
"""

import os
import sys
import json
import time
import gc
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import soundfile as sf

from fs30.config import PROJECT_ROOT, load_config

def apply_pronunciation_hints(text: str, hints: Dict[str, str]) -> str:
    """Replaces words with phonetic spellings for TTS only."""
    spoken = text
    for name, phon in hints.items():
        if name in spoken:
            spoken = spoken.replace(name, phon)
    return spoken

def append_silence_wav(input_wav: Path, output_wav: Path, silence_sec: float = 0.3) -> float:
    """Appends silence_sec of silence to a wav file and returns new total duration."""
    data, sr = sf.read(str(input_wav))
    silence_samples = int(sr * silence_sec)
    
    if data.ndim == 1:
        silence = np.zeros(silence_samples, dtype=data.dtype)
        combined = np.concatenate([data, silence])
    else:
        silence = np.zeros((silence_samples, data.shape[1]), dtype=data.dtype)
        combined = np.concatenate([data, silence], axis=0)

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_wav), combined, sr)
    total_dur = len(combined) / float(sr)
    return total_dur

def synthesize_all_scenes(
    script_data: Dict[str, Any],
    plan_data: Dict[str, Any],
    run_dir: Path,
    config: Optional[Dict[str, Any]] = None,
    log_func=print
) -> Dict[int, Dict[str, Any]]:
    """
    Executes Stage 5:
    Loads Qwen3-TTS, synthesizes one audio per scene, updates plan.json, and frees GPU.
    """
    run_dir = Path(run_dir)
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    if config is None:
        config = load_config()

    voice_cfg = config.get("voice", {})
    silence_sec = voice_cfg.get("scene_silence_sec", 0.3)
    calm_instruct = voice_cfg.get(
        "instruct",
        "Speak in a calm, measured, deep, chilling, and engaging storytelling voice. Steady cadence, thoughtful pauses, zero breathless rush. Let the words breathe."
    )

    scenes = plan_data.get("scenes", [])
    hints = script_data.get("pronunciation_hints", {})

    log_func(f"[Stage 5: synthesize_voice] Synthesizing audio for {len(scenes)} scene(s) via Qwen3-TTS...")
    log_func(f"  Instruct: \"{calm_instruct[:70]}...\"")

    all_exist = True
    for sc in scenes:
        s_id = sc.get("id")
        final_wav = audio_dir / f"scene_{s_id}.wav"
        if not (final_wav.exists() and final_wav.stat().st_size > 1000):
            all_exist = False
            break

    if all_exist:
        log_func("  ✓ All scene audio files already exist. Re-using cached audios without loading model.")
        audio_results = {}
        for sc in scenes:
            s_id = sc.get("id")
            final_wav = audio_dir / f"scene_{s_id}.wav"
            dur = sc.get("est_seconds", 4.0)
            audio_results[s_id] = {
                "audio_path": final_wav,
                "duration": dur
            }
        return audio_results

    from stages.qwen_tts_synthesizer import get_qwen3_tts_model, synthesize_qwen3

    # Load model
    model = get_qwen3_tts_model()

    audio_results = {}
    for sc in scenes:
        s_id = sc.get("id")
        raw_text = sc.get("narration", "")
        spoken_text = apply_pronunciation_hints(raw_text, hints)

        raw_wav = audio_dir / f"scene_{s_id}_raw.wav"
        final_wav = audio_dir / f"scene_{s_id}.wav"

        log_func(f"\n[Scene {s_id}] Synthesizing ({len(spoken_text.split())} words): \"{spoken_text[:60]}...\"")
        
        # Synthesize via Qwen3
        synthesize_qwen3(
            text=spoken_text,
            output_path=raw_wav,
            instruct=calm_instruct
        )

        # Append 0.3s silence and measure exact duration
        measured_dur = append_silence_wav(raw_wav, final_wav, silence_sec=silence_sec)
        
        # Overwrite est_seconds in plan
        sc["est_seconds"] = round(measured_dur, 2)
        log_func(f"  ✓ Measured duration: {measured_dur:.2f}s (incl. {silence_sec}s silence) -> {final_wav.name}")

        audio_results[s_id] = {
            "audio_path": final_wav,
            "duration": measured_dur
        }

        if raw_wav.exists():
            raw_wav.unlink()

    # Save updated plan.json with exact measured seconds
    plan_file = run_dir / "plan.json"
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2)

    # UNLOAD Qwen3-TTS from GPU memory strictly per Part 1 rules
    log_func("\n[Stage 5: synthesize_voice] Purging Qwen3-TTS model from memory...")
    try:
        import torch
        from stages import qwen_tts_synthesizer
        qwen_tts_synthesizer._MODEL_INSTANCE = None
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception as e:
        log_func(f"  Memory purge note: {e}")

    log_func("[Stage 5: synthesize_voice] ✓ All audio files mastered and GPU memory freed.")
    return audio_results
