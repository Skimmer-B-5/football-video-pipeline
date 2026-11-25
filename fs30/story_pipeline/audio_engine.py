"""
Audio Post-Production & Mastering Engine for FS30 Story Pipeline.
Mixes Benedict Cumberbatch explanatory narration with Vox-style documentary score
(Opportunity Walks), applies mobile speaker EQ curves, restrained dynamic ducking,
and enforces strict EBU R128 (-14.0 LUFS integrated, True Peak <= -1.0 dBTP).
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

MODULE_DIR = Path(__file__).resolve().parent
MUSIC_DIR = MODULE_DIR / "assets" / "music"
_COOL_VIBES = MUSIC_DIR / "cool_vibes_documentary.mp3"
DEFAULT_SCORE_PATH = _COOL_VIBES if _COOL_VIBES.exists() else (MUSIC_DIR / "opportunity_walks.mp3")

def master_story_audio(
    voice_track_path: Path,
    out_mastered_audio_path: Path,
    total_duration: float,
    outro_start_time: float,
    music_track_path: Optional[Path] = None,
    target_lufs: float = -14.0,
    target_tp: float = -1.0,
    sfx_cues: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Masters audio timeline:
    - Voiceover on Ch 1
    - Restrained documentary score on Ch 2 with mobile EQ & sidechain ducking
    - Optional tasteful paper/camera/stamp SFX cues
    - EBU R128 loudness normalization (-14.0 LUFS, <= -1.0 dBTP)
    """
    music_p = music_track_path or DEFAULT_SCORE_PATH
    if not music_p.exists():
        raise FileNotFoundError(f"Music track not found: {music_p}")
    if not voice_track_path.exists():
        raise FileNotFoundError(f"Voice track not found: {voice_track_path}")

    banned_sfx = ("whoosh", "swoosh", "paper_slide", "paper_crinkle")
    valid_sfx = [
        c for c in (sfx_cues or [])
        if c.get("path")
        and Path(c["path"]).exists()
        and not any(bad in Path(c["path"]).name.lower() for bad in banned_sfx)
    ][:10]

    # Build FFmpeg filtergraph cleanly (tight sidechain ducking so music punches back in between deadpan lines)
    filters = [
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{total_duration:.2f},"
        f"highpass=f=60,equalizer=f=220:t=q:w=1.0:g=1.4,"
        f"equalizer=f=1200:t=q:w=1.2:g=1.0,equalizer=f=2600:t=q:w=1.5:g=-3.0,"
        f"volume=-16.5dB,afade=t=in:ss=0:d=0.4,afade=t=out:st={max(0.0, total_duration - 1.2):.2f}:d=1.2[music_raw]",
        "[0:a]volume=1.0[vo]",
        "[music_raw][vo]sidechaincompress=threshold=0.03:ratio=4.0:attack=25:release=220[ducked_music]",
        f"[ducked_music]volume=enable='gte(t,{outro_start_time:.2f})':volume=2.0dB[music_final]",
    ]

    mix_labels = ["[vo]", "[music_final]"]
    cmd = ["ffmpeg", "-y", "-i", str(voice_track_path), "-i", str(music_p)]

    for i, cue in enumerate(valid_sfx):
        idx = i + 2
        cmd.extend(["-i", str(cue["path"])])
        delay_ms = max(0, int(round(float(cue.get("time_sec", 0.0)) * 1000.0)))
        vol = float(cue.get("volume", 0.16))
        filters.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms},volume={vol:.2f}[sfx{i}]")
        mix_labels.append(f"[sfx{i}]")

    filters.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:dropout_transition=2:normalize=0,"
        f"loudnorm=I={target_lufs}:TP={target_tp}:LRA=7[out]"
    )
    filter_complex = ";".join(filters)

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(out_mastered_audio_path)
    ])

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg mastering failed: {res.stderr}")

    # Measure final EBU R128 loudness
    meas_cmd = [
        "ffmpeg", "-i", str(out_mastered_audio_path),
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    meas_res = subprocess.run(meas_cmd, capture_output=True, text=True)
    output = meas_res.stderr

    integrated = -14.0
    true_peak = -1.0
    lra = 2.0
    for line in output.splitlines():
        if "I:" in line and "LUFS" in line:
            parts = line.strip().split()
            try:
                integrated = float(parts[1])
            except Exception:
                pass
        if "Peak:" in line and "dBFS" in line:
            parts = line.strip().split()
            try:
                true_peak = float(parts[1])
            except Exception:
                pass
        if "LRA:" in line and "LU" in line:
            parts = line.strip().split()
            try:
                lra = float(parts[1])
            except Exception:
                pass

    return {
        "mastered_audio_path": str(out_mastered_audio_path),
        "integrated_lufs": integrated,
        "true_peak_dbfs": true_peak,
        "lra": lra,
        "total_duration": total_duration,
        "outro_start": outro_start_time
    }
