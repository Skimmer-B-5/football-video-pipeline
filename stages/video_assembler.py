"""
Stage 7: 90s Retro Sports Broadcast Master Video Assembler (v2.0 Rebuild).
Assembles a broadcast-grade vertical Short (1080x1920, 30fps) with:
- Top-Left: Channel Bezel Logo Bug
- Top-Right: Dynamic, truthful kicker capsule (e.g. ● TRANSFER WATCH or ● NEWS UPDATE, NEVER fake ● LIVE)
- Lower Third: Two-tier broadcast box in Barlow Condensed ExtraBold (Line 1 White, Line 2 Gold)
- Truthful Category Badge (REPORTED, RUMOUR, TACTICAL ANALYSIS, OFFICIALLY CONFIRMED, CONTRACT CLAUSE)
- Subtitles: Synchronized burned-in phrase captions (.srt generated alongside video)
- Ticker Tape: Concise factual bullets (NO whole narration paragraphs)
- Explainer Graphics integration (Transfer flowcharts, buy-back clauses, stat cards)
- Mastered Audio: -14 LUFS integrated loudness, -1.0 dBTP true-peak ceiling, 48 kHz stereo, zero pink noise hiss
- Frame-locked A/V synchronization with zero drift
- Outro: Crisp 1.0–1.2s broadcast branding card (never 4.6s long)
"""

import sys
import os
import re
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker

DATA_DIR = PROJECT_ROOT / "data"
BRANDING_DIR = DATA_DIR / "branding"
RETRO_DIR = DATA_DIR / "retro_90s" if (DATA_DIR / "retro_90s").exists() else DATA_DIR / "retro_effects"
SFX_DIR = DATA_DIR / "sfx"
FONT_HEADLINE_PATH = DATA_DIR / "fonts" / "BarlowCondensed-ExtraBold.ttf"
FONT_TICKER_PATH = DATA_DIR / "fonts" / "BarlowCondensed-Bold.ttf"

def get_audio_duration(audio_path: str) -> float:
    """Extracts exact physical duration of an audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    try:
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return float(res)
    except Exception as e:
        print(f"[Assembler] Warning: ffprobe duration read error on {audio_path}: {e}")
        return 3.0

def split_headline_text(text: str) -> Tuple[str, str]:
    """Fallback: Splits long headline text into two punchy, balanced broadcast lines."""
    clean = re.sub(r'[^\w\s\d€$£\-!?]', '', text).strip().upper()
    words = clean.split()
    if not words:
        return ("BREAKING NEWS", "SPECIAL REPORT")
    if len(words) <= 4:
        return (" ".join(words[:2]), " ".join(words[2:])) if len(words) > 2 else (" ".join(words), "EXCLUSIVE")

    mid = len(words) // 2
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:])
    if len(line1) > 34:
        line1 = line1[:31] + "..."
    if len(line2) > 34:
        line2 = line2[:31] + "..."
    return (line1, line2)

def determine_badge(scene_info: Dict[str, Any], idx: int, total_scenes: int) -> Tuple[str, Tuple[int, int, int, int]]:
    """
    Derives an authentic, truth-anchored status badge from scene metadata.
    NEVER defaults scene 0 to 'BREAKING EXCLUSIVE' unless officially confirmed exclusive.
    """
    on_screen = scene_info.get("on_screen", {})
    explicit_badge = on_screen.get("status_badge") or scene_info.get("badge")
    role = scene_info.get("role", "")

    # 1. Check explicit status_badge from Schema v2.0
    if explicit_badge:
        b_upper = str(explicit_badge).upper().strip()
        if b_upper in ("CONFIRMED", "OFFICIALLY CONFIRMED"):
            return "OFFICIALLY CONFIRMED", (0, 130, 50, 255)
        elif b_upper in ("REPORTED", "TRANSFER REPORT", "TRANSFER WATCH"):
            return "REPORTED", (0, 45, 120, 255)
        elif b_upper in ("RUMOUR", "TRANSFER RUMOUR"):
            return "RUMOUR / TALKS", (180, 85, 0, 255)
        elif b_upper in ("ANALYSIS", "TACTICAL ANALYSIS"):
            return "TACTICAL ANALYSIS", (50, 50, 90, 255)
        elif b_upper in ("CONTRACT CLAUSE", "CLAUSE BREAKDOWN"):
            return "CONTRACT CLAUSE", (120, 20, 140, 255)
        elif b_upper in ("DEBATE", "FINAL VERDICT", "VERDICT"):
            return "THE FINAL VERDICT", (204, 0, 0, 255)
        else:
            return b_upper, (0, 45, 120, 255)

    # 2. Contextual derivation based on role or narration text
    s_type = str(scene_info.get("type", "")).lower()
    text_lower = (scene_info.get("narration") or scene_info.get("text", "")).lower()

    if idx == total_scenes - 1 or s_type in ("climax", "verdict") or role == "debate":
        return "THE FINAL VERDICT", (204, 0, 0, 255)
    elif "clause" in text_lower or "buy-back" in text_lower or "contract" in text_lower:
        return "CONTRACT CLAUSE", (120, 20, 140, 255)
    elif "tactics" in text_lower or "squad" in text_lower or role == "tactical_fit":
        return "TACTICAL ANALYSIS", (50, 50, 90, 255)
    elif "rumour" in text_lower or "speculation" in text_lower:
        return "RUMOUR / TALKS", (180, 85, 0, 255)
    else:
        return "REPORTED", (0, 45, 120, 255)

def create_scene_base_canvas(img_path: str, target_w: int = 1080, target_h: int = 1920) -> Image.Image:
    """
    Format visual asset to 1080x1920:
    - If already 1080x1920 (e.g. explainer graphic): return directly.
    - If wide landscape: apply broadcast pillar-box with smooth blurred background and sharp bordered window.
    - If tall/portrait: center crop cleanly.
    """
    orig = Image.open(img_path).convert("RGB")
    ow, oh = orig.size

    # Check if image is already formatted to target canvas
    if ow == target_w and oh == target_h:
        return orig.convert("RGBA")

    aspect = ow / oh
    canvas = Image.new("RGBA", (target_w, target_h), (8, 12, 24, 255))

    if aspect > 1.25:
        # Wide landscape image: blurred background + sharp centered broadcast window
        bg_scale = max(target_w / ow, target_h / oh) * 1.15
        bg_w, bg_h = int(ow * bg_scale), int(oh * bg_scale)
        bg = orig.resize((bg_w, bg_h), Image.Resampling.BICUBIC)
        bx = (bg_w - target_w) // 2
        by = (bg_h - target_h) // 2
        bg_crop = bg.crop((bx, by, bx + target_w, by + target_h))
        bg_blurred = bg_crop.filter(ImageFilter.GaussianBlur(30))
        enhancer = Image.new("RGB", (target_w, target_h), (0, 0, 0))
        bg_final = Image.blend(bg_blurred, enhancer, 0.40)
        canvas.paste(bg_final.convert("RGBA"), (0, 0))

        # Sharp foreground TV window with 90s metallic broadcast border
        fg_w = 1000
        fg_h = int(fg_w / aspect)
        fg = orig.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

        fg_bordered = Image.new("RGBA", (fg_w + 16, fg_h + 16), (20, 30, 50, 255))
        draw_b = ImageDraw.Draw(fg_bordered)
        draw_b.rectangle([0, 0, fg_w + 15, fg_h + 15], outline=(100, 145, 210), width=3)
        fg_bordered.paste(fg.convert("RGBA"), (8, 8))

        fg_y = 380
        canvas.paste(fg_bordered, ((target_w - fg_w - 16) // 2, fg_y))
    else:
        # Vertical or square image: center crop
        scale = max(target_w / ow, target_h / oh)
        nw, nh = int(ow * scale), int(oh * scale)
        scaled = orig.resize((nw, nh), Image.Resampling.LANCZOS)
        cx = (nw - target_w) // 2
        cy = max(0, (nh - target_h) // 3)
        crop = scaled.crop((cx, cy, cx + target_w, cy + target_h))
        canvas.paste(crop.convert("RGBA"), (0, 0))

    return canvas

def create_scene_hud(
    scene_info: Dict[str, Any],
    tv_bug_img: Image.Image,
    ticker_base_img: Image.Image,
    font_headline: ImageFont.FreeTypeFont,
    font_badge: ImageFont.FreeTypeFont,
    font_live: ImageFont.FreeTypeFont,
    idx: int,
    total_scenes: int,
    target_w: int = 1080,
    target_h: int = 1920
) -> Image.Image:
    """Renders pixel-perfect 90s Sports Broadcast HUD with authentic typography and badges."""
    hud = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hud)

    # 1. Top-Left: User Bezel TV Bug
    hud.paste(tv_bug_img, (48, 65), mask=tv_bug_img.split()[-1])

    # 2. Top-Right: Truthful kicker capsule (Never fake ● LIVE)
    on_screen = scene_info.get("on_screen", {})
    kicker_raw = on_screen.get("kicker") or scene_info.get("kicker") or "NEWS UPDATE"
    kicker_text = f"● {kicker_raw.upper().strip()}"

    bbox_live = font_live.getbbox(kicker_text)
    lw = bbox_live[2] - bbox_live[0]
    lh = bbox_live[3] - bbox_live[1]

    pill_w = max(130, lw + 32)
    pill_h = 42
    pill_x1 = target_w - 60
    pill_x0 = pill_x1 - pill_w
    pill_y0 = 85
    pill_y1 = pill_y0 + pill_h

    # Kicker styling: rich crimson red with high-visibility outline
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=8, fill=(215, 10, 10, 240))
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=8, outline=(255, 120, 120, 200), width=1)

    live_tx = pill_x0 + (pill_w - lw) // 2
    live_ty = pill_y0 + (pill_h - lh) // 2 - bbox_live[1]
    draw.text((live_tx, live_ty), kicker_text, fill=(255, 255, 255), font=font_live)

    # 3. Lower Third in Barlow Condensed ExtraBold
    badge_text, badge_color = determine_badge(scene_info, idx, total_scenes)

    # Category Badge
    draw.rounded_rectangle([60, 1375, 460, 1435], radius=6, fill=badge_color)
    bbox_b = font_badge.getbbox(badge_text)
    bh = bbox_b[3] - bbox_b[1]
    b_ty = 1375 + (60 - bh) // 2 - bbox_b[1]
    draw.text((84, b_ty), badge_text, fill=(255, 255, 255), font=font_badge)

    # Gold separator line
    draw.rectangle([60, 1435, 460, 1440], fill=(255, 215, 0, 255))

    # Main News Box: Deep Royal Navy
    draw.rectangle([60, 1440, 1020, 1640], fill=(0, 22, 60, 248))
    draw.rectangle([60, 1440, 74, 1640], fill=(255, 215, 0, 255))  # Left gold accent bar

    # Headlines: Line 1 (White) & Line 2 (Gold)
    h1 = on_screen.get("headline") or scene_info.get("h1")
    h2 = on_screen.get("subheadline") or scene_info.get("h2")
    if not h1 or not h2:
        h1, h2 = split_headline_text(scene_info.get("narration") or scene_info.get("text", "BREAKING FOOTBALL NEWS"))

    # Render headlines with slight shadow for readability
    draw.text((102, 1468), h1.upper(), fill=(0, 0, 0, 180), font=font_headline)
    draw.text((100, 1466), h1.upper(), fill=(255, 255, 255), font=font_headline)

    draw.text((102, 1540), h2.upper(), fill=(0, 0, 0, 180), font=font_headline)
    draw.text((100, 1538), h2.upper(), fill=(255, 215, 0), font=font_headline)

    # 4. Bottom 3D Beveled Ticker Base Plate
    hud.paste(ticker_base_img, (0, 1730), mask=ticker_base_img.split()[-1])

    return hud

def create_outro_plate(
    logo_master_img: Image.Image,
    ticker_base_img: Image.Image,
    font_follow: ImageFont.FreeTypeFont,
    font_sub: ImageFont.FreeTypeFont,
    target_w: int = 1080,
    target_h: int = 1920
) -> Image.Image:
    """Renders the pristine 90s Sports Broadcast Outro Plate."""
    plate = Image.new("RGBA", (target_w, target_h), (3, 8, 20, 255))
    draw = ImageDraw.Draw(plate)

    # 1. Subtle Radial Studio Spotlight behind the logo
    spot_x = target_w // 2
    spot_y = 700
    for r in range(600, 0, -8):
        factor = 1.0 - (r / 600.0)
        alpha = int(factor * factor * 110)
        draw.ellipse([spot_x - r, spot_y - r, spot_x + r, spot_y + r], fill=(15, 45, 120, alpha))

    # Subtle angled stadium beams
    beams_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(beams_layer)
    for x_off in [-380, -190, 0, 190, 380]:
        b_draw.polygon([
            (spot_x + x_off - 40, 0),
            (spot_x + x_off + 40, 0),
            (spot_x + int(x_off * 1.8) + 120, target_h),
            (spot_x + int(x_off * 1.8) - 120, target_h)
        ], fill=(25, 75, 190, 16))
    plate = Image.alpha_composite(plate, beams_layer)
    draw = ImageDraw.Draw(plate)

    # 2. Place User Bezel Logo mathematically centered horizontally
    mw, mh = logo_master_img.size
    target_mw = 740
    target_mh = int(target_mw * (mh / mw))
    logo_resized = logo_master_img.resize((target_mw, target_mh), Image.Resampling.LANCZOS)

    lx = (target_w - target_mw) // 2
    ly = 560
    plate.paste(logo_resized, (lx, ly), mask=logo_resized.split()[-1])

    # 3. Interactive Follow Card (Centered)
    card_w = 680
    card_h = 76
    card_x0 = (target_w - card_w) // 2
    card_y0 = ly + target_mh + 90
    card_x1 = card_x0 + card_w
    card_y1 = card_y0 + card_h

    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=14, fill=(6, 18, 48, 235))
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=14, outline=(255, 215, 0, 230), width=2)
    draw.line([(card_x0 + 14, card_y0 + 2), (card_x1 - 14, card_y0 + 2)], fill=(120, 190, 255, 180), width=1)

    follow_text = "FOLLOW FOR DAILY BREAKING NEWS"
    bbox_f = font_follow.getbbox(follow_text)
    text_w = bbox_f[2] - bbox_f[0]
    text_h = bbox_f[3] - bbox_f[1]
    text_x = (target_w - text_w) // 2
    text_y = card_y0 + (card_h - text_h) // 2 - bbox_f[1]
    draw.text((text_x, text_y), follow_text, fill=(255, 215, 0), font=font_follow)

    # 4. Sub-tagline below pill (Centered)
    sub_text = "DAILY TRANSFERS  |  EXCLUSIVE SCOOPS  |  BREAKING DRAMA"
    bbox_s = font_sub.getbbox(sub_text)
    sub_w = bbox_s[2] - bbox_s[0]
    sub_x = (target_w - sub_w) // 2
    sub_y = card_y1 + 32
    draw.text((sub_x, sub_y), sub_text, fill=(160, 195, 240, 240), font=font_sub)

    # 5. Bottom 3D Ticker Base Plate
    plate.paste(ticker_base_img, (0, 1730), mask=ticker_base_img.split()[-1])

    return plate

def generate_outro_audio(temp_dir: Path, voice_name: str = "en-GB-ThomasNeural") -> Tuple[Path, float]:
    """
    Synthesizes the official broadcast outro voiceover with calm, unhurried delivery.
    Outputs a standardized 48kHz stereo pcm_s16le WAV with 0.25s pre-delay and 0.60s post-roll
    to ensure seamless concatenation without clipping, pops, or screeching.
    """
    import edge_tts
    temp_raw = temp_dir / "outro_raw.mp3"
    out_wav = temp_dir / "outro_vo.wav"
    text = "Follow Football Plus for daily football intelligence."

    async def _synth():
        comm = edge_tts.Communicate(text, voice=voice_name, rate="+0%", pitch="+0Hz")
        await comm.save(str(temp_raw))

    try:
        asyncio.run(_synth())
    except Exception as e:
        print(f"[Assembler] Outro TTS error ({e}), using SAPI fallback...")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Rate = 0; "
            f"$s.SetOutputToWaveFile('{str(temp_raw).replace(chr(92), '/')}'); "
            f"$s.Speak('Follow Football Plus for daily football intelligence.'); "
            f"$s.Dispose();"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, capture_output=True)

    # Standardize to 48kHz 16-bit stereo PCM with 0.25s pre-roll and 0.60s post-roll silence
    cmd_std = [
        "ffmpeg", "-y",
        "-i", str(temp_raw),
        "-af", "adelay=250|250,apad=pad_dur=0.60",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
        str(out_wav)
    ]
    subprocess.run(cmd_std, check=True, capture_output=True)
    temp_raw.unlink(missing_ok=True)

    dur = get_audio_duration(str(out_wav))
    return out_wav, dur

def build_ticker_text(headline: str, scenes: List[Dict[str, Any]], credit_source_name: str = "Football Plus") -> str:
    """Build clean rolling news ticker text with concise, factual bullets (never whole narration dumps)."""
    bullets = [
        f"FOOTBALL UPDATE  |  {headline.upper()}",
        f"SOURCE: {credit_source_name.upper()}  |  STATUS: REPORTED"
    ]
    for s in scenes:
        on_screen = s.get("on_screen", {})
        h = on_screen.get("headline")
        sub = on_screen.get("subheadline")
        if h and len(h) <= 50:
            bullets.append(h.upper())
        elif sub and len(sub) <= 50:
            bullets.append(sub.upper())

    bullets.append("THIS IS FOOTBALL IN 30 SECONDS")
    bullets.append("FOLLOW FOR DAILY BREAKING NEWS")
    return "   |   ".join(bullets) + "   |   "

def generate_subtitles_srt(scenes: List[Dict[str, Any]], srt_out_path: Path) -> Path:
    """
    Generates timed .srt subtitles for the entire video from scene narration and exact audio durations.
    Splits scene sentences into natural 3-5 word rhythmic phrases with accurate start/end timestamps.
    """
    entries = []
    global_time = 0.0
    sub_index = 1

    for sc in scenes:
        narration = (sc.get("narration") or sc.get("text", "")).strip()
        dur = float(sc.get("audio_duration_sec") or sc.get("duration", 3.0))
        if not narration or dur <= 0:
            global_time += dur
            continue

        words = narration.split()
        if not words:
            global_time += dur
            continue

        # Group words into 3 to 5 words per subtitle card
        chunks = []
        cur_chunk = []
        for w in words:
            cur_chunk.append(w)
            if len(cur_chunk) >= 4 or w.endswith((".", "!", "?", ",", ";", ":")):
                chunks.append(" ".join(cur_chunk))
                cur_chunk = []
        if cur_chunk:
            if chunks and len(cur_chunk) <= 2:
                chunks[-1] += " " + " ".join(cur_chunk)
            else:
                chunks.append(" ".join(cur_chunk))

        # Distribute scene duration across chunks based on character length
        total_chars = sum(len(c) for c in chunks)
        chunk_start = global_time

        for c_idx, c in enumerate(chunks):
            weight = len(c) / max(1, total_chars)
            c_dur = dur * weight
            c_end = chunk_start + c_dur
            if c_idx == len(chunks) - 1:
                c_end = global_time + dur

            def fmt_time(t_sec: float) -> str:
                hours = int(t_sec // 3600)
                minutes = int((t_sec % 3600) // 60)
                seconds = int(t_sec % 60)
                millis = int(round((t_sec - int(t_sec)) * 1000))
                return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

            start_str = fmt_time(chunk_start)
            end_str = fmt_time(c_end)

            clean_phrase = c.upper().replace('"', '').strip()
            entries.append(f"{sub_index}\n{start_str} --> {end_str}\n{clean_phrase}\n")
            sub_index += 1
            chunk_start = c_end

        global_time += dur

    srt_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(srt_out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))

    return srt_out_path

def assemble_video_ffmpeg(
    scenes: List[Dict[str, Any]],
    output_mp4_path: Path,
    credit_source_name: str = "Football Plus",
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    include_logo_outro: bool = True,
    include_hud: bool = True,
    story_headline: Optional[str] = None
) -> Path:
    """
    Assembles a broadcast-grade 90s sports TV video Short with:
    - User's beveled transparent channel logo
    - Minimalist glowing red ● KICKER capsule (Never fake ● LIVE)
    - Two-tier lower third breaking news box with Barlow Condensed ExtraBold typography
    - 3D embossed rolling ticker tape with concise bullets
    - Timed burned-in subtitles (.srt) positioned in safe vertical zone
    - CRT scanlines, chromatic aberration, and authentic TV analog grading
    - Frame-locked audio-visual synchronization with zero boundary drift
    - Mastered audio at -14 LUFS, -1.0 dBTP true-peak ceiling, 48 kHz stereo (zero pink noise hiss)
    """
    with ResourceTracker("Video_Assembly_90s_Broadcast"):
        output_mp4_path = Path(output_mp4_path)
        output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = DATA_DIR / "temp_assembly"
        temp_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[Assembler] >>> Assembling 90s Retro Sports Broadcast Short: {output_mp4_path.name}")

        # 1. Load Core Assets
        font_headline = ImageFont.truetype(str(FONT_HEADLINE_PATH), 46)
        font_badge = ImageFont.truetype(str(FONT_HEADLINE_PATH), 28)
        font_live = ImageFont.truetype(str(FONT_HEADLINE_PATH), 20)
        font_follow = ImageFont.truetype(str(FONT_HEADLINE_PATH), 38)
        font_sub = ImageFont.truetype(str(FONT_TICKER_PATH), 26)

        tv_bug_img = Image.open(BRANDING_DIR / "user_bezel_tv_bug.png").convert("RGBA") if (BRANDING_DIR / "user_bezel_tv_bug.png").exists() else None
        if tv_bug_img is None:
            tv_bug_img = Image.open(BRANDING_DIR / "tv_bug_football_plus_v3.png").convert("RGBA")

        logo_master_img = Image.open(BRANDING_DIR / "user_bezel_logo_master.png").convert("RGBA") if (BRANDING_DIR / "user_bezel_logo_master.png").exists() else tv_bug_img
        ticker_base_img = Image.open(BRANDING_DIR / "ticker_base_3d.png").convert("RGBA")
        tab_img_path = BRANDING_DIR / "headlines_tab_3d.png"
        crt_overlay_path = RETRO_DIR / "crt_scanlines.png"
        if not crt_overlay_path.exists():
            for alt_dir in [DATA_DIR / "retro_90s", DATA_DIR / "retro_effects"]:
                if (alt_dir / "crt_scanlines.png").exists():
                    crt_overlay_path = alt_dir / "crt_scanlines.png"
                    break

        # 2. Extract Exact Audio Durations & Prepare Scene Still Plates
        render_scenes = [dict(s) for s in scenes]
        total_scenes_count = len(render_scenes)

        scene_composites = []
        audio_clip_paths = []
        audio_durations = []

        headline = story_headline or render_scenes[0].get("narration") or render_scenes[0].get("text", "Football Breaking News")

        for idx, sc in enumerate(render_scenes):
            s_id = sc.get("scene_id", idx + 1)
            img_path = sc.get("image_path")
            audio_path = sc.get("audio_path")

            if not img_path or not os.path.exists(img_path):
                raise FileNotFoundError(f"Missing image path for scene {s_id}: {img_path}")
            if not audio_path or not os.path.exists(audio_path):
                raise FileNotFoundError(f"Missing audio path for scene {s_id}: {audio_path}")

            # Audio standardization to 48kHz stereo pcm_s16le:
            # If final scene before channel outro, add 0.75s silence padding so closing punchline breathes
            if idx == total_scenes_count - 1 and include_logo_outro:
                std_scene_wav = temp_dir / f"scene_{s_id}_padded.wav"
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", str(audio_path),
                    "-af", "apad=pad_dur=0.75",
                    "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                    str(std_scene_wav)
                ], check=True, capture_output=True)
            else:
                std_scene_wav = temp_dir / f"scene_{s_id}_std.wav"
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", str(audio_path),
                    "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                    str(std_scene_wav)
                ], check=True, capture_output=True)

            audio_path = str(std_scene_wav)
            a_dur = get_audio_duration(audio_path)
            sc["audio_duration_sec"] = a_dur
            audio_durations.append(a_dur)
            audio_clip_paths.append(audio_path)

            # Frame budget strictly locked to standardized audio duration
            frame_count = round(a_dur * fps)

            # Motion pattern: read from schema v2.0 or context
            motion_data = sc.get("motion", {})
            m_type = motion_data.get("type", "").lower() if isinstance(motion_data, dict) else str(motion_data).lower()

            if "push" in m_type or "zoom_in" in m_type or idx == 1:
                motion = "push_in"
            elif "pan" in m_type or (idx == total_scenes_count - 1 and total_scenes_count > 3):
                motion = "lateral_pan"
            elif "pull" in m_type or "zoom_out" in m_type:
                motion = "pull_out"
            elif "ease" in m_type:
                motion = "subtle_ease"
            else:
                motion = "static"

            # Create Base Canvas & Static HUD Layer separately
            base_frame = create_scene_base_canvas(img_path, width, height)
            hud = create_scene_hud(
                sc, tv_bug_img, ticker_base_img,
                font_headline, font_badge, font_live,
                idx, total_scenes_count, width, height
            )
            base_path = temp_dir / f"scene_base_{idx+1}.png"
            hud_path = temp_dir / f"scene_hud_{idx+1}.png"
            base_frame.save(base_path)
            hud.save(hud_path)

            scene_composites.append({
                "base_path": str(base_path),
                "hud_path": str(hud_path),
                "duration": a_dur,
                "frames": frame_count,
                "motion": motion
            })
            print(f"[Assembler] Prepared Scene {s_id}: {frame_count} frames ({a_dur:.3f}s, motion: {motion})")

        # 3. Append Outro Scene
        if include_logo_outro:
            outro_wav, outro_a_dur = generate_outro_audio(temp_dir)
            audio_clip_paths.append(str(outro_wav))
            audio_durations.append(outro_a_dur)

            # Frame budget strictly locked to outro audio duration
            outro_frames = round(outro_a_dur * fps)
            outro_v_dur = outro_frames / fps

            outro_still = create_outro_plate(logo_master_img, ticker_base_img, font_follow, font_sub, width, height)
            outro_still_path = temp_dir / "scene_comp_outro.png"
            outro_still.save(outro_still_path)

            scene_composites.append({
                "base_path": str(outro_still_path),
                "hud_path": None,
                "duration": outro_v_dur,
                "frames": outro_frames,
                "motion": "static"
            })
            print(f"[Assembler] Prepared Outro Scene: {outro_frames} frames ({outro_v_dur:.3f}s, audio: {outro_a_dur:.3f}s)")

        total_video_frames = sum(c["frames"] for c in scene_composites)
        total_video_dur = total_video_frames / fps
        total_speech_dur = sum(audio_durations)
        print(f"[Assembler] Total Planned Video: {total_video_dur:.3f}s ({total_video_frames} frames) | Speech: {total_speech_dur:.3f}s")

        # 4. Render Individual Frame-Accurate Video Clips (Background zooms, HUD stays 100% FIXED)
        clip_paths = []
        for i, c in enumerate(scene_composites):
            c_out = temp_dir / f"clip_{i+1}.mp4"
            frames = c["frames"]
            dur = c["duration"]
            motion = c["motion"]
            base_p = c["base_path"]
            hud_p = c.get("hud_path")

            if hud_p and os.path.exists(hud_p):
                # Normal scene: zoom the background photo ONLY, overlay HUD statically so lower-third & ticker stay completely fixed
                if motion == "push_in":
                    zoom_expr = f"zoompan=z='min(zoom+0.0004,1.05)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
                elif motion == "pull_out":
                    zoom_expr = f"zoompan=z='max(1.05-on*0.0004,1.0)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
                elif motion == "lateral_pan":
                    zoom_expr = f"zoompan=z=1.03:x='min(on*0.25,30)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}"
                elif motion == "subtle_ease":
                    zoom_expr = f"zoompan=z='min(zoom+0.0005,1.03)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
                else:
                    zoom_expr = f"scale={width}:{height},fps={fps}"

                vf = f"[0:v]{zoom_expr}[v_zoomed]; [v_zoomed][1:v]overlay=0:0[v_out]"
                cmd = f'ffmpeg -y -i "{base_p}" -i "{hud_p}" -filter_complex "{vf}" -map "[v_out]" -frames:v {frames} -c:v libx264 -pix_fmt yuv420p -preset fast "{c_out}"'
            else:
                # Outro still plate: static render with zero drifting
                vf = f"scale={width}:{height},fps={fps}"
                cmd = f'ffmpeg -y -loop 1 -t {dur:.3f} -i "{base_p}" -vf "{vf}" -frames:v {frames} -c:v libx264 -pix_fmt yuv420p -preset fast "{c_out}"'

            subprocess.check_call(cmd, shell=True)
            clip_paths.append(str(c_out))

        # 5. Concatenate Video Clips
        concat_txt = temp_dir / "video_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                f.write(f"file '{cp.replace(chr(92), '/')}'\n")

        concat_raw_video = temp_dir / "raw_video_concat.mp4"
        cmd_concat = f'ffmpeg -y -f concat -safe 0 -i "{concat_txt}" -c copy "{concat_raw_video}"'
        subprocess.check_call(cmd_concat, shell=True)

        # 6. Concatenate Audio & Master to -14 LUFS (Clean broadcast sound, zero shrieking noise)
        audio_concat_txt = temp_dir / "audio_concat.txt"
        with open(audio_concat_txt, "w", encoding="utf-8") as f:
            for ap in audio_clip_paths:
                clean_p = Path(ap).resolve().as_posix()
                f.write(f"file '{clean_p}'\n")

        raw_vo_wav = temp_dir / "master_vo_raw.wav"
        cmd_a_concat = f'ffmpeg -y -f concat -safe 0 -i "{audio_concat_txt}" -c:a pcm_s16le "{raw_vo_wav}"'
        subprocess.check_call(cmd_a_concat, shell=True)

        # Clean broadcast audio: NO loud meme whooshes, smooth 0.35s fade-out at outro
        mixed_audio_raw = temp_dir / "master_audio_raw_mix.wav"
        fade_start = max(0.0, total_video_dur - 0.35)
        cmd_audio_mix = (
            f'ffmpeg -y -i "{raw_vo_wav}" '
            f'-af "afade=t=out:st={fade_start:.3f}:d=0.35,apad=whole_dur={total_video_dur:.3f}" '
            f'-c:a pcm_s16le "{mixed_audio_raw}"'
        )
        subprocess.check_call(cmd_audio_mix, shell=True)

        # Master with loudnorm: target -14 LUFS, true peak -1.0 dBTP, 48kHz stereo
        mixed_audio = temp_dir / "master_audio_mastered.wav"
        cmd_loudnorm = (
            f'ffmpeg -y -i "{mixed_audio_raw}" '
            f'-af "loudnorm=I=-14:TP=-1.0:LRA=7,aformat=sample_rates=48000:channel_layouts=stereo" '
            f'-c:a pcm_s16le "{mixed_audio}"'
        )
        subprocess.check_call(cmd_loudnorm, shell=True)

        # 7. Subtitles Generation (.srt)
        srt_file = temp_dir / f"{output_mp4_path.stem}.srt"
        generate_subtitles_srt(render_scenes, srt_file)

        # Copy SRT to output directory alongside MP4
        output_srt_path = output_mp4_path.with_suffix(".srt")
        import shutil
        shutil.copy2(srt_file, output_srt_path)

        # 8. Generate Rolling Ticker Tape
        ticker_text = build_ticker_text(headline, render_scenes, credit_source_name=credit_source_name)
        ticker_file = temp_dir / "ticker_tape.txt"
        with open(ticker_file, "w", encoding="utf-8") as f:
            f.write(ticker_text)

        font_ticker_esc = str(FONT_TICKER_PATH).replace("\\", "/").replace(":", "\\:")
        ticker_file_esc = str(ticker_file).replace("\\", "/").replace(":", "\\:")
        srt_esc = str(srt_file).replace("\\", "/").replace(":", "\\:")

        # 9. Master Assembly: CRT Scanlines, Chromatic Aberration, TV Noise, Rolling Ticker & Burned-in Subtitles
        # Ticker text is strictly bounded to an 800px transparent window (x: 280 to 1080) so it rolls cleanly and NEVER goes under the red HEADLINES tab
        cmd_master = (
            f'ffmpeg -y -i "{concat_raw_video}" -i "{tab_img_path}" -i "{crt_overlay_path}" -i "{mixed_audio}" '
            f'-filter_complex "'
            f'[0:v]subtitles=\'{srt_esc}\':force_style=\'FontName=BarlowCondensed-ExtraBold,FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,MarginV=610,Alignment=2\'[v_sub]; '
            f'color=c=black@0:s=785x110:d={total_video_dur:.3f}[t_canvas]; '
            f'[t_canvas]drawtext=fontfile=\'{font_ticker_esc}\':textfile=\'{ticker_file_esc}\':fontcolor=0xFFD700:fontsize=32:x=\'w-t*180\':y=(h-text_h)/2[t_strip]; '
            f'[v_sub][t_strip]overlay=295:1730[v_tick]; '
            f'[v_tick][1:v]overlay=0:1730[v_masked]; '
            f'[v_masked][2:v]overlay=0:0[v_crt]; '
            f'[v_crt]chromashift=cbh=1.8:crh=-1.8,colorbalance=rs=0.04:gs=0.02:bs=-0.02,noise=alls=3:allf=t+u[v_final]" '
            f'-map "[v_final]" -map 3:a -c:v libx264 -pix_fmt yuv420p -preset medium -crf 19 '
            f'-c:a aac -b:a 192k -t {total_video_dur:.3f} "{output_mp4_path}"'
        )
        print(f"[Assembler] Rendering Master 90s Broadcast Short ({total_video_dur:.2f}s)...")
        subprocess.check_call(cmd_master, shell=True)

        final_dur = get_audio_duration(str(output_mp4_path))
        final_size = os.path.getsize(output_mp4_path)
        print(f"[Assembler] <<< Master 90s Broadcast Render Complete!")
        print(f"[Assembler] Output MP4: {output_mp4_path} ({final_dur:.2f}s, {final_size / (1024*1024):.2f} MB)")
        print(f"[Assembler] Output SRT: {output_srt_path}")

        return output_mp4_path

if __name__ == "__main__":
    print("Testing 90s Retro Sports Broadcast Assembler v2.0...")
