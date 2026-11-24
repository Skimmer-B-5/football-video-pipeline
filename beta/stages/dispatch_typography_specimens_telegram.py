"""
beta/stages/dispatch_typography_specimens_telegram.py
Dispatches the V7.1.3 Typography Specimen and Before/After Comparison to Telegram.
"""

import os
import sys
import json
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.story_workspace_manager import StoryWorkspace
from stages.telegram_bot import get_env_credentials

def dispatch_typography_specimens():
    ws = StoryWorkspace("endrick_milan", "run_v7_1")
    token, chat_id = get_env_credentials()
    if not token or not chat_id:
        print("Telegram credentials missing.")
        return {"status": "SKIPPED"}

    typo_dir = ws.base_dir / "typography"
    showcase_path = typo_dir / "master_typography_showcase_telegram.jpg"
    comp_path = typo_dir / "typography_before_after_comparison.png"

    if not showcase_path.exists() or not comp_path.exists():
        raise FileNotFoundError("Specimen images missing.")

    caption_comp = (
        "📊 <b>TYPOGRAPHY UPGRADE: BEFORE vs AFTER (V7.1.3)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔴 <b>BEFORE (V7 Legacy):</b> Inconsistent Arial / system font fallbacks, uncontrolled headline scale, cartoon-box subtitles.\n"
        "🟢 <b>AFTER (V7.1.3):</b> Three dedicated font families, calibrated broadcast hierarchy, bundled local TTFs (zero fallback)."
    )

    caption_showcase = (
        "🔤 <b>PERMANENT TYPOGRAPHY SPECIMEN SHOWCASE (V7.1.3)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎨 <b>Approved Font Collection:</b>\n"
        "1. <b>Barlow Condensed</b> (600–900): Headlines, player reveal, €60M transfer hero\n"
        "2. <b>Inter</b> (400–800): Sentence-case subtitles, lower-thirds, outro CTA\n"
        "3. <b>IBM Plex Mono</b> (500–600): Kickers, categories, data labels, status badges\n\n"
        "📐 <b>Calibrated Scale & Safe Zones:</b>\n"
        " • Primary Headlines: 72–84px | Subtitles: 44–48px\n"
        " • Hero Data: 112–140px | Data Labels: 24–28px\n"
        " • Safe Margins: 84px preferred | Avoid below y=1640\n"
        " • Multilingual Glyphs Verified: EN, PT-BR & ES-419 (á, é, í, ó, ú, ü, ç, ñ, ¿, ¡)\n\n"
        "<i>Review the typography specimen above before approving:</i>"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Typography System", "callback_data": f"typo_app_{ws.story_id}"},
                {"text": "✏️ Request Adjustments", "callback_data": f"typo_adj_{ws.story_id}"}
            ]
        ]
    }

    print("Uploading Before/After Comparison to Telegram...")
    with open(comp_path, "rb") as f:
        r1 = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption_comp, "parse_mode": "HTML"},
            files={"photo": f},
            timeout=60
        ).json()
    mid1 = r1.get("result", {}).get("message_id")
    print("  Before/After sent. Message ID:", mid1)

    print("Uploading Master Typography Showcase to Telegram...")
    with open(showcase_path, "rb") as f:
        r2 = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption_showcase, "parse_mode": "HTML", "reply_markup": json.dumps(reply_markup)},
            files={"photo": f},
            timeout=60
        ).json()
    mid2 = r2.get("result", {}).get("message_id")
    print("  Master Showcase sent. Message ID:", mid2)

    return {
        "status": "DELIVERED",
        "comparison_message_id": mid1,
        "showcase_message_id": mid2
    }

if __name__ == "__main__":
    res = dispatch_typography_specimens()
    print("Dispatch result:", res)
