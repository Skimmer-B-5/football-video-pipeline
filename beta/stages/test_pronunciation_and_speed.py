import sys
import time
import subprocess
import soundfile as sf
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.qwen_tts_synthesizer import get_qwen3_tts_model

# Pronunciation test passage containing all three names
TEST_PASSAGE = "Milan have made their move, but Mourinho wants Endrick to stay in Madrid."

# Variations for testing phonetic respellings
VARIANTS = [
    {
        "id": "standard",
        "text": "Milan have made their move, but Mourinho wants Endrick to stay in Madrid."
    },
    {
        "id": "phonetic_1",
        "text": "Mee-lahn have made their move, but Moo-reen-yoh wants En-drick to stay in Madrid."
    },
    {
        "id": "phonetic_2",
        "text": "Mih-lahn have made their move, but Muh-reen-yo wants En-drick to stay in Madrid."
    }
]

def apply_time_stretch(in_wav: Path, out_wav: Path, speed: float = 1.2):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(in_wav),
        "-filter:a", f"atempo={speed}",
        "-ar", "48000", "-ac", "2",
        str(out_wav)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def main():
    out_dir = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "voice" / "pronunciation_test"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("=== Loading Qwen3-TTS Model ===")
    model = get_qwen3_tts_model()
    instruct = (
        "A mature British male sports correspondent delivering breaking football transfer news from the studio desk. "
        "Measured, authoritative, calm baritone with clear British pronunciation, and restrained emphasis."
    )
    
    for v in VARIANTS:
        vid = v["id"]
        txt = v["text"]
        print(f"\n--- Testing variant '{vid}': \"{txt}\" ---")
        t0 = time.time()
        wavs, sr = model.generate_custom_voice(
            text=txt,
            language="English",
            speaker="Ryan",
            instruct=instruct
        )
        raw_path = out_dir / f"test_{vid}_1x.wav"
        sf.write(str(raw_path), wavs[0], sr)
        dur_1x = len(wavs[0]) / sr
        print(f"  1.0x generated in {time.time()-t0:.2f}s | Duration: {dur_1x:.2f}s")
        
        # Apply 1.2x atempo
        speed_12_path = out_dir / f"test_{vid}_1.2x.wav"
        apply_time_stretch(raw_path, speed_12_path, speed=1.2)
        info_12 = sf.info(str(speed_12_path))
        print(f"  1.2x duration: {info_12.duration:.2f}s ({speed_12_path.name})")

if __name__ == "__main__":
    main()
