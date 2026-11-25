"""
End-to-End Execution Runner for the Blended FS30 2.5D Paper-Cut Documentary Engine.
Coordinates:
1. Two-pass grounded StoryDirector (GPT-OSS-120B draft -> Qwen-27B editorial polish)
2. V2.5 Visual Sourcing & Cutout Engine (ESPN/Wiki/News/Social, CUDA FasterRCNN, SFace identity, rembg defringed paper cutouts, newsprint highlighter cards)
3. Calm, witty British Qwen3-TTS Ryan narration + Whisper canonical word-level subtitles + Cool Vibes (-17dB ducked, -14.0 LUFS)
4. Remotion GPU composition (`DocumentaryPaperShort` @ 1080x1920 30fps)
5. FFprobe integrity & audio/visual QA verification
"""

import os
import re
import gc
import sys
import json
import time
import shutil
import argparse
import difflib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "beta") not in sys.path:
    sys.path.insert(1, str(PROJECT_ROOT / "beta"))

from fs30.story_pipeline.story_director import generate_documentary_package, StoryPackage
from fs30.story_pipeline.v25_visual_director import V25DocumentaryVisualDirector
from fs30.story_pipeline.audio_engine import master_story_audio

REMOTION_DIR = PROJECT_ROOT / "beta" / "remotion"
SFX_DIR = PROJECT_ROOT / "assets" / "sfx"

CALM_DOC_INSTRUCT = (
    "Speak in an unhurried, articulate British documentary voice with dry intellectual wit, "
    "clean measured pauses, warm conversational authority, and no rushed shouting."
)


def _release_qwen3_tts():
    try:
        from beta.stages import qwen_tts_synthesizer
        if getattr(qwen_tts_synthesizer, "_MODEL_INSTANCE", None) is not None:
            qwen_tts_synthesizer._MODEL_INSTANCE = None
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[Runner] Unloaded Qwen3-TTS model cleanly.")
    except Exception:
        pass


def _trim_silence_and_master_clip(raw_wav: Path, out_wav: Path, pad_lead: float = 0.16, pad_tail: float = 0.24) -> Tuple[float, float, float]:
    """Trims trailing whisper tails cleanly via RMS energy envelope and pads smooth air gaps."""
    data, sr = sf.read(str(raw_wav))
    mono = np.mean(data, axis=1) if data.ndim > 1 else data
    win = max(1, int(0.04 * sr))
    n_f = len(mono) // win
    raw_dur = len(mono) / float(sr) if sr > 0 else 0.0
    if n_f > 0:
        env = np.array([np.mean(np.abs(mono[i * win : (i + 1) * win])) for i in range(n_f)])
        active = env > 0.015
        start_f = next((max(0, i - 1) for i, a in enumerate(active) if a), 0)
        end_f = n_f
        sil_run = 0
        # Only stop on sustained trailing dead silence (>= 1.24s) so natural documentary comma/period pauses stay intact
        trailing_sil_frames = int(1.24 / 0.04)
        for i in range(start_f, n_f):
            if not active[i]:
                sil_run += 1
                if (i - start_f) * 0.04 >= 1.5 and sil_run >= trailing_sil_frames:
                    end_f = i - sil_run + 3
                    break
            else:
                sil_run = 0
        # Trim dead silent frames off the very tail if speech ended early
        while end_f > start_f + 8 and not active[end_f - 1]:
            end_f -= 1
        end_f = min(n_f, end_f + 3)
        trimmed = data[start_f * win : min(len(data), end_f * win)]
    else:
        trimmed = data
    print(f"    [AudioTrim] {raw_wav.name}: {raw_dur:.2f}s -> {len(trimmed)/float(sr):.2f}s")

    tmp_trim = raw_wav.with_name(raw_wav.stem + "_trim.wav")
    sf.write(str(tmp_trim), trimmed, sr)
    speech_dur = len(trimmed) / float(sr)

    cmd = [
        "ffmpeg", "-y", "-i", str(tmp_trim),
        "-af",
        f"highpass=f=80,lowpass=f=12500,equalizer=f=2700:t=q:w=1.2:g=1.8,"
        f"loudnorm=I=-14.5:TP=-1.0:LRA=7,"
        f"adelay={int(pad_lead*1000)}|{int(pad_lead*1000)},"
        f"apad=pad_dur={pad_tail:.2f},aformat=sample_rates=48000:channel_layouts=stereo",
        "-c:a", "pcm_s16le",
        str(out_wav),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    if tmp_trim.exists():
        tmp_trim.unlink()

    out_data, out_sr = sf.read(str(out_wav))
    total_clip_dur = len(out_data) / float(out_sr)
    return total_clip_dur, pad_lead, pad_lead + speech_dur


def _align_whisper_with_canonical_text(
    wav_path: Path,
    canonical_text: str,
    clip_start_sec: float,
    speech_start_sec: float,
    speech_end_sec: float,
    fps: float = 30.0,
) -> List[Dict[str, Any]]:
    """
    Runs local Whisper (CPU) if available and aligns recognized tokens back to exact
    canonical ground-truth spelling so names like 'Suárez' / 'Chiellini' are never corrupted.
    """
    tokens = [w for w in canonical_text.strip().split() if w]
    if not tokens:
        return []

    speech_dur = max(0.4, speech_end_sec - speech_start_sec)
    matched_times: Optional[List[Tuple[float, float]]] = None

    try:
        import whisper
        if not hasattr(_align_whisper_with_canonical_text, "_model"):
            print("[Runner] Loading Whisper base (CPU) for word timestamp alignment...")
            _align_whisper_with_canonical_text._model = whisper.load_model("base", device="cpu")
        wmodel = _align_whisper_with_canonical_text._model
        res = wmodel.transcribe(str(wav_path), word_timestamps=True, language="en")
        w_words = []
        for seg in res.get("segments", []):
            for wi in seg.get("words", []):
                w_words.append((re.sub(r"[^a-z0-9]", "", (wi.get("word") or "").lower()), float(wi["start"]), float(wi["end"])))

        if w_words:
            c_clean = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in tokens]
            w_clean = [w[0] for w in w_words]
            sm = difflib.SequenceMatcher(None, c_clean, w_clean)
            aligned: List[Optional[Tuple[float, float]]] = [None] * len(tokens)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag in ("equal", "replace") and (i2 - i1) > 0 and (j2 - j1) > 0:
                    span_t0 = w_words[j1][1]
                    span_t1 = w_words[j2 - 1][2]
                    cnt = i2 - i1
                    dt = max(0.12, span_t1 - span_t0) / cnt
                    for k in range(cnt):
                        aligned[i1 + k] = (clip_start_sec + span_t0 + k * dt, clip_start_sec + span_t0 + (k + 1) * dt)

            # Interpolate any unmatched words smoothly
            for idx in range(len(tokens)):
                if aligned[idx] is None:
                    frac0 = idx / float(len(tokens))
                    frac1 = (idx + 1) / float(len(tokens))
                    aligned[idx] = (clip_start_sec + speech_start_sec + frac0 * speech_dur, clip_start_sec + speech_start_sec + frac1 * speech_dur)
            matched_times = [x for x in aligned if x is not None]
    except Exception as e:
        print(f"[Runner] Whisper alignment note ({e}), using weighted speech-envelope timing.")

    if matched_times is None:
        weights = [max(2.0, len(re.sub(r"[^a-zA-Z0-9]", "", t))) for t in tokens]
        tot_w = sum(weights)
        matched_times = []
        acc_t = clip_start_sec + speech_start_sec
        for w_val in weights:
            dt = speech_dur * (w_val / tot_w)
            matched_times.append((acc_t, acc_t + dt))
            acc_t += dt

    # Group into crisp 3-4 word documentary subtitle cues
    cues: List[Dict[str, Any]] = []
    chunk_size = 4
    for i in range(0, len(tokens), chunk_size):
        chunk_toks = tokens[i : i + chunk_size]
        chunk_tms = matched_times[i : i + chunk_size]
        cue_start_f = int(round(chunk_tms[0][0] * fps))
        cue_end_f = max(cue_start_f + 6, int(round(chunk_tms[-1][1] * fps)))
        words_list = []
        for tok, (wt0, wt1) in zip(chunk_toks, chunk_tms):
            wf0 = int(round(wt0 * fps))
            wf1 = max(wf0 + 2, int(round(wt1 * fps)))
            words_list.append({"word": tok, "start_frame": wf0, "end_frame": wf1})
        cues.append({
            "id": len(cues) + 1,
            "start_frame": cue_start_f,
            "end_frame": cue_end_f,
            "words": words_list,
        })
    return cues


def synthesize_documentary_voice_and_mix(
    pkg: StoryPackage,
    run_dir: Path,
    fps: float = 30.0,
) -> Dict[str, Any]:
    """Synthesizes Qwen3-TTS Ryan documentary voice, extracts subtitles, and mixes audio to -14 LUFS."""
    from beta.stages.qwen_tts_synthesizer import synthesize_qwen3

    voice_dir = run_dir / "audio"
    voice_dir.mkdir(parents=True, exist_ok=True)
    concat_inputs: List[Path] = []
    beat_timings: List[Dict[str, Any]] = []
    all_cues: List[Dict[str, Any]] = []

    cum_sec = 0.0
    sfx_cues: List[Dict[str, Any]] = []

    try:
        items = [(f"beat_{b.beat_number}", b.voiceover_text, b) for b in pkg.beats]
        items.append(("outro", pkg.outro_narration, None))

        for tag, text, beat_obj in items:
            raw_wav = voice_dir / f"raw_{tag}.wav"
            clean_wav = voice_dir / f"clean_{tag}.wav"
            synthesize_qwen3(
                text=text,
                output_path=raw_wav,
                speaker="Ryan",
                instruct=CALM_DOC_INSTRUCT,
                language="English",
            )
            pad_tail = 0.35 if beat_obj is not None else 0.55
            dur_sec, sp_start, sp_end = _trim_silence_and_master_clip(raw_wav, clean_wav, pad_lead=0.16, pad_tail=pad_tail)
            # Enforce exact 30fps integer frame boundaries so audio and visual cuts never drift!
            dur_frames = max(30, int(round(dur_sec * fps)))
            exact_dur_sec = dur_frames / fps

            concat_inputs.append(clean_wav)
            beat_timings.append({
                "tag": tag,
                "start_sec": cum_sec,
                "duration_sec": exact_dur_sec,
                "duration_frames": dur_frames,
                "speech_start": sp_start,
                "speech_end": sp_end,
                "text": text,
                "wav": str(clean_wav),
            })

            # Place restrained tactile SFX cues aligned with visual transitions/stamps
            if beat_obj is not None:
                if beat_obj.beat_number == 1:
                    sfx_cues.append({"path": str(SFX_DIR / "sfx_paper_slide.wav"), "time_sec": cum_sec + 0.12, "volume": 0.16})
                elif beat_obj.layout_style == "newspaper_highlighter":
                    sfx_cues.append({"path": str(SFX_DIR / "sfx_paper_crinkle.wav"), "time_sec": cum_sec + 0.25, "volume": 0.18})
                elif beat_obj.layout_style == "archival_pinboard":
                    sfx_cues.append({"path": str(SFX_DIR / "sfx_camera_shutter.wav"), "time_sec": cum_sec + 0.20, "volume": 0.18})
                elif beat_obj.layout_style == "puppet_confrontation_25d":
                    sfx_cues.append({"path": str(SFX_DIR / "sfx_paper_slide.wav"), "time_sec": cum_sec + 0.22, "volume": 0.18})
                if beat_obj.stamp_text:
                    stamp_t = cum_sec + max(1.1, exact_dur_sec * 0.56)
                    sfx_cues.append({"path": str(SFX_DIR / "sfx_stamp_thud.wav"), "time_sec": stamp_t, "volume": 0.22})

            cum_sec += exact_dur_sec
    finally:
        _release_qwen3_tts()

    # Align subtitles (using Whisper CPU now that Qwen3-TTS GPU memory is free!)
    for bt in beat_timings:
        cues = _align_whisper_with_canonical_text(
            Path(bt["wav"]),
            bt["text"],
            clip_start_sec=bt["start_sec"],
            speech_start_sec=bt["speech_start"],
            speech_end_sec=bt["speech_end"],
            fps=fps,
        )
        for c in cues:
            c["id"] = len(all_cues) + 1
            all_cues.append(c)

    # Concatenate clean voice segments via ffmpeg filter_complex concat
    vo_full = voice_dir / "full_voiceover.wav"
    cmd_cat = ["ffmpeg", "-y"]
    for p in concat_inputs:
        cmd_cat.extend(["-i", str(p)])
    streams = "".join(f"[{i}:a]" for i in range(len(concat_inputs)))
    cmd_cat.extend(["-filter_complex", f"{streams}concat=n={len(concat_inputs)}:v=0:a=1[vo]", "-map", "[vo]", str(vo_full)])
    subprocess.run(cmd_cat, check=True, capture_output=True)

    total_frames = sum(bt["duration_frames"] for bt in beat_timings)
    total_dur = total_frames / fps
    outro_frames = beat_timings[-1]["duration_frames"]
    outro_start_sec = (total_frames - outro_frames) / fps

    mastered_wav = voice_dir / "mastered_documentary_audio.wav"
    audio_stats = master_story_audio(
        voice_track_path=vo_full,
        out_mastered_audio_path=mastered_wav,
        total_duration=total_dur,
        outro_start_time=outro_start_sec,
        sfx_cues=sfx_cues,
    )

    return {
        "mastered_wav": str(mastered_wav),
        "total_duration_sec": total_dur,
        "total_frames": total_frames,
        "outro_frames": outro_frames,
        "beat_timings": beat_timings,
        "subtitles": all_cues,
        "audio_stats": audio_stats,
    }


def render_documentary_video(
    pkg: StoryPackage,
    visual_manifest: Dict[str, Any],
    audio_info: Dict[str, Any],
    run_dir: Path,
) -> Path:
    """Compiles Remotion DocumentaryPaperProps, renders GPU MP4, muxes mastered audio, and cleans temp video."""
    remotion_beats = []
    beat_assets = visual_manifest["beats"]
    timings = audio_info["beat_timings"]

    for idx, b in enumerate(pkg.beats):
        ba = beat_assets.get(b.beat_number) or beat_assets.get(str(b.beat_number), {})
        t_row = timings[idx]
        remotion_beats.append({
            "beat_number": b.beat_number,
            "layout_style": b.layout_style,
            "camera_move": b.camera_move,
            "transition_in": b.transition_in,
            "durationInFrames": t_row["duration_frames"],
            "visual_kicker": b.visual_kicker,
            "visual_headline": b.visual_headline,
            "sub_caption": b.sub_caption,
            "bg_path": ba.get("bg_path"),
            "banner_path": ba.get("banner_path"),
            "cutout": ba.get("cutout"),
            "secondary_cutout": ba.get("secondary_cutout"),
            "mounted": ba.get("mounted"),
            "editorial": ba.get("editorial"),
            "newspaper_path": ba.get("newspaper_path"),
            "highlight_rects": ba.get("highlight_rects"),
            "stamp_path": ba.get("stamp_path"),
            "timeline_items": [ti.model_dump() for ti in b.timeline_items] if b.timeline_items else None,
            "tactical_reticle": b.tactical_reticle.model_dump() if b.tactical_reticle else None,
        })

    # Outro beat appended seamlessly
    outro_t = timings[-1]
    remotion_beats.append({
        "beat_number": len(remotion_beats) + 1,
        "layout_style": "fs30_brand_outro",
        "camera_move": "static_breathe",
        "transition_in": "cross_dissolve",
        "durationInFrames": outro_t["duration_frames"],
        "visual_kicker": "FS30 ARCHIVE",
        "visual_headline": pkg.outro_headline,
    })

    props = {
        "story_id": pkg.story_id,
        "title": pkg.title,
        "era": pkg.era,
        "totalDurationInFrames": audio_info["total_frames"],
        "outroDurationInFrames": audio_info["outro_frames"],
        "outro_headline": pkg.outro_headline,
        "outro_subtitle": pkg.outro_subtitle,
        "outro_cta": pkg.outro_cta,
        "shared_assets": visual_manifest.get("shared", {}),
        "beats": remotion_beats,
        "subtitles": audio_info["subtitles"],
    }

    props_path = (run_dir / "remotion_doc_props.json").resolve()
    props_path.write_text(json.dumps(props, indent=2, ensure_ascii=False), encoding="utf-8")

    raw_mp4 = (run_dir / f"raw_{pkg.story_id}.mp4").resolve()
    final_mp4 = (run_dir / f"{pkg.story_id}_25d_master.mp4").resolve()

    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    print(f"[Render] Rendering {audio_info['total_frames']} frames via Remotion DocumentaryPaperShort...")
    render_cmd = [
        npx_cmd, "remotion", "render",
        "DocumentaryPaperShort",
        str(raw_mp4),
        f"--props={props_path}",
        "--concurrency=2",
        "--log=info",
    ]
    subprocess.run(render_cmd, cwd=str(REMOTION_DIR), check=True)

    # Mux clean mastered WAV with H.264 stream cleanly (strictly locked to video frames)
    mux_cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_mp4),
        "-i", str(audio_info["mastered_wav"]),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000",
        "-shortest",
        "-movflags", "+faststart",
        str(final_mp4),
    ]
    subprocess.run(mux_cmd, check=True, capture_output=True)

    # Clean up unmuxed raw intermediate MP4 to keep storage lean
    if raw_mp4.exists():
        raw_mp4.unlink()

    return final_mp4


def run_story_pipeline(
    story_input: Optional[str] = None,
    run_dir: Optional[Path] = None,
    log_func=print,
) -> Dict[str, Any]:
    """Full general data-driven FS30 Blended 2.5D Paper-Cut Documentary Pipeline."""
    t0 = time.time()
    topic = story_input or "Luis Suarez biting Liverpool Ajax Chiellini saga"
    pkg = generate_documentary_package(topic)

    run_id = pkg.story_id
    if run_dir is None:
        run_dir = PROJECT_ROOT / "runs" / f"doc25d_{run_id}"
    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "story_package.json").write_text(pkg.model_dump_json(indent=2), encoding="utf-8")

    log_func("===========================================================================")
    log_func(f"  FS30 BLENDED 2.5D DOCUMENTARY PIPELINE — {pkg.title}")
    log_func("===========================================================================")
    for b in pkg.beats:
        log_func(f"  Beat {b.beat_number} [{b.layout_style} | {b.transition_in}]: ({len(b.voiceover_text.split())}w) {b.voiceover_text}")

    # Stage 2: Visual Sourcing + CUDA Identity/Body Awareness + rembg Cutouts -> unloads GPU models
    director = V25DocumentaryVisualDirector(run_id=run_dir.name, run_dir=run_dir)
    visual_manifest = director.prepare_story_visual_assets(pkg)

    # Stage 3: Calm Qwen3-TTS Ryan Voiceover + Whisper Subtitles + Cool Vibes -14 LUFS Mix
    audio_info = synthesize_documentary_voice_and_mix(pkg, run_dir, fps=30.0)

    # Stage 4: Remotion DocumentaryPaperShort Render & Final Audio Mux
    final_mp4 = render_documentary_video(pkg, visual_manifest, audio_info, run_dir)

    # Verification via ffprobe
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", str(final_mp4)],
        capture_output=True, text=True, check=True,
    ).stdout)
    dur = float(probe["format"]["duration"])
    v_stream = next((s for s in probe["streams"] if "width" in s), {})

    report = {
        "status": "SUCCESS",
        "story_id": pkg.story_id,
        "title": pkg.title,
        "final_mp4": str(final_mp4),
        "width": v_stream.get("width"),
        "height": v_stream.get("height"),
        "duration_sec": round(dur, 2),
        "integrated_lufs": audio_info["audio_stats"]["integrated_lufs"],
        "true_peak_dbfs": audio_info["audio_stats"]["true_peak_dbfs"],
        "provenance_count": len(visual_manifest.get("provenance", [])),
        "elapsed_sec": round(time.time() - t0, 2),
    }
    (run_dir / "production_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    log_func(f"\nSUCCESS: {final_mp4} ({report['width']}x{report['height']}, {report['duration_sec']}s, {report['integrated_lufs']} LUFS)")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FS30 Blended 2.5D Documentary Runner")
    parser.add_argument("--topic", type=str, default="Luis Suarez biting Liverpool Ajax Chiellini saga")
    parser.add_argument("--run-dir", type=str, default=None)
    args = parser.parse_args()
    run_story_pipeline(story_input=args.topic, run_dir=Path(args.run_dir) if args.run_dir else None)
