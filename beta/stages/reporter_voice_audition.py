"""
beta/stages/reporter_voice_audition.py - Original English Reporter Voice Audition & Synthesis Engine.

Fulfills Beta V7.1 Mandate:
"Create an original English football-news reporter voice with these broad attributes:
- Mature male voice.
- British English pronunciation.
- Mid-to-low register.
- Warm, slightly textured timbre.
- Clear consonants.
- Confident sports-news delivery.
- Natural pitch movement.
- Strong but restrained emphasis.
- Conversational rhythm.
- Professional broadcast authority.
- No exaggerated commentator shouting.
- No monotone documentary narration.
- No synthetic customer-service cadence.

Use the official Qwen3-TTS workflow.
Create three genuinely distinct English voice candidates.
Use the same approximately 20-25-second football-news passage for each candidate.
Send the actual audio files to Telegram for listening."
"""

import os
import sys
import time
import subprocess
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.story_workspace_manager import StoryWorkspace

AUDITION_PASSAGE = (
    "A sixty-million-euro transfer proposal is developing in Italy, but Madrid want protection. "
    "Milan are targeting Endrick, exploring an ambitious move for the twenty-year-old forward. "
    "Reports suggest buy-back clauses between eighty and eighty-five million euros, though nothing is agreed. "
    "A fresh right-thigh injury complicates his campaign, yet Italian interest remains active. "
    "Should Madrid consider sanctioning a departure, or retain him for the long term?"
)

VOICE_CANDIDATES = [
    {
        "id": "VOICE_A",
        "name": "Correspondent Newsdesk",
        "speaker": "Ryan",
        "profile": "Mature British male sports correspondent, measured pacing, calm authoritative broadcast baritone, clear consonants, restrained emphasis.",
        "instruct": "A mature British male sports correspondent delivering breaking football transfer news from the studio desk. Measured, authoritative, calm baritone with natural conversational pauses, clear British pronunciation, and restrained emphasis.",
        "wpm": 135.0,
        "pitch_shift": 0.98,
        "presence_boost_db": 2.2
    },
    {
        "id": "VOICE_B",
        "name": "Transfer Insider Specialist",
        "speaker": "Aiden",
        "profile": "Experienced British transfer specialist, crisp articulation, dynamic pitch contours, subtle investigative intrigue, warm textured tenor.",
        "instruct": "An experienced British football transfer insider speaking directly to the audience. Crisp articulation, engaging cadence with slight intrigue, confident emphasis on figures and club names, warm textured tenor.",
        "wpm": 142.0,
        "pitch_shift": 1.02,
        "presence_boost_db": 2.8
    },
    {
        "id": "VOICE_C",
        "name": "Senior Sports Anchor",
        "speaker": "Eric",
        "profile": "Senior British sports desk anchor, rich seasoned baritone, deliberate broadcast rhythm, natural pauses, professional broadcast gravitas.",
        "instruct": "A senior British sports anchor with a warm, seasoned, deep baritone voice. Professional broadcast authority, deliberate pacing with steady natural pauses, dignified and engaging delivery without shouting.",
        "wpm": 130.0,
        "pitch_shift": 0.95,
        "presence_boost_db": 2.0
    }
]


class ReporterVoiceAuditionEngine:
    """Manages generation, mastering, and auditioning of reporter voice candidates."""

    def __init__(self, workspace: StoryWorkspace):
        self.workspace = workspace
        self.voice_dir = workspace.voice_dir

    def _get_qwen_custom_model(self):
        from stages.qwen_tts_synthesizer import get_qwen3_tts_model
        return get_qwen3_tts_model()

    def generate_audition_wav(self, candidate: Dict[str, Any]) -> Tuple[Path, float]:
        """Synthesizes raw audio for a voice candidate using Qwen3-TTS on CUDA."""
        cid = candidate["id"]
        raw_out = self.voice_dir / f"{cid}_raw.wav"
        mastered_out = self.voice_dir / f"{cid}_mastered.wav"

        print(f"[VoiceAudition] Synthesizing Candidate {cid} ({candidate['name']})...")
        t0 = time.time()

        model = self._get_qwen_custom_model()
        speaker = candidate.get("speaker", "Ryan")
        instruct = candidate.get("instruct", "")

        wavs, sr = model.generate_custom_voice(
            text=AUDITION_PASSAGE,
            language="English",
            speaker=speaker,
            instruct=instruct,
        )

        import soundfile as sf
        audio_data = wavs[0]
        sf.write(str(raw_out), audio_data, sr)

        dur_sec = len(audio_data) / float(sr)
        print(f"[VoiceAudition] Raw audio generated in {time.time()-t0:.2f}s ({dur_sec:.2f}s duration)")

        # Apply broadcast mastering chain
        self.apply_broadcast_mastering(
            raw_path=raw_out,
            out_path=mastered_out,
            presence_boost_db=candidate.get("presence_boost_db", 2.5)
        )

        return mastered_out, dur_sec

    @staticmethod
    def apply_broadcast_mastering(raw_path: Path, out_path: Path, presence_boost_db: float = 2.5):
        """
        Broadcast vocal mastering chain:
        1. High-pass filter at 90Hz (cuts sub-rumble).
        2. Low-pass filter at 11kHz (tames harshness).
        3. Presence EQ boost at 3.2kHz (+2.5dB) for British articulation.
        4. Broadcast compand leveling.
        5. ITU-R BS.1770-4 loudnorm (-14 LUFS, -1.0 dBTP ceiling).
        """
        af_chain = (
            f"highpass=f=90,"
            f"lowpass=f=11000,"
            f"equalizer=f=3200:t=q:w=1.2:g={presence_boost_db},"
            f"compand=attacks=0.02:decays=0.15:points=-60/-60|-24/-18|-12/-8|0/-1:gain=0,"
            f"loudnorm=I=-14:TP=-1.0:LRA=7"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_path),
            "-af", af_chain,
            "-ar", "48000",
            "-ac", "2",
            str(out_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[VoiceAudition] Mastering fallback note: {res.stderr[:200]}")
            # If ffmpeg filter failed, copy raw
            import shutil
            shutil.copy2(str(raw_path), str(out_path))

    def generate_all_auditions(self) -> List[Dict[str, Any]]:
        """Generates all 3 distinct voice candidates using identical script."""
        results = []
        for cand in VOICE_CANDIDATES:
            out_path, dur = self.generate_audition_wav(cand)
            results.append({
                "id": cand["id"],
                "name": cand["name"],
                "profile": cand["profile"],
                "file_path": str(out_path),
                "duration_sec": round(dur, 2),
                "script_passage": AUDITION_PASSAGE
            })
        return results
