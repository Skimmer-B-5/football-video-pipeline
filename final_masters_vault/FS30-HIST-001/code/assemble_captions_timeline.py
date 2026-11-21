"""
Assembles the complete, validated MrBeast phrase timeline for the 60.0-second Cantona video.
Outputs cantona_mrbeast_captions.json.
"""

import json
from pathlib import Path

RUN_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\runs\cantona_kungfu_kick_story")
WHISPER_PATH = RUN_DIR / "whisper_by_beat.json"
whisper_data = json.load(open(WHISPER_PATH))

# Ground truth beats with global start offsets and phrase chunk definitions
# Each beat will have a list of phrases. Each phrase is a list of words.
# We will match the words to the local Whisper timestamps + global offset.

BEATS_CONFIG = [
    {
        "beat": "beat_1",
        "offset": 0.0,
        "phrases": [
            [("JANUARY", 0), ("1995", 1)],
            [("SELHURST", 2), ("PARK", 3)],
            [("FOR", 4), ("48", 5), ("MINUTES", 6)],
            [("PALACE", 7), ("DEFENDER", 8)],
            [("RICHARD", 9), ("SHAW", 10)],
            [("SHADOWS", 11), ("ERIC", 12), ("CANTONA", 13)],
            [("LIKE", 14), ("A", 15), ("ZEALOUS", 16)],
            [("TAX", 17), ("COLLECTOR", 18)],
            [("THE", 19), ("TRAP", 20), ("IS", 21), ("SET", 22)]
        ]
    },
    {
        "beat": "beat_2",
        "offset": 8.0,
        "phrases": [
            # In beat 2: w0+w1 = Cantona, w2+w3 = retaliates
            [("CANTONA", (0, 1)), ("RETALIATES", (2, 3))],
            [("REFEREE", 4), ("ALAN", 5), ("WILKIE", 6)],
            [("PRODUCES", 7), ("A", 8), ("STRAIGHT", 9), ("RED", 10)],
            [("WALKING", 11), ("OFF", 12)],
            [("SUPPORTER", 13), ("MATTHEW", 14), ("SIMMONS", 15)],
            [("SPRINTS", 16), ("DOWN", 17), ("11", 18), ("ROWS", 19)],
            [("TO", 20), ("OFFER", 21), ("SOME", 22)],
            [("RATHER", 23), ("UNFILTERED", 24)],
            [("PERSONAL", 25), ("ADVICE", 26)]
        ]
    },
    {
        "beat": "beat_3",
        "offset": 16.5,
        "phrases": [
            [("CANTONA", 0), ("EVIDENTLY", 1), ("DECIDED", 2)],
            [("THE", 3), ("REFEREE", 4), ("WASN'T", 5)],
            [("THE", 6), ("ONLY", 7), ("PERSON", 8)],
            [("REQUIRING", 9), ("CROWD", 10), ("CONTROL", 11)],
            [("HE", 12), ("HURDLES", 13), ("THE", 14), ("HOARDINGS", 15)],
            [("AND", 16), ("LAUNCHES", 17), ("AN", 18), ("AIRBORNE", 19)],
            # w20+w21 = studs-first
            [("STUDS-FIRST", (20, 21)), ("FLYING", 22), ("KICK", 23)],
            [("INTO", 24), ("THE", 25), ("SUPPORTER'S", 26), ("CHEST", 27)],
            # w28+w29 = Football
            [("FOOTBALL", (28, 29)), ("WAS", 30), ("SHATTERED", 31)],
            [("FOREVER", 32)]
        ]
    },
    {
        "beat": "beat_4",
        "offset": 28.0,
        "phrases": [
            [("THE", 0), ("OUTRAGE", 1), ("WAS", 2)],
            [("THERMONUCLEAR", 3)],
            # w5+w6 = FA
            [("THE", 4), ("FA", (5, 6)), ("BANNED", 7), ("HIM", 8)],
            [("FOR", 9), ("EIGHT", 10), ("MONTHS", 11)],
            [("IN", 12), ("COURT", 13)],
            [("TWO", 14), ("WEEKS", 15), ("IN", 16), ("PRISON", 17)],
            [("BECAME", 18), ("120", 19), ("HOURS", 20)],
            [("OF", 21), ("COMMUNITY", 22), ("SERVICE", 23)],
            [("APPARENTLY", 24), ("EVEN", 25), ("KINGS", 26)],
            [("CAN", 27), ("BE", 28), ("SENT", 29)],
            [("TO", 30), ("THEIR", 31), ("ROOMS", 32)]
        ]
    },
    {
        "beat": "beat_5",
        "offset": 39.5,
        "phrases": [
            [("AT", 0), ("THE", 1), ("PRESS", 2), ("CONFERENCE", 3)],
            [("CANTONA", 4), ("TAKES", 5), ("A", 6), ("SINGLE", 7)],
            [("SIP", 8), ("OF", 9), ("WATER", 10)],
            [("AND", 11), ("DELIVERS", 12), ("15", 13)],
            [("CRYPTIC", 14), ("WORDS", 15)],
            [("WHEN", 16), ("THE", 17), ("SEAGULLS", 18)],
            [("FOLLOW", 19), ("THE", 20), ("TRAWLER", 21)],
            [("IT", 22), ("IS", 23), ("BECAUSE", 24)],
            [("THEY", 25), ("THINK", 26), ("SARDINES", 27)],
            [("WILL", 28), ("BE", 29), ("THROWN", 30)],
            [("INTO", 31), ("THE", 32), ("SEA", 33)]
        ]
    },
    {
        "beat": "beat_6",
        "offset": 51.5,
        "phrases": [
            [("EIGHT", 0), ("MONTHS", 1), ("LATER", 2)],
            [("HE", 3), ("RETURNED", 4), ("TO", 5), ("FIRE", 6)],
            [("UNITED", 7), ("TO", 8), ("ANOTHER", 9), ("DOUBLE", 10)],
            [("LONG", 11), ("LIVE", 12), ("THE", 13), ("KING", 14)]
        ]
    },
    {
        "beat": "outro_speech",
        "offset": 56.0,
        "phrases": [
            [("SEE", 0), ("YOU", 1), ("LATER", 2)],
            [("THIS", 3), ("IS", 4), ("FOOTBALL", 5)],
            [("IN", 6), ("30", 7), ("SECONDS", 8)],
            [("FOLLOW", 9), ("FOR", 10), ("MORE", 11)]
        ]
    }
]

all_phrases = []

for cfg in BEATS_CONFIG:
    bid = cfg["beat"]
    offset = cfg["offset"]
    w_chunks = whisper_data[bid]
    
    for phrase_spec in cfg["phrases"]:
        p_words = []
        for word_text, idx_ref in phrase_spec:
            if isinstance(idx_ref, tuple):
                # Merged chunks (e.g. Can't + zone or studs + first)
                first_c = w_chunks[idx_ref[0]]
                last_c = w_chunks[idx_ref[-1]]
                t_start = round(offset + first_c["timestamp"][0], 2)
                t_end = round(offset + last_c["timestamp"][1], 2)
            else:
                c = w_chunks[idx_ref]
                t_start = round(offset + c["timestamp"][0], 2)
                t_end = round(offset + c["timestamp"][1], 2)
                
            # Guarantee min duration of 0.12s for ultra-short words so highlight is visible
            if t_end <= t_start:
                t_end = t_start + 0.15
            elif t_end - t_start < 0.10:
                t_end = t_start + 0.12
                
            p_words.append({
                "word": word_text,
                "start": t_start,
                "end": t_end
            })
            
        # Phrase bounds
        p_start = p_words[0]["start"]
        p_end = p_words[-1]["end"]
        # Add slight trailing breath buffer so phrase doesn't abruptly vanish before next one
        all_phrases.append({
            "beat": bid,
            "start": p_start,
            "end": p_end + 0.08,
            "words": p_words
        })

# Fix gaps between consecutive phrases so phrases flow seamlessly
for i in range(len(all_phrases) - 1):
    curr_p = all_phrases[i]
    next_p = all_phrases[i + 1]
    # If gap is small (< 0.25s) and within same beat, extend curr_p end to next_p start
    if curr_p["beat"] == next_p["beat"] and 0 < (next_p["start"] - curr_p["end"]) < 0.25:
        curr_p["end"] = next_p["start"]

out_json = RUN_DIR / "cantona_mrbeast_captions.json"
with open(out_json, "w") as f:
    json.dump(all_phrases, f, indent=2)

print(f"✓ Assembled {len(all_phrases)} MrBeast subtitle phrases across 60.0s.")
print(f"✓ Saved to {out_json.name}")
