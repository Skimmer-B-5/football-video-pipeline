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
    voice_dir = base_ws / "voice" / "auditions_v7_1_6_5_qwen3"

    # Intro message
    intro_text = (
        "🎙️ <b>QWEN 3 PUNDIT & REPORTER AUDITIONS (SAMPLE-CLONED)</b>\n\n"
        "As requested, here are 3 real sports personalities who talk fast, sampled and cloned using <b>Qwen 3 (Base 0.6B Zero-Shot)</b> on the benchmark passage:\n\n"
        "<i>\"Milan have made their move, but Mourinho wants him to stay. Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.\"</i>\n\n"
        "• <b>Option 1: Jeff Stelling</b> — Sky Sports Soccer Saturday fast-talking studio pundit (8.89s).\n"
        "• <b>Option 2: Martin Tyler</b> — Legendary Premier League fast commentary & analysis (8.43s).\n"
        "• <b>Option 3: Fabrizio Romano</b> — Fast-talking breaking transfer news reporter (10.24s).\n\n"
        "Listen to the 3 voice notes below:"
    )
    msg_id = client.send_message(intro_text, chat_id=target_chat_id)
    print(f"Sent intro message: {msg_id}")
    time.sleep(1)

    auditions = [
        (
            voice_dir / "audition_qwen3_jeff_stelling_pundit.mp3",
            "🎙️ Option 1: Jeff Stelling (Sky Sports Soccer Saturday)\n"
            "Engine: Qwen3-TTS Zero-Shot Clone\n"
            "Style: Fast-talking British sports studio pundit & host (8.89s)\n"
            "Cadence: Breathless goal-alert tempo, sharp wit, urgent breaking news delivery."
        ),
        (
            voice_dir / "audition_qwen3_martin_tyler_commentator.mp3",
            "🎙️ Option 2: Martin Tyler (Premier League Commentary)\n"
            "Engine: Qwen3-TTS Zero-Shot Clone\n"
            "Style: Legendary football commentator / broadcast analyst (8.43s)\n"
            "Cadence: Rapid matchday excitement, punchy British consonants, dramatic tension."
        ),
        (
            voice_dir / "audition_qwen3_fabrizio_romano_reporter.mp3",
            "🎙️ Option 3: Fabrizio Romano (Transfer News Reporter)\n"
            "Engine: Qwen3-TTS Zero-Shot Clone\n"
            "Style: Fast-paced breaking transfer desk reporter (10.24s)\n"
            "Cadence: Iconic urgent scoops cadence, rapid staccato delivery on clubs and figures."
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

    print("Qwen 3 pundit auditions dispatch complete!")

if __name__ == "__main__":
    main()
