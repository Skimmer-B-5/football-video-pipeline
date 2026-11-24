import subprocess
from pathlib import Path

voice_dir = Path("beta/workspaces/endrick_milan/run_v7_1/voice")
for f in sorted(voice_dir.glob("*.mp3")):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(f)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    dur = float(res.stdout.strip()) if res.stdout.strip() else 0.0
    print(f"{f.name}: {dur:.2f}s ({f.stat().st_size} bytes)")
