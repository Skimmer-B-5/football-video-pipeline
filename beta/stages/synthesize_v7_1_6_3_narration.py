import os
import sys
import time
import json
import subprocess
import soundfile as sf
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.qwen_tts_synthesizer import get_qwen3_tts_model

SCENES = [
    {
        "scene_id": "S01",
        "text": "Milan have made their move, but Mourinho wants him to stay.",
        "target_dur": 5.28
    },
    {
        "scene_id": "S02",
        "text": "Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.",
        "target_dur": 7.46
    },
    {
        "scene_id": "S03",
        "text": "Reports cite eighty to eighty-five million repurchase figures, but nothing is agreed.",
        "target_dur": 6.15
    },
    {
        "scene_id": "S04",
        "text": "Now a left-leg muscle injury complicates matters, with no official return date.",
        "target_dur": 6.15
    },
    {
        "scene_id": "S05",
        "text": "Will Mourinho keep the Brazilian or will Milan force a compromise?",
        "target_dur": 5.10
    }
]

def trim_silence_with_padding(audio: np.ndarray, sr: int, pad_end_sec: float = 0.25) -> np.ndarray:
    energy = np.abs(audio)
    thresh = 0.015 * np.max(energy) if np.max(energy) > 0 else 0.001
    active_indices = np.where(energy > thresh)[0]
    if len(active_indices) == 0:
        return audio
    start_idx = max(0, active_indices[0] - int(0.05 * sr))
    end_idx = min(len(audio), active_indices[-1] + int(0.05 * sr))
    trimmed = audio[start_idx:end_idx]
    
    pad_samples = int(pad_end_sec * sr)
    padded = np.pad(trimmed, (0, pad_samples), mode='constant')
    return padded

def apply_broadcast_mastering(raw_path: Path, out_path: Path, presence_boost_db: float = 2.2):
    af_chain = (
        f"highpass=f=90,"
        f"lowpass=f=11000,"
        f"equalizer=f=3200:t=q:w=1.2:g={presence_boost_db},"
        f"compand=attacks=0.02:decays=0.15:points=-60/-60|-24/-18|-12/-8|0/-1:gain=0,"
        f"loudnorm=I=-14:TP=-1.0:LRA=7"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_path),
        "-af", af_chain,
        "-ar", "48000",
        "-ac", "2",
        str(out_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Mastering note for {raw_path.name}: {res.stderr[:200]}")
        import shutil
        shutil.copy2(str(raw_path), str(out_path))

def main():
    audio_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "data" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = audio_dir / "temp_raw"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print("=== Loading Qwen3-TTS Model on CUDA ===")
    model = get_qwen3_tts_model()

    instruct = (
        "A mature British male sports correspondent delivering breaking football transfer news from the studio desk. "
        "Measured, authoritative, calm baritone with natural conversational pauses, clear British pronunciation, and restrained emphasis."
    )

    total_physical_duration = 0.0
    scene_audios = []

    print("\n=== Synthesizing 5 Scenes via Qwen3-TTS (Speaker: Ryan) ===")
    for sc in SCENES:
        sid = sc["scene_id"]
        text = sc["text"]
        print(f"[{sid}] Synthesizing ({len(text.split())} words): \"{text}\"")
        t0 = time.time()
        
        wavs, sr = model.generate_custom_voice(
            text=text,
            language="English",
            speaker="Ryan",
            instruct=instruct,
        )
        raw_audio = wavs[0]
        trimmed_padded = trim_silence_with_padding(raw_audio, sr, pad_end_sec=0.25)
        
        raw_wav_path = temp_dir / f"scene_{sid}_raw.wav"
        mastered_wav_path = audio_dir / f"scene_{sid}.wav"
        
        sf.write(str(raw_wav_path), trimmed_padded, sr)
        apply_broadcast_mastering(raw_wav_path, mastered_wav_path)
        
        info = sf.info(str(mastered_wav_path))
        phys_dur = info.duration
        total_physical_duration += phys_dur
        scene_audios.append({
            "scene_id": sid,
            "text": text,
            "audio_path": str(mastered_wav_path),
            "physical_duration_sec": round(phys_dur, 2),
            "target_duration_sec": sc["target_dur"],
            "variance_sec": round(phys_dur - sc["target_dur"], 2)
        })
        print(f"  -> Generated {mastered_wav_path.name} in {time.time()-t0:.2f}s | Physical duration: {phys_dur:.2f}s (Target: {sc['target_dur']}s)")

    print(f"\nTotal Physical Narration Duration: {total_physical_duration:.2f}s (Target: 30.15s)")
    
    summary_path = audio_dir / "voice_synthesis_manifest.json"
    summary_path.write_text(json.dumps({
        "voice": "VOICE_A_CORRESPONDENT_NEWSDESK",
        "engine": "Qwen3-TTS (0.6B CustomVoice)",
        "speaker": "Ryan",
        "loudness_target": "-14 LUFS",
        "total_physical_duration_sec": round(total_physical_duration, 2),
        "target_duration_sec": 30.15,
        "scenes": scene_audios
    }, indent=2), encoding="utf-8")
    print(f"Saved audio manifest: {summary_path}")

if __name__ == "__main__":
    main()
