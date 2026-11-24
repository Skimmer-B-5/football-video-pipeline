"""
beta/stages/test_spoken_token_timing.py
Validates the token expansion and exact timing calculations.
"""

import re
from typing import List, Tuple

def expand_spoken_tokens(text: str) -> List[str]:
    clean = re.sub(r'[\.,\?!\"“”\']', '', text)
    tokens = []
    for word in clean.split():
        if '-' in word:
            parts = word.split('-')
            tokens.extend([p for p in parts if p])
        else:
            tokens.append(word)
    return tokens

def calculate_spoken_duration_v7_1_6(text: str, wpm: float = 138.0) -> Tuple[int, int, float]:
    written_words = len(text.strip().split())
    spoken_tokens = expand_spoken_tokens(text)
    token_count = len(spoken_tokens)

    # User mandate: duration = spoken_tokens / configured_wpm * 60
    base_speech_sec = (token_count / wpm) * 60.0

    comma_count = text.count(",") + text.count("—")
    period_count = text.count(".") + text.count("?") + text.count("!")
    pause_sec = (comma_count * 0.18) + (period_count * 0.32)

    total_sec = round(base_speech_sec + pause_sec, 2)
    return written_words, token_count, total_sec

if __name__ == "__main__":
    beats = [
        ("S01", "Milan are plotting a January approach, but José Mourinho refuses to let him leave."),
        ("S02", "Italian reports link twenty-year-old Endrick to sixty million fixed, plus ten in bonuses."),
        ("S03", "Madrid discussed eighty to eighty-five million repurchase terms, but nothing is agreed."),
        ("S04", "A left-adductor injury adds uncertainty, leaving any transfer impact unknown."),
        ("S05", "Will Mourinho keep the Brazilian, or will Milan force a compromise?")
    ]

    total_w = 0
    total_t = 0
    total_dur = 0.0

    curr_t = 0.0
    for sid, text in beats:
        w_cnt, t_cnt, dur = calculate_spoken_duration_v7_1_6(text)
        start_t = round(curr_t, 2)
        end_t = round(curr_t + dur, 2)
        curr_t = end_t
        total_w += w_cnt
        total_t += t_cnt
        total_dur += dur
        tokens = expand_spoken_tokens(text)
        print(f"[{sid}] {start_t}s–{end_t}s ({dur}s) | {w_cnt} written words | {t_cnt} spoken tokens")
        print(f"     Tokens: {' '.join(tokens)}")

    print(f"\nTOTAL: {total_w} written words | {total_t} spoken tokens | {round(total_dur, 2)}s duration")
