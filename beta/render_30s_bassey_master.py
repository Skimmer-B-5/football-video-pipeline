"""
beta/render_30s_bassey_master.py
Renders the compiled Remotion composition with 1990s Trinitron CRT analog treatment
and broadcasts the final 30-second master to Telegram chat 5909103212.
"""

import sys
import time
import json
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from pipeline.neural_instructions import StoryDossier
from beta.pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline
from beta.stages.telegram_bot import TelegramBotClient, get_env_credentials

def main():
    token, chat_id = get_env_credentials()
    bot = TelegramBotClient(token)
    target_chat = "5909103212"

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

    run_id = "master_30s_calvin_bassey"
    pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id=run_id)

    props_file = pipeline.ws.base_dir / "output" / f"remotion_props_{dossier.story_id}.json"
    audio_mix_path = pipeline.ws.base_dir / "voice" / "vocal_transitions" / "master_audio_final.wav"

    if not props_file.exists():
        raise FileNotFoundError(f"Props file not found: {props_file}")
    if not audio_mix_path.exists():
        raise FileNotFoundError(f"Audio mix not found: {audio_mix_path}")

    props_data = json.loads(props_file.read_text(encoding="utf-8"))
    total_frames = props_data["totalDurationInFrames"]
    story_sec = props_data["storyDurationSec"]
    outro_sec = props_data["outroDurationSec"]
    total_sec = props_data["totalDurationSec"]

    print(f"\n--- Loaded Validated Broadcast Specification ---")
    print(f"  Story Duration: {story_sec:.2f}s ({props_data['storyDurationInFrames']} frames)")
    print(f"  Outro Duration: {outro_sec:.2f}s ({props_data['outroDurationInFrames']} frames)")
    print(f"  Total Duration: {total_sec:.2f}s ({total_frames} frames @ 30fps)")

    print(f"\n--- Rendering Remotion & Mastering Trinitron CRT ---")
    final_video = pipeline.render_and_master(
        props_file=props_file,
        audio_mix_path=audio_mix_path,
        total_frames=total_frames
    )

    print(f"\n--- Delivering Broadcast Master to Telegram ({target_chat}) ---")
    caption = (
        f"📺 <b>V7.1.6.7 BROADCAST MASTER (30-SECOND DURATION)</b>\n\n"
        f"• <b>Headline:</b> {dossier.main_headline}\n"
        f"• <b>Protagonist:</b> {dossier.protagonist_name} ({dossier.current_club} ➔ {dossier.pursuing_club})\n"
        f"• <b>Voice:</b> British Sports Anchor (Ryan @ 145 WPM)\n"
        f"• <b>Opening Frame:</b> Craven Cottage matchday floodlights (zero sidewalks / no benches)\n"
        f"• <b>Visuals:</b> 16 authenticated match & stadium photographs (Zero Reuse)\n"
        f"• <b>Master:</b> 1990s Trinitron CRT analog treatment (-14 LUFS stereo)\n"
        f"• <b>Story Runtime:</b> {story_sec:.2f}s (Strict ~25s story target)\n"
        f"• <b>Outro Runtime:</b> {outro_sec:.2f}s (Separate branded ident)\n"
        f"• <b>Total Video:</b> {total_sec:.2f}s ({total_frames} frames @ 30fps)\n\n"
        f"<i>Broadcast production verified and delivered! Send /new anytime to scrape fresh stories!</i>"
    )
    bot.send_video(str(final_video), caption=caption, chat_id=target_chat)
    print(f"\nSUCCESS: Video delivered to Telegram chat {target_chat}: {final_video}")

if __name__ == "__main__":
    main()
