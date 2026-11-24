"""
beta/stages/dispatch_v7_1_6_telegram_package.py
Dispatches the complete V7.1.6 Review Package to Telegram:
1. Clean Remotion Typography Master Showcase & Dedicated Clean Broadcast Specimens:
   - Opening headline (1080x1920)
   - Player-name reveal (1080x1920)
   - Single-line subtitle (1080x1920)
   - Two-line subtitle (1080x1920)
   - Transfer graphic (€60M fixed + €10M bonuses / €80M-€85M buy-back / NOT AGREED)
   - Lower-third (1080x1920)
   - Outro (1080x1920)
   - PT-BR specimen (1080x1920)
   - ES-419 specimen (1080x1920)
2. Upgraded Clean Scene Contact Sheet V7.1.6 (Enlarged 300x533 photos, spoken tokens, rights breakdown)
3. Three opening candidates and selected script evaluation (Opt 1: José Mourinho tension, 6.59s secrecy)
4. Refreshed Dialogue Screenplay (Script A - V7.1.6 Reconciled Spoken Token Timing: 60 words | 64 tokens | 30.32s)
5. Refreshed Image Key Screenplay (Script B - V7.1.6 Visual Narrative Blueprints)
6. State machine invalidation to SCRIPT_REVIEW_PENDING awaiting explicit approval.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.story_workspace_manager import StoryWorkspace
from stages.telegram_bot import get_env_credentials
from stages.dual_script_architecture import DualScriptDirector
from stages.approval_state_machine import ApprovalStateMachine, PipelineState

def dispatch_package():
    ws = StoryWorkspace("endrick_milan", "run_v7_1")
    token, chat_id = get_env_credentials()
    if not token or not chat_id:
        print("Telegram credentials missing.")
        return {"status": "SKIPPED"}

    state_file = ws.state_dir / "approval_state.json"
    sm = ApprovalStateMachine(state_file, ws.story_id, ws.run_id)

    # 1. Invalidate previous script approval because dialogue has changed to V7.1.6
    print("Invalidating previous script approvals due to V7.1.6 dialogue updates...")
    sm.invalidate_downstream_on_script_change("v7.1.6", "editorial_v7_1_6_reconciliation")

    typo_dir = ws.base_dir / "typography"
    chart_path = ws.telegram_dir / "clean_scene_chart_master_v7_1_6.jpg"
    remotion_showcase = typo_dir / "typography_master_clean.png"

    specimen_files = [
        ("headline_specimen.png", "A. Opening Headline (Barlow Condensed 120px / Inter 48px)"),
        ("player_reveal_specimen.png", "B. Player Reveal (Barlow Condensed 160px / Inter 48px)"),
        ("single_line_subtitle_specimen.png", "C. Single-Line Subtitle (Inter 46px on Bernabéu night)"),
        ("two_line_subtitle_specimen.png", "D. Two-Line Subtitle (Inter 46px on Valdebebas training)"),
        ("transfer_graphic_specimen.png", "E. Transfer Graphic (€60M fixed + €10M bonuses / €80M-€85M / NOT AGREED)"),
        ("lower_third_specimen.png", "F. Broadcast Lower-Third (Barlow Condensed 68px / Inter 36px)"),
        ("outro_specimen.png", "G. Outro Plate (Barlow Condensed 80px / Inter 36px)"),
        ("pt_br_specimen.png", "H. PT-BR Typography (Full diacritics / Inter 46px subtitle)"),
        ("es_419_specimen.png", "I. ES-419 Typography (Full accents & inverted punctuation)")
    ]

    for fname, _ in specimen_files:
        p = typo_dir / fname
        if not p.exists():
            raise FileNotFoundError(f"Specimen file missing: {p}")

    director = DualScriptDirector()
    script_a_file = ws.scripts_dir / "dialogue_script.json"
    script_b_file = ws.scripts_dir / "image_key_script.json"
    script_a = json.loads(script_a_file.read_text(encoding="utf-8"))
    script_b = json.loads(script_b_file.read_text(encoding="utf-8"))

    results = {}

    # -------------------------------------------------------------
    # 1. MESSAGE 1: Remotion Typography Master Showcase
    # -------------------------------------------------------------
    caption_typo = (
        "🔤 <b>GATE A: PERMANENT TYPOGRAPHY SYSTEM (V7.1.6 BROADCAST SPECIMENS)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Status:</b> Ready for Editorial & Visual Approval\n"
        "🎨 <b>Font Stack (Locked):</b>\n"
        " • <b>Barlow Condensed</b> (600–900): Headlines, player reveals, transfer values\n"
        " • <b>Inter</b> (400–800): Sentence-case subtitles (46px), lower-thirds, CTA\n"
        " • <b>IBM Plex Mono</b> (500–600): Structured kickers, categories, data labels\n\n"
        "📐 <b>Visual Proof:</b> Rendered directly via Remotion Still CLI (Chromium headless) with 100% bundled local TTFs.\n"
        "<i>Review the Master Clean broadcast showcase attached above:</i>"
    )
    markup_typo = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Typography System", "callback_data": f"typo_app_{ws.story_id}"},
                {"text": "✏️ Request Typography Changes", "callback_data": f"typo_chg_{ws.story_id}"}
            ]
        ]
    }
    print("Uploading Message 1 (Remotion Master Showcase)...")
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

    # -------------------------------------------------------------
    # 2. MEDIA GROUP: 9 Clean 1080x1920 Remotion Broadcast Specimens
    # -------------------------------------------------------------
    print("Uploading Media Group of 9 Clean 1080x1920 Specimens...")
    media_list = []
    files_dict = {}
    for i, (fname, desc) in enumerate(specimen_files):
        var_name = f"specimen_{i}"
        files_dict[var_name] = open(typo_dir / fname, "rb")
        media_entry = {
            "type": "photo",
            "media": f"attach://{var_name}"
        }
        if i == 0:
            media_entry["caption"] = "📸 <b>REMOTION 1080×1920 BROADCAST SPECIMENS (CLEAN RENDERS A–I)</b>\nFull native frames: Headlines, Single/Two-Line Subtitles, S03 Transfer Card, Lower-Thirds & Multilingual."
            media_entry["parse_mode"] = "HTML"
        media_list.append(media_entry)

    try:
        r_group = requests.post(
            f"https://api.telegram.org/bot{token}/sendMediaGroup",
            data={"chat_id": chat_id, "media": json.dumps(media_list)},
            files=files_dict,
            timeout=120
        ).json()
        group_mids = [m.get("message_id") for m in r_group.get("result", [])]
        print(f"  Media group sent. IDs: {group_mids}")
        results["specimen_media_group_mids"] = group_mids
    finally:
        for f in files_dict.values():
            f.close()

    # -------------------------------------------------------------
    # 3. MESSAGE 3: Clean Scene Pictures Contact Sheet V7.1.6
    # -------------------------------------------------------------
    caption_chart = (
        "🖼️ <b>GATE B: SCENE PICTURES CHART (V7.1.6)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 <b>Status:</b> Visual Assets & Layout Ready for Review\n"
        "📸 <b>Photograph Priority:</b> Enlarged 300×533 previews (true 9:16 aspect ratio, zero obscuring boxes)\n"
        "📐 <b>Text Handling:</b> Fully wrapped lines in Inter (no word truncation)\n\n"
        "📋 <b>Rights Breakdown:</b>\n"
        " • <b>S01 (Bernabéu Night):</b> CC BY-SA 2.0 (Wikimedia Commons / loco085)\n"
        " • <b>S02 (Endrick Presentation):</b> Editorial Reference Only (Reuters / Straits Times)\n"
        " • <b>S03 (Transfer Structure):</b> 100% Studio Owned & Cleared Graphic\n"
        " • <b>S04 (Valdebebas Training):</b> Editorial Reference Only (Telemadrid / Real Madrid press pool)\n"
        " • <b>S05 (San Siro Matchday):</b> Editorial Reference Only (Football Italia / Shutterstock)\n"
        "⚠️ <i>Commercial licenses for Reuters, Telemadrid and Shutterstock unacquired; strictly for editorial evaluation.</i>\n\n"
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
    print("Uploading Message 3 (Enlarged Scene Contact Sheet V7.1.6)...")
    with open(chart_path, "rb") as f:
        r2 = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption_chart, "parse_mode": "HTML", "reply_markup": json.dumps(markup_chart)},
            files={"photo": f},
            timeout=90
        ).json()
    mid2 = r2.get("result", {}).get("message_id")
    print("  Message 3 sent. ID:", mid2)
    results["scene_chart_mid"] = mid2

    # -------------------------------------------------------------
    # 4. MESSAGE 4: Dialogue Screenplay (Script A - V7.1.6 Reconciled)
    # -------------------------------------------------------------
    msg_a_text = director.format_telegram_message_a_dialogue(script_a)
    markup_script = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Script", "callback_data": f"script_app_{ws.story_id}"},
                {"text": "✏️ Request Dialogue Changes", "callback_data": f"script_chg_{ws.story_id}"}
            ]
        ]
    }
    print("Uploading Message 4 (Dialogue Screenplay)...")
    r3 = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": msg_a_text, "parse_mode": "HTML", "reply_markup": markup_script},
        timeout=30
    ).json()
    mid3 = r3.get("result", {}).get("message_id")
    print("  Message 4 sent. ID:", mid3)
    results["dialogue_script_mid"] = mid3

    # -------------------------------------------------------------
    # 5. MESSAGE 5: Image Key Screenplay (Script B - Part 1 & Part 2)
    # -------------------------------------------------------------
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
        + "\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Select approval option for the proposed visual descriptions:</i>"
    )

    markup_image_key = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve Image Key", "callback_data": f"imgkey_app_{ws.story_id}"},
                {"text": "🔍 Request Image Desc Changes", "callback_data": f"imgkey_chg_{ws.story_id}"}
            ]
        ]
    }

    print("Uploading Message 5A (Image Key Part 1)...")
    r4a = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": part1, "parse_mode": "HTML"},
        timeout=30
    ).json()
    mid4a = r4a.get("result", {}).get("message_id")
    print("  Message 5A sent. ID:", mid4a)

    print("Uploading Message 5B (Image Key Part 2)...")
    r4b = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": part2, "parse_mode": "HTML", "reply_markup": markup_image_key},
        timeout=30
    ).json()
    mid4b = r4b.get("result", {}).get("message_id")
    print("  Message 5B sent. ID:", mid4b)
    results["image_key_mid"] = mid4b

    # Update state machine to SCRIPT_REVIEW_PENDING
    sm.transition_to(
        PipelineState.SCRIPT_REVIEW_PENDING,
        f"telegram_chat_{chat_id}",
        f"Dispatched V7.1.6 Package (Showcase:{mid1}, Chart:{mid2}, ScriptA:{mid3}, ScriptB:{mid4b})"
    )

    print("\n✅ V7.1.6 Telegram Package successfully dispatched.")
    return results

if __name__ == "__main__":
    dispatch_package()
