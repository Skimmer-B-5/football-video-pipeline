"""
Stage 8: preview_and_approve
Sends the final master video to Telegram with title, certainty, source name,
and inline interactive buttons: [Approve], [Reject], [Regenerate script].
Never uploads anywhere without approval.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from fs30.config import PROJECT_ROOT, load_config
from stages.telegram_bot import TelegramBotClient

def send_approval_request(
    video_path: Path,
    story_data: Dict[str, Any],
    script_data: Dict[str, Any],
    run_id: str,
    config: Optional[Dict[str, Any]] = None,
    log_func=print
) -> Dict[str, Any]:
    """
    Sends master MP4 with interactive approval keyboard to Telegram.
    """
    if config is None:
        config = load_config()

    tel_cfg = config.get("telegram", {})
    bot_token = tel_cfg.get("bot_token")
    chat_id = tel_cfg.get("chat_id")

    if not bot_token or not chat_id:
        log_func("[Stage 8: preview_and_approve] Telegram token or chat_id missing. Skipping Telegram notification.")
        return {"status": "SKIPPED", "reason": "No credentials"}

    log_func(f"[Stage 8: preview_and_approve] Dispatching approval request to Telegram chat {chat_id}...")

    title = script_data.get("title", story_data.get("headline", "Breaking News"))
    certainty = script_data.get("certainty", "CONFIRMED").upper()
    source_name = story_data.get("source_name", "BBC Sport")
    wc = script_data.get("word_count", 0)

    caption = (
        f"<b>🎬 FS 30 — NEW MASTER READY FOR APPROVAL</b>\n\n"
        f"<b>Title:</b> {title}\n"
        f"<b>Certainty:</b> <code>{certainty}</code>\n"
        f"<b>Source:</b> {source_name}\n"
        f"<b>Words:</b> {wc} | <b>Run ID:</b> <code>{run_id}</code>\n\n"
        f"<i>Please review the 2.5D paper-cut preview below and select an action:</i>"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve & Publish", "callback_data": f"approve_{run_id}"},
                {"text": "❌ Reject", "callback_data": f"reject_{run_id}"}
            ],
            [
                {"text": "🔄 Regenerate Script", "callback_data": f"regen_{run_id}"}
            ]
        ]
    }

    try:
        bot = TelegramBotClient(token=bot_token, default_chat_id=chat_id)
        msg_id = bot.send_video(
            video_path=str(video_path),
            caption=caption,
            reply_markup=reply_markup,
            chat_id=chat_id
        )
        log_func(f"[Stage 8: preview_and_approve] ✓ Video successfully delivered to Telegram! (Message ID: {msg_id})")
        return {"status": "DELIVERED", "message_id": msg_id}
    except Exception as e:
        log_func(f"[Stage 8: preview_and_approve] ⚠ Telegram delivery failed: {e}")
        return {"status": "FAILED", "error": str(e)}
