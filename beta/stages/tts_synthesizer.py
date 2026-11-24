"""
# PROVENANCE: Copied from stages/tts_synthesizer.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Stage 7 Component: Expressive Neural Speech Synthesizer.
Primary: Alibaba Qwen3-TTS (0.6B CustomVoice with Ryan / British cadence instruction).
Secondary Fallback: Microsoft Edge Neural Voices (en-GB-ThomasNeural / en-GB-RyanNeural).
Offline Fallback: Local Kokoro-82M ONNX / Windows SAPI.
"""

import sys
import os
import wave
import time
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker

AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
MODELS_DIR = PROJECT_ROOT.parent / "models"
JEFF_STELLING_PROMPT = MODELS_DIR / "jeff_stelling_prompt.pt"
JEFF_STELLING_VOICE_DIR = PROJECT_ROOT / "data" / "branding" / "voices" / "jeff_stelling"
MARTIN_TYLER_WEIGHTS = MODELS_DIR / "qwen3_tts_base" / "model.safetensors"
QWEN3_WEIGHTS_FILE = MODELS_DIR / "qwen3_tts_customvoice" / "model.safetensors"

def get_audio_duration_wave(file_path: Path) -> float:
    """Read WAV duration directly."""
    with wave.open(str(file_path), "r") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return round(frames / float(rate), 3)

def synthesize_with_jeff_stelling(
    text: str,
    out_wav_path: Path,
    speed_factor: float = 0.98,
    pad_sec: float = 0.15
) -> Tuple[float, float]:
    """
    Synthesize natural, authoritative television breaking transfer news commentary
    via Jeff Stelling zero-shot voice clone (Qwen3-TTS Base).
    Includes clean studio broadcast EQ and presence mastering.
    """
    from stages.jeff_stelling_synthesizer import synthesize_jeff_stelling_scene
    
    res = synthesize_jeff_stelling_scene(
        text=text,
        output_wav_path=out_wav_path,
        speed_factor=speed_factor,
        master=True
    )
    
    if pad_sec > 0:
        temp_padded = out_wav_path.with_name(f"pad_{out_wav_path.name}")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(out_wav_path),
            "-af", f"apad=pad_dur={pad_sec}",
            "-ar", "48000",
            "-ac", "2",
            "-c:a", "pcm_s16le",
            str(temp_padded)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        temp_padded.replace(out_wav_path)

    total_dur = get_audio_duration_wave(out_wav_path)
    spoken_dur = max(0.1, round(total_dur - pad_sec, 3))
    return (total_dur, spoken_dur)

def synthesize_with_martin_tyler(
    text: str,
    out_wav_path: Path,
    speed_factor: float = 1.14,
    pad_sec: float = 0.15
) -> Tuple[float, float]:
    """
    Synthesize high-retention sports commentary via cloned Martin Tyler (Qwen3-TTS Base).
    Applies broadcast vocal mastering and tail padding.
    """
    from stages.martin_tyler_synthesizer import synthesize_martin_tyler
    
    synthesize_martin_tyler(
        text=text,
        output_path=out_wav_path,
        speed_factor=speed_factor
    )
    
    if pad_sec > 0:
        temp_padded = out_wav_path.with_name(f"pad_{out_wav_path.name}")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(out_wav_path),
            "-af", f"apad=pad_dur={pad_sec}",
            "-ar", "24000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            str(temp_padded)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        temp_padded.replace(out_wav_path)

    total_dur = get_audio_duration_wave(out_wav_path)
    spoken_dur = max(0.1, round(total_dur - pad_sec, 3))
    return (total_dur, spoken_dur)

def synthesize_with_qwen3(
    text: str,
    out_wav_path: Path,
    speaker: str = "Ryan",
    instruct: str = "Speak in an urgent, dramatic sports breaking news anchor tone with punchy, high-energy British cadence.",
    pad_sec: float = 0.15
) -> Tuple[float, float]:
    """
    Synthesize high-retention sports commentary via local Qwen3-TTS.
    Applies broadcast-grade compression, EQ, and tail padding.
    """
    from stages.qwen_tts_synthesizer import synthesize_qwen3
    
    raw_wav = out_wav_path.with_name(f"raw_qwen_{out_wav_path.stem}.wav")
    synthesize_qwen3(
        text=text,
        output_path=raw_wav,
        speaker=speaker,
        instruct=instruct
    )
    
    af_chain = (
        "highpass=f=80,"
        "equalizer=f=3200:t=q:w=1.2:g=3.5,"
        "acompressor=threshold=-15dB:ratio=4.0:attack=4:release=45,"
        "loudnorm=I=-14:LRA=6:TP=-1.0,"
        f"apad=pad_dur={pad_sec}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_wav),
        "-af", af_chain,
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(out_wav_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    raw_wav.unlink(missing_ok=True)
    
    total_dur = get_audio_duration_wave(out_wav_path)
    spoken_dur = max(0.1, round(total_dur - pad_sec, 3))
    return (total_dur, spoken_dur)

async def synthesize_with_edge_tts(
    text: str,
    out_wav_path: Path,
    voice: str = "en-GB-ThomasNeural",
    rate: str = "+5%",
    pitch: str = "+0Hz",
    pad_sec: float = 0.15
) -> Tuple[float, float]:
    """
    Synthesize text using expressive neural edge-tts and apply broadcast-grade
    dynamic compression, vocal presence boost, loudness mastering, and tail padding.
    """
    import edge_tts
    temp_mp3 = out_wav_path.with_suffix(".mp3")
    
    clean_text = text.strip()
    comm = edge_tts.Communicate(clean_text, voice=voice, rate=rate, pitch=pitch)
    await comm.save(str(temp_mp3))
    
    af_chain = (
        "highpass=f=80,"
        "equalizer=f=3200:t=q:w=1.2:g=4.0,"
        "acompressor=threshold=-15dB:ratio=4.5:attack=4:release=45,"
        "loudnorm=I=-14:LRA=6:TP=-1.0,"
        f"apad=pad_dur={pad_sec}"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_mp3),
        "-af", af_chain,
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(out_wav_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    temp_mp3.unlink(missing_ok=True)
    
    total_dur = get_audio_duration_wave(out_wav_path)
    spoken_dur = max(0.1, round(total_dur - pad_sec, 3))
    return (total_dur, spoken_dur)

def synthesize_with_kokoro(
    text: str,
    out_wav_path: Path,
    voice: str = "bm_george",
    speed: float = 1.08,
    pad_sec: float = 0.15
) -> Tuple[float, float]:
    """Synthesize high-fidelity speech using local Kokoro-82M ONNX model."""
    python_bin = sys.executable
    model_path = MODELS_DIR / "kokoro-v0_19.onnx"
    voices_path = MODELS_DIR / "voices.json"
    
    if not model_path.exists() or not voices_path.exists():
        raise FileNotFoundError(f"Kokoro model assets not found in {MODELS_DIR}")
    
    raw_wav = out_wav_path.with_name(f"raw_kokoro_{out_wav_path.stem}.wav")
    
    escaped_text = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
    lang = "en-gb" if voice.startswith("bm") or voice.startswith("bf") else "en-us"
    
    inline_script = (
        "import sys\n"
        "from kokoro_onnx import Kokoro\n"
        "import soundfile as sf\n"
        f"k = Kokoro(r'{model_path}', r'{voices_path}')\n"
        f"s, sr = k.create('{escaped_text}', voice='{voice}', speed={speed}, lang='{lang}')\n"
        f"sf.write(r'{raw_wav}', s, sr)\n"
    )
    
    res = subprocess.run([python_bin, "-c", inline_script], capture_output=True, text=True)
    if res.returncode != 0 or not raw_wav.exists():
        raise RuntimeError(f"Kokoro synthesis failed: {res.stderr}")

    af_chain = (
        "highpass=f=80,"
        "equalizer=f=3200:t=q:w=1.2:g=3.0,"
        "acompressor=threshold=-15dB:ratio=4.0:attack=4:release=45,"
        "loudnorm=I=-14:LRA=6:TP=-1.0,"
        f"apad=pad_dur={pad_sec}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_wav),
        "-af", af_chain,
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(out_wav_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    raw_wav.unlink(missing_ok=True)
    
    total_dur = get_audio_duration_wave(out_wav_path)
    spoken_dur = max(0.1, round(total_dur - pad_sec, 3))
    return (total_dur, spoken_dur)

def synthesize_scenes_sapi(scenes: List[Dict[str, Any]], pad_sec: float = 0.15) -> List[Dict[str, Any]]:
    """
    Fallback neural synthesizer using EdgeTTS RyanNeural (SAPI Microsoft David is permanently eliminated).
    """
    print("[TTS] Fallback synthesizer invoked: routing to EdgeTTS en-GB-RyanNeural (Zero SAPI David)")
    return synthesize_scenes_expressive(scenes, voice_name="en-GB-RyanNeural", rate="+5%", pitch="+0Hz", pad_sec=pad_sec)

def synthesize_scenes_expressive(
    scenes: List[Dict[str, Any]],
    voice_name: str = "en-GB-ThomasNeural",
    rate: str = "+5%",
    pitch: str = "+0Hz",
    pad_sec: float = 0.15,
    preferred_engine: str = "auto"
) -> List[Dict[str, Any]]:
    """
    Synthesize audio for each scene line.
    If Qwen3-TTS weights are present on disk, uses Qwen3-TTS as primary.
    Otherwise gracefully uses expressive edge-tts or Kokoro.
    """
    with ResourceTracker("TTS_Synthesizer"):
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        results = []

        use_presenter = False
        use_jeff_stelling = False
        use_martin_tyler = False
        use_qwen = False

        # Only route English text to English-specific clone engines
        is_non_english = any(voice_name.lower().startswith(prefix) for prefix in ["pt-", "es-", "fr-", "de-", "it-"])

        if not is_non_english:
            if preferred_engine in ("presenter", "classic_football_presenter", "des_lynam"):
                use_presenter = True
            elif preferred_engine in ("jeff_stelling", "auto") and (JEFF_STELLING_PROMPT.exists() or JEFF_STELLING_VOICE_DIR.exists()):
                use_jeff_stelling = True
            elif preferred_engine == "martin_tyler" and MARTIN_TYLER_WEIGHTS.exists():
                use_martin_tyler = True
            elif preferred_engine == "qwen3" or (preferred_engine == "auto" and QWEN3_WEIGHTS_FILE.exists()):
                use_qwen = True

        for s in scenes:
            scene_id = s.get("scene_id", 1)
            text = (s.get("narration") or s.get("text", "")).strip()
            out_path = AUDIO_DIR / f"scene_{scene_id}.wav"

            start_t = time.time()
            success = False

            # 0. Try Signature Classic Football Presenter (Des Lynam Style Reference)
            if use_presenter:
                try:
                    from stages.presenter_voice import ClassicFootballPresenter
                    presenter = ClassicFootballPresenter()
                    mode = s.get("delivery_mode", "NEWS")
                    print(f"[TTS-Presenter] Synthesizing Scene {scene_id} (Classic Football Presenter / {mode}): \"{text[:45]}...\"")
                    res_p = presenter.synthesize_scene(text, out_path, mode=mode, pad_sec=pad_sec)
                    total_dur = res_p["total_duration_sec"]
                    spoken_dur = res_p["spoken_duration_sec"]
                    success = True
                except Exception as pe:
                    print(f"[TTS-Presenter] Scene {scene_id} note: {pe}. Falling back to default engines.")

            # 1. Try Jeff Stelling Cloned Voice (Qwen3 Base with pristine studio audio)
            if use_jeff_stelling:
                try:
                    print(f"[TTS-JeffStelling] Synthesizing Scene {scene_id} (Jeff Stelling Studio 1.08x): \"{text[:45]}...\"")
                    total_dur, spoken_dur = synthesize_with_jeff_stelling(text, out_path, speed_factor=1.08, pad_sec=pad_sec)
                    success = True
                except Exception as jse:
                    print(f"[TTS-JeffStelling] Scene {scene_id} note: {jse}. Falling back to Martin Tyler/Qwen3.")

            # 2. Try Martin Tyler Cloned Voice (Qwen3 Base)
            if not success and use_martin_tyler:
                try:
                    print(f"[TTS-MartinTyler] Synthesizing Scene {scene_id} (Martin Tyler Commentary 1.14x): \"{text[:45]}...\"")
                    total_dur, spoken_dur = synthesize_with_martin_tyler(text, out_path, speed_factor=1.14, pad_sec=pad_sec)
                    success = True
                except Exception as mte:
                    print(f"[TTS-MartinTyler] Scene {scene_id} note: {mte}. Falling back to Qwen3/Edge-TTS.")

            # 3. Try Qwen3-TTS CustomVoice if enabled
            if not success and use_qwen:
                try:
                    print(f"[TTS-Qwen3] Synthesizing Scene {scene_id} (Speaker: Ryan, British cadence): \"{text[:45]}...\"")
                    total_dur, spoken_dur = synthesize_with_qwen3(text, out_path, speaker="Ryan", pad_sec=pad_sec)
                    success = True
                except Exception as qe:
                    print(f"[TTS-Qwen3] Scene {scene_id} note: {qe}. Falling back to edge-tts.")

            # 4. Try Edge-TTS
            if not success:
                print(f"[TTS-Edge] Synthesizing Scene {scene_id} ({voice_name}): \"{text[:45]}...\"")
                for tts_retry in range(1, 4):
                    try:
                        total_dur, spoken_dur = asyncio.run(synthesize_with_edge_tts(text, out_path, voice=voice_name, rate=rate, pitch=pitch, pad_sec=pad_sec))
                        success = True
                        break
                    except Exception as e:
                        print(f"[TTS-Edge] attempt {tts_retry}/3 error: {e}")
                        time.sleep(1.0)

            # 5. Fallback to Kokoro
            if not success:
                print(f"[TTS] Falling back to Kokoro Neural HD for Scene {scene_id}...")
                try:
                    total_dur, spoken_dur = synthesize_with_kokoro(text, out_path, voice="bm_george", pad_sec=pad_sec)
                    success = True
                except Exception as ke:
                    print(f"[TTS] Kokoro failed: {ke}. Falling back to SAPI.")
                    return synthesize_scenes_sapi(scenes, pad_sec)

            dur_time = round(time.time() - start_t, 2)
            print(f"[TTS] Scene {scene_id} rendered in {dur_time}s | Spoken: {spoken_dur}s | Total slide with pad: {total_dur}s")

            if use_presenter and success:
                used_engine = "ClassicFootballPresenter"
                used_voice = f"classic_football_presenter ({s.get('delivery_mode', 'NEWS')})"
            elif use_jeff_stelling and success:
                used_engine = "JeffStelling-Qwen3"
                used_voice = "Jeff Stelling (Sky Sports Studio 1.08x)"
            elif use_martin_tyler and success:
                used_engine = "MartinTyler-Qwen3"
                used_voice = "Martin Tyler (Cloned 1.14x)"
            elif success:
                used_engine = "EdgeTTS"
                used_voice = voice_name
            else:
                used_engine = "Kokoro"
                used_voice = "bm_george"

            results.append({
                "scene_id": scene_id,
                "text": text,
                "type": s.get("type", "body"),
                "audio_path": str(out_path),
                "audio_duration_sec": spoken_dur,
                "slide_duration_sec": total_dur,
                "engine": used_engine,
                "voice": used_voice
            })

        return results

if __name__ == "__main__":
    test_scenes = [
        {"scene_id": 1, "text": "Is this the deal of the summer?! Manchester United have made their move.", "type": "hook"},
        {"scene_id": 2, "text": "According to Sky Sports, terms are agreed on a hundred million pound deal.", "type": "body"},
        {"scene_id": 3, "text": "Should they pull the trigger, or is this a disaster? Tell us in the comments: yes or no!", "type": "outlook"}
    ]
    res = synthesize_scenes_expressive(test_scenes)
    print(f"Synthesized {len(res)} scenes successfully.")
