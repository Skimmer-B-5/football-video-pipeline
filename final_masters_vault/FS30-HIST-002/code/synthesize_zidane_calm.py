"""
Synthesize calm, unhurried 60-second British narration for Zinedine Zidane documentary.
Deliberate, measured cadence (~0.8x of previous speed / ~150 WPM).
Exact 60.00s total duration.
"""

import sys
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT))

from stages.qwen_tts_synthesizer import synthesize_qwen3

RUN_DIR = PROJECT_ROOT / "runs" / "zidane_headbutt_story"
AUDIO_DIR = RUN_DIR / "audio_calm"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

BEATS = [
    (
        "beat_1",
        "July 2006. Berlin. Zinedine Zidane steps onto the pitch for his final professional match. Seven minutes in, he chips a Panenka penalty past Gianluigi Buffon. Pure audacity.",
        8.5,
        "Speak as a calm, measured, articulate British documentary presenter. Unhurried cadence, thoughtful pauses, warm baritone resonance, subtle intellectual irony."
    ),
    (
        "beat_2",
        "In extra time, Marco Materazzi aggressively grabs Zidane's shirt. Zizou offers to give it to him after the match. Materazzi, however, chose a toxic insult regarding Zidane's sister.",
        9.0,
        "Narrate with understated irony, calm curiosity, crisp consonants. Controlled emphasis on the punchline, unhurried pacing."
    ),
    (
        "beat_3",
        "Zidane turns around and delivers a ferocious headbutt directly into Materazzi's chest. The Italian collapses instantly. One billion viewers stared in utter disbelief.",
        11.5,
        "Deliver with dramatic historical weight, measured storytelling, vivid clarity on the shock impact. Unhurried, deliberate delivery."
    ),
    (
        "beat_4",
        "The fourth official saw everything through his headset. A straight red card was brandished. Zidane walked into the tunnel, passing inches from the golden World Cup trophy without looking back.",
        11.5,
        "Narrate the dismissal with solemn authority and dramatic weight. Calm, grave, measured pacing."
    ),
    (
        "beat_5",
        "Italy won the shootout. FIFA banned Zidane for three matches, commuted to community service. Remarkably, he was still voted the tournament's best player.",
        11.0,
        "Calm, theatrical storytelling with dry British wit. Pause slightly before the punchline, letting the understated irony land naturally."
    ),
    (
        "beat_6",
        "One hundred and eight caps. A majestic career ended in fury. Long live Zizou.",
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
    print("  SYNTHESIZING CALM UNHURRIED BRITISH NARRATION (QWEN3-TTS)")
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
    print("  CALM AUDIO SYNTHESIS COMPLETE SUMMARY")
    print("=" * 70)
    for bid, d in durations.items():
        print(f"  {bid:14s}: {d:.2f}s")

if __name__ == "__main__":
    main()
