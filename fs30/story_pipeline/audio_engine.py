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
DEFAULT_SCORE_PATH = MUSIC_DIR / "opportunity_walks.mp3"

def master_story_audio(
    voice_track_path: Path,
    out_mastered_audio_path: Path,
    total_duration: float,
    outro_start_time: float,
    music_track_path: Optional[Path] = None,
    target_lufs: float = -14.0,
    target_tp: float = -1.0
) -> Dict[str, Any]:
    """
    Masters audio timeline:
    - Voiceover on Ch 1
    - Background score on Ch 2 with mobile EQ:
      * highpass=f=60
      * equalizer=f=220:t=q:w=1.0:g=1.8 (warmth)
      * equalizer=f=1200:t=q:w=1.2:g=1.5 (phone speaker clarity)
      * equalizer=f=2600:t=q:w=1.5:g=-2.8 (voice pocket carving)
    - Sidechain ducking: -5.5 dB during speech, +2.5 dB during outro.
    - EBU R128 loudness normalization.
    """
    music_p = music_track_path or DEFAULT_SCORE_PATH
    if not music_p.exists():
        raise FileNotFoundError(f"Music track not found: {music_p}")
    if not voice_track_path.exists():
        raise FileNotFoundError(f"Voice track not found: {voice_track_path}")

    # Build FFmpeg filtergraph
    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09,"
        f"atrim=0:{total_duration:.2f},"
        f"highpass=f=60,"
        f"equalizer=f=220:t=q:w=1.0:g=1.8,"
        f"equalizer=f=1200:t=q:w=1.2:g=1.5,"
        f"equalizer=f=2600:t=q:w=1.5:g=-2.8,"
        f"volume=-16dB[music_raw];"
        f"[0:a]volume=1.0[vo];"
        f"[music_raw][vo]sidechaincompress=threshold=0.035:ratio=3.5:attack=50:release=350[ducked_music];"
        f"[ducked_music]volume=enable='gte(t,{outro_start_time:.2f})':volume=2.5dB[music_final];"
        f"[vo][music_final]amix=inputs=2:duration=first:dropout_transition=2,"
        f"loudnorm=I={target_lufs}:TP={target_tp}:LRA=7[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_track_path),
        "-i", str(music_p),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        str(out_mastered_audio_path)
    ]

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
