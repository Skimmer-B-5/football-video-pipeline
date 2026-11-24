import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ws_base = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1"
clean_dir = ws_base / "voice" / "v7_1_6_7_clean_vocal_transitions"
output_dir = ws_base / "output"
output_dir.mkdir(parents=True, exist_ok=True)

concat_txt = clean_dir / "concat_list.txt"
scene_ids = ["S01", "S02", "S03", "S04", "S05", "outro"]

with open(concat_txt, "w", encoding="utf-8") as f:
    for sid in scene_ids:
        wav_path = clean_dir / f"scene_{sid}.wav"
        f.write(f"file '{wav_path.resolve().as_posix()}'\n")

unmastered_vo = clean_dir / "master_clean_vo.wav"
subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", str(concat_txt),
    "-c:a", "pcm_s16le",
    str(unmastered_vo)
], check=True, capture_output=True)

music_bed = PROJECT_ROOT / "beta" / "data" / "music" / "transfer_pulse.wav"
final_mix = clean_dir / "master_audio_v7_1_6_7.wav"

mix_cmd = [
    "ffmpeg", "-y",
    "-i", str(unmastered_vo),
    "-stream_loop", "-1", "-i", str(music_bed),
    "-filter_complex",
    "[1:a]volume=0.07,aloop=loop=-1:size=2e+09[bed];"
    "[0:a][bed]amix=inputs=2:duration=first:dropout_transition=2[mixed];"
    "[mixed]loudnorm=I=-14:TP=-1.0:LRA=7,aformat=sample_rates=48000:channel_layouts=stereo[out]",
    "-map", "[out]",
    "-c:a", "pcm_s16le",
    str(final_mix)
]
subprocess.run(mix_cmd, check=True, capture_output=True)

# Also create an mp3 preview
final_mp3 = clean_dir / "master_audio_v7_1_6_7.mp3"
subprocess.run([
    "ffmpeg", "-y",
    "-i", str(final_mix),
    "-c:a", "libmp3lame",
    "-b:a", "192k",
    str(final_mp3)
], check=True, capture_output=True)

# Copy to artifacts for easy user inspection
artifact_dir = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")
import shutil
shutil.copy2(str(final_mp3), str(artifact_dir / "v7_1_6_7_clean_vocal_audio_preview.mp3"))

print(f"Master audio created: {final_mix}")
print(f"Preview mp3: {artifact_dir / 'v7_1_6_7_clean_vocal_audio_preview.mp3'}")
