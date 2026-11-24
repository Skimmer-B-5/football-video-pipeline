"""
beta/stages/synthesize_v7_1_6_4_audio.py
Synthesizes V7.1.6.4 English narration with:
1. Pronunciation dictionary (Endrick -> En-drick, Mourinho -> Moo-reen-yoh, Milan -> Mee-lahn).
2. 1.2x pitch-preserving time stretching (atempo=1.2).
3. Dedicated spoken outro: "This is football in thirty seconds. Follow for more."
4. Broadcast mastering (-14.0 LUFS, broadcast EQ).
5. Separate Pronunciation Test audio deliverable.
"""

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

BEATS = [
    {
        "scene_id": "S01",
        "display_text": "Milan have made their move, but Mourinho wants him to stay.",
        "tts_text": "Mee-lahn have made their move, but Moo-reen-yoh wants him to stay."
    },
    {
        "scene_id": "S02",
        "display_text": "Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.",
        "tts_text": "Italian reports put Mee-lahn's package for En-drick at sixty million fixed, plus ten in potential bonuses."
    },
    {
        "scene_id": "S03",
        "display_text": "Reports cite eighty to eighty-five million repurchase figures, but nothing is agreed.",
        "tts_text": "Reports cite eighty to eighty-five million repurchase figures, but nothing is agreed."
    },
    {
        "scene_id": "S04",
        "display_text": "Now a left-leg muscle injury complicates matters, with no official return date.",
        "tts_text": "Now a left-leg muscle injury complicates matters, with no official return date."
    },
    {
        "scene_id": "S05",
        "display_text": "Will Mourinho keep the Brazilian or will Milan force a compromise?",
        "tts_text": "Will Moo-reen-yoh keep the Brazilian or will Mee-lahn force a compromise?"
    },
    {
        "scene_id": "outro",
        "display_text": "This is football in 30 seconds. Follow for more.",
        "tts_text": "This is football in thirty seconds. Follow for more."
    }
]

PRONUNCIATION_TEST = {
    "display_text": "Milan have made their move, but Mourinho wants Endrick to stay.",
    "tts_text": "Mee-lahn have made their move, but Moo-reen-yoh wants En-drick to stay."
}

def trim_silence_with_padding(audio: np.ndarray, sr: int, pad_end_sec: float = 0.20) -> np.ndarray:
    energy = np.abs(audio)
    thresh = 0.015 * np.max(energy) if np.max(energy) > 0 else 0.001
    active_indices = np.where(energy > thresh)[0]
    if len(active_indices) == 0:
        return audio
    start_idx = max(0, active_indices[0] - int(0.04 * sr))
    end_idx = min(len(audio), active_indices[-1] + int(0.04 * sr))
    trimmed = audio[start_idx:end_idx]
    pad_samples = int(pad_end_sec * sr)
    return np.pad(trimmed, (0, pad_samples), mode='constant')

def master_and_speed_stretch(raw_wav: Path, out_wav: Path, speed: float = 1.2, presence_boost_db: float = 2.4):
    """
    Applies pitch-preserving time-stretching (atempo=1.2) + broadcast vocal mastering
    (-14 LUFS, 90Hz highpass, 11kHz lowpass, articulation boost).
    """
    af_chain = (
        f"atempo={speed},"
        f"highpass=f=90,"
        f"lowpass=f=11000,"
        f"equalizer=f=3200:t=q:w=1.2:g={presence_boost_db},"
        f"compand=attacks=0.02:decays=0.15:points=-60/-60|-24/-18|-12/-8|0/-1:gain=0,"
        f"loudnorm=I=-14:TP=-1.0:LRA=7"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_wav),
        "-af", af_chain,
        "-ar", "48000",
        "-ac", "2",
        str(out_wav)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def main():
    audio_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "data" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = audio_dir / "temp_raw_v7_1_6_4"
    temp_dir.mkdir(parents=True, exist_ok=True)
    voice_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "voice"

    print("=== Loading Qwen3-TTS Model on CUDA ===")
    model = get_qwen3_tts_model()
    instruct = (
        "A mature British male sports correspondent delivering breaking football transfer news from the studio desk. "
        "Measured, authoritative, calm baritone with clear British pronunciation, dynamic news cadence, and restrained emphasis."
    )

    # 1. Synthesize Pronunciation Test Deliverable
    print("\n--- Synthesizing Pronunciation Test Audio ---")
    t0 = time.time()
    wavs_p, sr_p = model.generate_custom_voice(
        text=PRONUNCIATION_TEST["tts_text"],
        language="English",
        speaker="Ryan",
        instruct=instruct
    )
    p_raw = temp_dir / "pronunciation_test_raw.wav"
    sf.write(str(p_raw), trim_silence_with_padding(wavs_p[0], sr_p), sr_p)
    
    p_master_wav = voice_dir / "pronunciation_test_v7_1_6_4.wav"
    p_master_mp3 = voice_dir / "pronunciation_test_v7_1_6_4.mp3"
    master_and_speed_stretch(p_raw, p_master_wav, speed=1.2)
    
    # Also create mp3 for easy listening
    subprocess.run(["ffmpeg", "-y", "-i", str(p_master_wav), "-b:a", "192k", str(p_master_mp3)], check=True, capture_output=True)
    p_dur = sf.info(str(p_master_wav)).duration
    print(f"Generated Pronunciation Test: {p_master_mp3.name} ({p_dur:.2f}s) in {time.time()-t0:.2f}s")

    # 2. Synthesize all scenes (S01 to S05 + Outro)
    print("\n--- Synthesizing 6 Scenes with Phonetic Guidance at 1.2x Speed ---")
    scene_manifest = []
    total_physical_dur = 0.0

    for sc in BEATS:
        sid = sc["scene_id"]
        disp_txt = sc["display_text"]
        tts_txt = sc["tts_text"]
        print(f"\n[{sid}] TTS Text: \"{tts_txt}\"")
        t0 = time.time()

        wavs, sr = model.generate_custom_voice(
            text=tts_txt,
            language="English",
            speaker="Ryan",
            instruct=instruct
        )
        trimmed = trim_silence_with_padding(wavs[0], sr, pad_end_sec=0.20)
        raw_path = temp_dir / f"scene_{sid}_raw.wav"
        sf.write(str(raw_path), trimmed, sr)
        
        mastered_wav = audio_dir / f"scene_{sid}.wav"
        master_and_speed_stretch(raw_path, mastered_wav, speed=1.2)
        
        dur = sf.info(str(mastered_wav)).duration
        total_physical_dur += dur
        print(f"  -> {mastered_wav.name}: {dur:.2f}s (1.2x speed) in {time.time()-t0:.2f}s")

        scene_manifest.append({
            "scene_id": sid,
            "display_text": disp_txt,
            "tts_phonetic_text": tts_txt,
            "speed": 1.2,
            "physical_duration_sec": round(dur, 2),
            "file_path": str(mastered_wav)
        })

    print(f"\n=======================================================")
    print(f"  TOTAL 1.2x PHYSICAL NARRATION DURATION: {total_physical_dur:.2f}s")
    print(f"=======================================================")

    manifest_path = audio_dir / "v7_1_6_4_audio_manifest.json"
    manifest_path.write_text(json.dumps({
        "version": "v7.1.6.4",
        "voice": "Voice Candidate A (Ryan, Correspondent Newsdesk)",
        "speed_factor": 1.2,
        "pronunciation_dictionary": {
            "Endrick": "EN-drick (phonetic: En-drick)",
            "Mourinho": "moo-REEN-yoh (phonetic: Moo-reen-yoh)",
            "Milan": "mih-LAHN (phonetic: Mee-lahn)"
        },
        "total_physical_duration_sec": round(total_physical_dur, 2),
        "scenes": scene_manifest
    }, indent=2), encoding="utf-8")
    print(f"Saved audio manifest: {manifest_path}")

if __name__ == "__main__":
    main()
