"""
beta/stages/dispatch_v7_1_4_telegram_package.py
Dispatches the complete V7.1.4 Clean Approval Package to Telegram:
1. Native Remotion Typography Master Showcase (Typography ready for approval)
2. Upgraded Clean Scene Contact Sheet (Enlarged 300x533 photos, verification states)
3. Refreshed Dialogue Screenplay (Script A - Script awaiting approval)
4. Refreshed Image Key Screenplay (Script B - Image Key awaiting approval)

Clearly distinguishes:
- Typography ready for approval
- Script awaiting approval
- Image key awaiting approval
- Existing visual asset limitations
- Qwen-VL verification status (Semantic VLM review pending)
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
from stages.dual_script_architecture import DualScriptDirector

def dispatch_package():
    ws = StoryWorkspace("endrick_milan", "run_v7_1")
    token, chat_id = get_env_credentials()
    if not token or not chat_id:
        print("Telegram credentials missing.")
        return {"status": "SKIPPED"}

    typo_dir = ws.base_dir / "typography"
    chart_path = ws.telegram_dir / "clean_scene_chart_master_v7_1_4.jpg"
    remotion_showcase = typo_dir / "typography_master_clean.png"

    if not chart_path.exists():
        raise FileNotFoundError(f"Contact sheet missing: {chart_path}")
    if not remotion_showcase.exists():
        raise FileNotFoundError(f"Remotion showcase missing: {remotion_showcase}")

    director = DualScriptDirector()
    script_a_file = ws.scripts_dir / "dialogue_script.json"
    script_b_file = ws.scripts_dir / "image_key_script.json"
    script_a = json.loads(script_a_file.read_text(encoding="utf-8"))
    script_b = json.loads(script_b_file.read_text(encoding="utf-8"))

    results = {}

    # 1. MESSAGE 1: Remotion Typography Master Showcase (Typography Ready for Approval)
    caption_typo = (
        "🔤 <b>GATE A: PERMANENT TYPOGRAPHY SYSTEM (REMOTION BROADCAST RENDER)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Status:</b> Ready for Editorial Approval\n"
        "🎨 <b>Font Stack:</b>\n"
        " • <b>Barlow Condensed</b> (600–900): Headlines, player reveals, transfer values (€60M)\n"
        " • <b>Inter</b> (400–800): Sentence-case subtitles (46px), lower-thirds, CTA\n"
        " • <b>IBM Plex Mono</b> (500–600): Structured kickers, categories, data labels\n\n"
        "📐 <b>Verification:</b> Rendered directly via Remotion Still CLI (Chromium headless) with 100% bundled local TTFs.\n"
        "<i>Review the attached native Remotion broadcast composition above:</i>"
    )
    markup_typo = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Typography System", "callback_data": f"typo_app_{ws.story_id}"},
                {"text": "✏️ Request Typography Changes", "callback_data": f"typo_chg_{ws.story_id}"}
            ]
        ]
    }
    print("Uploading Message 1 (Remotion Typography Showcase)...")
    with open(remotion_showcase, "rb") as f:
        r1 = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption_typo, "parse_mode": "HTML", "reply_markup": json.dumps(markup_typo)},
            files={"photo": f},
            timeout=90
        ).json()
    mid1 = r1.get("result", {}).get("message_id")
    print("  Message 1 sent. ID:", mid1)
    results["typography_showcase_mid"] = mid1

    # 2. MESSAGE 2: Clean Scene Pictures Contact Sheet (Enlarged 300x533 Photos)
    caption_chart = (
        "🖼️ <b>GATE B: SCENE PICTURES CHART (V7.1.4)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Status:</b> Visual Assets & Layout Ready for Review\n"
        "📸 <b>Photograph Priority:</b> Enlarged 300×533 previews (true 9:16 aspect ratio, no covering diagnostic boxes)\n"
        "📐 <b>Text Handling:</b> Fully wrapped lines (no word truncation)\n\n"
        "📋 <b>Verification & Rights Status:</b>\n"
        " • OpenCV crop validated (Upper-Third safe zone)\n"
        " • Source provenance verified (Wikimedia, Straits Times, Telemadrid, Football Italia)\n"
        " • <b>Semantic VLM review:</b> ⏳ PENDING (DASHSCOPE_API_KEY unconfigured)\n"
        " • <b>Commercial Rights:</b> ⚠️ Editorial reference only (Reuters, Telemadrid, Shutterstock commercial licenses unacquired)\n\n"
        "<i>Review the enlarged scene contact sheet above:</i>"
    )
    markup_chart = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Scene Visuals", "callback_data": f"visual_app_{ws.story_id}"},
                {"text": "🔄 Replace Scene Asset", "callback_data": f"visual_rep_{ws.story_id}"}
            ]
        ]
    }
    print("Uploading Message 2 (Enlarged Scene Contact Sheet)...")
    with open(chart_path, "rb") as f:
        r2 = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption_chart, "parse_mode": "HTML", "reply_markup": json.dumps(markup_chart)},
            files={"photo": f},
            timeout=90
        ).json()
    mid2 = r2.get("result", {}).get("message_id")
    print("  Message 2 sent. ID:", mid2)
    results["scene_chart_mid"] = mid2

    # 3. MESSAGE 3: Dialogue Screenplay (Script A - Refreshed Nov 23 Facts)
    msg_a_text = director.format_telegram_message_a_dialogue(script_a)
    msg_a_formatted = (
        "📝 <b>GATE C: DIALOGUE SCREENPLAY (SCRIPT A - AWAITING APPROVAL)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Status:</b> Script Awaiting Explicit User Approval\n"
        "🩺 <b>Refreshed Facts (Nov 23):</b>\n"
        " • Endrick age: <b>20 years old</b> (DOB: 2006-07-21)\n"
        " • Injury: <b>Left-leg adductor muscle injury</b> (Real Madrid official medical release; recovery timetable unestablished)\n"
        " • Milan status: Previously reported €60M inquiry; terms unformalized\n"
        " • Buy-back range: €80M–€85M explicitly <b>NOT AGREED</b>\n"
        " • Opening 4s secrecy rule strictly enforced\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        + msg_a_text
    )
    markup_script = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Script", "callback_data": f"script_app_{ws.story_id}"},
                {"text": "✏️ Request Dialogue Changes", "callback_data": f"script_chg_{ws.story_id}"}
            ]
        ]
    }
    print("Uploading Message 3 (Dialogue Screenplay)...")
    r3 = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg_a_formatted, "parse_mode": "HTML", "reply_markup": markup_script},
        timeout=30
    ).json()
    mid3 = r3.get("result", {}).get("message_id")
    print("  Message 3 sent. ID:", mid3)
    results["dialogue_script_mid"] = mid3

    # 4. MESSAGE 4: Image Key Screenplay (Script B - Part 1 and Part 2)
    msg_b_text = director.format_telegram_message_b_image_key(script_b)
    mid_point = msg_b_text.find("<b>━━━━━━━━ BEAT S04")
    part1 = (
        "📋 <b>GATE D: IMAGE KEY SCREENPLAY (SCRIPT B - PART 1)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Status:</b> Image Key Awaiting Explicit User Approval\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        + msg_b_text[:mid_point].strip()
        + "\n\n<i>(Continued in Part 2 below...)</i>"
    )
    part2 = (
        "📋 <b>GATE D: IMAGE KEY SCREENPLAY (SCRIPT B - PART 2)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        + msg_b_text[mid_point:].strip()
    )
    markup_key = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Image Key", "callback_data": f"key_app_{ws.story_id}"},
                {"text": "✏️ Request Image Key Changes", "callback_data": f"key_chg_{ws.story_id}"}
            ]
        ]
    }

    print("Uploading Message 4A (Image Key Part 1)...")
    r4a = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": part1, "parse_mode": "HTML"},
        timeout=30
    ).json()
    mid4a = r4a.get("result", {}).get("message_id")
    print("  Message 4A sent. ID:", mid4a)
    results["image_key_part1_mid"] = mid4a

    print("Uploading Message 4B (Image Key Part 2)...")
    r4b = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": part2, "parse_mode": "HTML", "reply_markup": markup_key},
        timeout=30
    ).json()
    mid4b = r4b.get("result", {}).get("message_id")
    print("  Message 4B sent. ID:", mid4b)
    results["image_key_part2_mid"] = mid4b

    return results

if __name__ == "__main__":
    res = dispatch_package()
    print("Final V7.1.4 Telegram Dispatch Results:", res)
