"""
presenter_voice.py - Signature Voice Identity Engine for 30 Football Plus.

Profile: `classic_football_presenter`
Stylistic Reference: Des Lynam (classic BBC Sport-era presentation).
Attributes:
- Mature British male presenter.
- Warm, rounded mid-low register.
- Measured, articulate, conversational authority with controlled excitement.

Supported Delivery Modes:
1. NEWS: Measured, clear, informative.
2. BREAKING: Slightly faster, firmer emphasis, controlled urgency.
3. EDITORIAL: Conversational, warm, dry emphasis, unhurried cadence.
"""

import os
import sys
import re
import wave
import time
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("presenter_voice")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# British Football Pronunciation & Currency Normalisation Dictionary
PRONUNCIATION_MAP = {
    r"\b€(\d+(?:\.\d+)?)\s*[mM]\b": r"\1 million euros",
    r"\b£(\d+(?:\.\d+)?)\s*[mM]\b": r"\1 million pounds",
    r"\$(\d+(?:\.\d+)?)\s*[mM]\b": r"\1 million dollars",
    r"\b€(\d+(?:\.\d+)?)\s*[bB]\b": r"\1 billion euros",
    r"\b£(\d+(?:\.\d+)?)\s*[bB]\b": r"\1 billion pounds",
    r"\b€(\d+)\b": r"\1 euros",
    r"\b£(\d+)\b": r"\1 pounds",
    r"\bxG\b": "expected goals",
    r"\bvs\b": "versus",
    r"\bv\.\b": "versus",
    r"\bUCL\b": "Champions League",
    r"\bUEL\b": "Europa League",
    r"\bSzoboszlai\b": "So-boss-lye",
    r"\bGyökeres\b": "Jeu-ker-esh",
    r"\bGyokeres\b": "Jeu-ker-esh",
    r"\bAncelotti\b": "An-che-lot-tee",
    r"\bAmorim\b": "Ah-mo-reem",
    r"\bSan Siro\b": "San See-ro",
    r"\bBernabéu\b": "Bair-nah-bay-oo",
    r"\bBernabeu\b": "Bair-nah-bay-oo",
    r"\bEndrick\b": "End-rick",
    r"\bPostecoglou\b": "Poss-te-cog-loo",
    r"\bDe Ligt\b": "De Ligt",
    r"\bCalafiori\b": "Cah-lah-fee-or-ee",
}

def normalise_football_narration(text: str) -> str:
    """Pre-processes sports text for accurate British presenter pronunciation and cadence."""
    cleaned = text.strip()
    for pattern, replacement in PRONUNCIATION_MAP.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    # Ensure natural commas before clauses for breath pauses
    cleaned = re.sub(r"\s*—\s*", ", ", cleaned)
    cleaned = re.sub(r"\s*\.\.\.\s*", ", ", cleaned)
    return cleaned

def get_audio_duration_wave(file_path: Path) -> float:
    """Obtains exact duration of PCM WAV file in seconds."""
    if not file_path.exists():
        return 0.0
    with wave.open(str(file_path), "r") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return round(frames / float(rate), 3)

def apply_broadcast_mastering(
    input_path: Path,
    output_path: Path,
    mode: str = "NEWS",
    pad_sec: float = 0.15
) -> None:
    """
    Applies professional television broadcast audio mastering:
    - 80Hz high-pass filter (proximity rumble cutoff)
    - Mid-low warmth EQ (250Hz gentle +1.2dB warmth)
    - Presenter clarity & consonant EQ (3.0kHz +3.2dB boost)
    - Studio dynamic compressor (transparent broadcast leveling)
    - ITU-R BS.1770-4 EBU R128 loudness normalisation (-14 LUFS integrated, -1.0 dBTP max)
    - Clean tail padding
    """
    if mode == "BREAKING":
        eq_presence = "equalizer=f=3200:t=q:w=1.2:g=3.8"
        comp_thresh = "-15dB"
        comp_ratio = "4.0"
    elif mode == "EDITORIAL":
        eq_presence = "equalizer=f=2800:t=q:w=1.1:g=2.6"
        comp_thresh = "-16dB"
        comp_ratio = "3.2"
    else:  # NEWS
        eq_presence = "equalizer=f=3000:t=q:w=1.2:g=3.2"
        comp_thresh = "-16dB"
        comp_ratio = "3.5"

    af_chain = (
        "highpass=f=80,"
        "equalizer=f=250:t=q:w=1.0:g=1.4,"
        f"{eq_presence},"
        f"acompressor=threshold={comp_thresh}:ratio={comp_ratio}:attack=5:release=50,"
        "loudnorm=I=-14:LRA=6:TP=-1.0,"
        f"apad=pad_dur={pad_sec}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-af", af_chain,
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

class ClassicFootballPresenter:
    """
    Signature Presenter Engine: Des Lynam Stylistic Reference.
    Profile: `classic_football_presenter`
    """

    def __init__(self):
        self.profile_name = "classic_football_presenter"
        self.reference_style = "Des Lynam (Classic BBC Sport delivery)"

    def _get_delivery_settings(self, mode: str) -> Dict[str, Any]:
        """Configures pitch, speed, and pacing according to the requested editorial mode."""
        mode_upper = mode.upper()
        if mode_upper == "BREAKING":
            return {
                "rate": "+3%",
                "pitch": "+0Hz",
                "speed_factor": 1.03,
                "qwen_instruct": "Present this breaking football transfer news with sharp British authority, crisp consonants, and urgent yet controlled excitement."
            }
        elif mode_upper == "EDITORIAL":
            return {
                "rate": "-3%",
                "pitch": "-2Hz",
                "speed_factor": 0.96,
                "qwen_instruct": "Deliver this football analysis with dry British warmth, wry conversational authority, and unhurried natural cadence."
            }
        else:  # NEWS
            return {
                "rate": "-1%",
                "pitch": "-1Hz",
                "speed_factor": 0.98,
                "qwen_instruct": "Present this football story with measured British television authority, warm rounded mid-register, and articulate pacing."
            }

    async def _synthesize_edge_neural(
        self,
        text: str,
        out_wav: Path,
        mode: str,
        pad_sec: float = 0.15
    ) -> Tuple[float, float]:
        """Synthesizes using Microsoft Edge British Neural Voice (en-GB-ThomasNeural)."""
        import edge_tts
        settings = self._get_delivery_settings(mode)
        temp_mp3 = out_wav.with_suffix(".temp.mp3")

        clean_text = normalise_football_narration(text)
        comm = edge_tts.Communicate(
            clean_text,
            voice="en-GB-ThomasNeural",
            rate=settings["rate"],
            pitch=settings["pitch"]
        )
        await comm.save(str(temp_mp3))

        apply_broadcast_mastering(temp_mp3, out_wav, mode=mode, pad_sec=pad_sec)
        temp_mp3.unlink(missing_ok=True)

        total_dur = get_audio_duration_wave(out_wav)
        spoken_dur = max(0.1, round(total_dur - pad_sec, 3))
        return (total_dur, spoken_dur)

    def _synthesize_qwen3_conditioned(
        self,
        text: str,
        out_wav: Path,
        mode: str,
        pad_sec: float = 0.15
    ) -> Tuple[float, float]:
        """Synthesizes via Qwen3-TTS using stylistic instruction conditioning."""
        from stages.qwen_tts_synthesizer import synthesize_qwen3
        settings = self._get_delivery_settings(mode)
        raw_wav = out_wav.with_suffix(".qwen_raw.wav")

        clean_text = normalise_football_narration(text)
        synthesize_qwen3(
            text=clean_text,
            output_path=raw_wav,
            speaker="Ryan",
            instruct=settings["qwen_instruct"]
        )

        apply_broadcast_mastering(raw_wav, out_wav, mode=mode, pad_sec=pad_sec)
        raw_wav.unlink(missing_ok=True)

        total_dur = get_audio_duration_wave(out_wav)
        spoken_dur = max(0.1, round(total_dur - pad_sec, 3))
        return (total_dur, spoken_dur)

    def synthesize_scene(
        self,
        text: str,
        out_wav_path: Path,
        mode: str = "NEWS",
        pad_sec: float = 0.15
    ) -> Dict[str, Any]:
        """
        Synthesizes a scene narration using the permanent `classic_football_presenter` profile.
        Maintains voice continuity across the video with automatic neural fallback.
        """
        out_wav_path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        engine_used = "EdgeNeural-Thomas (Des Lynam Conditioning)"
        
        # 1. Primary: Edge-TTS British Neural with Des Lynam pitch/warmth conditioning
        try:
            total_dur, spoken_dur = asyncio.run(
                self._synthesize_edge_neural(text, out_wav_path, mode=mode, pad_sec=pad_sec)
            )
        except Exception as e:
            logger.warning(f"Edge-TTS neural error ({e}); attempting Qwen3-TTS conditioning...")
            try:
                total_dur, spoken_dur = self._synthesize_qwen3_conditioned(
                    text, out_wav_path, mode=mode, pad_sec=pad_sec
                )
                engine_used = "Qwen3-TTS (British Presenter Conditioning)"
            except Exception as qe:
                logger.error(f"Qwen3-TTS also failed ({qe}); falling back to local synthesizer.")
                from stages.tts_synthesizer import synthesize_with_kokoro
                total_dur, spoken_dur = synthesize_with_kokoro(
                    text, out_wav_path, voice="bm_george", pad_sec=pad_sec
                )
                engine_used = "Kokoro-82M (bm_george)"

        elapsed = round(time.time() - t0, 2)
        logger.info(
            f"Synthesized scene in {elapsed}s [{self.profile_name} / {mode}] "
            f"via {engine_used} -> {spoken_dur}s spoken ({total_dur}s total)"
        )

        return {
            "profile": self.profile_name,
            "mode": mode,
            "engine": engine_used,
            "audio_path": str(out_wav_path.resolve()),
            "spoken_duration_sec": spoken_dur,
            "total_duration_sec": total_dur,
            "latency_sec": elapsed,
        }

    def synthesize_story_scenes(
        self,
        scenes: List[Dict[str, Any]],
        default_mode: str = "NEWS"
    ) -> List[Dict[str, Any]]:
        """Synthesizes all scenes in a story maintaining signature voice consistency."""
        results = []
        for s in scenes:
            scene_id = s.get("scene_id", "s01")
            text = (s.get("narration") or s.get("text") or "").strip()
            mode = s.get("delivery_mode", default_mode)
            out_file = AUDIO_DIR / f"scene_{scene_id}.wav"

            res = self.synthesize_scene(text, out_file, mode=mode)
            res["scene_id"] = scene_id
            res["text"] = text
            results.append(res)
        return results
