import os
import sys
import subprocess
from pathlib import Path
import soundfile as sf
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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
    print("  ASSEMBLING V7.1.6.7 PURE VOCAL TRANSITIONS (ZERO WHOOSHES)      ")
    print("==================================================================")
    
    ws_base = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1"
    voice_dir = ws_base / "voice" / "test_vocal_transitions"
    clean_scenes_dir = ws_base / "voice" / "v7_1_6_7_clean_vocal_transitions"
    clean_scenes_dir.mkdir(parents=True, exist_ok=True)
    
    sr = 48000
    
    # We want natural vocal pacing:
    # Each scene:
    # 1. Lead-in pause (quiet studio air / room tone) of ~0.15s (5 frames)
    # 2. Jeff's natural voice (with conjunction and vocal pause)
    # 3. Tail pause of ~0.25s (8 frames) to let the point breathe before the next cut
    # ZERO whoosh, ZERO marker wipe, ZERO artificial SFX.
    
    scene_defs = [
        ("S01", "beat_S01_master.wav", 0.10, 0.25),
        ("S02", "beat_S02_master.wav", 0.15, 0.25),
        ("S03", "beat_S03_master.wav", 0.15, 0.25),
        ("S04", "beat_S04_master.wav", 0.15, 0.25),
        ("S05", "beat_S05_master.wav", 0.15, 0.25),
        ("outro", "beat_outro_master.wav", 0.15, 0.35),
    ]
    
    manifest = []
    fps = 30.0
    
    for sid, filename, lead_sec, tail_sec in scene_defs:
        src_path = voice_dir / filename
        data, file_sr = sf.read(str(src_path))
        if file_sr != sr:
            import scipy.signal
            data = scipy.signal.resample(data, int(len(data) * sr / file_sr))
            
        if data.ndim == 1:
            data = np.column_stack([data, data])
            
        lead_padding = np.zeros((int(lead_sec * sr), 2))
        tail_padding = np.zeros((int(tail_sec * sr), 2))
        
        composite = np.concatenate([lead_padding, data, tail_padding])
        dur_sec = len(composite) / sr
        dur_frames = int(round(dur_sec * fps))
        
        # Ensure exact frame alignment: pad or trim to exact frame boundary
        target_samples = int(dur_frames * (sr / fps))
        if len(composite) < target_samples:
            diff = target_samples - len(composite)
            composite = np.pad(composite, ((0, diff), (0, 0)))
        elif len(composite) > target_samples:
            composite = composite[:target_samples]
            
        dur_sec = len(composite) / sr
        out_wav = clean_scenes_dir / f"scene_{sid}.wav"
        sf.write(str(out_wav), composite, sr)
        
        manifest.append({
            "scene_id": sid,
            "wav_path": str(out_wav),
            "duration_sec": round(dur_sec, 3),
            "duration_frames": dur_frames,
            "lead_frames": int(round(lead_sec * fps)),
            "tail_frames": int(round(tail_sec * fps))
        })
        print(f"Scene [{sid}]: {dur_sec:.2f}s ({dur_frames} frames) - lead: {lead_sec*1000:.0f}ms, tail: {tail_sec*1000:.0f}ms")

    import json
    manifest_file = clean_scenes_dir / "transition_scenes_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    total_sec = sum(m["duration_sec"] for m in manifest)
    total_frames = sum(m["duration_frames"] for m in manifest)
    print(f"\nTotal Clean Voice Timeline: {total_sec:.2f}s ({total_frames} frames @ {fps}fps)")

if __name__ == "__main__":
    main()
