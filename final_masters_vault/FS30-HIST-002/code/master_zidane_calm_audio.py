"""
Mastering and sequence alignment for calm 60.0s Zidane documentary soundtrack:
- Beat 1: 0.0s - 8.5s (8.5s)
- Beat 2: 8.5s - 17.5s (9.0s)
- Beat 3: 17.5s - 29.0s (11.5s)
- Beat 4: 29.0s - 40.5s (11.5s)
- Beat 5: 40.5s - 51.5s (11.0s)
- Beat 6: 51.5s - 56.0s (4.5s)
- Outro:  56.0s - 60.0s (4.0s)
- EBU R128 loudness normalization (-14.0 LUFS, <= -1.0 dBTP)
"""

import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
RUN_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story"
AUDIO_DIR = RUN_DIR / "audio_calm"
MUSIC_SRC = PROJECT_ROOT / "fs30" / "story_pipeline" / "assets" / "music" / "opportunity_walks.mp3"

TARGET_BEATS = [
    ("beat_1", 11.20),
    ("beat_2", 9.96),
    ("beat_3", 8.98),
    ("beat_4", 9.11),
    ("beat_5", 8.65),
    ("beat_6", 8.10),
    ("outro_speech", 4.00)
]

def get_duration(p: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(proc.stdout.strip())
    except:
        return 0.0

def master_audio():
    print("=" * 70)
    print("  BALANCED AUDIO MASTERING (UNHURRIED PACING // EXACT 60.00s)")
    print("=" * 70)

    processed_wavs = []
    for bid, target_dur in TARGET_BEATS:
        raw_wav = AUDIO_DIR / f"{bid}.wav"
        if not raw_wav.exists():
            raise FileNotFoundError(f"Missing {raw_wav}")
        
        # Strip dead silence
        stripped_wav = AUDIO_DIR / f"{bid}_pure.wav"
        cmd_strip = [
            "ffmpeg", "-y", "-i", str(raw_wav),
            "-af", "silenceremove=stop_periods=-1:stop_duration=0.15:stop_threshold=-38dB",
            str(stripped_wav)
        ]
        subprocess.run(cmd_strip, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        pure_dur = get_duration(stripped_wav)
        
        # Calm, natural tempo stretching
        tempo = pure_dur / target_dur
        print(f"[{bid}] Pure speech: {pure_dur:.2f}s | Target: {target_dur:.2f}s | Applied tempo: {tempo:.2f}x")
        
        proc_wav = AUDIO_DIR / f"{bid}_timed.wav"
        af_chain = f"atempo={tempo:.4f},apad=whole_dur={target_dur:.2f}"
        cmd_tempo = [
            "ffmpeg", "-y", "-i", str(stripped_wav),
            "-af", af_chain,
            "-t", f"{target_dur:.2f}",
            "-ar", "44100", "-ac", "2",
            str(proc_wav)
        ]
        subprocess.run(cmd_tempo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        processed_wavs.append(proc_wav)

    # Concat
    concat_list = AUDIO_DIR / "concat_full_speech.txt"
    with open(concat_list, "w") as f:
        for p in processed_wavs:
            f.write(f"file '{p.name}'\n")

    full_speech_wav = AUDIO_DIR / "full_speech_60s.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(full_speech_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    master_wav = RUN_DIR / "zidane_mastered_audio_60s.wav"
    filter_complex = (
        "[1:a]aloop=loop=-1:size=200000000,"
        "highpass=f=60,equalizer=f=220:t=q:w=1.2:g=1.8,equalizer=f=2600:t=q:w=1.4:g=-2.8,equalizer=f=1200:t=q:w=1.2:g=1.5,"
        "volume=0.55[music_eq];"
        "[music_eq][0:a]sidechaincompress=threshold=0.04:ratio=3.2:attack=35:release=250[ducked_music];"
        "[0:a][ducked_music]amix=inputs=2:duration=first:dropout_transition=1,"
        "afade=t=out:st=58.5:d=1.5,"
        "loudnorm=I=-14.0:TP=-1.0:LRA=7.0[master_out]"
    )

    cmd_mix = [
        "ffmpeg", "-y",
        "-i", str(full_speech_wav),
        "-i", str(MUSIC_SRC),
        "-filter_complex", filter_complex,
        "-map", "[master_out]",
        "-c:a", "pcm_s16le",
        "-ar", "48000",
        "-t", "60.00",
        str(master_wav)
    ]
    subprocess.run(cmd_mix, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    master_dur = get_duration(master_wav)
    print(f"✓ Master soundtrack generated: {master_wav.name} ({master_dur:.2f}s)")

    cmd_meas = ["ffmpeg", "-i", str(master_wav), "-af", "ebur128=framelog=verbose", "-f", "null", "-"]
    proc = subprocess.run(cmd_meas, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    i_m = re.search(r"Integrated loudness:\s+I:\s+([-\d\.]+)\s+LUFS", proc.stderr)
    lufs = i_m.group(1) if i_m else "N/A"
    print(f"✓ EBU R128 Loudness: {lufs} LUFS")

if __name__ == "__main__":
    master_audio()
