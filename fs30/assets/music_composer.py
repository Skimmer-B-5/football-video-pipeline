"""
Quirky Orchestral Investigation Music Composer (CC0).
Instruments:
- Pizzicato strings (violin/viola staccato plucks)
- Muted cello and acoustic double bass
- Subtle woodwinds (soft harmonic swells)
- Light ticking clockwork percussion
Key: C minor / G minor | Tempo: 112 BPM | Duration: 36.0s | 48kHz Stereo
"""

import math
import struct
import wave
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MUSIC_DIR = PROJECT_ROOT / "assets" / "music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 48000
BPM = 112.0
BEAT_DUR = 60.0 / BPM # ~0.5357s
DURATION = 36.0 # 36 seconds
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION)

# Note frequencies (Hz)
NOTES = {
    "C2": 65.41, "G2": 98.00, "C3": 130.81, "Eb3": 155.56, "F3": 174.61, "G3": 196.00, "Ab3": 207.65, "Bb3": 233.08,
    "C4": 261.63, "D4": 293.66, "Eb4": 311.13, "F4": 349.23, "G4": 392.00, "Ab4": 415.30, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "Eb5": 622.25, "G5": 783.99
}

def generate_pizzicato_pluck(freq: float, duration: float, pan: float = 0.0) -> list:
    """Simulates a tight pizzicato string pluck with body resonance."""
    n_samp = int(SAMPLE_RATE * duration)
    out = []
    decay_rate = 18.0
    for i in range(n_samp):
        t = i / float(SAMPLE_RATE)
        # Fast attack, exponential decay
        env = math.exp(-decay_rate * t) * (1.0 - math.exp(-t * 800))
        # Fundamental + woody harmonics
        wave_val = (
            1.0 * math.sin(2 * math.pi * freq * t) +
            0.5 * math.sin(2 * math.pi * freq * 2.0 * t) * math.exp(-30.0 * t) +
            0.25 * math.sin(2 * math.pi * freq * 3.0 * t) * math.exp(-45.0 * t) +
            0.15 * math.sin(2 * math.pi * freq * 4.0 * t) * math.exp(-60.0 * t)
        )
        val = wave_val * env * 0.4
        left = val * (1.0 - max(0.0, pan))
        right = val * (1.0 + min(0.0, pan))
        out.append((left, right))
    return out

def generate_bass_pluck(freq: float, duration: float) -> list:
    """Muted double bass pluck with warm sub frequencies."""
    n_samp = int(SAMPLE_RATE * duration)
    out = []
    decay_rate = 7.0
    for i in range(n_samp):
        t = i / float(SAMPLE_RATE)
        env = math.exp(-decay_rate * t) * (1.0 - math.exp(-t * 400))
        wave_val = (
            1.0 * math.sin(2 * math.pi * freq * t) +
            0.4 * math.sin(2 * math.pi * freq * 2.0 * t) * math.exp(-12.0 * t) +
            0.15 * math.sin(2 * math.pi * freq * 3.0 * t) * math.exp(-25.0 * t)
        )
        val = wave_val * env * 0.55
        out.append((val, val))
    return out

def generate_clock_tick(duration: float = 0.06, is_wood: bool = False) -> list:
    """Light clockwork mechanical ticking percussion."""
    n_samp = int(SAMPLE_RATE * duration)
    out = []
    freq = 1800 if not is_wood else 900
    for i in range(n_samp):
        t = i / float(SAMPLE_RATE)
        env = math.exp(-70.0 * t)
        noise = ((i % 13) / 6.5 - 1.0) * 0.3
        sine = math.sin(2 * math.pi * freq * t)
        val = (sine * 0.7 + noise) * env * 0.22
        out.append((val, val))
    return out

def compose_investigation_theme(output_wav: Path) -> Path:
    """Composes the complete 36-second orchestral track."""
    mix_left = [0.0] * TOTAL_SAMPLES
    mix_right = [0.0] * TOTAL_SAMPLES

    def add_sound(samples_stereo, start_time_sec):
        start_idx = int(start_time_sec * SAMPLE_RATE)
        for i, (l, r) in enumerate(samples_stereo):
            idx = start_idx + i
            if idx < TOTAL_SAMPLES:
                mix_left[idx] += l
                mix_right[idx] += r

    # 1. Light Ticking Percussion on every eighth note
    eighth_dur = BEAT_DUR / 2.0
    cur_t = 0.0
    tick_count = 0
    while cur_t < DURATION:
        is_accent = (tick_count % 4 == 0)
        tick_samples = generate_clock_tick(is_wood=is_accent)
        add_sound(tick_samples, cur_t)
        cur_t += eighth_dur
        tick_count += 1

    # 2. Pizzicato Strings Ostinato (Curious investigative motif)
    # Pattern: C4 - Eb4 - G4 - Eb4 | B4 - D4 - G4 - D4 | Bb3 - D4 - F4 - D4 | Ab3 - C4 - Eb4 - C4
    motifs = [
        ["C4", "Eb4", "G4", "Eb4", "C4", "Eb4", "G4", "Eb4"],
        ["B4", "D4", "G4", "D4", "B4", "D4", "G4", "D4"],
        ["Bb3", "D4", "F4", "D4", "Bb3", "D4", "F4", "D4"],
        ["Ab3", "C4", "Eb4", "C4", "G3", "B4", "D4", "B4"]
    ]
    cur_t = 0.0
    bar_idx = 0
    while cur_t < DURATION - 1.0:
        bar_motif = motifs[bar_idx % len(motifs)]
        for note_idx, note_name in enumerate(bar_motif):
            t_note = cur_t + note_idx * eighth_dur
            if t_note >= DURATION:
                break
            freq = NOTES.get(note_name, 261.63)
            pan = -0.35 if note_idx % 2 == 0 else 0.35
            pluck = generate_pizzicato_pluck(freq, duration=0.45, pan=pan)
            add_sound(pluck, t_note)
        cur_t += BEAT_DUR * 4.0 # 4 beats per bar
        bar_idx += 1

    # 3. Muted Cello & Double Bass walking notes on beats 1 and 3
    bass_lines = [
        ["C2", "G2"],
        ["B4", "G2"], # G-based root
        ["Bb3", "F3"],
        ["Ab3", "G3"]
    ]
    cur_t = 0.0
    bar_idx = 0
    while cur_t < DURATION - 1.0:
        b_bar = bass_lines[bar_idx % len(bass_lines)]
        # Beat 1
        f1 = NOTES.get(b_bar[0], 65.41)
        add_sound(generate_bass_pluck(f1, duration=BEAT_DUR * 1.8), cur_t)
        # Beat 3
        f2 = NOTES.get(b_bar[1], 98.00)
        add_sound(generate_bass_pluck(f2, duration=BEAT_DUR * 1.8), cur_t + BEAT_DUR * 2.0)
        cur_t += BEAT_DUR * 4.0
        bar_idx += 1

    # 4. Subtle Woodwinds (Entering at bar 3 to build curiosity)
    cur_t = BEAT_DUR * 8.0 # After 2 bars
    woodwind_notes = [NOTES["G4"], NOTES["Ab4"], NOTES["G4"], NOTES["F4"], NOTES["Eb4"], NOTES["D4"]]
    w_idx = 0
    while cur_t < DURATION - 2.0:
        freq = woodwind_notes[w_idx % len(woodwind_notes)]
        n_samp = int(SAMPLE_RATE * (BEAT_DUR * 3.5))
        ww_samples = []
        for i in range(n_samp):
            t = i / float(SAMPLE_RATE)
            p = t / (BEAT_DUR * 3.5)
            # Gentle swell envelope
            env = math.sin(p * math.pi)**1.8
            sine = (math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2.0 * t)) * env * 0.16
            ww_samples.append((sine * 0.7, sine * 0.9)) # slight stereo pan
        add_sound(ww_samples, cur_t)
        cur_t += BEAT_DUR * 4.0
        w_idx += 1

    # Master Normalization: Peak at -1.5 dB, warm stereo mastering
    max_peak = max(max(abs(x) for x in mix_left), max(abs(x) for x in mix_right))
    if max_peak > 0:
        target_amp = 10.0 ** (-1.5 / 20.0) # -1.5 dB
        scale = target_amp / max_peak
    else:
        scale = 1.0

    samples_16bit = []
    for i in range(TOTAL_SAMPLES):
        # Fade out in last 1.5 seconds
        t = i / float(SAMPLE_RATE)
        fade = 1.0
        if t > DURATION - 1.5:
            fade = (DURATION - t) / 1.5

        l_val = max(-1.0, min(1.0, mix_left[i] * scale * fade))
        r_val = max(-1.0, min(1.0, mix_right[i] * scale * fade))
        samples_16bit.append(int(l_val * 32767))
        samples_16bit.append(int(r_val * 32767))

    with wave.open(str(output_wav), "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f"<{len(samples_16bit)}h", *samples_16bit))

    return output_wav

if __name__ == "__main__":
    out_theme = MUSIC_DIR / "quirky_orchestral_investigation.wav"
    compose_investigation_theme(out_theme)
    print(f"✓ Orchestral investigation theme rendered to {out_theme}")
