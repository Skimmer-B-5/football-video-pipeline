"""
Main Pipeline Orchestrator.
Plain Python control flow managing subprocess lifecycles, memory tracking,
and persistent SQLite state machine with Telegram mobile approvals.
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.state_manager import JobState, get_db_connection
from pipeline.resource_monitor import ResourceTracker, get_vram_usage, get_system_ram
from stages.telegram_bot import TelegramBotClient, get_env_credentials

CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
PYTHON_EXE = str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

def run_stage_subprocess(module_name: str, args: Optional[list] = None) -> subprocess.CompletedProcess:
    """Executes a pipeline stage in a dedicated subprocess to ensure complete memory release upon exit."""
    cmd = [PYTHON_EXE, "-m", module_name] + (args or [])
    print(f"\n[Orchestrator] >>> Launching Subprocess: {' '.join(cmd)}")
    start_t = time.time()
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    dur = round(time.time() - start_t, 2)

    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(f"[Subprocess Stderr]:\n{res.stderr.strip()}", file=sys.stderr)

    if res.returncode != 0:
        raise RuntimeError(f"Stage '{module_name}' failed with exit code {res.returncode}")

    print(f"[Orchestrator] <<< Subprocess {module_name} finished in {dur}s (Memory freed back to OS).\n")
    return res

def resolve_cluster_article(cl: Dict[str, Any]) -> tuple:
    """Retrieve full raw_text and URL for a story cluster from SQLite database."""
    rep_id = cl.get("representative_id")
    raw_t = cl.get("raw_text", "")
    art_url = cl.get("url", "https://www.besoccer.com/news")
    with get_db_connection() as conn:
        if rep_id:
            row = conn.execute("SELECT raw_text, url FROM articles WHERE id = ?", (rep_id,)).fetchone()
        else:
            row = conn.execute("SELECT raw_text, url FROM articles WHERE title = ? LIMIT 1", (cl["headline"],)).fetchone()
        if row:
            if row["raw_text"]:
                raw_t = row["raw_text"]
            if row["url"]:
                art_url = row["url"]
    return raw_t, art_url

class PipelineOrchestrator:
    def __init__(self, job: Optional[JobState] = None):
        self.job = job or JobState.get_latest_active_job() or JobState.create()
        self.progress_msg_id = None
        print(f"[Orchestrator] Active Job ID: {self.job.job_id} | Initial Status: {self.job.get_status()}")

    def update_progress(self, bot_client, caller_chat_id: Optional[str], pct: int, stage_name: str, details_str: str):
        """Unified, persistent live progress bar updating in Telegram chat."""
        if not bot_client:
            return
        blocks = min(10, max(0, int(pct / 10)))
        bar_str = "█" * blocks + "░" * (10 - blocks)
        txt = (
            f"🎬 <b>VIDEO GENERATION IN PROGRESS</b>\n"
            f"<code>[{bar_str}] {pct}%</code> — <b>{stage_name}</b>\n\n"
            f"<i>{details_str}</i>"
        )
        if not self.progress_msg_id:
            try:
                self.progress_msg_id = bot_client.send_message(txt, chat_id=caller_chat_id)
            except Exception as pe:
                print(f"[Orchestrator] Progress bar initialization error: {pe}")
        else:
            try:
                bot_client.edit_message_text(txt, message_id=self.progress_msg_id, chat_id=caller_chat_id)
            except Exception:
                pass

    def execute_pipeline(self, skip_telegram: bool = False, caller_chat_id: Optional[str] = None):
        skip_telegram = skip_telegram or os.environ.get("SKIP_TELEGRAM", "0") == "1" or "--auto" in sys.argv or "--skip-telegram" in sys.argv
        token, chat_id = get_env_credentials()
        primary_chat = caller_chat_id or chat_id
        bot_client = None if skip_telegram else (TelegramBotClient(token=token, default_chat_id=primary_chat) if token and primary_chat else None)
        if bot_client and caller_chat_id:
            bot_client.active_chat_id = caller_chat_id

        try:
            self._execute_stages(bot_client=bot_client, caller_chat_id=caller_chat_id)
        except Exception as e:
            import traceback
            err_msg = f"{type(e).__name__}: {str(e)}"
            print(f"[Orchestrator] PIPELINE RUNTIME ERROR: {err_msg}")
            traceback.print_exc()
            self.job.update_status("FAILED", error_message=err_msg)
            if bot_client:
                try:
                    bot_client.send_message(
                        f"🚨 <b>Pipeline Stage Error:</b>\n<code>{err_msg[:300]}</code>\n\nJob ID: <code>{self.job.job_id}</code>\nStatus marked as FAILED.",
                        chat_id=caller_chat_id
                    )
                except Exception:
                    pass
            raise

    def _execute_stages(self, bot_client: Optional[TelegramBotClient], caller_chat_id: Optional[str]):
        status = self.job.get_status()
        loop_guard = 0
        max_loop_iterations = 25

        while status != "COMPLETED":
            loop_guard += 1
            if loop_guard > max_loop_iterations:
                raise RuntimeError(f"Pipeline loop limit exceeded ({max_loop_iterations} iterations). Current status: {status}")
            # Step 1: Collection
            if status in ("INIT", "UNKNOWN"):
                print("==================================================")
                print("           STEP 1: NEWS COLLECTION                ")
                print("==================================================")
                run_stage_subprocess("stages.collector")
                self.job.update_status("COLLECTED")
                status = "COLLECTED"

            # Step 2: Ranking
            if status == "COLLECTED":
                print("==================================================")
                print("           STEP 2: STORY CLUSTERING & RANKING     ")
                print("==================================================")
                run_stage_subprocess("stages.ranker")
                self.job.update_status("RANKED")
                status = "RANKED"

            # Step 3: Phone Approval 1 (Topic Selection)
            if status in ("RANKED", "TOPIC_APPROVAL_PENDING"):
                print("==================================================")
                print("      STEP 3: PHONE APPROVAL 1 (TOPIC SELECTION)  ")
                print("==================================================")
                self.job.update_status("TOPIC_APPROVAL_PENDING")

                with open(PROJECT_ROOT / "evidence" / "ranking_log.json", "r", encoding="utf-8") as f:
                    top_clusters = json.load(f)

                if not top_clusters:
                    raise RuntimeError("No ranked stories available for topic approval.")

                if bot_client:
                    # Format full pool of stories with raw_text for Telegram pagination
                    story_pool = []
                    for cl in top_clusters[:15]:
                        raw_t, art_url = resolve_cluster_article(cl)
                        story_pool.append({
                            "headline": cl["headline"],
                            "source": cl["sources"][0] if cl.get("sources") else "News Outlet",
                            "url": art_url,
                            "reliability_tier": cl["tier"],
                            "ranking_score": cl["score"],
                            "raw_text": raw_t
                        })
                    picked_story = bot_client.request_topic_approval(story_pool)
                    if picked_story == "REFRESH":
                        print("[Orchestrator] User requested refresh during topic selection. Re-ranking stories...")
                        self.job.update_status("COLLECTED")
                        status = "COLLECTED"
                        continue
                    elif picked_story == "CANCEL":
                        print("[Orchestrator] Job cancelled by user.")
                        self.job.update_status("CANCELLED")
                        return
                    elif not picked_story or not isinstance(picked_story, dict):
                        print("[Orchestrator] Topic skipped or invalid. Terminating job.")
                        self.job.update_status("SKIPPED")
                        return
                else:
                    print("[Orchestrator] Direct execution mode. Auto-selecting #1 ranked story.")
                    cl = top_clusters[0]
                    raw_text, art_url = resolve_cluster_article(cl)
                    picked_story = {
                        "headline": cl["headline"],
                        "source": cl["sources"][0] if cl.get("sources") else "News Outlet",
                        "url": art_url,
                        "reliability_tier": cl["tier"],
                        "raw_text": raw_text
                    }

                self.job.record_approval("TOPIC", "APPROVED", picked_story)
                self.job.update_status("TOPIC_APPROVED", topic_data=picked_story)
                status = "TOPIC_APPROVED"

            # Step 4: Script Generation & Claim Checker
            if status in ("TOPIC_APPROVED", "SCRIPT_APPROVAL_PENDING"):
                print("==================================================")
                print("       STEP 4: SCRIPT GENERATION & CLAIM CHECK    ")
                print("==================================================")
                topic = self.job.get_record().get("topic_data")
                if isinstance(topic, str):
                    topic = json.loads(topic)

                headline = topic.get("headline", "Football Transfer Breaking News")
                source = topic.get("source", "BBC Sport")
                tier = topic.get("reliability_tier", "confirmed")

                # Check if custom link already provided raw_text
                article_text = topic.get("raw_text")
                if not article_text:
                    with get_db_connection() as conn:
                        row = conn.execute("SELECT raw_text FROM articles WHERE title = ? LIMIT 1", (headline,)).fetchone()
                        if row and row["raw_text"]:
                            article_text = row["raw_text"]
                        else:
                            article_text = headline

                # Guard: Insufficient evidence check (min 35 words required)
                word_count = len(article_text.split()) if article_text else 0
                if word_count < 35:
                    err_msg = f"Insufficient evidence for topic '{headline}': article text has only {word_count} words (< 35 required). Generation stopped."
                    print(f"[Orchestrator] ERROR: {err_msg}")
                    if bot_client:
                        bot_client.send_message(f"⚠️ <b>Generation halted:</b> Insufficient article evidence ({word_count} words). Please select a story with full reporting.")
                    self.job.update_status("FAILED", error_message=err_msg)
                    return

                # Upgrade 4: Reddit Outrage Harvester - weaponize fan debates
                from stages.reddit_harvester import harvest_reddit_outrage
                fan_outrage = harvest_reddit_outrage(headline)

                # Execute LLM Script Generation
                from stages.script_generator import generate_script_llm
                current_script = generate_script_llm(
                    title=headline,
                    source_name=source,
                    article_text=article_text,
                    reliability_tier=tier,
                    fan_outrage=fan_outrage
                )

                # Step 4.5: Phone Approval (Script Approval with interactive revision loop)
                script_rejected = False
                while True:
                    self.job.update_status("SCRIPT_APPROVAL_PENDING")
                    if bot_client:
                        decision, reply_payload = bot_client.request_script_approval(
                            headline, current_script["full_text"], current_script.get("claim_report", {}), scenes=current_script.get("scenes")
                        )
                        if decision in ("NEW_CYCLE", "REFRESH"):
                            print("[Orchestrator] User requested /new during script approval. Restarting fresh cycle...")
                            self.job.update_status("ARCHIVED")
                            self.job = JobState.create()
                            status = "INIT"
                            script_rejected = True
                            break
                        elif decision == "REJECTED":
                            print("[Orchestrator] Script rejected by user. Returning to topic selection.")
                            bot_client.send_message("❌ <b>Script rejected.</b> Returning to story selection so you can pick another topic...")
                            self.job.update_status("RANKED")
                            status = "RANKED"
                            script_rejected = True
                            break
                        elif decision == "AI_REWRITE":
                            rewrite_counter = getattr(self, "_ai_rewrite_count", 0) + 1
                            self._ai_rewrite_count = rewrite_counter
                            print(f"[Orchestrator] User requested AI Rewrite #{rewrite_counter}...")
                            ai_directive = (
                                f"Rewrite this script from a fresh alternate tactical angle (revision #{rewrite_counter}). "
                                "Plan 5 to 8 dynamic scenes matching narrative beats. Provide deep tactical and squad analysis grounded in evidence, "
                                "and end on a provocative YES/NO debate question."
                            )
                            current_script = generate_script_llm(
                                title=headline,
                                source_name=source,
                                article_text=article_text,
                                reliability_tier=tier,
                                user_directive=ai_directive
                            )
                            continue
                        elif decision == "EDITED":
                            user_directive = reply_payload
                            print(f"[Orchestrator] User requested script revision: {user_directive}")
                            bot_client.send_message(
                                f"🔄 <b>Re-generating script incorporating your instructions:</b>\n"
                                f"<i>\"{user_directive}\"</i>\n\n"
                                f"<i>Generating new 7-scene rapid draft...</i>"
                            )
                            current_script = generate_script_llm(
                                title=headline,
                                source_name=source,
                                article_text=article_text,
                                reliability_tier=tier,
                                user_directive=user_directive
                            )
                            continue
                        elif decision == "APPROVED":
                            print("[Orchestrator] Script approved by user.")
                            self.job.record_approval("SCRIPT", "APPROVED", {"script": current_script["full_text"]})
                            script_data = current_script
                            break
                    else:
                        print("[Orchestrator] Telegram credentials not configured. Script approved by default.")
                        script_data = current_script
                        break

                if script_rejected:
                    continue

                self.job.update_status("SCRIPT_APPROVED", script_data=script_data)
                status = "SCRIPT_APPROVED"

            # Step 5 & 6: Sourcing Visuals & Audio
            if status == "SCRIPT_APPROVED":
                print("==================================================")
                print("       STEP 5 & 6: ASSETS & AUDIO GENERATION      ")
                print("==================================================")
                rec = self.job.get_record()
                script_data = json.loads(rec["script_data"])
                topic = json.loads(rec["topic_data"])
                headline = topic.get("headline", "Football Breaking News")
                scenes_list = script_data.get("scenes", [])
                total_scenes = max(1, len(scenes_list))

                self.update_progress(bot_client, caller_chat_id, 10, "Auditing Visual Assets", f"Scanning candidate match stills for {total_scenes} scenes...")

                # 1. Clean wipe all old images from previous runs so they NEVER leak into new videos!
                images_dir = PROJECT_ROOT / "data" / "images"
                if images_dir.exists():
                    for old_f in images_dir.glob("scene_*.*"):
                        try:
                            old_f.unlink()
                        except Exception:
                            pass
                temp_ass = PROJECT_ROOT / "data" / "temp_assembly"
                if temp_ass.exists():
                    for old_f in temp_ass.glob("scene_*.*"):
                        try:
                            old_f.unlink()
                        except Exception:
                            pass

                # 2. Web Editorial Sourcing: Zero AI quota reliance, 100% real match photos
                print("[Orchestrator] Web Editorial Sourcing Engine Active: Scrapes real match & press photos (No quotas).")

                from stages.image_sourcing import source_scene_image, reset_image_registry
                from stages.tts_synthesizer import synthesize_scenes_expressive, synthesize_scenes_sapi

                # Reset visual registries for clean cycle
                reset_image_registry()

                # Sourcing visual images per scene with candidate auditing & metadata preservation
                sourced_scenes = []
                for idx, s in enumerate(scenes_list):
                    s_id = s.get("scene_id", idx + 1)
                    scene_pct = 15 + int(((idx + 1) / total_scenes) * 45)
                    scene_text = s.get("narration") or s.get("text", "")
                    ent = s.get("visual", {}).get("primary_subject") or s.get("search_entity") or "Match Stills"
                    self.update_progress(
                        bot_client,
                        caller_chat_id,
                        scene_pct,
                        f"Auditing Visuals (Scene {idx + 1}/{total_scenes})",
                        f"Auditing candidates for '{ent}' | Evaluating temporal relevance & sharpness..."
                    )
                    img_entry = source_scene_image(
                        scene_id=s_id,
                        headline=topic["headline"],
                        scene_text=scene_text,
                        visual_prompt=s.get("visual", {}).get("action_or_context") or s.get("visual_prompt", "football stadium"),
                        source_name=topic["source"],
                        backend_name="editorial",
                        search_entity=ent,
                        search_context=s.get("visual", {}).get("action_or_context") or s.get("search_context"),
                        scene_data=s
                    )
                    
                    # Safe copy/merge to preserve all Schema v2.0 fields
                    sc_merged = dict(s)
                    sc_merged.update({
                        "scene_id": s_id,
                        "text": scene_text,
                        "narration": scene_text,
                        "image_path": img_entry["chosen_image"],
                        "asset_manifest": img_entry.get("asset_manifest")
                    })
                    sourced_scenes.append(sc_merged)

                # Synthesize Audio via expressive neural British commentator voice
                self.update_progress(bot_client, caller_chat_id, 65, "British Voiceover Narration", "Synthesizing expressive British anchor audio & broadcast mastering...")
                try:
                    audio_scenes = synthesize_scenes_expressive(sourced_scenes, voice_name="en-GB-ThomasNeural", rate="+0%", pitch="+0Hz")
                except Exception as e:
                    print(f"[Orchestrator] Expressive neural TTS failed ({e}), falling back to offline SAPI...")
                    audio_scenes = synthesize_scenes_sapi(sourced_scenes)

                for idx, ascene in enumerate(audio_scenes):
                    sourced_scenes[idx].update({
                        "audio_path": ascene["audio_path"],
                        "audio_duration_sec": ascene["audio_duration_sec"],
                        "slide_duration_sec": ascene["slide_duration_sec"],
                        "tts_engine": ascene.get("engine", "EdgeTTS-Thomas"),
                        "tts_voice": ascene.get("voice", "en-GB-ThomasNeural")
                    })

                self.job.update_status("ASSETS_SOURCED", assets_data=sourced_scenes)
                status = "ASSETS_SOURCED"

            # Step 7: Video Assembly (FFmpeg)
            if status == "ASSETS_SOURCED":
                print("==================================================")
                print("           STEP 7: FFMPEG VIDEO ASSEMBLY          ")
                print("==================================================")
                rec = self.job.get_record()
                assets = json.loads(rec["assets_data"])
                topic = json.loads(rec["topic_data"])

                self.update_progress(bot_client, caller_chat_id, 80, "90s TV Broadcast Rendering", "Applying CRT scanlines, 3D beveled logo bug, lower thirds & crossfades...")

                out_video = PROJECT_ROOT / "evidence" / f"{self.job.job_id}_final.mp4"
                rendered = False
                try:
                    from stages.remotion_renderer import render_remotion_video
                    print(f"[Orchestrator] Rendering 90s broadcast short with Remotion engine...")
                    render_remotion_video(
                        assets=assets,
                        story_meta=topic,
                        output_path=out_video,
                        include_retro=True
                    )
                    rendered = True
                    print(f"[Orchestrator] ✓ Remotion rendering succeeded: {out_video}")
                except Exception as rem_err:
                    print(f"[Orchestrator] Remotion render failed ({rem_err}), falling back to FFmpeg assembler...")

                if not rendered:
                    from stages.video_assembler import assemble_video_ffmpeg
                    assemble_video_ffmpeg(
                        scenes=assets,
                        output_mp4_path=out_video,
                        credit_source_name=topic["source"],
                        include_logo_outro=True,
                        story_headline=topic.get("headline")
                    )

                # Audit final video with See-Back and Self-Healing
                self.update_progress(bot_client, caller_chat_id, 95, "Video Quality Verification", "Running See-Back verification and visual integrity audit...")

                from stages.see_back import inspect_and_heal_video
                from stages.verify_video import inspect_video

                see_back_report = inspect_and_heal_video(out_video, scenes=assets)
                inspect_video(out_video, scenes=assets)

                self.update_progress(bot_client, caller_chat_id, 100, "Rendering Complete", "Packaging video with viral titles and description...")

                self.job.update_status("VIDEO_ASSEMBLED", video_path=str(out_video))
                status = "VIDEO_ASSEMBLED"

            # Step 8: Phone Approval 2 (Video Preview)
            if status in ("VIDEO_ASSEMBLED", "VIDEO_APPROVAL_PENDING"):
                print("==================================================")
                print("       STEP 8: PHONE APPROVAL 2 (VIDEO PREVIEW)   ")
                print("==================================================")
                rec = self.job.get_record()
                video_path = rec["video_path"]
                topic = json.loads(rec["topic_data"])

                self.job.update_status("VIDEO_APPROVAL_PENDING")
                publish_approved = True

                from stages.youtube_uploader import format_description
                script_data = json.loads(rec["script_data"])
                desc_text = format_description(
                    story_title=topic["headline"],
                    script_text=script_data.get("full_text", ""),
                    source_name=topic["source"],
                    source_url=topic.get("url", "https://www.besoccer.com/news"),
                    reliability_tier=topic["reliability_tier"]
                )

                if bot_client:
                    publish_approved = bot_client.request_video_approval(
                        video_path,
                        topic["headline"],
                        description=desc_text,
                        pinned_comment=script_data.get("pinned_comment"),
                        viral_titles=script_data.get("viral_titles")
                    )
                    if not publish_approved:
                        print("[Orchestrator] Video publication rejected by user. Returning to topic selection.")
                        bot_client.send_message("❌ <b>Video rejected.</b> Returning to story selection so you can pick a different topic...")
                        self.job.update_status("RANKED")
                        status = "RANKED"
                        continue

                self.job.record_approval("VIDEO", "PUBLISH_APPROVED" if publish_approved else "REJECTED")
                self.job.update_status("VIDEO_APPROVED")
                status = "VIDEO_APPROVED"

            # Step 9: YouTube Upload
            if status == "VIDEO_APPROVED":
                print("==================================================")
                print("           STEP 9: YOUTUBE UPLOAD                 ")
                print("==================================================")
                rec = self.job.get_record()
                topic = json.loads(rec["topic_data"])
                script_data = json.loads(rec["script_data"])

                allow_public_upload = False
                try:
                    import yaml
                    if CONFIG_PATH.exists():
                        with open(CONFIG_PATH, "r", encoding="utf-8") as yf:
                            cfg = yaml.safe_load(yf) or {}
                            allow_public_upload = cfg.get("youtube", {}).get("allow_public_upload", False)
                except Exception:
                    pass

                from stages.youtube_uploader import upload_video_youtube
                receipt = upload_video_youtube(
                    video_path=Path(rec["video_path"]),
                    title=topic["headline"],
                    script_text=script_data.get("full_text", ""),
                    source_name=topic["source"],
                    source_url=topic.get("url", "https://bbc.com/sport/football"),
                    reliability_tier=topic["reliability_tier"],
                    allow_public=allow_public_upload
                )

                upload_status = receipt.get("status")
                video_id = receipt.get("video_id")
                if upload_status in ("UPLOADED", "MOCK_VERIFIED") and video_id:
                    self.job.update_status("COMPLETED", youtube_id=video_id)
                    status = "COMPLETED"
                    print(f"[Orchestrator] Pipeline complete! Video ID: {video_id} (Status: {upload_status})")
                    break
                else:
                    err = receipt.get("error") or f"Upload failed with status: {upload_status}"
                    self.job.update_status("FAILED", error_message=err)
                    raise RuntimeError(f"YouTube upload failed: {err}")

if __name__ == "__main__":
    orch = PipelineOrchestrator()
    orch.execute_pipeline()
