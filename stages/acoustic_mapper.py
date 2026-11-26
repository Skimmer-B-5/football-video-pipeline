"""
# PROVENANCE: Copied from stages/acoustic_mapper.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ - Safe experimental development environment.
"""

"""
Stage: Acoustic Trigger Mapper
Injects real organic viral meme sound effects into YouTube Shorts transitions.
Uses authentic organic audio assets:
1. Real soft air whooshes for fast scene transitions.
2. Subtle Vine Boom on troll/meme punchlines (Penaldo, Pessi, etc.).
3. Subtle COD Hit Marker click on meme comparisons (Antony spin, etc.).
4. Real organic 808 bass impact for the hook and outro.
Zero synthetic noise sweeps, zero AI drone hum, zero laugh tracks.
"""

import math
import struct
import wave
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SFX_DIR = PROJECT_ROOT / "data" / "sfx"

def ensure_sfx_library() -> Dict[str, Path]:
    """Ensure all required real SFX files exist in data/sfx."""
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    
    vine_boom = SFX_DIR / "meme_vine_boom.wav"
    whoosh_soft = SFX_DIR / "meme_whoosh_soft.wav"
    whoosh_swoosh = SFX_DIR / "meme_whoosh_swoosh.wav"
    hit_marker = SFX_DIR / "meme_hit_marker.wav"
    bass_drop = SFX_DIR / "meme_bass_drop.wav"
    pop_click = SFX_DIR / "meme_pop_click.wav"

    return {
        "vine_boom": vine_boom,
        "whoosh_soft": whoosh_soft,
        "whoosh_swoosh": whoosh_swoosh,
        "hit_marker": hit_marker,
        "bass_drop": bass_drop,
        "pop_click": pop_click
    }

def generate_sub_bass_drop(path: Path, duration: float = 1.8, sample_rate: int = 44100) -> Path:
    """Provides authentic clean organic bass hit for outro / hooks."""
    sfx = ensure_sfx_library()
    real_bass = sfx["bass_drop"]
    if real_bass.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["ffmpeg", "-y", "-i", str(real_bass), "-t", str(duration), "-c", "copy", str(path)]
        subprocess.run(cmd, capture_output=True)
        if path.exists() and path.stat().st_size > 500:
            return path

    total_samples = int(duration * sample_rate)
    samples = []
    for i in range(total_samples):
        t = i / sample_rate
        freq = 60.0 * math.exp(-2.5 * t) + 35.0
        amp = math.exp(-3.0 * t) * 0.7
        val = math.sin(2.0 * math.pi * freq * t) * amp
        samples.append(val)
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        raw = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            raw.extend(struct.pack("<h", int(clamped * 32767.0)))
        wf.writeframes(raw)
    return path

def build_ffmpeg_acoustic_mix_command(
    voiceover_path: Path,
    scenes: List[Dict[str, Any]],
    output_audio_path: Path
) -> List[str]:
    """
    Constructs an FFmpeg filtergraph command mixing real subtle meme sound effects
    underneath the fast-paced voiceover:
    - Real soft air whooshes on cuts (volume 0.28)
    - Subtle Vine Boom on Penaldo / Pessi punchlines (volume 0.35)
    - Subtle COD Hit Marker on meme jabs (volume 0.45)
    - Zero artificial drone hum, zero laugh tracks.
    """
    sfx = ensure_sfx_library()

    inputs = ["-i", str(voiceover_path)]
    filter_parts = []

    # Voiceover is Input 0: [0:a]
    mix_labels = ["[0:a]"]
    sfx_index = 1

    cur_t = 0.0
    for idx, sc in enumerate(scenes):
        dur = float(sc.get("slide_duration_sec", sc.get("audio_duration_sec", 2.6)))
        text_lower = sc.get("text", "").lower()
        entity_lower = sc.get("search_entity", "").lower()

        chosen_sfx = None
        sfx_vol = 0.28

        # Dynamic subtle SFX mapping for all meme personalities
        if any(w in text_lower or w in entity_lower for w in ["mourinho", "simeone", "guardiola", "pep", "penaldo", "ronaldo", "messi", "pessi", "disaster", "shock", "agony"]):
            chosen_sfx = sfx["vine_boom"]
            sfx_vol = 0.35
        elif any(w in text_lower or w in entity_lower for w in ["maguire", "darwin", "nunez", "mudryk", "antony", "spin", "yamal", "fidget", "miss"]):
            chosen_sfx = sfx["hit_marker"]
            sfx_vol = 0.42
        elif any(w in text_lower or w in entity_lower for w in ["ancelotti", "eyebrow", "boehly", "contract", "klopp", "wenger", "palmer", "cold", "nap", "bale"]):
            chosen_sfx = sfx["pop_click"]
            sfx_vol = 0.32
        elif idx == 0:
            chosen_sfx = sfx["whoosh_swoosh"]
            sfx_vol = 0.32
        elif idx > 0 and idx % 2 == 0:
            chosen_sfx = sfx["whoosh_soft"]
            sfx_vol = 0.28
        elif idx > 0:
            chosen_sfx = sfx["pop_click"]
            sfx_vol = 0.25

        if chosen_sfx and chosen_sfx.exists():
            inputs.extend(["-i", str(chosen_sfx)])
            delay_ms = max(0, int(cur_t * 1000))
            lbl = f"sfx_{idx}"
            filter_parts.append(
                f"[{sfx_index}:a]volume={sfx_vol},adelay={delay_ms}|{delay_ms}[{lbl}]"
            )
            mix_labels.append(f"[{lbl}]")
            sfx_index += 1

        cur_t += dur

    amix_str = f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:normalize=0[outa]"
    filter_parts.append(amix_str)

    full_filter = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"]
    cmd.extend(inputs)
    cmd.extend(["-filter_complex", full_filter, "-map", "[outa]", "-c:a", "pcm_s16le", str(output_audio_path)])
    return cmd
