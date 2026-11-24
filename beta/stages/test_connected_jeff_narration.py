import os
import sys
import json
import time
from pathlib import Path
import soundfile as sf
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.jeff_stelling_synthesizer import (
    get_base_model,
    get_jeff_stelling_prompt,
    master_jeff_audio,
    inject_breath_into_scene
)

def get_audio_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def main():
    print("==================================================================")
    print("  SYNTHESIZING CONNECTED JEFF STELLING NARRATION WITH CONJUNCTIONS")
    print("==================================================================")
    
    ws_base = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1"
    output_voice_dir = ws_base / "voice" / "v7_1_6_6_jeff_connected"
    output_voice_dir.mkdir(parents=True, exist_ok=True)

    # Connected dialogue script with natural broadcast conjunctions and conversational bridges
    connected_scenes = [
        {
            "scene_id": "S01",
            "text": "Milan have made their move, but Mourinho wants him to stay."
        },
        {
            "scene_id": "S02",
            "text": "And Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses."
        },
        {
            "scene_id": "S03",
            "text": "Now, reports cite eighty to eighty-five million repurchase figures, but crucially, nothing is agreed."
        },
        {
            "scene_id": "S04",
            "text": "Meanwhile, a left-leg muscle injury complicates matters, with no official return date."
        },
        {
            "scene_id": "S05",
            "text": "So, will Mourinho keep the Brazilian, or will Milan force a compromise?"
        },
        {
            "scene_id": "outro",
            "text": "Either way, this is football in thirty seconds. Follow for daily transfer updates."
        }
    ]

    model = get_base_model()
    prompt = get_jeff_stelling_prompt()
    
    results = []

    for sc in connected_scenes:
        sid = sc["scene_id"]
        text = sc["text"]
        print(f"\n--- Synthesizing Scene [{sid}] ---")
        print(f"Text: \"{text}\"")

        raw_wav = output_voice_dir / f"raw_{sid}.wav"
        master_wav = output_voice_dir / f"scene_{sid}.wav"
        master_mp3 = output_voice_dir / f"scene_{sid}.mp3"

        t0 = time.time()
        wavs, sr = model.generate_voice_clone(
            text=text,
            language="English",
            voice_clone_prompt=prompt,
            non_streaming_mode=True,
            temperature=0.7,
            repetition_penalty=1.1,
        )
        synth_time = time.time() - t0
        sf.write(str(raw_wav), wavs[0], sr)
        print(f"  Raw audio generated in {synth_time:.2f}s")

        # Master through broadcast vocal chain
        master_jeff_audio(raw_wav, master_wav, speed_factor=1.0)
        master_jeff_audio(raw_wav, master_mp3, speed_factor=1.0)

        dur = get_audio_duration(master_wav)
        print(f"  Mastered duration: {dur:.2f}s")

        results.append({
            "scene_id": sid,
            "text": text,
            "duration_sec": round(dur, 3),
            "wav_path": str(master_wav.resolve()),
            "mp3_path": str(master_mp3.resolve()),
            "synth_time_sec": round(synth_time, 2)
        })

    manifest_path = output_voice_dir / "connected_narration_manifest.json"
    manifest_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nConnected narration manifest saved to: {manifest_path}")

if __name__ == "__main__":
    main()
