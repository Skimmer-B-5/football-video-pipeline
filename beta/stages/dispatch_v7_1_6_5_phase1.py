import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.stages.telegram_bot import TelegramBotClient, get_env_credentials

CHAT_ID = "5909103212"

def main():
    token, env_chat_id = get_env_credentials()
    target_chat_id = CHAT_ID or env_chat_id
    if not token or not target_chat_id:
        print(f"Error: Missing token ({bool(token)}) or chat_id ({target_chat_id})")
        sys.exit(1)

    client = TelegramBotClient(token=token, default_chat_id=target_chat_id)
    print(f"Connected to Telegram Bot. Target Chat ID: {target_chat_id}")

    base_ws = PROJECT_ROOT / "beta" / "workspaces" / "endrick_milan" / "run_v7_1"
    voice_dir = base_ws / "voice" / "auditions_v7_1_6_5"
    visuals_dir = base_ws / "visuals" / "crt_comparison_v7_1_6_5"
    crops_dir = base_ws / "crops"

    # Intro message
    intro_text = (
        "🚨 <b>V7.1.6.5 PHASE 1 DELIVERABLES — 30 FOOTBALL PLUS</b>\n\n"
        "Here are the requested preliminary assets for editorial review before the final master render:\n"
        "1. <b>Three Voice Auditions</b> (natural speed, expressive sports delivery, tested on the mandatory passage).\n"
        "2. <b>1990s CRT Treatment Comparison</b> (Still + 3s Video Shimmer showing Trinitron scanlines & phosphor bloom).\n"
        "3. <b>Revised 16-Shot Editorial Rhythm Contact Sheet</b> (visual change every ~1.5–2.0s).\n\n"
        "Please review the audio options below and confirm your preferred voice."
    )
    msg_id = client.send_message(intro_text, chat_id=target_chat_id)
    print(f"Sent intro message: {msg_id}")
    time.sleep(1)

    # 1. Voice Auditions
    auditions = [
        (
            voice_dir / "audition_voice_A_ryan_energetic.mp3",
            "🎙️ Option A: Ryan (Qwen3-TTS Energetic)\n"
            "Cadence: Energetic sports correspondent, natural unaccelerated pacing (12.4s).\n"
            "Passage: 'Milan have made their move, but Mourinho wants him to stay. Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.'"
        ),
        (
            voice_dir / "audition_voice_B_british_expressive.mp3",
            "🎙️ Option B: Ryan (Edge-TTS en-GB-Ryan)\n"
            "Cadence: Crisp British sports desk presenter, bright consonants, television tempo (11.0s), natural Endrick & Milan pronunciation.\n"
            "Passage: 'Milan have made their move, but Mourinho wants him to stay. Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.'"
        ),
        (
            voice_dir / "audition_voice_C_alternative_anchor.mp3",
            "🎙️ Option C: Thomas (Edge-TTS en-GB-Thomas)\n"
            "Cadence: Authoritative broadcast journalist, deep newsroom presence, clear numbers & names (10.8s).\n"
            "Passage: 'Milan have made their move, but Mourinho wants him to stay. Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.'"
        ),
    ]

    for audio_path, caption in auditions:
        if audio_path.exists():
            print(f"Sending audio: {audio_path.name}...")
            aid = client.send_audio(str(audio_path), caption=caption, chat_id=target_chat_id)
            print(f"  Sent audio id: {aid}")
            time.sleep(1.5)
        else:
            print(f"  Warning: Audio file not found: {audio_path}")

    # 2. CRT Comparison Still
    crt_img_path = visuals_dir / "crt_treatment_comparison_v7_1_6_5.jpg"
    if not crt_img_path.exists():
        crt_img_path = visuals_dir / "crt_treatment_comparison_v7_1_6_5.png"
    if crt_img_path.exists():
        print(f"Sending CRT comparison image: {crt_img_path.name}...")
        caption = (
            "📺 1990s CRT Broadcast Treatment Comparison\n\n"
            "• Panel 1 (Left): Raw unprocessed image\n"
            "• Panel 2 (Middle): V7.1.6.4 treatment (too faint on phone screens)\n"
            "• Panel 3 (Right): V7.1.6.5 treatment (visible Trinitron scanlines, phosphor bloom on highlights, RGB edge fringing, warm analog grade). Subtitles remain crisp."
        )
        pid = client.send_photo(str(crt_img_path), caption=caption, chat_id=target_chat_id)
        print(f"  Sent CRT photo id: {pid}")
        time.sleep(1.5)

    # 3. CRT Comparison Video
    crt_vid_path = visuals_dir / "crt_treatment_comparison_v7_1_6_5.mp4"
    if crt_vid_path.exists():
        print(f"Sending CRT comparison video: {crt_vid_path.name}...")
        caption = "📺 1990s CRT Treatment in Motion (3s Shimmer Loop)\nNotice live phosphor highlight bloom and subtle analog sync jitter."
        vid = client.send_video(str(crt_vid_path), caption=caption, chat_id=target_chat_id)
        print(f"  Sent CRT video id: {vid}")
        time.sleep(1.5)

    # 4. Revised Editorial Contact Sheet
    contact_sheet_path = crops_dir / "clean_scene_chart_master_v7_1_6_5.jpg"
    if contact_sheet_path.exists():
        print(f"Sending contact sheet: {contact_sheet_path.name}...")
        caption = (
            "📋 Revised Editorial Rhythm Contact Sheet (V7.1.6.5)\n\n"
            "16 distinct visual shots across 5 narrative beats (cut every ~1.5–2.0s):\n"
            "• S01 (3 shots): Mystery hook, Casa Milan HQ, Mourinho resistance (face concealed)\n"
            "• S02 (2 shots): San Siro stadium + Endrick identity reveal\n"
            "• S03 (4 shots): Cadena SER report, €70M offer, buyback clause, bonuses\n"
            "• S04 (4 shots): Medical bulletin, grim injury reaction, Bernabéu sideline\n"
            "• S05 (3 shots): Real Madrid jersey dilemma, Milan horizon, final decision callout"
        )
        cid = client.send_photo(str(contact_sheet_path), caption=caption, chat_id=target_chat_id)
        print(f"  Sent contact sheet photo id: {cid}")
        time.sleep(1)

    print("Phase 1 dispatch completed successfully!")

if __name__ == "__main__":
    main()
