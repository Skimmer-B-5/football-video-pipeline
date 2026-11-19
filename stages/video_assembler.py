"""
Stage 7: 90s Retro Sports Broadcast Video Assembler.
Definitive Production Pipeline Engine for "Football in 30 Seconds" / "Football Plus":
1. 1080x1920 90s Sports Broadcast Aesthetic (Sky Sports / BBC Sport DNA).
2. User's Bezelified Transparent Channel Logo (top-left TV bug & outro plate).
3. Sleek, minimalist glowing red ● LIVE capsule (top-right).
4. Two-Tier Royal Navy Lower-Third Breaking News Card with Gold Accent & Barlow Condensed ExtraBold typography.
5. Continuous 3D Beveled Ticker Base with Smooth Rolling Ticker Tape (Clean ● bullets, zero '***', zero obsolete references).
6. 3D Embossed HEADLINES Tab Overlay.
7. Authentic CRT Scanlines, Subtle Chromatic Aberration & TV Broadcast Grain.
8. Exact Frame-Budgeted Synchronization: Audio and video locked to sub-frames with zero cutoff.
9. Outro Scene with Midnight Radial Spotlight, Centered 3D Logo, Centered Follow Card, and Outro Whoosh SFX.
"""

import sys
import os
import re
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker

DATA_DIR = PROJECT_ROOT / "data"
BRANDING_DIR = DATA_DIR / "branding"
FONTS_DIR = DATA_DIR / "fonts"
RETRO_DIR = DATA_DIR / "retro_90s"
SFX_DIR = DATA_DIR / "sfx"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

# Font paths
FONT_HEADLINE_PATH = FONTS_DIR / "BarlowCondensed-ExtraBold.ttf"
FONT_TICKER_PATH = FONTS_DIR / "BarlowCondensed-Bold.ttf"

def get_audio_duration(file_path: str) -> float:
    """Extract exact audio duration in seconds via ffprobe."""
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    out = subprocess.check_output(cmd, shell=True).decode().strip()
    return float(out)

def split_headline_text(text: str) -> Tuple[str, str]:
    """Split a sentence or headline into two balanced, punchy uppercase lines."""
    clean = text.strip().replace('"', '').replace("'", "").upper()
    for sep in [': ', ' - ', '? ', '! ']:
        if sep in clean:
            parts = clean.split(sep, 1)
            p0, p1 = parts[0].strip(), parts[1].strip()
            if p0 and p1:
                return p0[:38], p1[:38]
    words = clean.split()
    if len(words) <= 4:
        mid = max(1, len(words) // 2)
        return ' '.join(words[:mid]), ' '.join(words[mid:])
    mid = len(words) // 2
    return ' '.join(words[:mid])[:38], ' '.join(words[mid:])[:38]

def determine_badge(scene: Dict[str, Any], idx: int, total_scenes: int) -> Tuple[str, Tuple[int, int, int, int]]:
    """Determine category badge text and color based on scene content."""
    if scene.get("badge"):
        color = scene.get("badge_color", (204, 0, 0, 255) if idx == 0 else (0, 45, 120, 255))
        return scene["badge"].upper(), color

    text_lower = scene.get("text", "").lower()
    s_type = scene.get("type", "").lower()

    if idx == 0 or s_type == "hook":
        return "BREAKING EXCLUSIVE", (204, 0, 0, 255)
    elif "debt" in text_lower or "crisis" in text_lower or s_type == "crisis":
        return "FINANCIAL CRISIS", (204, 0, 0, 255)
    elif "mourinho" in text_lower:
        return "SPECIAL ONE REACTION", (0, 45, 120, 255)
    elif "boehly" in text_lower or "amortization" in text_lower:
        return "CHELSEA AMORTIZATION", (0, 45, 120, 255)
    elif "bale" in text_lower and "golf" in text_lower:
        return "THE WELSH ORDER", (204, 0, 0, 255)
    elif "board" in text_lower or "takeover" in text_lower or "control" in text_lower:
        return "BOARDROOM POWER", (0, 45, 120, 255)
    elif idx == total_scenes - 1 or s_type in ("climax", "verdict"):
        return "THE FINAL VERDICT", (204, 0, 0, 255)
    else:
        return "TRANSFER REPORT", (0, 45, 120, 255)

def create_scene_base_canvas(img_path: str, target_w: int = 1080, target_h: int = 1920) -> Image.Image:
    """
    Format image to 1080x1920:
    If wide landscape, apply broadcast pillar-box with smooth blurred background.
    If tall/portrait, crop and center cleanly.
    """
    orig = Image.open(img_path).convert("RGB")
    ow, oh = orig.size
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

        fg_y = 420
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
    """Renders pixel-perfect 90s Sports Broadcast HUD."""
    hud = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hud)

    # 1. Top-Left: User Bezel TV Bug (Width 360, Height 147)
    hud.paste(tv_bug_img, (48, 65), mask=tv_bug_img.split()[-1])

    # 2. Top-Right: Sleek, minimalist glowing red ● LIVE capsule (Centered)
    pill_x0, pill_y0, pill_w, pill_h = 920, 85, 110, 42
    pill_x1, pill_y1 = pill_x0 + pill_w, pill_y0 + pill_h
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=8, fill=(215, 10, 10, 240))
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=8, outline=(255, 120, 120, 200), width=1)

    bbox_live = font_live.getbbox("● LIVE")
    lw = bbox_live[2] - bbox_live[0]
    lh = bbox_live[3] - bbox_live[1]
    live_tx = pill_x0 + (pill_w - lw) // 2
    live_ty = pill_y0 + (pill_h - lh) // 2 - bbox_live[1]
    draw.text((live_tx, live_ty), "● LIVE", fill=(255, 255, 255), font=font_live)

    # 3. Lower Third in Barlow Condensed ExtraBold
    badge_text, badge_color = determine_badge(scene_info, idx, total_scenes)

    # Category Badge
    draw.rounded_rectangle([60, 1375, 430, 1435], radius=6, fill=badge_color)
    bbox_b = font_badge.getbbox(badge_text)
    bh = bbox_b[3] - bbox_b[1]
    b_ty = 1375 + (60 - bh) // 2 - bbox_b[1]
    draw.text((84, b_ty), badge_text, fill=(255, 255, 255), font=font_badge)

    # Gold separator line
    draw.rectangle([60, 1435, 430, 1440], fill=(255, 215, 0, 255))

    # Main News Box: Deep Royal Navy
    draw.rectangle([60, 1440, 1020, 1640], fill=(0, 22, 60, 248))
    draw.rectangle([60, 1440, 74, 1640], fill=(255, 215, 0, 255))  # Left gold accent bar

    # Headlines: Line 1 (White) & Line 2 (Gold)
    h1 = scene_info.get("h1")
    h2 = scene_info.get("h2")
    if not h1 or not h2:
        h1, h2 = split_headline_text(scene_info.get("text", "BREAKING FOOTBALL NEWS"))

    draw.text((100, 1466), h1, fill=(255, 255, 255), font=font_headline)
    draw.text((100, 1538), h2, fill=(255, 215, 0), font=font_headline)

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
    sub_text = "DAILY TRANSFERS  ●  EXCLUSIVE SCOOPS  ●  BREAKING DRAMA"
    bbox_s = font_sub.getbbox(sub_text)
    sub_w = bbox_s[2] - bbox_s[0]
    sub_x = (target_w - sub_w) // 2
    sub_y = card_y1 + 32
    draw.text((sub_x, sub_y), sub_text, fill=(160, 195, 240, 240), font=font_sub)

    # 5. Bottom 3D Ticker Base Plate
    plate.paste(ticker_base_img, (0, 1730), mask=ticker_base_img.split()[-1])

    return plate

def generate_outro_audio(temp_dir: Path, voice_name: str = "en-GB-RyanNeural") -> Tuple[Path, float]:
    """Synthesizes the official broadcast outro voiceover with high-energy broadcast punch."""
    import edge_tts
    out_mp3 = temp_dir / "outro_vo.mp3"
    text = "This is Football in 30 Seconds. Follow for daily breaking news."

    async def _synth():
        comm = edge_tts.Communicate(text, voice=voice_name, rate="+18%", pitch="+3Hz")
        await comm.save(str(out_mp3))

    try:
        asyncio.run(_synth())
    except Exception as e:
        print(f"[Assembler] Outro TTS error ({e}), using SAPI fallback...")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SetOutputToWaveFile('{str(out_mp3).replace(chr(92), '/')}'); "
            f"$s.Speak('This is Football in thirty seconds. Follow for daily breaking news.'); "
            f"$s.Dispose();"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, capture_output=True)

    dur = get_audio_duration(str(out_mp3))
    return out_mp3, dur

def build_ticker_text(headline: str, scenes: List[Dict[str, Any]]) -> str:
    """Build clean rolling news ticker text with sports bullets ●, zero ***, zero obsolete dates."""
    bullets = [f"FOOTBALL PLUS BREAKING  ●  {headline.upper()}"]
    for s in scenes[:4]:
        t = s.get("text", "").replace('"', '').replace("'", "").strip().upper()
        if t:
            bullets.append(t)
    bullets.append("THIS IS FOOTBALL IN 30 SECONDS")
    bullets.append("FOLLOW FOR DAILY BREAKING NEWS  ●")
    return "  ●  ".join(bullets)

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
    - Minimalist glowing red ● LIVE capsule
    - Two-tier lower third breaking news box with Barlow Condensed ExtraBold typography
    - 3D embossed rolling ticker tape
    - CRT scanlines, chromatic aberration, and TV noise
    - Sub-frame audio-visual synchronization with zero cutoff
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
            # Fallback
            tv_bug_img = Image.open(BRANDING_DIR / "tv_bug_football_plus_v3.png").convert("RGBA")

        logo_master_img = Image.open(BRANDING_DIR / "user_bezel_logo_master.png").convert("RGBA") if (BRANDING_DIR / "user_bezel_logo_master.png").exists() else tv_bug_img
        ticker_base_img = Image.open(BRANDING_DIR / "ticker_base_3d.png").convert("RGBA")
        tab_img_path = BRANDING_DIR / "headlines_tab_3d.png"
        crt_overlay_path = RETRO_DIR / "crt_scanlines.png"
        whoosh_sfx_path = SFX_DIR / "meme_whoosh_swoosh.wav"

        # 2. Extract Audio Durations & Prepare Scene Still Plates
        render_scenes = [dict(s) for s in scenes]
        total_scenes_count = len(render_scenes)

        scene_composites = []
        audio_clip_paths = []
        audio_durations = []

        headline = story_headline or render_scenes[0].get("text", "Football Breaking News")

        for idx, sc in enumerate(render_scenes):
            s_id = sc.get("scene_id", idx + 1)
            img_path = sc.get("image_path")
            audio_path = sc.get("audio_path")

            if not img_path or not os.path.exists(img_path):
                raise FileNotFoundError(f"Missing image path for scene {s_id}: {img_path}")
            if not audio_path or not os.path.exists(audio_path):
                raise FileNotFoundError(f"Missing audio path for scene {s_id}: {audio_path}")

            # Audio duration
            a_dur = sc.get("audio_duration_sec") or get_audio_duration(audio_path)
            audio_durations.append(a_dur)
            audio_clip_paths.append(audio_path)

            # Frame budget
            frame_count = round(a_dur * fps)

            # Motion pattern:
            # Scene 2 (crisis) -> push_in
            # Second to last scene -> lateral_pan
            # Others -> static (crisp, zero camera jitter)
            if idx == 1:
                motion = "push_in"
            elif idx == total_scenes_count - 1 and total_scenes_count > 3:
                motion = "lateral_pan"
            else:
                motion = "static"

            # Create Base Canvas & Composite HUD
            base_frame = create_scene_base_canvas(img_path, width, height)
            hud = create_scene_hud(
                sc, tv_bug_img, ticker_base_img,
                font_headline, font_badge, font_live,
                idx, total_scenes_count, width, height
            )
            comp = Image.alpha_composite(base_frame, hud)
            still_path = temp_dir / f"scene_comp_{idx+1}.png"
            comp.save(still_path)

            scene_composites.append({
                "still_path": str(still_path),
                "duration": a_dur,
                "frames": frame_count,
                "motion": motion
            })
            print(f"[Assembler] Prepared Scene {s_id}: {frame_count} frames ({a_dur:.3f}s, motion: {motion})")

        # 3. Append Outro Scene (if requested)
        if include_logo_outro:
            outro_mp3, outro_a_dur = generate_outro_audio(temp_dir)
            audio_clip_paths.append(str(outro_mp3))
            audio_durations.append(outro_a_dur)

            # Tail breathing room: +0.60s so speech finishes cleanly before video cut
            outro_v_dur = outro_a_dur + 0.60
            outro_frames = round(outro_v_dur * fps)

            outro_still = create_outro_plate(logo_master_img, ticker_base_img, font_follow, font_sub, width, height)
            outro_still_path = temp_dir / "scene_comp_outro.png"
            outro_still.save(outro_still_path)

            scene_composites.append({
                "still_path": str(outro_still_path),
                "duration": outro_v_dur,
                "frames": outro_frames,
                "motion": "subtle_ease"
            })
            print(f"[Assembler] Prepared Outro Scene: {outro_frames} frames ({outro_v_dur:.3f}s, audio: {outro_a_dur:.3f}s)")

        total_video_frames = sum(c["frames"] for c in scene_composites)
        total_video_dur = total_video_frames / fps
        total_speech_dur = sum(audio_durations)
        print(f"[Assembler] Total Planned Video: {total_video_dur:.3f}s ({total_video_frames} frames) | Speech: {total_speech_dur:.3f}s")

        # 4. Render Individual Frame-Accurate Video Clips
        clip_paths = []
        for i, c in enumerate(scene_composites):
            c_out = temp_dir / f"clip_{i+1}.mp4"
            frames = c["frames"]
            dur = c["duration"]
            motion = c["motion"]
            still_p = c["still_path"]

            if motion == "push_in":
                vf = f"zoompan=z='min(zoom+0.0003,1.04)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
                cmd = f'ffmpeg -y -i "{still_p}" -vf "{vf}" -frames:v {frames} -c:v libx264 -pix_fmt yuv420p -preset fast "{c_out}"'
            elif motion == "lateral_pan":
                vf = f"zoompan=z=1.03:x='min(on*0.25,30)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={fps}"
                cmd = f'ffmpeg -y -i "{still_p}" -vf "{vf}" -frames:v {frames} -c:v libx264 -pix_fmt yuv420p -preset fast "{c_out}"'
            elif motion == "subtle_ease":
                vf = f"zoompan=z='min(zoom+0.0005,1.03)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
                cmd = f'ffmpeg -y -i "{still_p}" -vf "{vf}" -frames:v {frames} -c:v libx264 -pix_fmt yuv420p -preset fast "{c_out}"'
            else:
                vf = f"scale={width}:{height},fps={fps}"
                cmd = f'ffmpeg -y -loop 1 -t {dur:.3f} -i "{still_p}" -vf "{vf}" -frames:v {frames} -c:v libx264 -pix_fmt yuv420p -preset fast "{c_out}"'

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

        # 6. Concatenate Audio & Mix Outro Whoosh
        audio_concat_txt = temp_dir / "audio_concat.txt"
        with open(audio_concat_txt, "w", encoding="utf-8") as f:
            for ap in audio_clip_paths:
                f.write(f"file '{ap.replace(chr(92), '/')}'\n")

        raw_vo_wav = temp_dir / "master_vo_raw.wav"
        cmd_a_concat = f'ffmpeg -y -f concat -safe 0 -i "{audio_concat_txt}" -c:a pcm_s16le "{raw_vo_wav}"'
        subprocess.check_call(cmd_a_concat, shell=True)

        # Mix with outro whoosh and pad to exact video duration
        mixed_audio = temp_dir / "master_audio_mixed.wav"
        whoosh_delay_ms = round(sum(audio_durations[:total_scenes_count]) * 1000)

        cmd_audio_mix = (
            f'ffmpeg -y -i "{raw_vo_wav}" -i "{whoosh_sfx_path}" -f lavfi -i "anoisesrc=d={total_video_dur+1.0}:c=pink:r=44100:a=0.005" '
            f'-filter_complex "'
            f'[0:a]highpass=f=120,volume=1.25,apad=whole_dur={total_video_dur:.3f}[vo]; '
            f'[1:a]adelay={whoosh_delay_ms}|{whoosh_delay_ms},volume=0.95[sfx]; '
            f'[2:a]highpass=f=400,lowpass=f=3000,volume=0.15[hiss]; '
            f'[vo][sfx][hiss]amix=inputs=3:duration=first:weights=1.0 0.90 0.12[aout]" '
            f'-map "[aout]" -c:a pcm_s16le "{mixed_audio}"'
        )
        subprocess.check_call(cmd_audio_mix, shell=True)

        # 7. Generate Rolling Ticker Tape
        ticker_text = build_ticker_text(headline, render_scenes)
        ticker_file = temp_dir / "ticker_tape.txt"
        with open(ticker_file, "w", encoding="utf-8") as f:
            f.write(ticker_text)

        font_ticker_esc = str(FONT_TICKER_PATH).replace("\\", "/").replace(":", "\\:")
        ticker_file_esc = str(ticker_file).replace("\\", "/").replace(":", "\\:")

        # 8. Master Assembly: CRT Scanlines, Chromatic Aberration, TV Noise & Rolling Ticker
        cmd_master = (
            f'ffmpeg -y -i "{concat_raw_video}" -i "{tab_img_path}" -i "{crt_overlay_path}" -i "{mixed_audio}" '
            f'-filter_complex "'
            f'[0:v]drawtext=fontfile=\'{font_ticker_esc}\':textfile=\'{ticker_file_esc}\':fontcolor=0xFFD700:fontsize=38:x=\'w-t*195\':y=1766[v_tick]; '
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
        print(f"[Assembler] Output: {output_mp4_path} ({final_dur:.2f}s, {final_size / (1024*1024):.2f} MB)")

        return output_mp4_path

if __name__ == "__main__":
    print("Testing 90s Retro Sports Broadcast Assembler module...")
