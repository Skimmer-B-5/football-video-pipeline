"""
Synthesize tight, witty 60-second voiceover for Zinedine Zidane 2006 World Cup Headbutt documentary.
Delivered with articulate British documentary presenter tone (Ryan voice):
Calm, knowledgeable, dry humor, controlled emphasis, natural pauses.
"""

import sys
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT))

from stages.qwen_tts_synthesizer import synthesize_qwen3

RUN_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story"
AUDIO_DIR = RUN_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

BEATS = [
    (
        "beat_1",
        "July 2006. Berlin. Zinedine Zidane steps onto the pitch for his final professional match. Seven minutes in, he chips a nonchalant Panenka penalty off the crossbar past Gianluigi Buffon. Pure poetry.",
        8.0,
        "Speak as an educated, warm British scholar explaining a historic football moment. Thoughtful pauses, crisp consonant articulation, warm baritone resonance."
    ),
    (
        "beat_2",
        "One hundred and ten minutes of grueling extra time later, Marco Materazzi grabs Zidane's shirt. Zizou politely offers to give it to him after the match. Materazzi, however, had an entirely different family heirloom in mind.",
        8.5,
        "Narrate with understated irony and controlled emphasis. Clear crisp consonants, calm scholarly curiosity, slight pause before punchline."
    ),
    (
        "beat_3",
        "Zidane stops, turns around, and delivers a ferocious, full-force headbutt directly into the Italian defender's chest. Materazzi hits the turf like a sack of damp cement. One billion viewers stared in utter disbelief.",
        11.5,
        "Deliver the opening observation with dry wit, followed by dramatic historical weight and vivid clarity on the sudden shock impact."
    ),
    (
        "beat_4",
        "Referee Horacio Elizondo missed it, but fourth official Medina Cantalejo saw everything through his headset. The red card is brandished. Zidane walks into the tunnel, passing inches from the golden World Cup trophy without looking back.",
        11.5,
        "Narrate the dismissal with measured authority and dramatic weight. Solemn, iconic historical atmosphere."
    ),
    (
        "beat_5",
        "Italy won the shootout. FIFA handed Zidane a three-match ban and three days of community service with UNICEF. Remarkably, he was still voted the tournament's best player. Apparently, legendary status comes with some diplomatic immunity.",
        12.0,
        "Calm, theatrical storytelling with dry British wit. Pause slightly before the punchline, letting the understated jab land naturally."
    ),
    (
        "beat_6",
        "One hundred and eight caps. A final act of explosive fury, yet forever adored. Long live Zizou.",
        4.5,
        "Deliver the concluding narrative tribute with quiet reverence, warmth, and mythic finality."
    ),
    (
        "outro_speech",
        "See you later. This is Football in 30 Seconds. Follow for more.",
        4.0,
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
    print("  SYNTHESIZING ZIDANE 2006 DOCUMENTARY NARRATION & SPOKEN OUTRO (QWEN3-TTS)")
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

if __name__ == "__main__":
    main()
