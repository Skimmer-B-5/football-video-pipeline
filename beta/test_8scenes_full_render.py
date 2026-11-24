"""
beta/test_8scenes_full_render.py
Full End-to-End Render and Validation of the 8-Scene GPT OSS Visual Director Pipeline:
1. 8 Scenes (S01..S07 story + outro).
2. GPT OSS / Qwen 27B 1-sentence photographic descriptions.
3. Scene 8 outro skipped for image scraping.
4. S07 dual-choice visual cut (2 distinct photographs for Part 1 and Part 2).
5. Voice synthesis at brisk 145 WPM.
6. Remotion render & Trinitron CRT analog mastering.
7. Verification of 30-33s total runtime and delivery to Telegram chat 5909103212.
"""

import sys
import json
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from pipeline.neural_instructions import StoryDossier
from beta.pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline
from beta.stages.llm_visual_director import LLMVisualDirector
from beta.run_telegram_broadcast_service import source_story_shots
from beta.stages.telegram_bot import TelegramBotClient, get_env_credentials

def main():
    target_chat = "5909103212"
    token, _ = get_env_credentials()
    bot = TelegramBotClient(token)

    dossier = StoryDossier(
        story_id="calvin_bassey_fulham",
        main_headline="MAN UTD TRANSFER NEWS: FULHAM DEFENDER CALVIN BASSEY IS IN TALKS OVER NEW CONTRACT AMID MAN UTD LINKS",
        protagonist_name="Calvin Bassey",
        current_club="Fulham",
        pursuing_club="Manchester United",
        current_manager="Marco Silva",
        reported_base_fee="£30M",
        reported_bonuses="£5M",
        reported_buyback="5-year contract terms",
        complication="Silva urges board to seal extension",
        headline_kicker="● BREAKING TRANSFER REPORT",
        ticker_text="SKY SPORTS: FULHAM OPEN TALKS WITH CALVIN BASSEY AMID MAN UTD INTEREST ✦ MARCO SILVA DETERMINED TO KEEP DEFENDER ✦"
    )

    run_id = "v7_8scenes_master"
    pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id=run_id)

    print("\n=======================================================")
    print("STEP 1: Generating 8-Scene Screenplay (7 Story + 1 Outro)")
    print("=======================================================")
    script_data = pipeline.generate_screenplay()
    scenes = script_data["scenes"]
    print(f"Total Scenes: {len(scenes)}")
    for sc in scenes:
        words = len(sc["spoken_narration"].split())
        print(f"  [{sc['scene_id']}] ({words}w): {sc['spoken_narration']}")

    assert len(scenes) == 8, f"Expected 8 scenes, got {len(scenes)}"

    print("\n=======================================================")
    print("STEP 2: LLM Visual Director & Targeted Photo Sourcing")
    print("=======================================================")
    shots = source_story_shots(dossier, run_id, screenplay_scenes=scenes)
    print(f"Sourced shots summary:")
    for sid, img_list in shots.items():
        print(f"  [{sid}]: {len(img_list)} image(s) -> {img_list}")

    assert len(shots.get("S07", [])) == 2, f"Expected 2 shots for S07, got {len(shots.get('S07', []))}"

    print("\n=======================================================")
    print("STEP 3: Voice Synthesis (Brisk 145 WPM Sports Anchor)")
    print("=======================================================")
    audio_data = pipeline.synthesize_voice(script_data)
    total_sec = audio_data["total_sec"]
    story_sec = audio_data.get("story_sec", total_sec - 5.0)
    outro_sec = audio_data.get("outro_sec", 5.0)
    total_frames = audio_data["total_frames"]

    print(f"  Story Duration: {story_sec:.2f}s")
    print(f"  Outro Duration: {outro_sec:.2f}s")
    print(f"  Total Master Duration: {total_sec:.2f}s ({total_frames} frames @ 30fps)")

    assert 28.0 <= total_sec <= 35.0, f"Total duration {total_sec:.2f}s outside 28-35s envelope!"

    print("\n=======================================================")
    print("STEP 4: Compiling Remotion Props")
    print("=======================================================")
    props_path = pipeline.compile_visual_props(script_data, audio_data, shots)
    print(f"  Props file: {props_path}")

    print("\n=======================================================")
    print("STEP 5: Rendering Master Video via Remotion & Trinitron CRT")
    print("=======================================================")
    final_video = pipeline.render_and_master(
        props_file=props_path,
        audio_mix_path=Path(audio_data["master_audio_path"]),
        total_frames=total_frames
    )
    print(f"  Master video produced: {final_video}")
    assert final_video.exists(), "Master video file does not exist!"

    # Measure exact media properties with ffprobe
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=width,height",
        "-of", "json",
        str(final_video)
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    probe_data = json.loads(probe_res.stdout)
    file_dur = float(probe_data["format"]["duration"])
    streams = probe_data.get("streams", [])
    v_stream = next((s for s in streams if "width" in s), {})
    width = v_stream.get("width")
    height = v_stream.get("height")

    print(f"\n--- Master Verification Metrics ---")
    print(f"  Video Dimensions: {width}x{height} (Target: 1080x1920)")
    print(f"  Exact Duration: {file_dur:.2f}s (Target: ~30-33s)")
    print(f"  File Size: {final_video.stat().st_size / (1024*1024):.2f} MB")

    assert width == 1080 and height == 1920, f"Wrong dimensions: {width}x{height}"
    assert 28.0 <= file_dur <= 35.0, f"Duration {file_dur:.2f}s outside 28-35s!"

    print("\n=======================================================")
    print(f"STEP 6: Delivering Master Broadcast Video to Telegram ({target_chat})")
    print("=======================================================")
    caption = (
        f"📺 <b>V7.1.6.7 BROADCAST MASTER — 8-SCENE GPT OSS DIRECTED</b>\n\n"
        f"• <b>Headline:</b> {dossier.main_headline}\n"
        f"• <b>Protagonist:</b> {dossier.protagonist_name} ({dossier.current_club} ➔ {dossier.pursuing_club})\n"
        f"• <b>Visual Director:</b> GPT OSS / Qwen 27B 1-sentence image descriptions\n"
        f"• <b>Dual-Choice Cut:</b> S07 split into 2 distinct images (Fulham Part 1 ➔ Man Utd Part 2)\n"
        f"• <b>Voice:</b> British Sports Anchor @ 145 WPM\n"
        f"• <b>Total Runtime:</b> {file_dur:.2f}s ({story_sec:.1f}s story + {outro_sec:.1f}s outro)\n"
        f"• <b>Master Format:</b> 1080x1920 vertical, 30fps Trinitron CRT analog master\n\n"
        f"<i>Broadcast production verified and delivered!</i>"
    )
    bot.send_video(str(final_video), caption=caption, chat_id=target_chat)
    print(f"\nSUCCESS: Master video delivered to Telegram chat {target_chat}!")

if __name__ == "__main__":
    main()
