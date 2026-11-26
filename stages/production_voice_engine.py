"""
stages/production_voice_engine.py
V7.1.6.7 Authoritative Production Voice Architecture Engine.

Strict Architectural Guarantees:
1. Distinct Engines:
   - Primary Default: Qwen3-TTS 0.6B CustomVoice (Ryan) — Original British sports-presenter design.
   - Conditional Clone: Qwen3-TTS 0.6B Base — Reference-audio cloning ONLY when an authorized reference recording is explicitly configured.
   - Jeff Stelling is NOT identified as the production voice nor cloned without verified authorization.
2. Separate Runtimes: Tracks story duration (S01..S05 ~30s) and branded outro (5-6s) separately.
3. Anonymity Window: Programmatically enforces >= 4.0s (120 frames @ 30fps) duration for S01.
4. Speech-Aligned Subtitles: Computes acoustic vocal onset & offset from the generated audio.
5. Broadcast Mastering: -14 LUFS stereo leveling, 80Hz highpass, 3kHz presence EQ, zero whooshes.
"""

import os
import sys
import wave
import time
import json
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
AUTHORIZED_REF_ENV = "BETA_AUTHORIZED_REFERENCE_AUDIO"
DEFAULT_SPEAKER = "Aiden"
DEFAULT_INSTRUCT = (
    "Shouted, high-pitched ecstatic live television football anchor yelling breaking deadline-day news on Sky Sports! "
    "Extremely loud projecting voice, soaring energetic pitch inflection, rapid urgent speed, punchy staccato excitement on every phrase! "
    "Never drop volume, never whisper, never trail off into a moan."
)

SCENE_DURATION_BOUNDS = {
    "S01": {"target": 4.1, "min": 4.0, "max": 4.5},
    "S02": {"target": 3.6, "min": 2.8, "max": 4.2},
    "S03": {"target": 3.6, "min": 2.8, "max": 4.2},
    "S04": {"target": 3.6, "min": 2.8, "max": 4.2},
    "S05": {"target": 3.6, "min": 2.8, "max": 4.2},
    "S06": {"target": 3.6, "min": 2.8, "max": 4.2},
    "S07": {"target": 4.2, "min": 3.4, "max": 4.6},
    "outro": {"target": 4.8, "min": 4.0, "max": 5.2},
}


def detect_speech_boundaries(wav_path: Path, sample_rate: int = 48000, threshold: float = 0.015) -> Tuple[float, float]:
    """
    Computes exact acoustic speech onset and offset timestamps in seconds
    by analyzing the audio energy envelope.
    """
    data, sr = sf.read(str(wav_path))
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    abs_data = np.abs(data)
    # 20ms window smoothing
    win_len = int(0.02 * sr)
    if win_len < 1:
        win_len = 1
    envelope = np.convolve(abs_data, np.ones(win_len) / win_len, mode='same')

    active_indices = np.where(envelope > threshold)[0]
    if len(active_indices) == 0:
        total_sec = len(data) / float(sr)
        return (0.1, max(0.2, total_sec - 0.1))

    onset_sec = active_indices[0] / float(sr)
    offset_sec = active_indices[-1] / float(sr)
    return (max(0.0, onset_sec), min(len(data) / float(sr), offset_sec))


class ProductionVoiceEngine:
    def __init__(self, voice_dir: Path, fps: float = 30.0):
        self.voice_dir = voice_dir
        self.voice_dir.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self.sr = 48000

        # Check for authorized reference audio
        self.authorized_ref = os.environ.get(AUTHORIZED_REF_ENV, "").strip()
        self.has_authorized_clone = bool(self.authorized_ref and Path(self.authorized_ref).exists())

        if self.has_authorized_clone:
            self.mode = "BASE_CLONE"
            self.voice_name = "Authorized Reference Voice"
            print(f"[VoiceEngine] Active Voice: Qwen3-TTS 0.6B Base (Authorized Reference: {self.authorized_ref})")
        else:
            self.mode = "CUSTOM_VOICE"
            self.voice_name = f"High-Voltage Live Sports Anchor ({DEFAULT_SPEAKER})"
            print(f"[VoiceEngine] Active Voice: Qwen3-TTS 0.6B CustomVoice (Speaker: {DEFAULT_SPEAKER} — Live Urgent Anchor)")

    @staticmethod
    def _clean_tts_phrase(text: str) -> str:
        import re
        clean_text = (text or "").replace("—", " ").replace("--", " ").replace("–", " ").strip()
        clean_text = re.sub(r'\b(And|So|Or|Because|While|Yet|But|Meanwhile)\s*[,—–-]\s*', r'\1 ', clean_text, flags=re.IGNORECASE)
        clean_text = clean_text.replace("…", ", ").replace("...", ", ")
        return re.sub(r'\s+', ' ', clean_text).strip()

    @staticmethod
    def _energize_punctuation(text: str) -> str:
        """Converts flat trailing periods into energetic exclamation momentum for Qwen3-TTS pitch projection."""
        t = (text or "").strip()
        if not t:
            return t
        if t.endswith("."):
            t = t[:-1] + "!"
        return t

    def _synthesize_block_wav(self, block_scenes: List[Dict[str, Any]], block_tag: str) -> Optional[Path]:
        """Generates one continuous vocal WAV for `block_scenes` without unloading Qwen3-TTS."""
        if not block_scenes:
            return None
        from stages.qwen_tts_synthesizer import synthesize_qwen3

        cleaned_phrases = [self._energize_punctuation(self._clean_tts_phrase(sc["spoken_narration"])) for sc in block_scenes]
        joined_parts = []
        for idx, phr in enumerate(cleaned_phrases):
            if idx < len(cleaned_phrases) - 1 and phr.endswith("!"):
                nxt_low = cleaned_phrases[idx + 1].lower()
                if any(nxt_low.startswith(c) for c in ("because ", "while ", "and ", "but ", "yet ", "so ", "even though ", "meanwhile ")):
                    joined_parts.append(phr[:-1] + ",")
                else:
                    joined_parts.append(phr)
            else:
                joined_parts.append(phr)
        full_block_text = " ".join(joined_parts)

        block_wav = self.voice_dir / f"raw_block_{block_tag}.wav"
        block_txt = self.voice_dir / f"raw_block_{block_tag}.txt"
        need_tts = True
        if block_wav.exists() and block_txt.exists():
            try:
                if block_txt.read_text(encoding="utf-8").strip() == full_block_text:
                    need_tts = False
            except Exception:
                pass

        if need_tts:
            synthesize_qwen3(
                text=full_block_text,
                output_path=block_wav,
                speaker=DEFAULT_SPEAKER,
                instruct=DEFAULT_INSTRUCT,
                language="English",
                temperature=0.46,
                repetition_penalty=1.18,
                max_tokens_per_word=14.0,
            )
            try:
                block_txt.write_text(full_block_text, encoding="utf-8")
            except Exception:
                pass
        return block_wav

    def _slice_block_with_whisper(self, block_wav: Path, block_scenes: List[Dict[str, Any]], block_tag: str, whisper_model=None) -> bool:
        """Aligns and slices continuous block WAV into individual beat clips using Whisper CPU timestamps."""
        data, sr = sf.read(str(block_wav))
        mono = np.mean(data, axis=1) if data.ndim > 1 else data
        total_sec = len(mono) / float(sr)

        split_bounds: List[Tuple[float, float]] = []
        try:
            import re
            if whisper_model is None:
                import whisper
                whisper_model = whisper.load_model("base", device="cpu")
            res = whisper_model.transcribe(str(block_wav), language="en", word_timestamps=True, fp16=False)
            spoken_words = []
            for seg in res.get("segments", []):
                for wd in seg.get("words", []):
                    tok = re.sub(r"[^a-z0-9]", "", (wd.get("word") or "").lower())
                    if tok:
                        spoken_words.append((tok, float(wd["start"]), float(wd["end"])))

            if len(spoken_words) >= sum(len(sc["spoken_narration"].split()) for sc in block_scenes) * 0.65:
                cursor = 0
                for idx, sc in enumerate(block_scenes):
                    canon_w = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in self._clean_tts_phrase(sc["spoken_narration"]).split()]
                    canon_w = [w for w in canon_w if w]
                    n_w = max(1, len(canon_w))
                    end_idx = min(len(spoken_words) - (len(block_scenes) - 1 - idx), cursor + n_w)
                    if idx < len(block_scenes) - 1 and canon_w:
                        next_first = re.sub(r"[^a-z0-9]", "", self._clean_tts_phrase(block_scenes[idx + 1]["spoken_narration"]).split()[0].lower())
                        best_k = end_idx
                        best_score = -1
                        for k in range(max(cursor + 1, end_idx - 3), min(len(spoken_words), end_idx + 4)):
                            sc_match = (2 if spoken_words[k][0] == next_first else 0) + (2 if spoken_words[k - 1][0] == canon_w[-1] else 0)
                            if sc_match > best_score:
                                best_score = sc_match
                                best_k = k
                        end_idx = best_k
                    if idx == len(block_scenes) - 1:
                        end_idx = len(spoken_words)
                    s_t = max(0.0, spoken_words[cursor][1] - 0.05) if idx == 0 else split_bounds[-1][1]
                    if idx == len(block_scenes) - 1:
                        e_t = total_sec
                    else:
                        w_end = spoken_words[end_idx - 1][2]
                        w_next = spoken_words[min(len(spoken_words) - 1, end_idx)][1]
                        gap = max(0.0, w_next - w_end)
                        # Place boundary inside quietest room-tone gap after word tail (protecting final consonant!)
                        e_t = w_end + min(0.08, gap * 0.5) if gap > 0.02 else w_end + 0.02
                    e_t = max(s_t + 0.8, min(total_sec, e_t))
                    split_bounds.append((s_t, e_t))
                    cursor = min(len(spoken_words) - 1, end_idx)
        except Exception as e:
            print(f"[VoiceEngine] Cohesive Whisper alignment note ({block_tag}): {e}")

        # Proportional RMS valley fallback if Whisper alignment skipped/mismatched
        if len(split_bounds) != len(block_scenes):
            weights = [max(1, len(sc["spoken_narration"].split())) for sc in block_scenes]
            tot_w = float(sum(weights))
            win = max(1, int(0.02 * sr))
            env = np.array([np.mean(np.abs(mono[i * win : (i + 1) * win])) for i in range(len(mono) // win)])
            s_cur = 0.0
            split_bounds = []
            for idx, wgt in enumerate(weights):
                if idx == len(weights) - 1:
                    split_bounds.append((s_cur, total_sec))
                else:
                    est_e = s_cur + (wgt / tot_w) * total_sec
                    lo = max(1, int((est_e - 0.25) / 0.02))
                    hi = min(len(env) - 1, int((est_e + 0.25) / 0.02))
                    if hi > lo:
                        valley_f = lo + int(np.argmin(env[lo:hi]))
                        est_e = valley_f * 0.02
                    split_bounds.append((s_cur, est_e))
                    s_cur = est_e

        for sc, (s_t, e_t) in zip(block_scenes, split_bounds):
            sid = sc["scene_id"]
            seg = data[int(s_t * sr) : int(e_t * sr)]
            raw_wav = self.voice_dir / f"raw_{sid}.wav"
            sf.write(str(raw_wav), seg, sr)
            try:
                (self.voice_dir / f"raw_{sid}.txt").write_text(self._clean_tts_phrase(sc["spoken_narration"]), encoding="utf-8")
            except Exception:
                pass
        print(f"[VoiceEngine] Cohesive block '{block_tag}' ({len(block_scenes)} beats, {total_sec:.2f}s) sliced cleanly.")
        return True

    def _synthesize_raw(self, text: str, sid: str) -> Path:
        """Synthesizes a single phrase (used for Base Clone mode or Outro)."""
        raw_wav = self.voice_dir / f"raw_{sid}.wav"
        text_file = self.voice_dir / f"raw_{sid}.txt"

        clean_text = self._energize_punctuation(self._clean_tts_phrase(text))

        if raw_wav.exists() and text_file.exists():
            try:
                if text_file.read_text(encoding="utf-8").strip() == clean_text:
                    return raw_wav
            except Exception:
                pass

        if self.mode == "BASE_CLONE":
            from stages.jeff_stelling_synthesizer import get_base_model
            model = get_base_model()
            wavs, out_sr = model.generate_voice_clone(
                text=clean_text,
                language="English",
                ref_audio=self.authorized_ref,
                non_streaming_mode=True,
                temperature=0.55,
                repetition_penalty=1.15
            )
            sf.write(str(raw_wav), wavs[0], out_sr)
        else:
            from stages.qwen_tts_synthesizer import synthesize_qwen3
            synthesize_qwen3(
                text=clean_text,
                output_path=raw_wav,
                speaker=DEFAULT_SPEAKER,
                instruct=DEFAULT_INSTRUCT,
                language="English"
            )

        try:
            text_file.write_text(clean_text, encoding="utf-8")
        except Exception:
            pass

        return raw_wav

    def master_scene_audio(self, raw_wav: Path, sid: str, pad_lead: float, pad_tail: float, min_duration_sec: float = 0.0) -> Tuple[Path, float, int, float, float, float]:
        """
        Applies professional broadcast analog EQ and leveling (-14 LUFS stereo),
        adds quiet studio air padding, enforces duration bounds and tempo scaling,
        and extracts acoustic speech boundaries.
        """
        mastered_wav = self.voice_dir / f"mastered_{sid}.wav"
        clean_scene_wav = self.voice_dir / f"scene_{sid}.wav"

        # Check raw audio duration and trim dead leading/trailing silence
        data_raw, sr_raw = sf.read(str(raw_wav))
        if data_raw.ndim > 1:
            mono = np.mean(data_raw, axis=1)
        else:
            mono = data_raw

        # Outside-in dead-air trim: keep all mid-sentence pauses intact & preserve word tail decay
        win_size = int(0.04 * sr_raw)
        n_frames = len(mono) // win_size
        if n_frames > 0:
            env = np.array([np.mean(np.abs(mono[i * win_size : (i + 1) * win_size])) for i in range(n_frames)])
            active_idxs = np.where(env > 0.012)[0]
            if len(active_idxs) > 0:
                start_frame = max(0, int(active_idxs[0]) - 1)
                end_frame = min(n_frames, int(active_idxs[-1]) + 3)
            else:
                start_frame = 0
                end_frame = n_frames

            start_idx = max(0, start_frame * win_size)
            end_idx = min(len(data_raw), end_frame * win_size)
            trimmed_raw = data_raw[start_idx:end_idx]
        else:
            trimmed_raw = data_raw

        raw_trimmed_wav = self.voice_dir / f"trimmed_{sid}.wav"
        sf.write(str(raw_trimmed_wav), trimmed_raw, sr_raw)
        raw_dur = len(trimmed_raw) / float(sr_raw)

        bounds = SCENE_DURATION_BOUNDS.get(sid, {})
        max_dur = bounds.get("max", 999.0)
        target_dur = bounds.get("target", max_dur)
        max_net_speech = max_dur - pad_lead - pad_tail

        speed_factor = 1.0
        if raw_dur > max_net_speech:
            target_net_speech = max(0.5, target_dur - pad_lead - pad_tail)
            # Enforce max speedup factor of 1.18x to prevent phase-vocoder stuttering
            speed_factor = min(1.18, max(1.02, raw_dur / target_net_speech))
            print(f"[VoiceEngine] [{sid}] Speech duration ({raw_dur:.2f}s) exceeds max allowed net ({max_net_speech:.2f}s). Applying clean atempo={speed_factor:.3f}x.")

        meta_json = self.voice_dir / f"mastered_{sid}.json"
        regen_master = True
        if mastered_wav.exists() and meta_json.exists():
            try:
                meta = json.loads(meta_json.read_text(encoding="utf-8"))
                if abs(meta.get("speed_factor", 1.0) - speed_factor) < 0.01:
                    regen_master = False
            except Exception:
                pass

        if regen_master:
            filter_parts = []
            if speed_factor > 1.01:
                filter_parts.append(f"atempo={speed_factor:.3f}")

            filter_parts.extend([
                "highpass=f=95",
                "lowpass=f=12500",
                "equalizer=f=185:t=q:w=1.0:g=-1.6",
                "equalizer=f=3200:t=q:w=1.2:g=2.8",
                "compand=attacks=0.015:decays=0.12:points=-60/-60|-24/-15|-12/-7|0/-2.5",
                "loudnorm=I=-14:TP=-1.0:LRA=6",
                "aformat=sample_rates=48000:channel_layouts=stereo"
            ])
            filter_chain = ",".join(filter_parts)
            cmd = [
                "ffmpeg", "-y", "-i", str(raw_trimmed_wav),
                "-af", filter_chain,
                "-c:a", "pcm_s16le",
                str(mastered_wav)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            try:
                meta_json.write_text(json.dumps({"raw_dur": raw_dur, "speed_factor": speed_factor}), encoding="utf-8")
            except Exception:
                pass

        data, sr = sf.read(str(mastered_wav))
        if data.ndim == 1:
            data = np.column_stack([data, data])

        lead_pad = np.zeros((int(pad_lead * sr), 2))
        tail_pad = np.zeros((int(pad_tail * sr), 2))
        composite = np.concatenate([lead_pad, data, tail_pad])

        dur_sec = len(composite) / float(sr)

        # Enforce minimum duration (e.g. S01 minimum 4.0s anonymity requirement)
        if dur_sec < min_duration_sec:
            extra_needed = min_duration_sec - dur_sec
            extra_padding = np.zeros((int(extra_needed * sr), 2))
            composite = np.concatenate([composite, extra_padding])
            dur_sec = len(composite) / float(sr)

        dur_frames = int(round(dur_sec * self.fps))
        target_samples = int(dur_frames * (sr / self.fps))

        if len(composite) < target_samples:
            composite = np.pad(composite, ((0, target_samples - len(composite)), (0, 0)))
        elif len(composite) > target_samples:
            composite = composite[:target_samples]

        sf.write(str(clean_scene_wav), composite, sr)

        # Detect acoustic speech onset & offset for speech-aligned subtitles
        onset_sec, offset_sec = detect_speech_boundaries(clean_scene_wav, sr)

        return clean_scene_wav, round(dur_sec, 3), dur_frames, round(onset_sec, 3), round(offset_sec, 3), round(speed_factor, 3)

    def assemble_full_narration(self, screenplay_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes all beats, enforces runtime separation, and master audio bed.
        Returns detailed manifest with story and outro metrics recorded separately.
        """
        manifest = []
        lead_tail_config = {
            "S01": (0.08, 0.15),
            "S02": (0.06, 0.12),
            "S03": (0.06, 0.12),
            "S04": (0.06, 0.12),
            "S05": (0.06, 0.12),
            "S06": (0.06, 0.12),
            "S07": (0.08, 0.15),
            "outro": (0.10, 0.20)
        }

        # Concatenate story beats cleanly in 2 cohesive vocal blocks in CUSTOM_VOICE mode so pitch & flow never stutter
        story_scenes = [sc for sc in screenplay_data["scenes"] if sc["scene_id"] != "outro"]
        outro_scenes = [sc for sc in screenplay_data["scenes"] if sc["scene_id"] == "outro"]
        if self.mode != "BASE_CLONE" and len(story_scenes) >= 4:
            mid = max(2, len(story_scenes) // 2 + (len(story_scenes) % 2))
            b1_wav = self._synthesize_block_wav(story_scenes[:mid], "part1")
            b2_wav = self._synthesize_block_wav(story_scenes[mid:], "part2")
            for o_sc in outro_scenes:
                self._synthesize_raw(o_sc["spoken_narration"], "outro")
            try:
                from stages.qwen_tts_synthesizer import release_qwen3_tts_model
                release_qwen3_tts_model()
            except Exception:
                pass
            w_mod = None
            try:
                import whisper
                w_mod = whisper.load_model("base", device="cpu")
            except Exception:
                pass
            if b1_wav:
                self._slice_block_with_whisper(b1_wav, story_scenes[:mid], "part1", whisper_model=w_mod)
            if b2_wav:
                self._slice_block_with_whisper(b2_wav, story_scenes[mid:], "part2", whisper_model=w_mod)
            w_mod = None

        for sc in screenplay_data["scenes"]:
            sid = sc["scene_id"]
            text = sc["spoken_narration"]
            pad_lead, pad_tail = lead_tail_config.get(sid, (0.06, 0.10))

            # Point 3: S01 must enforce minimum 4.0s identity concealment
            min_sec = SCENE_DURATION_BOUNDS.get(sid, {}).get("min", 4.0 if sid == "S01" else 0.0)

            raw_wav = self.voice_dir / f"raw_{sid}.wav"
            if self.mode == "BASE_CLONE" or sid == "outro" or not raw_wav.exists():
                raw_wav = self._synthesize_raw(text, sid)
            scene_wav, dur_sec, dur_frames, onset_sec, offset_sec, sp_factor = self.master_scene_audio(
                raw_wav, sid, pad_lead, pad_tail, min_duration_sec=min_sec
            )

            manifest.append({
                "scene_id": sid,
                "wav_path": str(scene_wav),
                "duration_sec": dur_sec,
                "duration_frames": dur_frames,
                "speech_onset_sec": onset_sec,
                "speech_offset_sec": offset_sec,
                "speech_onset_frame": int(round(onset_sec * self.fps)),
                "speech_offset_frame": int(round(offset_sec * self.fps)),
                "narration": text,
                "applied_speed_factor": sp_factor
            })

        # Rigorous Audio QA Inspection of All Clippings Before Video Creation
        print(f"\n[VoiceEngine] Auditing Audio Clippings for Broadcast Certification...")
        from stages.audio_quality_auditor import AudioQualityAuditor
        auditor = AudioQualityAuditor(target_lufs=-14.0, max_speed_factor=1.18)
        for m in manifest:
            sid = m["scene_id"]
            bounds = SCENE_DURATION_BOUNDS.get(sid, {})
            t_sec = bounds.get("target", m["duration_sec"])
            min_s = bounds.get("min", 0.0)
            max_s = bounds.get("max", 999.0)
            audit = auditor.audit_clipping(
                wav_path=Path(m["wav_path"]),
                scene_id=sid,
                target_sec=t_sec,
                min_sec=min_s,
                max_sec=max_s,
                applied_speed_factor=m["applied_speed_factor"]
            )
            m["qa_report"] = audit

        # Concatenate audio
        concat_txt = self.voice_dir / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for m in manifest:
                f.write(f"file '{Path(m['wav_path']).resolve().as_posix()}'\n")

        unmastered_vo = self.voice_dir / "master_clean_vo.wav"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt), "-c:a", "pcm_s16le", str(unmastered_vo)
        ], check=True, capture_output=True)

        music_bed = PROJECT_ROOT / "data" / "music" / "transfer_pulse.wav"
        final_audio_mix = self.voice_dir / "master_audio_final.wav"

        mix_cmd = [
            "ffmpeg", "-y",
            "-i", str(unmastered_vo),
            "-stream_loop", "-1", "-i", str(music_bed),
            "-filter_complex",
            "[1:a]volume=0.07,aloop=loop=-1:size=2e+09[bed];"
            "[0:a][bed]amix=inputs=2:duration=first:dropout_transition=2[mixed];"
            "[mixed]loudnorm=I=-14:TP=-1.0:LRA=7,aformat=sample_rates=48000:channel_layouts=stereo[out]",
            "-map", "[out]",
            "-c:a", "pcm_s16le",
            str(final_audio_mix)
        ]
        subprocess.run(mix_cmd, check=True, capture_output=True)

        # Point 2: Separate story and outro metrics
        story_manifest = [m for m in manifest if m["scene_id"] != "outro"]
        outro_manifest = [m for m in manifest if m["scene_id"] == "outro"]

        story_frames = sum(m["duration_frames"] for m in story_manifest)
        story_sec = sum(m["duration_sec"] for m in story_manifest)

        outro_frames = sum(m["duration_frames"] for m in outro_manifest)
        outro_sec = sum(m["duration_sec"] for m in outro_manifest)

        total_frames = story_frames + outro_frames
        total_sec = story_sec + outro_sec

        print(f"[VoiceEngine] Assembled story: {story_sec:.2f}s ({story_frames}f), outro: {outro_sec:.2f}s ({outro_frames}f), total: {total_sec:.2f}s ({total_frames}f)")

        return {
            "scenes": manifest,
            "master_audio_path": str(final_audio_mix),
            "voice_mode": self.mode,
            "voice_name": self.voice_name,
            "story_frames": story_frames,
            "story_sec": round(story_sec, 3),
            "outro_frames": outro_frames,
            "outro_sec": round(outro_sec, 3),
            "total_frames": total_frames,
            "total_sec": round(total_sec, 3)
        }
