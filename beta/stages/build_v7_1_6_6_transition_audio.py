import os
import sys
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import scipy.signal

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

def resample_and_normalize(wav: np.ndarray, orig_sr: int, target_sr: int = 48000) -> np.ndarray:
    if orig_sr != target_sr:
        num_samples = int(len(wav) * target_sr / orig_sr)
        wav = scipy.signal.resample(wav, num_samples)
    return wav

def main():
    print("==================================================================")
    print("  BUILDING V7.1.6.6 COMPOSITE SCENES WITH TRANSITION STOPS/STARTS ")
    print("==================================================================")
    
    ws_base = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1"
    voice_dir = ws_base / "voice" / "v7_1_6_6_jeff_connected"
    sfx_dir = PROJECT_ROOT / "data" / "sfx"
    target_dir = ws_base / "voice" / "v7_1_6_6_scenes_with_transitions"
    target_dir.mkdir(parents=True, exist_ok=True)

    sr = 48000

    # Load SFX assets
    dark_whoosh, w_sr = sf.read(str(sfx_dir / "dark_whoosh.wav"))
    dark_whoosh = resample_and_normalize(dark_whoosh, w_sr, sr)
    if dark_whoosh.ndim == 2:
        dark_whoosh = np.mean(dark_whoosh, axis=1)

    marker_wipe, m_sr = sf.read(str(sfx_dir / "marker_wipe.wav"))
    marker_wipe = resample_and_normalize(marker_wipe, m_sr, sr)
    if marker_wipe.ndim == 2:
        marker_wipe = np.mean(marker_wipe, axis=1)

    paper_slide, p_sr = sf.read(str(sfx_dir / "paper_slide.wav"))
    paper_slide = resample_and_normalize(paper_slide, p_sr, sr)
    if paper_slide.ndim == 2:
        paper_slide = np.mean(paper_slide, axis=1)

    breath_quick, bq_sr = sf.read(str(sfx_dir / "breath_quick_02.wav"))
    breath_quick = resample_and_normalize(breath_quick, bq_sr, sr)
    if breath_quick.ndim == 2:
        breath_quick = np.mean(breath_quick, axis=1)

    breath_soft, bs_sr = sf.read(str(sfx_dir / "breath_soft_01.wav"))
    breath_soft = resample_and_normalize(breath_soft, bs_sr, sr)
    if breath_soft.ndim == 2:
        breath_soft = np.mean(breath_soft, axis=1)

    jeff_breath1, jb_sr = sf.read(str(sfx_dir / "jeff_breath_01.wav"))
    jeff_breath1 = resample_and_normalize(jeff_breath1, jb_sr, sr)
    if jeff_breath1.ndim == 2:
        jeff_breath1 = np.mean(jeff_breath1, axis=1)

    jeff_breath2, jb2_sr = sf.read(str(sfx_dir / "jeff_breath_02.wav"))
    jeff_breath2 = resample_and_normalize(jeff_breath2, jb2_sr, sr)
    if jeff_breath2.ndim == 2:
        jeff_breath2 = np.mean(jeff_breath2, axis=1)

    scene_configs = [
        {
            "scene_id": "S01",
            "sting": None,
            "breath": breath_soft * 0.7,
            "lead_silence_sec": 0.05,
            "tail_silence_sec": 0.22,
        },
        {
            "scene_id": "S02",
            "sting": marker_wipe * 0.35, # subtle wipe sound
            "breath": jeff_breath2 * 0.75, # crisp intake of breath
            "lead_silence_sec": 0.04,
            "tail_silence_sec": 0.25,
        },
        {
            "scene_id": "S03",
            "sting": dark_whoosh * 0.30, # smooth transitional whoosh
            "breath": jeff_breath1 * 0.70, # breath
            "lead_silence_sec": 0.04,
            "tail_silence_sec": 0.22,
        },
        {
            "scene_id": "S04",
            "sting": paper_slide * 0.40, # medical document / paper texture
            "breath": jeff_breath2 * 0.75, # breath
            "lead_silence_sec": 0.04,
            "tail_silence_sec": 0.25,
        },
        {
            "scene_id": "S05",
            "sting": dark_whoosh * 0.30, # dramatic shift to closing dilemma
            "breath": jeff_breath1 * 0.75, # breath
            "lead_silence_sec": 0.04,
            "tail_silence_sec": 0.30,
        },
        {
            "scene_id": "outro",
            "sting": marker_wipe * 0.40, # clean outro transition
            "breath": breath_quick * 0.70,
            "lead_silence_sec": 0.04,
            "tail_silence_sec": 0.35,
        }
    ]

    manifest = []
    fps = 30.0

    for cfg in scene_configs:
        sid = cfg["scene_id"]
        speech_wav_path = voice_dir / f"scene_{sid}.wav"
        assert speech_wav_path.exists(), f"Missing speech: {speech_wav_path}"

        speech, s_sr = sf.read(str(speech_wav_path))
        speech = resample_and_normalize(speech, s_sr, sr)
        if speech.ndim == 2:
            speech = np.mean(speech, axis=1)

        # Assemble transition prefix: [lead silence] + [mixed sting & breath] + [gap]
        parts = []
        if cfg["lead_silence_sec"] > 0:
            parts.append(np.zeros(int(cfg["lead_silence_sec"] * sr)))

        # Transition event: overlay sting and breath if present
        transition_len = 0
        if cfg["sting"] is not None:
            transition_len = max(transition_len, len(cfg["sting"]))
        if cfg["breath"] is not None:
            transition_len = max(transition_len, len(cfg["breath"]))

        if transition_len > 0:
            trans_buf = np.zeros(transition_len)
            if cfg["sting"] is not None:
                trans_buf[:len(cfg["sting"])] += cfg["sting"]
            if cfg["breath"] is not None:
                # Place breath slightly towards the end of the transition sting so it flows into the first syllable
                b_start = max(0, transition_len - len(cfg["breath"]))
                trans_buf[b_start:b_start + len(cfg["breath"])] += cfg["breath"]
            parts.append(trans_buf)
            # 50ms micro-gap before speech onset for consonant clarity
            parts.append(np.zeros(int(0.05 * sr)))

        parts.append(speech)

        if cfg["tail_silence_sec"] > 0:
            parts.append(np.zeros(int(cfg["tail_silence_sec"] * sr)))

        composite = np.concatenate(parts)

        # Convert to stereo
        composite_stereo = np.column_stack([composite, composite])

        out_wav = target_dir / f"scene_{sid}.wav"
        sf.write(str(out_wav), composite_stereo, sr)

        dur_sec = len(composite) / float(sr)
        dur_frames = int(round(dur_sec * fps))

        print(f"Scene [{sid}]: composite duration = {dur_sec:.2f}s ({dur_frames} frames @ 30fps)")

        manifest.append({
            "scene_id": sid,
            "wav_path": str(out_wav.resolve()),
            "duration_sec": round(dur_sec, 3),
            "duration_frames": dur_frames,
            "has_sting": cfg["sting"] is not None,
            "has_breath": cfg["breath"] is not None,
        })

    import json
    out_manifest = target_dir / "transition_scenes_manifest.json"
    out_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    total_sec = sum(m["duration_sec"] for m in manifest)
    total_frames = sum(m["duration_frames"] for m in manifest)
    print(f"\nAll scenes assembled with transition stops and starts!")
    print(f"Total Master Duration: {total_sec:.2f}s ({total_frames} frames @ 30fps)")

if __name__ == "__main__":
    main()
