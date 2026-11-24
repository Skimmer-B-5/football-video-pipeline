import os
import sys
import json
import time
import subprocess
from pathlib import Path
import soundfile as sf
import torch

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
    print("==========================================================")
    print("  SYNTHESIZING V7.1.6.5 NARRATION WITH JEFF STELLING QWEN3 ")
    print("==========================================================")
    
    ws_base = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1"
    output_voice_dir = ws_base / "voice" / "v7_1_6_5_jeff"
    audio_target_dir = ws_base / "data" / "audio"
    output_voice_dir.mkdir(parents=True, exist_ok=True)
    audio_target_dir.mkdir(parents=True, exist_ok=True)
    
    dialogue_script_path = ws_base / "scripts" / "dialogue_script.json"
    dialogue_data = json.loads(dialogue_script_path.read_text(encoding="utf-8"))
    
    beats = dialogue_data["beats"]
    
    # Also define outro
    outro_beat = {
        "beat_id": "outro",
        "spoken_dialogue": "This is football in thirty seconds. Follow for daily transfer updates."
    }
    all_scenes = list(beats) + [outro_beat]
    
    print(f"Loaded {len(all_scenes)} scenes to synthesize.")
    
    model = get_base_model()
    prompt = get_jeff_stelling_prompt()
    
    results = []
    
    for sc in all_scenes:
        bid = sc["beat_id"]
        text = sc["spoken_dialogue"]
        print(f"\n--- Synthesizing Scene [{bid}] ---")
        print(f"Text: \"{text}\"")
        
        raw_wav = output_voice_dir / f"raw_{bid}.wav"
        master_wav = output_voice_dir / f"scene_{bid}.wav"
        master_mp3 = output_voice_dir / f"scene_{bid}.mp3"
        
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
        
        # Master with broadcast vocal chain (speed_factor=1.0 for natural pacing)
        master_jeff_audio(raw_wav, master_wav, speed_factor=1.0)
        master_jeff_audio(raw_wav, master_mp3, speed_factor=1.0)
        
        # Inject natural breath for opening hook and outro if available
        if bid in ["S01", "outro"]:
            inject_breath_into_scene(master_wav, breath_type="soft")
            inject_breath_into_scene(master_mp3, breath_type="soft")
            
        dur = get_audio_duration(master_wav)
        print(f"  Mastered duration: {dur:.2f}s")
        
        # Copy to pipeline audio target directory
        shutil_dest_wav = audio_target_dir / f"scene_{bid}.wav"
        shutil_dest_mp3 = audio_target_dir / f"scene_{bid}.mp3"
        import shutil
        shutil.copy2(str(master_wav), str(shutil_dest_wav))
        shutil.copy2(str(master_mp3), str(shutil_dest_mp3))
        
        results.append({
            "scene_id": bid,
            "text": text,
            "duration_sec": round(dur, 3),
            "wav_path": str(master_wav.resolve()),
            "mp3_path": str(master_mp3.resolve()),
            "synth_time_sec": round(synth_time, 2)
        })
        
    summary_path = output_voice_dir / "narration_manifest.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nAll scenes synthesized! Manifest saved to: {summary_path}")
    total_dur = sum(r["duration_sec"] for r in results)
    print(f"Total narration duration: {total_dur:.2f}s")

if __name__ == "__main__":
    main()
