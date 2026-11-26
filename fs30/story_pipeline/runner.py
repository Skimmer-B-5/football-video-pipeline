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

from fs30.story_pipeline.story_director import generate_documentary_package, StoryPackage
from fs30.story_pipeline.v25_visual_director import V25DocumentaryVisualDirector
from fs30.story_pipeline.audio_engine import master_story_audio

REMOTION_DIR = PROJECT_ROOT / "remotion"
SFX_DIR = PROJECT_ROOT / "assets" / "sfx"

MODELS_DIR = PROJECT_ROOT / "models"
CUMBERBATCH_PROMPT_PATH = MODELS_DIR / "cumberbatch_prompt.pt"
CUMBERBATCH_REF_WAV = MODELS_DIR / "cumberbatch_clean_ref.wav"
CUMBERBATCH_REF_TXT = MODELS_DIR / "cumberbatch_clean_ref.txt"


def _apply_pronunciation_hints(text: str, hints: Dict[str, str]) -> str:
    """Applies phonetic spellings for foreign surnames before TTS only (preserving UI subtitles)."""
    spoken = text or ""
    for src, phon in (hints or {}).items():
        if src and phon and src in spoken:
            spoken = re.sub(rf"\b{re.escape(src)}\b", phon, spoken)
    return spoken


def _release_qwen3_tts():
    try:
        from stages import qwen_tts_synthesizer
        if getattr(qwen_tts_synthesizer, "_MODEL_INSTANCE", None) is not None:
            qwen_tts_synthesizer._MODEL_INSTANCE = None
    except Exception:
        pass
    try:
        if hasattr(_get_cumberbatch_clone, "_model"):
            delattr(_get_cumberbatch_clone, "_model")
        if hasattr(_get_cumberbatch_clone, "_prompt"):
            delattr(_get_cumberbatch_clone, "_prompt")
    except Exception:
        pass
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[Runner] Unloaded Qwen3-TTS model cleanly.")
    except Exception:
        pass


def _get_cumberbatch_clone():
    """Singleton loader for Qwen3-TTS Base + Benedict Cumberbatch ICL prompt."""
    if hasattr(_get_cumberbatch_clone, "_model") and hasattr(_get_cumberbatch_clone, "_prompt"):
        return _get_cumberbatch_clone._model, _get_cumberbatch_clone._prompt
    import torch
    from qwen_tts import Qwen3TTSModel

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    model_dir = MODELS_DIR / "qwen3_tts_base"
    print(f"[Runner] Loading Cumberbatch BBC Voice Clone from {model_dir.name}...")
    model = Qwen3TTSModel.from_pretrained(str(model_dir), device_map=device, dtype=dtype)
    if CUMBERBATCH_PROMPT_PATH.exists():
        prompt = torch.load(str(CUMBERBATCH_PROMPT_PATH), weights_only=False)
    else:
        ref_txt = CUMBERBATCH_REF_TXT.read_text(encoding="utf-8").strip() if CUMBERBATCH_REF_TXT.exists() else ""
        prompt = model.create_voice_clone_prompt(
            ref_audio=str(CUMBERBATCH_REF_WAV),
            ref_text=ref_txt,
            x_vector_only_mode=False,
        )
        torch.save(prompt, str(CUMBERBATCH_PROMPT_PATH))
    _get_cumberbatch_clone._model = model
    _get_cumberbatch_clone._prompt = prompt
    return model, prompt


def _trim_silence_and_master_clip(
    raw_wav: Path,
    out_wav: Path,
    pad_lead: float = 0.05,
    pad_tail: float = 0.14,
    atempo: float = 1.07,
) -> Tuple[float, float, float]:
    """Trims dead air outside-in (preserving natural mid-sentence dry pauses), sharpens British wit cadence & EQ."""
    data, sr = sf.read(str(raw_wav))
    mono = np.mean(data, axis=1) if data.ndim > 1 else data
    win = max(1, int(0.03 * sr))
    n_f = len(mono) // win
    raw_dur = len(mono) / float(sr) if sr > 0 else 0.0
    if n_f > 0:
        env = np.array([np.mean(np.abs(mono[i * win : (i + 1) * win])) for i in range(n_f)])
        active_idxs = np.where(env > 0.011)[0]
        if len(active_idxs) > 0:
            start_f = max(0, int(active_idxs[0]) - 1)
            end_f = min(n_f, int(active_idxs[-1]) + 4)
        else:
            start_f, end_f = 0, n_f
        trimmed = data[start_f * win : min(len(data), end_f * win)]
    else:
        trimmed = data
    print(f"    [AudioTrim] {raw_wav.name}: {raw_dur:.2f}s -> {len(trimmed)/float(sr):.2f}s (atempo={atempo:.2f}x)")

    tmp_trim = raw_wav.with_name(raw_wav.stem + "_trim.wav")
    sf.write(str(tmp_trim), trimmed, sr)

    cmd = [
        "ffmpeg", "-y", "-i", str(tmp_trim),
        "-af",
        f"atempo={atempo:.3f},highpass=f=85,lowpass=f=12500,"
        f"equalizer=f=185:t=q:w=1.0:g=-1.5,equalizer=f=2900:t=q:w=1.2:g=2.2,"
        f"loudnorm=I=-14.2:TP=-1.0:LRA=6,"
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
    speech_dur = max(0.3, total_clip_dur - pad_lead - pad_tail)
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


def _slice_block_with_whisper(
    block_wav: Path,
    block_items: List[Tuple[str, str]],
    wmodel: Any,
    voice_dir: Path,
) -> None:
    """Slices a multi-beat cohesive Cumberbatch block WAV into per-beat raw WAVs preserving tails & pauses."""
    data, sr = sf.read(str(block_wav))
    mono = np.mean(data, axis=1) if data.ndim > 1 else data
    total_sec = len(mono) / float(sr)

    bounds: List[Tuple[float, float]] = []
    try:
        res = wmodel.transcribe(str(block_wav), language="en", word_timestamps=True, fp16=False)
        spoken = []
        for seg in res.get("segments", []):
            for wd in seg.get("words", []):
                tok = re.sub(r"[^a-z0-9]", "", (wd.get("word") or "").lower())
                if tok:
                    spoken.append((tok, float(wd["start"]), float(wd["end"])))

        expected_w = sum(len(sp_txt.split()) for _, sp_txt in block_items)
        if len(spoken) >= expected_w * 0.65:
            cursor = 0
            for idx, (_, sp_txt) in enumerate(block_items):
                c_toks = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in sp_txt.split() if re.sub(r"[^a-z0-9]", "", w.lower())]
                n_w = max(1, len(c_toks))
                est_end = min(len(spoken) - (len(block_items) - 1 - idx), cursor + n_w)
                if idx < len(block_items) - 1 and c_toks:
                    nxt_first = re.sub(r"[^a-z0-9]", "", block_items[idx + 1][1].split()[0].lower())
                    best_k, best_sc = est_end, -1
                    for k in range(max(cursor + 1, est_end - 3), min(len(spoken), est_end + 4)):
                        sc = (2 if spoken[k][0] == nxt_first else 0) + (2 if spoken[k - 1][0] == c_toks[-1] else 0)
                        if sc > best_sc:
                            best_sc, best_k = sc, k
                    est_end = best_k
                if idx == len(block_items) - 1:
                    est_end = len(spoken)
                s_t = max(0.0, spoken[cursor][1] - 0.05) if idx == 0 else bounds[-1][1]
                if idx == len(block_items) - 1:
                    e_t = total_sec
                else:
                    w_end = spoken[est_end - 1][2]
                    w_nxt = spoken[min(len(spoken) - 1, est_end)][1]
                    gap = max(0.0, w_nxt - w_end)
                    e_t = w_end + min(0.11, gap * 0.55) if gap > 0.02 else w_end + 0.04
                e_t = max(s_t + 0.7, min(total_sec, e_t))
                bounds.append((s_t, e_t))
                cursor = min(len(spoken) - 1, est_end)
    except Exception as e:
        print(f"[Runner] Whisper cohesive block slice note: {e}")

    if len(bounds) != len(block_items):
        wts = [max(1, len(txt.split())) for _, txt in block_items]
        tot_w = float(sum(wts))
        cur_t = 0.0
        bounds = []
        for idx, wt in enumerate(wts):
            if idx == len(wts) - 1:
                bounds.append((cur_t, total_sec))
            else:
                nxt_t = cur_t + (wt / tot_w) * total_sec
                bounds.append((cur_t, nxt_t))
                cur_t = nxt_t

    for (tag, _), (st, et) in zip(block_items, bounds):
        seg = data[int(st * sr) : int(et * sr)]
        sf.write(str(voice_dir / f"raw_{tag}.wav"), seg, sr)


def synthesize_documentary_voice_and_mix(
    pkg: StoryPackage,
    run_dir: Path,
    fps: float = 30.0,
) -> Dict[str, Any]:
    """Synthesizes cohesive Benedict Cumberbatch clone narration, slices & aligns captions, and masters -14 LUFS with ZERO whoosh SFX."""
    voice_dir = run_dir / "audio"
    voice_dir.mkdir(parents=True, exist_ok=True)
    concat_inputs: List[Path] = []
    beat_timings: List[Dict[str, Any]] = []
    all_cues: List[Dict[str, Any]] = []

    hints = getattr(pkg, "pronunciation_hints", None) or {}
    story_items = [(f"beat_{b.beat_number}", b.voiceover_text, _apply_pronunciation_hints(b.voiceover_text, hints)) for b in pkg.beats]
    mid = max(2, len(story_items) // 2)
    blocks = [
        ("part1", story_items[:mid]),
        ("part2", story_items[mid:]),
    ]

    model, cb_prompt = _get_cumberbatch_clone()
    try:
        for blk_tag, blk_rows in blocks:
            blk_text = " ".join(sp for _, _, sp in blk_rows)
            blk_wav = voice_dir / f"raw_block_{blk_tag}.wav"
            w_cnt = len(blk_text.split())
            wavs, out_sr = model.generate_voice_clone(
                text=blk_text,
                language="English",
                voice_clone_prompt=cb_prompt,
                non_streaming_mode=True,
                temperature=0.52,
                repetition_penalty=1.18,
                max_new_tokens=max(420, int(w_cnt * 13.5)),
            )
            sf.write(str(blk_wav), wavs[0], out_sr)

        # Outro in same cohesive Cumberbatch voice
        outro_wav_raw = voice_dir / "raw_outro.wav"
        owavs, o_sr = model.generate_voice_clone(
            text=pkg.outro_narration,
            language="English",
            voice_clone_prompt=cb_prompt,
            non_streaming_mode=True,
            temperature=0.48,
            repetition_penalty=1.18,
            max_new_tokens=260,
        )
        sf.write(str(outro_wav_raw), owavs[0], o_sr)
    finally:
        _release_qwen3_tts()

    # Load CPU Whisper once for BOTH cohesive block slicing and canonical caption alignment
    import whisper
    if not hasattr(_align_whisper_with_canonical_text, "_model"):
        print("[Runner] Loading Whisper base (CPU) for slicing & caption alignment...")
        _align_whisper_with_canonical_text._model = whisper.load_model("base", device="cpu")
    wmodel = _align_whisper_with_canonical_text._model

    for blk_tag, blk_rows in blocks:
        _slice_block_with_whisper(
            voice_dir / f"raw_block_{blk_tag}.wav",
            [(tag, sp) for tag, _, sp in blk_rows],
            wmodel,
            voice_dir,
        )

    cum_sec = 0.0
    items = [(f"beat_{b.beat_number}", b.voiceover_text, b) for b in pkg.beats]
    items.append(("outro", pkg.outro_narration, None))

    for tag, canon_text, beat_obj in items:
        raw_wav = voice_dir / f"raw_{tag}.wav"
        clean_wav = voice_dir / f"clean_{tag}.wav"
        pad_tail = 0.16 if beat_obj is not None else 0.35
        dur_sec, sp_start, sp_end = _trim_silence_and_master_clip(
            raw_wav, clean_wav, pad_lead=0.05, pad_tail=pad_tail, atempo=1.08 if beat_obj is not None else 1.05
        )
        dur_frames = max(24, int(round(dur_sec * fps)))
        exact_dur_sec = dur_frames / fps

        concat_inputs.append(clean_wav)
        beat_timings.append({
            "tag": tag,
            "start_sec": cum_sec,
            "duration_sec": exact_dur_sec,
            "duration_frames": dur_frames,
            "speech_start": sp_start,
            "speech_end": sp_end,
            "text": canon_text,
            "wav": str(clean_wav),
        })
        cum_sec += exact_dur_sec

    # Strict ZERO AI whoosh policy — rely on crisp vocal cuts + groovy upright bass score!
    sfx_cues: List[Dict[str, Any]] = []

    # Align subtitles strictly to canonical spelling
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

    # Concatenate clean voice segments
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
            "kinetic_word": b.kinetic_word,
            "sub_caption": b.sub_caption,
            "bg_path": ba.get("bg_path"),
            "banner_path": ba.get("banner_path"),
            "cutout": ba.get("cutout"),
            "secondary_cutout": ba.get("secondary_cutout"),
            "mounted": ba.get("mounted"),
            "editorial": ba.get("editorial"),
            "newspaper_path": ba.get("newspaper_path"),
            "quote_card_path": ba.get("quote_card_path"),
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
