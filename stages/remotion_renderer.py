"""
remotion_renderer.py - Programmatic Remotion Video Composition & Mastering Engine.

Integrates Remotion (React) as the visual motion graphics engine with local FFmpeg
for audio mastering (-14 LUFS) and quality verification, orchestrated via Python.
"""

import base64
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FPS = 30.0


def get_physical_audio_duration(audio_path: str) -> float:
    """Uses ffprobe to obtain the exact physical duration in seconds."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        logger.warning(f"ffprobe duration failed on {audio_path}: {e}")
        return 4.0


def parse_srt_to_frame_cues(srt_path: Path, fps: float = 30.0) -> List[Dict[str, Any]]:
    """Parses an SRT file into Remotion subtitle cues with start/end frames."""
    if not srt_path.exists():
        return []
    
    content = srt_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", content.strip())
    cues = []
    
    time_pat = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")
    
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            cue_id = int(lines[0].strip()) if lines[0].strip().isdigit() else len(cues) + 1
            m = time_pat.search(lines[1])
            if m:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, m.groups())
                t1 = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                t2 = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
                text = " ".join([l.strip() for l in lines[2:]])
                cues.append({
                    "id": cue_id,
                    "start_frame": int(round(t1 * fps)),
                    "end_frame": int(round(t2 * fps)),
                    "text": text
                })
    return cues


def prepare_remotion_props(
    script_data: Dict[str, Any],
    workspace_root: Path,
    fps: float = 30.0
) -> Dict[str, Any]:
    """Builds typed Remotion props from the Schema v2.0 scene plan."""
    story = script_data.get("story", {})
    scenes_in = script_data.get("scenes", [])
    
    total_frames = 0
    remotion_scenes = []
    
    for s in scenes_in:
        scene_id = s.get("scene_id", "s01")
        audio_file = workspace_root / "data" / "audio" / f"scene_{scene_id}.wav"
        image_file = workspace_root / "data" / "images" / f"scene_{scene_id}.png"
        
        # Exact frame duration locked to physical audio file
        dur_sec = get_physical_audio_duration(str(audio_file)) if audio_file.exists() else 4.0
        frame_dur = int(round(dur_sec * fps))
        total_frames += frame_dur
        
        # Convert image to base64 data URI to bypass Chromium file:/// security restrictions
        image_data_uri = None
        if image_file.exists():
            with open(image_file, "rb") as img_f:
                b64_content = base64.b64encode(img_f.read()).decode("ascii")
                image_data_uri = f"data:image/png;base64,{b64_content}"
        
        remotion_scenes.append({
            "scene_id": scene_id,
            "role": s.get("role", "context"),
            "narration": s.get("narration", ""),
            "durationInFrames": frame_dur,
            "audio_path": str(audio_file.resolve()) if audio_file.exists() else None,
            "image_path": image_data_uri,
            "on_screen": s.get("on_screen", {}),
            "visual": s.get("visual", {}),
            "motion": s.get("motion", {"type": "subtle_push_in"})
        })
        
    # Append dedicated broadcast outro scene if available
    outro_audio = workspace_root / "data" / "audio" / "scene_outro.wav"
    if outro_audio.exists():
        outro_dur = get_physical_audio_duration(str(outro_audio))
        outro_frames = int(round(outro_dur * fps))
        total_frames += outro_frames
        remotion_scenes.append({
            "scene_id": "outro",
            "role": "outro",
            "narration": "Follow Football in Thirty Seconds for daily breaking news.",
            "durationInFrames": outro_frames,
            "audio_path": str(outro_audio.resolve()),
            "image_path": None,
            "on_screen": {
                "headline": "FOLLOW FOR DAILY BREAKING NEWS",
                "kicker": "OFFICIAL"
            },
            "visual": {"kind": "outro_branding"},
            "motion": {"type": "static"}
        })

    srt_path = workspace_root / "evidence" / "endrick_milan_v2_rebuild.srt"
    subtitles = parse_srt_to_frame_cues(srt_path, fps=fps)
    
    kicker = remotion_scenes[0]["on_screen"].get("kicker", "TRANSFER WATCH") if remotion_scenes else "TRANSFER WATCH"
    headline = story.get("headline", "Milan line up €60m Endrick bid")
    ticker_text = f"CORRIERE DELLO SPORT: {headline.upper()} ✦ €60M BID + €10M ADD-ONS ✦ €80M BUY-BACK CLAUSE ✦"

    # Load authentic branding assets (Top-Left TV Bug, Outro Master Logo, Ticker Base Plate, CRT Scanlines)
    logo_file = workspace_root / "data" / "branding" / "user_bezel_tv_bug.png"
    master_logo_file = workspace_root / "data" / "branding" / "user_bezel_logo_master.png"
    ticker_base_file = workspace_root / "data" / "branding" / "ticker_base_3d.png"
    scanlines_file = workspace_root / "data" / "retro_90s" / "crt_scanlines.png"

    logo_data_uri = None
    if logo_file.exists():
        with open(logo_file, "rb") as f:
            logo_data_uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

    master_logo_data_uri = None
    if master_logo_file.exists():
        with open(master_logo_file, "rb") as f:
            master_logo_data_uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

    ticker_base_data_uri = None
    if ticker_base_file.exists():
        with open(ticker_base_file, "rb") as f:
            ticker_base_data_uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

    scanlines_data_uri = None
    if scanlines_file.exists():
        with open(scanlines_file, "rb") as f:
            scanlines_data_uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"

    return {
        "story_id": story.get("story_id", "endrick_milan_short"),
        "headline": headline,
        "totalDurationInFrames": total_frames,
        "scenes": remotion_scenes,
        "tickerText": ticker_text,
        "subtitles": subtitles,
        "kicker": kicker,
        "logoSrc": logo_data_uri,
        "masterLogoSrc": master_logo_data_uri,
        "tickerBaseSrc": ticker_base_data_uri,
        "scanlinesSrc": scanlines_data_uri,
        "enableRetroEffects": True
    }


def render_with_remotion(
    props: Dict[str, Any],
    output_raw_video: Path,
    remotion_dir: Path
) -> Path:
    """Renders the video stream headlessly using Remotion CLI."""
    props_file = remotion_dir / "temp_render_props.json"
    props_file.write_text(json.dumps(props, indent=2), encoding="utf-8")
    
    output_raw_video.parent.mkdir(parents=True, exist_ok=True)
    
    total_frames = props.get("totalDurationInFrames", 1137)
    cmd = [
        "npx.cmd", "remotion", "render",
        "FootballShort",
        str(output_raw_video.resolve()),
        f"--props={props_file.resolve()}",
        f"--frames=0-{total_frames - 1}",
        "--concurrency=4",
        "--gl=angle",
        "--log=warn",
        "--overwrite"
    ]
    
    logger.info(f"Rendering Remotion composition: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(remotion_dir), capture_output=True, text=True)
    if res.returncode != 0:
        logger.error(f"Remotion render error: {res.stderr}")
        raise RuntimeError(f"Remotion rendering failed: {res.stderr}")
        
    logger.info(f"Remotion raw video render completed: {output_raw_video}")
    return output_raw_video


def master_audio_and_mux(
    raw_video_path: Path,
    scenes: List[Dict[str, Any]],
    output_master_path: Path,
    temp_dir: Path,
    apply_retro_grading: bool = True
) -> Path:
    """
    Concatenates scene audio, normalizes to -14 LUFS, applies authentic 90s broadcast
    analog color grading and chromatic aberration, and muxes with the Remotion video.
    """
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Build ffmpeg concat list for scene audio
    concat_txt = temp_dir / "audio_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for s in scenes:
            a_path = s.get("audio_path")
            if a_path and os.path.exists(a_path):
                clean_path = a_path.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
                
    unmastered_audio = temp_dir / "unmastered_audio.wav"
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c:a", "pcm_s16le",
        str(unmastered_audio)
    ]
    subprocess.run(concat_cmd, capture_output=True, check=True)
    
    # 2. Loudness normalization to -14 LUFS (BS.1770-4)
    mastered_audio = temp_dir / "mastered_audio.wav"
    loudnorm_cmd = [
        "ffmpeg", "-y",
        "-i", str(unmastered_audio),
        "-af", "loudnorm=I=-14:TP=-1.0:LRA=7,aformat=sample_rates=48000:channel_layouts=stereo",
        str(mastered_audio)
    ]
    subprocess.run(loudnorm_cmd, capture_output=True, check=True)
    
    # 3. Mux mastered audio with Remotion video (with optional 90s analog broadcast grading)
    if apply_retro_grading:
        # Authentic 90s analog broadcast chain:
        # - chromashift: real CRT horizontal chromatic fringing (red/blue misalignment)
        # - colorbalance: cathode ray tube warm broadcast analog grading
        # - noise: micro-scale TV broadcast RF/phosphor grain
        retro_filter = "chromashift=cbh=1.8:crh=-1.8,colorbalance=rs=0.04:gs=0.02:bs=-0.02,noise=alls=2.5:allf=t+u"
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_video_path),
            "-i", str(mastered_audio),
            "-vf", retro_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_master_path)
        ]
    else:
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_video_path),
            "-i", str(mastered_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_master_path)
        ]
    subprocess.run(mux_cmd, capture_output=True, check=True)
    logger.info(f"Final mastered video produced: {output_master_path}")
    return output_master_path


def generate_remotion_storyboard(
    video_path: Path,
    output_storyboard: Path,
    num_samples: int = 6
) -> Path:
    """Extracts evenly spaced keyframes and tiles them into a high-res storyboard contact sheet."""
    dur = get_physical_audio_duration(str(video_path))
    step = dur / (num_samples + 1)
    timestamps = [round(step * (i + 1), 2) for i in range(num_samples)]
    
    temp_frames_dir = video_path.parent / "temp_remotion_frames"
    temp_frames_dir.mkdir(parents=True, exist_ok=True)
    frame_files = []
    
    for i, ts in enumerate(timestamps):
        out_f = temp_frames_dir / f"frame_{i:02d}.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(ts),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(out_f)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        if out_f.exists():
            frame_files.append(out_f)
            
    # Tile into a 3x2 contact sheet
    tile_cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_frames_dir / "frame_%02d.jpg"),
        "-filter_complex", "scale=540:960,tile=3x2:padding=10:color=black",
        "-q:v", "2",
        str(output_storyboard)
    ]
    subprocess.run(tile_cmd, capture_output=True, check=True)
    logger.info(f"Remotion storyboard generated: {output_storyboard}")
    return output_storyboard
