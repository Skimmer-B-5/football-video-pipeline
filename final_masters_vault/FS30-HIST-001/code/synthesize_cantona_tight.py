"""
Synthesize tight, witty 60-second voiceover for Eric Cantona documentary.
Total words: 173 words across 60.0s (~165 WPM) with natural pauses and subtle British wit.
"""

import sys
from pathlib import Path
import subprocess
import shutil

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT))

from stages.qwen_tts_synthesizer import synthesize_qwen3

RUN_DIR = PROJECT_ROOT / "runs" / "cantona_kungfu_kick_story"
AUDIO_DIR = RUN_DIR / "audio"
ARTIFACT_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")

BEATS = [
    (
        "beat_1",
        "January 1995. Selhurst Park. For forty-eight minutes, Palace defender Richard Shaw shadows Eric Cantona like a zealous tax collector. The trap is set.",
        9.0,
        "Speak as an educated, warm British scholar explaining a fascinating football history scandal. Thoughtful pauses, dry humor, crisp consonant articulation, warm baritone resonance."
    ),
    (
        "beat_2",
        "Cantona retaliates. Referee Alan Wilkie produces a straight red. Walking off, supporter Matthew Simmons sprints down eleven rows to offer some rather unfiltered personal advice.",
        10.0,
        "Narrate with understated irony and controlled emphasis. Clear crisp consonants, calm scholarly curiosity."
    ),
    (
        "beat_3",
        "Cantona evidently decided the referee wasn't the only person requiring crowd control. He hurdles the hoardings and launches an airborne, studs-first flying kick into the supporter's chest. Football was shattered forever.",
        12.0,
        "Deliver the opening observation with dry wit, followed by dramatic historical weight and vivid clarity on the martial arts impact."
    ),
    (
        "beat_4",
        "The outrage was thermonuclear. The FA banned him for eight months. In court, two weeks in prison became one hundred and twenty hours of community service. Apparently, even kings can be sent to their rooms.",
        11.0,
        "Narrate the legal consequences with measured authority. Pause slightly before the punchline, letting the dry humour land naturally."
    ),
    (
        "beat_5",
        "At the press conference, Cantona takes a single sip of water and delivers fifteen cryptic words: When the seagulls follow the trawler, it is because they think sardines will be thrown into the sea.",
        12.0,
        "Calm, theatrical storytelling. Build the mystique of the press conference, then deliver the famous quotation with quiet philosophical gravity."
    ),
    (
        "beat_6",
        "Eight months later, he returned to fire United to another double. Long live the King.",
        3.0,
        "Deliver the concluding narrative victory with quiet triumph and finality. Decisive, warm cadence."
    ),
    (
        "outro_speech",
        "See you later. This is Football in 30 Seconds. Follow for more.",
        3.0,
        "Natural, warm conversational farewell from the same British presenter. Not robotic. A genuine parting sign-off."
    )
]

def get_audio_duration(p: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(proc.stdout.strip())
    except:
        return 0.0

def main():
    print("=" * 70)
    print("  SYNTHESIZING TIGHT 173-WORD NARRATION & SPOKEN OUTRO (QWEN3-TTS)")
    print("=" * 70)

    durations = {}
    for bid, text, target_dur, instruct in BEATS:
        out_wav = AUDIO_DIR / f"{bid}.wav"
        print(f"\n[Audio] Synthesizing {bid} (target ~{target_dur}s)...")
        print(f"  Text: {text}")
        
        path, dur = synthesize_qwen3(
            text=text,
            output_path=out_wav,
            speaker="Ryan",
            instruct=instruct,
            language="English"
        )
        actual_dur = get_audio_duration(out_wav)
        durations[bid] = actual_dur
        print(f"  -> Generated {bid}.wav: duration = {actual_dur:.2f}s (target: {target_dur}s)")

    print("\n" + "=" * 70)
    print("  AUDIO SYNTHESIS COMPLETE SUMMARY")
    print("=" * 70)
    for bid, d in durations.items():
        print(f"  {bid:14s}: {d:.2f}s")
        
    for bid, _, _, _ in BEATS:
        wav_p = AUDIO_DIR / f"{bid}.wav"
        if wav_p.exists():
            shutil.copyfile(str(wav_p), str(ARTIFACT_DIR / f"cantona_{bid}.wav"))
            
    print("✓ All audio stems synthesized and staged in artifacts.")

if __name__ == "__main__":
    main()
