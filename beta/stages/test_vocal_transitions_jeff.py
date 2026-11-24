import os
import sys
import time
from pathlib import Path
import soundfile as sf
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.jeff_stelling_synthesizer import (
    get_base_model,
    get_jeff_stelling_prompt,
    master_jeff_audio
)

def main():
    print("==================================================================")
    print("  TESTING VOCAL TRANSITIONS & CONJUNCTIONS IN JEFF'S VOICE       ")
    print("==================================================================")
    
    test_dir = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1" / "voice" / "test_vocal_transitions"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    model = get_base_model()
    prompt = get_jeff_stelling_prompt()
    
    full_script = (
        "Milan have made their move, but Mourinho wants him to stay.\n\n"
        "And — Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.\n\n"
        "Now — reports cite eighty to eighty-five million repurchase figures, but crucially... nothing is agreed.\n\n"
        "Meanwhile — a left-leg muscle injury complicates matters, with no official return date.\n\n"
        "So — will Mourinho keep the Brazilian, or will Milan force a compromise?\n\n"
        "Either way — this is football in thirty seconds. Follow for daily transfer updates."
    )
    
    print("\n--- 1. Testing Full Continuous Take ---")
    t0 = time.time()
    wavs, sr = model.generate_voice_clone(
        text=full_script,
        language="English",
        voice_clone_prompt=prompt,
        non_streaming_mode=True,
        temperature=0.7,
        repetition_penalty=1.1,
    )
    full_raw = test_dir / "full_continuous_take_raw.wav"
    sf.write(str(full_raw), wavs[0], sr)
    full_master = test_dir / "full_continuous_take_master.wav"
    master_jeff_audio(full_raw, full_master, speed_factor=1.0)
    print(f"Full continuous take generated in {time.time()-t0:.2f}s: {full_master}")

    print("\n--- 2. Testing Beat-by-Beat with Em-Dash Pacing ---")
    beats = [
        ("S01", "Milan have made their move, but Mourinho wants him to stay."),
        ("S02", "And — Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses."),
        ("S03", "Now — reports cite eighty to eighty-five million repurchase figures, but crucially... nothing is agreed."),
        ("S04", "Meanwhile — a left-leg muscle injury complicates matters, with no official return date."),
        ("S05", "So — will Mourinho keep the Brazilian, or will Milan force a compromise?"),
        ("outro", "Either way — this is football in thirty seconds. Follow for daily transfer updates.")
    ]
    
    for sid, text in beats:
        t0 = time.time()
        wavs, sr = model.generate_voice_clone(
            text=text,
            language="English",
            voice_clone_prompt=prompt,
            non_streaming_mode=True,
            temperature=0.7,
            repetition_penalty=1.1,
        )
        b_raw = test_dir / f"beat_{sid}_raw.wav"
        sf.write(str(b_raw), wavs[0], sr)
        b_master = test_dir / f"beat_{sid}_master.wav"
        master_jeff_audio(b_raw, b_master, speed_factor=1.0)
        print(f"Beat [{sid}] generated in {time.time()-t0:.2f}s: {b_master}")

if __name__ == "__main__":
    main()
