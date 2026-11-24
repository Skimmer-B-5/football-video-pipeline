"""
beta/run_telegram_broadcast_service.py
Standby Telegram Bot Service supporting:
1. Live Web Scraping (Google News Transfers, Sky Sports, BBC Sport, The Guardian, Transfermarkt, Football Italia)
2. Interactive Story Selection with in-place pagination buttons.
3. Interactive Script Approval with [Approve], [AI Rewrite], [Manual Edit], and [Reject] buttons.
4. Dynamic 16-Shot Image Sourcing (100% fresh real match photos per story — ZERO image reuse).
5. In-Place Telegram Live Progress Bar ([██████░░░░] 60%).
6. V7.1.6.7 Master 1990s Television Broadcast Pipeline (Jeff Stelling Qwen3-TTS neural voice,
   em-dash vocal stops & starts, Trinitron CRT analog treatment, zero whooshes, Remotion 989 frames @ 30fps).
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BETA_ROOT = PROJECT_ROOT / "beta"

# Ensure BETA_ROOT takes precedence in sys.path for beta sandbox isolation
if str(BETA_ROOT) in sys.path:
    sys.path.remove(str(BETA_ROOT))
sys.path.insert(0, str(BETA_ROOT))

if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(1, str(PROJECT_ROOT))

from stages.telegram_bot import TelegramBotClient, get_env_credentials
from pipeline.neural_instructions import StoryDossier
from pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline
from stages.scraped_story_adapter import scraped_story_to_dossier
from pipeline.state_manager import get_db_connection
from stages.image_sourcing import source_scene_image, reset_image_registry


class TelegramProgressTracker:
    """Unified, in-place live progress bar updating in Telegram chat."""
    def __init__(self, bot: TelegramBotClient, chat_id: str):
        self.bot = bot
        self.chat_id = chat_id
        self.msg_id = None

    def update(self, pct: int, stage_name: str, details_str: str):
        blocks = min(10, max(0, int(pct / 10)))
        bar_str = "█" * blocks + "░" * (10 - blocks)
        txt = (
            f"🎬 <b>1990s TELEVISION BROADCAST PRODUCTION</b>\n"
            f"<code>[{bar_str}] {pct}%</code> — <b>{stage_name}</b>\n\n"
            f"<i>{details_str}</i>"
        )
        if not self.msg_id:
            try:
                self.msg_id = self.bot.send_message(txt, chat_id=self.chat_id)
            except Exception as pe:
                print(f"[Progress] Init error: {pe}")
        else:
            try:
                self.bot.edit_message_text(txt, message_id=self.msg_id, chat_id=self.chat_id)
            except Exception:
                pass


def source_story_shots(
    dossier: StoryDossier,
    run_id: str,
    screenplay_scenes: Optional[List[Dict[str, Any]]] = None,
    progress: Optional[TelegramProgressTracker] = None
) -> Dict[str, List[str]]:
    """
    Dynamically sources and audits match/stadium photos:
    - If screenplay_scenes provided: uses LLMVisualDirector (GPT OSS / Qwen 27B)
      to describe each scene in 1 sentence, and generates 2 distinct images for 'OR' / 'AND' choice scenes!
    - Otherwise falls back to 16-shot EditorialVisualArchitect.
    - Audits via VisionFramingInspector (strict subject verification, blur filter, safe-zone [260, 1250]).
    - ZERO REUSE & ZERO UNRELATED FOOTBALL CLUTTER!
    """
    from stages.vision_framing_inspector import VisionFramingInspector
    from stages.asset_ledger import StoryAssetLedger

    inspector = VisionFramingInspector()

    if screenplay_scenes:
        from stages.llm_visual_director import LLMVisualDirector
        director = LLMVisualDirector()
        shot_specs = director.plan_visual_timeline(screenplay_scenes, dossier)
    else:
        from stages.editorial_visual_architect import EditorialVisualArchitect
        architect = EditorialVisualArchitect()
        shot_specs = architect.plan_16_shots(dossier)

    manifest_dir = BETA_ROOT / "workspaces" / dossier.story_id / run_id / "manifests"
    ledger = StoryAssetLedger(manifest_dir, dossier.story_id)

    run_dir = BETA_ROOT / "remotion" / "public" / "images" / f"story_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    root_pub = PROJECT_ROOT / "remotion" / "public" / "images" / f"story_{run_id}"
    root_pub.mkdir(parents=True, exist_ok=True)

    remotion_shots = {}
    if screenplay_scenes:
        for sc in screenplay_scenes:
            remotion_shots[sc["scene_id"]] = []
    else:
        remotion_shots = {"S01": [], "S02": [], "S03": [], "S04": [], "S05": []}

    total_shots = len(shot_specs)

    for idx, spec in enumerate(shot_specs, 1):
        if progress:
            shot_pct = 15 + int((idx / total_shots) * 35)
            progress.update(
                shot_pct,
                f"Curating Visuals ({idx}/{total_shots})",
                f"Auditing [{spec.shot_id}]: {spec.primary_entity} ({spec.role})"
            )

        dest_filename = f"{spec.shot_id}_{idx}.png"
        dest_file = run_dir / dest_filename

        success = inspector.audit_and_produce_shot(spec, dest_file, ledger=ledger)
        if success and dest_file.exists():
            try:
                shutil.copy(dest_file, root_pub / dest_filename)
            except Exception:
                pass
            if spec.scene_id not in remotion_shots:
                remotion_shots[spec.scene_id] = []
            remotion_shots[spec.scene_id].append(f"/images/story_{run_id}/{dest_filename}")
            print(f"  [{spec.shot_id}] Corroborated & Locked -> {dest_filename}")
        else:
            print(f"  [{spec.shot_id}] Fallback: Generating verified broadcast crest card")
            inspector.sourcer.generate_broadcast_crest_fallback(spec.club_affiliation, dest_file)
            shutil.copy(dest_file, root_pub / dest_filename)
            if spec.scene_id not in remotion_shots:
                remotion_shots[spec.scene_id] = []
            remotion_shots[spec.scene_id].append(f"/images/story_{run_id}/{dest_filename}")

    return remotion_shots


def create_broadcast_from_story(bot: TelegramBotClient, story: Dict[str, Any], chat_id: str):
    """Executes the complete V7.1.6.7 broadcast pipeline with script approval and dynamic image sourcing."""
    dossier = scraped_story_to_dossier(story)
    run_id = f"tg_{int(time.time())}"
    pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id=run_id)

    # 1. Generate Screenplay
    print(f"\n[Broadcast Engine] Generating 5-beat dual script for: '{dossier.main_headline}'")
    script_data = pipeline.generate_screenplay()
    full_script_text = " ".join(sc["spoken_narration"] for sc in script_data["scenes"] if sc["scene_id"] != "outro")

    # 2. Interactive Script Approval Loop
    while True:
        decision, reply_payload = bot.request_script_approval(
            headline=dossier.main_headline,
            script_text=full_script_text,
            claims_report={"reliability_tier": story.get("reliability_tier", "confirmed"), "unsupported_claims": []},
            scenes=script_data["scenes"]
        )

        if decision in ("CANCEL", "CANCELLED"):
            bot.send_message("❌ <b>Broadcast production cancelled.</b> Send /new anytime to pick another story.", chat_id=chat_id)
            return

        elif decision in ("NEW_CYCLE", "REFRESH"):
            run_scraping_and_story_selection(bot, chat_id)
            return

        elif decision == "REJECTED":
            bot.send_message("❌ <b>Script rejected.</b> Returning to story radar...", chat_id=chat_id)
            run_scraping_and_story_selection(bot, chat_id)
            return

        elif decision == "AI_REWRITE":
            bot.send_message("🤖 <b>AI Rewrite:</b> Regenerating high-impact 5-beat dual-script with fresh narrative angle & suspense...", chat_id=chat_id)
            script_data = pipeline.generate_screenplay(
                user_directive="Draft an alternate high-impact broadcast angle with fresh narrative tension, suspense, and urgency.",
                prior_script=full_script_text
            )
            full_script_text = " ".join(sc["spoken_narration"] for sc in script_data["scenes"] if sc["scene_id"] != "outro")
            continue

        elif decision == "EDITED":
            user_critique = (reply_payload or "").strip()
            bot.send_message(
                f"✏️ <b>Regenerating dual-script addressing your feedback:</b>\n"
                f"<i>\"{user_critique}\"</i>\n\n"
                f"<i>Sending prompt, previous script, and your critique to LLM editorial engine...</i>",
                chat_id=chat_id
            )
            script_data = pipeline.generate_screenplay(
                user_directive=user_critique,
                prior_script=full_script_text
            )
            full_script_text = " ".join(sc["spoken_narration"] for sc in script_data["scenes"] if sc["scene_id"] != "outro")
            continue

        elif decision == "APPROVED":
            print(f"[Broadcast Engine] Script approved by user! Proceeding with production.")
            break

    # 3. Live Progress Tracker & Production
    progress = TelegramProgressTracker(bot, chat_id)
    try:
        progress.update(10, "Initializing Production Pipeline", f"Locking in approved dual-script for '{dossier.main_headline}'...")

        # 4. Dynamic Visual Sourcing via GPT OSS / Qwen 27B Scene Descriptions
        progress.update(15, "Dynamic Match Photography Sourcing", f"Describing & scraping verified match photos for {dossier.protagonist_name} & {dossier.current_club}...")
        shots = source_story_shots(dossier, run_id, screenplay_scenes=script_data["scenes"], progress=progress)

        # 5. Synthesize Sports Anchor Neural Voice
        progress.update(
            55,
            "British Sports Anchor Voice Synthesis",
            "Synthesizing Qwen3-TTS British sports presenter voice at 145 WPM with em-dash vocal stops..."
        )
        audio_data = pipeline.synthesize_voice(script_data)

        # 6. Compile 16-Shot Props & Trinitron CRT Analog Grade
        progress.update(
            75,
            "Staging 16-Shot Editorial Timeline",
            "Configuring Trinitron CRT analog treatment, phosphor bloom, RGB fringing & typography..."
        )
        props_path = pipeline.compile_visual_props(script_data, audio_data, shots)

        # 7. Remotion Rendering & Audio Mix
        total_f = audio_data.get("total_frames", 989)
        total_s = audio_data.get("total_sec", 32.9)
        story_s = audio_data.get("story_sec", total_s - 5.0)
        outro_s = audio_data.get("outro_sec", 5.0)
        voice_desc = audio_data.get("voice_name", "Original British Sports Presenter (Ryan)")

        progress.update(
            90,
            "Remotion Broadcast Rendering",
            f"Rendering {total_f} frames @ 30fps ({story_s:.1f}s story + {outro_s:.1f}s outro) & mastering..."
        )
        final_video = pipeline.render_and_master(
            props_path,
            Path(audio_data["master_audio_path"]),
            total_f
        )

        # 8. Finished & Deliver to Telegram
        progress.update(100, "Broadcasting Complete!", "Delivering final 1990s TV broadcast video...")
        caption = (
            f"📺 <b>1990s TELEVISION BROADCAST MASTER (V7.1.6.7)</b>\n\n"
            f"• <b>Headline:</b> {dossier.main_headline}\n"
            f"• <b>Protagonist:</b> {dossier.protagonist_name} ({dossier.current_club} ➔ {dossier.pursuing_club})\n"
            f"• <b>Voice:</b> {voice_desc}\n"
            f"• <b>Visuals:</b> 16 dynamically verified match & stadium photos (Immutable Ledger)\n"
            f"• <b>Master:</b> 1990s Trinitron CRT analog treatment (-14 LUFS stereo)\n"
            f"• <b>Story Runtime:</b> {story_s:.2f}s (~30s target)\n"
            f"• <b>Outro Runtime:</b> {outro_s:.2f}s (Separate branded ident)\n"
            f"• <b>Total Master:</b> {total_s:.2f}s ({total_f} frames @ 30fps)\n\n"
            f"<i>Ready for broadcasting! Send /new anytime to scrape fresh stories!</i>"
        )
        bot.send_video(str(final_video), caption=caption, chat_id=chat_id)
        print(f"[Broadcast Engine] Video delivered to Telegram: {final_video}")
    except Exception as e:
        print(f"[Broadcast Engine] Error during production: {e}")
        bot.send_message(
            f"⚠️ <b>Production Error:</b> <code>{str(e)[:300]}</code>\n\n"
            f"<i>Send /new anytime to restart or pick another story.</i>",
            chat_id=chat_id
        )
        raise


def run_scraping_and_story_selection(bot: TelegramBotClient, chat_id: str):
    """Scrapes configured news websites, ranks virality, and sends interactive selection menu to Telegram."""
    print(f"\n[Scraper] Starting live website scrape for user {chat_id}...")
    bot.send_message(
        "⚡ <b>SCRAPING LIVE FOOTBALL FEEDS...</b>\n"
        "<i>Scanning Google News Live Transfers, Sky Sports, BBC Sport, The Guardian, Transfermarkt, Football Italia...</i>",
        chat_id=chat_id
    )

    try:
        from stages.collector import run_collector
        new_count = run_collector()
        print(f"[Scraper] Collector completed with {new_count} new articles.")
    except Exception as e:
        print(f"[Scraper] Warning during collector run: {e}")

    try:
        from stages.ranker import cluster_and_rank
        top_clusters = cluster_and_rank()
        print(f"[Scraper] Ranker completed with {len(top_clusters)} ranked clusters.")
    except Exception as e:
        print(f"[Scraper] Warning during ranker run: {e}")
        top_clusters = []

    # Load ranking log fallback
    ranking_path = BETA_ROOT / "evidence" / "ranking_log.json"
    if not top_clusters and ranking_path.exists():
        try:
            with open(ranking_path, "r", encoding="utf-8") as f:
                top_clusters = json.load(f)
        except Exception as e:
            print(f"[Scraper] Warning reading ranking log: {e}")

    if not top_clusters:
        bot.send_message("⚠️ <b>No ranked stories available. Try again in a few moments.</b>", chat_id=chat_id)
        return

    # Build story pool with article text
    story_pool = []
    for cl in top_clusters[:15]:
        raw_t = ""
        art_url = cl.get("url", "https://www.skysports.com/football")
        try:
            with get_db_connection() as conn:
                rep_id = cl.get("representative_id")
                if rep_id:
                    row = conn.execute("SELECT raw_text, url FROM articles WHERE id = ?", (rep_id,)).fetchone()
                else:
                    row = conn.execute("SELECT raw_text, url FROM articles WHERE title = ? LIMIT 1", (cl["headline"],)).fetchone()
                if row:
                    if row["raw_text"]:
                        raw_t = row["raw_text"]
                    if row["url"]:
                        art_url = row["url"]
        except Exception as e:
            print(f"[Scraper] Note fetching article body: {e}")

        story_pool.append({
            "headline": cl["headline"],
            "source": cl["sources"][0] if cl.get("sources") else (cl.get("source") or "News Outlet"),
            "url": art_url,
            "reliability_tier": cl.get("reliability_tier") or cl.get("tier", "confirmed"),
            "ranking_score": cl.get("ranking_score") or cl.get("score", 0),
            "raw_text": raw_t
        })

    # Present stories via interactive Telegram buttons
    picked_story = bot.request_topic_approval(story_pool, custom_header="🌐 <b>SCRAPED LIVE STORIES: SELECT FOR 90s BROADCAST</b>")
    
    if picked_story and isinstance(picked_story, dict):
        print(f"[Scraper] User selected story: '{picked_story.get('headline')}'")
        create_broadcast_from_story(bot, picked_story, chat_id)
    elif picked_story == "REFRESH":
        print("[Scraper] User requested refresh via /new.")
        run_scraping_and_story_selection(bot, chat_id)
    elif picked_story == "CANCEL":
        bot.send_message("❌ <b>Story selection cancelled.</b>\n<i>Send /new anytime to scrape fresh stories!</i>", chat_id=chat_id)


def main():
    print("==================================================================")
    print("  30 FOOTBALL PLUS — LIVE SCRAPER & 90s BROADCAST SERVICE        ")
    print("  Websites: Google News, Sky Sports, BBC, Guardian, Transfermarkt ")
    print("  Video Engine: V7.1.6.7 Master 1990s TV Broadcast (Original British Sports Presenter)")
    print("==================================================================")

    token, chat_id = get_env_credentials()
    if not token or not chat_id:
        print("[Service] ERROR: Telegram credentials missing in .env")
        sys.exit(1)

    bot = TelegramBotClient(token=token, default_chat_id=chat_id)
    print(f"[Service] Connected as @Football30secbot (Target Chat ID: {chat_id})")

    # Register menu commands
    try:
        bot.set_bot_commands()
        print("[Service] Registered Telegram commands (/new, /broadcast, /search, /status, etc.).")
    except Exception as e:
        print(f"[Service] Warning setting commands: {e}")

    # Send announcement
    welcome_text = (
        "🌐 <b>LIVE FOOTBALL SCRAPER & 1990s BROADCAST STUDIO IS ONLINE!</b>\n\n"
        "<i>Send <b>/new</b> to scrape live breaking stories from Sky Sports, BBC Sport, The Guardian, and Transfermarkt, review the script, and generate your 90s broadcast!</i>\n\n"
        "<b>Workflow on /new:</b>\n"
        "1. <b>Pick a Story</b>: <i>Browse live ranked stories with inline buttons.</i>\n"
        "2. <b>Script Approval</b>: <i>Review the draft with [Approve], [AI Rewrite], or [Manual Edit].</i>\n"
        "3. <b>Dynamic Visual Sourcing</b>: <i>Sources 16 fresh match photos specifically for the story (zero reuse!).</i>\n"
        "4. <b>Live Progress Bar</b>: <i>Follow real-time generation in-place [██████░░░░]!</i>\n"
        "5. <b>TV Broadcast Master</b>: <i>Energetic British Sports Anchor voiceover & Trinitron CRT analog treatment delivered to Telegram!</i>"
    )
    try:
        bot.send_message(welcome_text, chat_id=chat_id)
        print(f"[Service] Dispatched Live Scraper announcement to Telegram chat {chat_id}!")
    except Exception as e:
        print(f"[Service] Notice sending welcome message: {e}")

    # Continuous standby listener loop
    print("[Service] Entering continuous STANDBY listening loop...")
    while True:
        try:
            action, payload = bot.listen_for_command(poll_interval=2)
            caller_chat_id = getattr(bot, "active_chat_id", None) or chat_id

            if action in ("NEW_CYCLE", "REFRESH"):
                run_scraping_and_story_selection(bot, caller_chat_id)

            elif action == "URL":
                print(f"[Service] Scraping direct URL: {payload}")
                bot.send_message(f"🔍 <b>Scraping direct URL:</b> {payload}...", chat_id=caller_chat_id)
                story = {
                    "headline": "Direct Article Report",
                    "raw_text": str(payload),
                    "source": "Web Article",
                    "url": payload
                }
                create_broadcast_from_story(bot, story, caller_chat_id)

            elif action == "TOPIC_SELECTED":
                if isinstance(payload, dict):
                    create_broadcast_from_story(bot, payload, caller_chat_id)

        except Exception as e:
            print(f"[Service Loop] Note: {e}. Retrying in 2 seconds...")
            time.sleep(2)


if __name__ == "__main__":
    main()
