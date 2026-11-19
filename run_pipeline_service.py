"""
Autonomous Pipeline Service Runner with Full Telegram Remote Control.
Runs standalone on the host machine with zero Antigravity token overhead.
Features:
1. Full Telegram Commands: /new, /status, /cancel, /help, and direct URL scraping.
2. Standby Mode: Stays alive while laptop is open; launches fresh cycles on /new from phone.
3. Rapid 7-8 Scene Videos: Cynical tactician script, high-energy British commentary.
4. Automated See-Back & Self-Healing audit after video generation.
5. Zero Button Lag: Instant callback acknowledgment and in-place message updates.
"""

import sys
import os
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.orchestrator import PipelineOrchestrator
from pipeline.state_manager import JobState, get_db_connection
from stages.telegram_bot import TelegramBotClient, get_env_credentials

def main():
    print("=" * 65)
    print("  FOOTBALL IN 30 SECONDS - AUTONOMOUS PIPELINE SERVICE  ")
    print("  Engine: Qwen Cynical Tactician | Remote Telegram Studio ")
    print("=" * 65)

    token, chat_id = get_env_credentials()
    if not token or not chat_id:
        print("[Service] ERROR: Telegram credentials missing in .env")
        sys.exit(1)

    bot = TelegramBotClient(token=token, default_chat_id=chat_id)
    print(f"[Service] Connected to Telegram as @Football30secbot (Chat ID: {chat_id})")

    # 1. Register Telegram UI Commands (/new, /status, /cancel, /help)
    try:
        bot.set_bot_commands()
        print("[Service] Successfully registered Telegram bot commands.")
    except Exception as e:
        print(f"[Service] Warning: Could not register menu commands: {e}")

    # 2. Check for unfinished active job to resume or clean standby
    active_job = JobState.get_latest_active_job()
    if active_job:
        job_status = active_job.get_status()
        print(f"[Service] Resuming active unfinished job: {active_job.job_id} (Status: {job_status})")
        try:
            bot.send_message(
                f"🔄 <b>RESUMING UNFINISHED JOB</b>\n\n"
                f"Job ID: <code>{active_job.job_id}</code>\n"
                f"Status: <b>{job_status}</b>\n\n"
                f"<i>Picking up pipeline execution right where it was paused...</i>"
            )
            orch = PipelineOrchestrator(job=active_job)
            orch.execute_pipeline(skip_telegram=False)
            if active_job.get_status() == "COMPLETED":
                bot.send_message("⚡ <b>CYCLE FINISHED</b>\n<i>Standing by. Send /new anytime to launch the next video!</i>")
        except Exception as re:
            print(f"[Service] Resume execution note: {re}")
    else:
        print("[Service] No pending unfinished jobs. Studio initialized in pure STANDBY mode.")

    startup_msg = (
        "🧠 <b>QWEN IS ONLINE & LISTENING</b>\n\n"
        "<i>Your automated YouTube Shorts studio is live on your laptop. You can now launch and control everything directly from your phone:</i>\n\n"
        "⚡ <b>/new</b> — <i>Scan live feeds, cluster trending topics, and launch a fresh video cycle</i>\n"
        "💬 <b>/chat [question]</b> — <i>Ask Qwen tactical opinions, debates & queries</i>\n"
        "📊 <b>/status</b> — <i>Check active job status and laptop GPU/RAM</i>\n"
        "❌ <b>/cancel</b> — <i>Abort and archive the active cycle</i>\n"
        "❓ <b>/help</b> — <i>Display tactical command manual</i>\n\n"
        "🔗 <i>Or paste any football news URL directly in chat to turn it into an 8-scene Short!</i>"
    )
    try:
        bot.send_message(startup_msg)
    except Exception as e:
        print(f"[Service] Startup greeting note: {e}")

    # 3. Continuous standby listener loop
    while True:
        try:
            # Standby mode: Wait for user's /new command, URL, or Qwen chat questions from phone
            action, payload = bot.listen_for_command(poll_interval=2)

            if action == "NEW_CYCLE":
                caller_chat_id = getattr(bot, "active_chat_id", None)
                print(f"\n[Service] User {caller_chat_id} triggered /new from phone! Launching fresh pipeline cycle...")
                # Archive any previous jobs so the new job starts 100% fresh
                with get_db_connection() as conn:
                    conn.execute("UPDATE jobs SET status = 'ARCHIVED' WHERE status NOT IN ('COMPLETED', 'ARCHIVED', 'FAILED', 'CANCELLED')")
                    conn.commit()
                fresh_job = JobState.create()
                orch = PipelineOrchestrator(job=fresh_job)
                try:
                    orch.execute_pipeline(skip_telegram=False, caller_chat_id=caller_chat_id)
                    if fresh_job.get_status() == "COMPLETED":
                        print("[Service] Cycle completed! Returning to standby...")
                        bot.send_message("⚡ <b>CYCLE FINISHED</b>\n<i>Standing by. Send /new anytime to launch the next video!</i>", chat_id=caller_chat_id)
                    else:
                        print(f"[Service] Cycle ended with non-completed status: {fresh_job.get_status()}")
                except Exception as ce:
                    print(f"[Service] Cycle error: {ce}")

            elif action == "TOPIC_SELECTED" and payload:
                caller_chat_id = getattr(bot, "active_chat_id", None)
                picked_story = payload
                headline = picked_story.get("headline", "Football Breaking News")
                print(f"\n[Service] User {caller_chat_id} selected story via /search: {headline}! Launching cycle...")
                with get_db_connection() as conn:
                    conn.execute("UPDATE jobs SET status = 'ARCHIVED' WHERE status NOT IN ('COMPLETED', 'ARCHIVED', 'FAILED', 'CANCELLED')")
                    conn.commit()
                fresh_job = JobState.create()
                orch = PipelineOrchestrator(job=fresh_job)
                
                art_text = picked_story.get("article_text") or picked_story.get("raw_text", "")
                art_url = picked_story.get("url", "")
                if len(art_text.split()) < 35 and art_url and not art_url.startswith("https://news.google.com"):
                    try:
                        from stages.url_scraper import scrape_article_from_url
                        scraped = scrape_article_from_url(art_url)
                        if scraped and scraped.get("text") and len(scraped["text"].split()) > 35:
                            art_text = scraped["text"]
                    except Exception as se:
                        print(f"[Service] Scrape note for search result: {se}")

                topic = {
                    "headline": headline,
                    "source": picked_story.get("source", "Web"),
                    "url": art_url,
                    "reliability_tier": picked_story.get("reliability_tier", "rumour"),
                    "raw_text": art_text
                }
                orch.job.record_approval("TOPIC", "APPROVED", topic)
                orch.job.update_status("TOPIC_APPROVED", topic_data=topic)
                orch.execute_pipeline(skip_telegram=False, caller_chat_id=caller_chat_id)
                try:
                    bot.send_message("⚡ <b>SEARCH STORY SHORT COMPLETED!</b>\n<i>Send /search or /new anytime to launch another video.</i>", chat_id=caller_chat_id)
                except Exception:
                    pass

            elif action == "URL" and payload:
                caller_chat_id = getattr(bot, "active_chat_id", None)
                print(f"\n[Service] User {caller_chat_id} provided custom URL: {payload}! Launching targeted cycle...")
                with get_db_connection() as conn:
                    conn.execute("UPDATE jobs SET status = 'ARCHIVED' WHERE status NOT IN ('COMPLETED', 'ARCHIVED', 'FAILED', 'CANCELLED')")
                    conn.commit()
                fresh_job = JobState.create()
                orch = PipelineOrchestrator(job=fresh_job)
                # Store URL into custom pipeline run
                from stages.url_scraper import scrape_article_from_url
                scraped = scrape_article_from_url(payload)
                if not scraped or not scraped.get("title"):
                    bot.send_message("❌ <b>Could not extract article content from that link.</b>\n<i>Please verify the link or send /new to browse trending stories.</i>", chat_id=caller_chat_id)
                    continue
                topic = {
                    "headline": scraped.get("title", "Football Breaking News"),
                    "source": scraped.get("source", "Web"),
                    "url": scraped.get("url", payload),
                    "reliability_tier": scraped.get("reliability_tier", "rumour"),
                    "raw_text": scraped.get("raw_text", "")
                }
                orch.job.update_status("TOPIC_APPROVED", topic_data=topic)
                orch.execute_pipeline(skip_telegram=False, caller_chat_id=caller_chat_id)
                try:
                    bot.send_message("⚡ <b>CUSTOM STORY SHORT COMPLETED!</b>\n<i>Send /new to launch another video.</i>", chat_id=caller_chat_id)
                except Exception:
                    pass

        except Exception as e:
            print(f"[Service] Error in service loop: {e}")
            try:
                bot.send_message(f"⚠️ <b>Notice:</b> <i>{e}</i>\n<i>Restarting listener in 15 seconds...</i>")
            except Exception:
                pass
            time.sleep(15)

if __name__ == "__main__":
    main()
