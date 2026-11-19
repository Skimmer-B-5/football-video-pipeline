# FFmpeg Reference Notes & Media Processing Guide

This reference documents the local FFmpeg operations, loudness standards, and quality verification workflows adapted from `ffmpeg-skill` for `football-video-pipeline`.

---

## 1. Selected Tools from `ffmpeg-skill`

The `ffmpeg-skill` package includes 42 Python CLI tools operating purely on Python standard library and local FFmpeg binaries. The key tools integrated into our pipeline include:

| Tool | Script Path | Function in Football Video Pipeline |
| :--- | :--- | :--- |
| **`probe.py`** | `scripts/probe.py` | Inspects streams, codecs, duration, frame rates, and sample rates with `--json` output. |
| **`loudness.py`** | `scripts/loudness.py` | Two-pass ITU-R BS.1770-4 loudness measurement and normalization (-14 LUFS, -1 dBTP ceiling). |
| **`look.py`** | `scripts/look.py` | Generates multi-tile visual contact sheets (e.g., 3x2 grid) for rapid visual QA. |
| **`verify.py`** | `scripts/verify.py` | Detects black frames, silent segments, audio clipping, and stream corruption. |
| **`sync.py`** | `scripts/sync.py` | Measures and compensates for audio-visual synchronization offset. |
| **`caption.py`** | `scripts/caption.py` | Ingests `.srt` files and validates styling, placement, and character overflow. |

---

## 2. Loudness Mastering Workflow (-14 LUFS, $\le -1.0$ dBTP)

Social platforms (YouTube Shorts, Instagram Reels, TikTok) dynamically penalize or distort videos with unnormalized audio. Videos exceeding -14 LUFS are compressed aggressively, while quiet videos underperform in user retention.

### Two-Pass Loudnorm Implementation
1. **Pass 1 (Measurement):**
   ```bash
   ffmpeg -i input_mix.wav -af loudnorm=I=-14:TP=-1.0:LRA=7:print_format=json -f null -
   ```
   Extracts `input_i`, `input_tp`, `input_lra`, and `input_thresh`.

2. **Pass 2 (Targeted Normalization & Limiting):**
   ```bash
   ffmpeg -i input_mix.wav -af loudnorm=I=-14:TP=-1.0:LRA=7:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:linear=true -ar 48000 -c:a pcm_s16le mastered_audio.wav
   ```

3. **Muxing into Master Container:**
   ```bash
   ffmpeg -i video_stream.mp4 -i mastered_audio.wav -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart master_output.mp4
   ```

---

## 3. Sub-Frame Audio-Visual Synchronization

Boundary drift between scene video frames and physical TTS audio was a primary failure point of legacy pipelines.

### The Invariant
Every scene's video frame count must be derived strictly from the **physical file duration on disk**, not from theoretical token counts or rounded text estimates:

$$\text{duration\_sec} = \text{ffprobe}(\text{audio\_scene.wav})$$
$$\text{frames} = \text{round}(\text{duration\_sec} \times 30.0)$$

By enforcing this invariant across both Remotion's scene durations and FFmpeg's timeline assembly, cumulative A/V drift is guaranteed to be **`0.000s`**.

---

## 4. Automated Video Quality Control (QA)

Before marking any video render as completed, the pipeline executes automated checks:

1. **Resolution & Aspect Ratio:** Enforces exactly `1080x1920` (9:16).
2. **Constant Frame Rate:** Enforces `30.0 fps` CFR.
3. **Black Frame Detection:** Scans every second with FFmpeg's `blackdetect=d=0.1:pic_th=0.98`. Any segment exceeding 0.1s of near-black pixels halts publication.
4. **Active Subtitle Band:** Samples the caption area (`y = 1200 - 1300`) to confirm subtitle visibility throughout spoken narration.
5. **Contact Sheet Storyboard:** Samples key timestamps to produce a high-resolution grid image for immediate review.
