"""
beta/stages/generate_v7_1_6_5_auditions.py
Generates three distinct voice auditions for Beta V7.1.6.5:
Passage: "Milan have made their move, but Mourinho wants him to stay. Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses."

Option A: Qwen3-TTS Ryan - Energetic Television Football Correspondent (Natural Speed, Dramatic Intonation)
Option B: Edge-TTS en-GB-RyanNeural - Crisp, Bright British Sports News Anchor (Strong Consonants, Natural British Delivery)
Option C: Edge-TTS en-GB-ThomasNeural - Authoritative, Expressive Broadcast Journalist (Natural European Name Pronunciation)
"""

import sys
import os
import json
import time
import asyncio
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

AUDITION_TEXT = (
    "Milan have made their move, but Mourinho wants him to stay. "
    "Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses."
)

OUTPUT_DIR = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "voice" / "auditions_v7_1_6_5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def master_audio(in_wav: Path, out_mp3: Path, out_wav: Path):
    """Applies broadcast-grade studio mastering (-14 LUFS, presence EQ, gentle compression)."""
    af_chain = (
        "highpass=f=75,"
        "equalizer=f=3000:t=q:w=1.2:g=3.0,"
        "acompressor=threshold=-16dB:ratio=3.5:attack=5:release=50,"
        "loudnorm=I=-14:LRA=7:TP=-1.0"
    )
    # Master to 48kHz WAV
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(in_wav),
        "-af", af_chain,
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
        str(out_wav)
    ], check=True, capture_output=True)

    # Export high-quality MP3 (192k)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(out_wav),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(out_mp3)
    ], check=True, capture_output=True)

def generate_voice_a():
    """Option A: Qwen3-TTS Ryan with energetic football correspondent instruction."""
    print("\n--- Generating Option A: Qwen3-TTS Ryan (Energetic Correspondent) ---")
    from stages.qwen_tts_synthesizer import synthesize_qwen3
    
    raw_wav = OUTPUT_DIR / "raw_voice_a_ryan.wav"
    out_wav = OUTPUT_DIR / "audition_voice_A_ryan_energetic.wav"
    out_mp3 = OUTPUT_DIR / "audition_voice_A_ryan_energetic.mp3"

    instruct = (
        "Speak in an urgent, energetic, and highly confident British football news correspondent delivery, "
        "breaking a massive developing transfer story on live television. Use expressive pitch variation, "
        "sharp emphasis on Endrick, Mourinho, and Milan, with natural changes in pace and authoritative sentence rhythm."
    )

    t0 = time.time()
    synthesize_qwen3(
        text=AUDITION_TEXT,
        output_path=raw_wav,
        speaker="Ryan",
        instruct=instruct,
        normalize_db=-0.5
    )
    master_audio(raw_wav, out_mp3, out_wav)
    print(f"Option A generated in {time.time()-t0:.2f}s: {out_mp3} ({out_mp3.stat().st_size} bytes)")
    return out_mp3, out_wav

async def generate_voice_b_async():
    """Option B: Edge-TTS en-GB-RyanNeural (Bright, Crisp British Sports News)."""
    print("\n--- Generating Option B: Edge Neural en-GB-Ryan (Bright Sports News) ---")
    import edge_tts
    
    raw_mp3 = OUTPUT_DIR / "raw_voice_b_edge_ryan.mp3"
    out_wav = OUTPUT_DIR / "audition_voice_B_british_expressive.wav"
    out_mp3 = OUTPUT_DIR / "audition_voice_B_british_expressive.mp3"

    t0 = time.time()
    comm = edge_tts.Communicate(
        text=AUDITION_TEXT,
        voice="en-GB-RyanNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    await comm.save(str(raw_mp3))
    master_audio(raw_mp3, out_mp3, out_wav)
    raw_mp3.unlink(missing_ok=True)
    print(f"Option B generated in {time.time()-t0:.2f}s: {out_mp3} ({out_mp3.stat().st_size} bytes)")
    return out_mp3, out_wav

async def generate_voice_c_async():
    """Option C: Edge-TTS en-GB-ThomasNeural (Authoritative, Expressive Broadcast Journalist)."""
    print("\n--- Generating Option C: Edge Neural en-GB-Thomas (Broadcast Journalist) ---")
    import edge_tts
    
    raw_mp3 = OUTPUT_DIR / "raw_voice_c_edge_thomas.mp3"
    out_wav = OUTPUT_DIR / "audition_voice_C_alternative_anchor.wav"
    out_mp3 = OUTPUT_DIR / "audition_voice_C_alternative_anchor.mp3"

    t0 = time.time()
    comm = edge_tts.Communicate(
        text=AUDITION_TEXT,
        voice="en-GB-ThomasNeural",
        rate="+1%",
        pitch="+0Hz"
    )
    await comm.save(str(raw_mp3))
    master_audio(raw_mp3, out_mp3, out_wav)
    raw_mp3.unlink(missing_ok=True)
    print(f"Option C generated in {time.time()-t0:.2f}s: {out_mp3} ({out_mp3.stat().st_size} bytes)")
    return out_mp3, out_wav

def main():
    print("==================================================================")
    print("  GENERATING THREE DISTINCT VOICE AUDITIONS FOR BETA V7.1.6.5   ")
    print("==================================================================")
    print(f"Passage: \"{AUDITION_TEXT}\"\n")

    # Option A (Qwen3-TTS Ryan)
    a_mp3, a_wav = generate_voice_a()

    # Option B (Edge-TTS en-GB-RyanNeural)
    b_mp3, b_wav = asyncio.run(generate_voice_b_async())

    # Option C (Edge-TTS en-GB-ThomasNeural)
    c_mp3, c_wav = asyncio.run(generate_voice_c_async())

    # Duration and quality verification via ffprobe
    auditions = [
        ("Option A: Qwen3 Ryan (Energetic Correspondent)", a_mp3),
        ("Option B: British Expressive (en-GB-Ryan)", b_mp3),
        ("Option C: Alternative Anchor (en-GB-Thomas)", c_mp3),
    ]

    print("\n--- Audition Verification Summary ---")
    summary = {}
    for label, mp3_path in auditions:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,bit_rate",
            "-of", "json",
            str(mp3_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        meta = json.loads(res.stdout)["format"]
        dur = float(meta["duration"])
        br = int(meta.get("bit_rate", 192000)) // 1000
        print(f"  • {label}: {dur:.2f}s @ {br}kbps ({mp3_path.stat().st_size} bytes)")
        summary[label] = {
            "file": mp3_path.name,
            "duration_sec": round(dur, 2),
            "bitrate_kbps": br,
            "size_bytes": mp3_path.stat().st_size,
            "path": str(mp3_path.resolve())
        }

    manifest_file = OUTPUT_DIR / "auditions_manifest.json"
    manifest_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved auditions manifest: {manifest_file}")

if __name__ == "__main__":
    main()
