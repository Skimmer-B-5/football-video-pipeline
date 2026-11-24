"""
# PROVENANCE: Copied from pipeline/orchestrator.py and adapted for beta runtime isolation.
Main Pipeline Orchestrator for Beta Experimental Environment.
Zero production interaction: outputs to beta/output/, uses beta/data/beta_news.db,
and never publishes to YouTube.
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

CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
PYTHON_EXE = str(PROJECT_ROOT.parent / ".venv" / "Scripts" / "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

def run_stage_subprocess(module_name: str, args: Optional[list] = None) -> subprocess.CompletedProcess:
    """Executes a beta pipeline stage in an isolated subprocess with beta PYTHONPATH."""
    cmd = [PYTHON_EXE, "-m", module_name] + (args or [])
    print(f"\n[Beta-Orchestrator] >>> Launching Subprocess: {' '.join(cmd)}")
    start_t = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env)
    dur = round(time.time() - start_t, 2)

    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(f"[Subprocess Stderr]:\n{res.stderr.strip()}", file=sys.stderr)

    if res.returncode != 0:
        raise RuntimeError(f"Beta Stage '{module_name}' failed with exit code {res.returncode}")

    print(f"[Beta-Orchestrator] <<< Subprocess {module_name} finished in {dur}s (Memory freed back to OS).\n")
    return res

def resolve_cluster_article(cl: Dict[str, Any]) -> tuple:
    """Retrieve full raw_text and URL for a story cluster from beta SQLite database."""
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
        print(f"[Beta-Orchestrator] Active Job ID: {self.job.job_id} | Status: {self.job.get_status()}")

    def execute_pipeline(
        self,
        custom_story: Optional[str] = None,
        custom_url: Optional[str] = None,
        dry_run: bool = False,
        preferred_engine: Optional[str] = None
    ):
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
                print("       BETA STEP 1: NEWS INGESTION                ")
                print("==================================================")
                if custom_story or custom_url:
                    # Direct manual story injection
                    headline = custom_story if custom_story else "Breaking Football Story"
                    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
                    with get_db_connection() as conn:
                        conn.execute(
                            "INSERT OR REPLACE INTO articles (title, source, url, published_at, raw_text, scraped_at, reliability_tier, ranking_score, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (headline, "Sky Sports", custom_url or "https://bbc.com/sport/football", now_str, custom_story or headline, now_str, "confirmed", 1.0, "RANKED")
                        )
                    self.job.update_status("COLLECTED")
                    status = "COLLECTED"
                else:
                    run_stage_subprocess("stages.collector")
                    self.job.update_status("COLLECTED")
                    status = "COLLECTED"

            # Step 2: Ranking
            if status == "COLLECTED":
                print("==================================================")
                print("       BETA STEP 2: CLUSTERING & RANKING          ")
                print("==================================================")
                if not (custom_story or custom_url):
                    run_stage_subprocess("stages.ranker")
                self.job.update_status("RANKED")
                status = "RANKED"

            # Step 3: Topic Selection
            if status in ("RANKED", "TOPIC_APPROVAL_PENDING"):
                print("==================================================")
                print("       BETA STEP 3: TOPIC SELECTION               ")
                print("==================================================")
                ranking_log_file = PROJECT_ROOT / "evidence" / "ranking_log.json"
                if custom_story:
                    picked_story = {
                        "headline": custom_story[:120],
                        "source": "Sky Sports",
                        "url": custom_url or "https://bbc.com/sport/football",
                        "reliability_tier": "confirmed",
                        "raw_text": custom_story
                    }
                elif ranking_log_file.exists():
                    with open(ranking_log_file, "r", encoding="utf-8") as f:
                        top_clusters = json.load(f)
                    if top_clusters:
                        cl = top_clusters[0]
                        raw_text, art_url = resolve_cluster_article(cl)
                        picked_story = {
                            "headline": cl["headline"],
                            "source": cl["sources"][0] if cl.get("sources") else "News Outlet",
                            "url": art_url,
                            "reliability_tier": cl["tier"],
                            "raw_text": raw_text
                        }
                    else:
                        raise RuntimeError("No ranked clusters found in evidence/ranking_log.json")
                else:
                    # Fallback to direct db query
                    with get_db_connection() as conn:
                        row = conn.execute("SELECT * FROM articles ORDER BY id DESC LIMIT 1").fetchone()
                        if row:
                            picked_story = {
                                "headline": row["title"],
                                "source": row["source"],
                                "url": row["url"],
                                "reliability_tier": row["reliability_tier"] or "confirmed",
                                "raw_text": row["raw_text"] or row["title"]
                            }
                        else:
                            raise RuntimeError("No articles available in beta database.")

                print(f"[Beta-Orchestrator] Topic selected: '{picked_story['headline']}' ({picked_story['source']})")
                self.job.record_approval("TOPIC", "APPROVED", picked_story)
                self.job.update_status("TOPIC_APPROVED", topic_data=picked_story)
                status = "TOPIC_APPROVED"

            # Step 4: Script Generation & Claim Verification
            if status in ("TOPIC_APPROVED", "SCRIPT_APPROVAL_PENDING"):
                print("==================================================")
                print("       BETA STEP 4: SCRIPTING & VERIFICATION      ")
                print("==================================================")
                topic = self.job.get_record().get("topic_data")
                if isinstance(topic, str):
                    topic = json.loads(topic)

                headline = topic.get("headline", "Football Transfer Breaking News")
                source = topic.get("source", "BBC Sport")
                tier = topic.get("reliability_tier", "confirmed")
                article_text = topic.get("raw_text") or headline

                from stages.reddit_harvester import harvest_reddit_outrage
                fan_outrage = harvest_reddit_outrage(headline)

                from stages.script_generator import generate_script_llm
                current_script = generate_script_llm(
                    title=headline,
                    source_name=source,
                    article_text=article_text,
                    reliability_tier=tier,
                    fan_outrage=fan_outrage
                )

                print(f"[Beta-Orchestrator] Script generated ({current_script.get('word_count', 0)} words, {len(current_script.get('scenes', []))} scenes).")
                self.job.record_approval("SCRIPT", "APPROVED", {"script": current_script["full_text"]})
                self.job.update_status("SCRIPT_APPROVED", script_data=current_script)
                status = "SCRIPT_APPROVED"

                if dry_run:
                    print("\n[Beta-Orchestrator] --dry-run specified. Halting before asset retrieval and rendering.")
                    print("--- SCRIPT DRAFT ---")
                    print(current_script["full_text"])
                    print("\n--- SCENE PLAN ---")
                    for s in current_script.get("scenes", []):
                        print(f"[{s.get('scene_id')}] ({s.get('role')}): {s.get('narration')}")
                    return

            # Step 5 & 6: Assets & Audio Generation
            if status == "SCRIPT_APPROVED":
                print("==================================================")
                print("       BETA STEP 5 & 6: SOURCING & AUDIO          ")
                print("==================================================")
                rec = self.job.get_record()
                script_data = json.loads(rec["script_data"])
                topic = json.loads(rec["topic_data"])
                scenes_list = script_data.get("scenes", [])

                # Clean wipe intermediate assets from prior beta runs
                images_dir = PROJECT_ROOT / "data" / "images"
                images_dir.mkdir(parents=True, exist_ok=True)
                for f in images_dir.glob("scene_*.*"):
                    try:
                        f.unlink()
                    except Exception:
                        pass

                from stages.image_sourcing import source_scene_image, reset_image_registry
                from stages.tts_synthesizer import synthesize_scenes_expressive, synthesize_scenes_sapi

                reset_image_registry()
                sourced_scenes = []

                for idx, s in enumerate(scenes_list):
                    s_id = s.get("scene_id", idx + 1)
                    scene_text = s.get("narration") or s.get("text", "")
                    ent = s.get("visual", {}).get("primary_subject") or s.get("search_entity") or "Match Stills"
                    print(f"[Beta-Orchestrator] Sourcing scene {idx+1}/{len(scenes_list)}: '{ent}'...")
                    img_entry = source_scene_image(
                        scene_id=s_id,
                        headline=topic["headline"],
                        scene_text=scene_text,
                        visual_prompt=s.get("visual", {}).get("action_or_context") or s.get("visual_prompt", "football match"),
                        source_name=topic["source"],
                        backend_name="editorial",
                        search_entity=ent,
                        search_context=s.get("visual", {}).get("action_or_context") or s.get("search_context"),
                        scene_data=s
                    )
                    sc_merged = dict(s)
                    sc_merged.update({
                        "scene_id": s_id,
                        "text": scene_text,
                        "narration": scene_text,
                        "image_path": img_entry["chosen_image"],
                        "asset_manifest": img_entry.get("asset_manifest")
                    })
                    sourced_scenes.append(sc_merged)

                print("[Beta-Orchestrator] Synthesizing British Commentary Voiceover...")
                try:
                    audio_scenes = synthesize_scenes_expressive(sourced_scenes, voice_name="en-GB-ThomasNeural", rate="+0%", pitch="+0Hz")
                except Exception as e:
                    print(f"[Beta-Orchestrator] Expressive TTS error ({e}), falling back to SAPI...")
                    audio_scenes = synthesize_scenes_sapi(sourced_scenes)

                for idx, ascene in enumerate(audio_scenes):
                    sourced_scenes[idx].update({
                        "audio_path": ascene["audio_path"],
                        "audio_duration_sec": ascene["audio_duration_sec"],
                        "slide_duration_sec": ascene["slide_duration_sec"],
                        "tts_engine": ascene.get("engine", "EdgeTTS"),
                        "tts_voice": ascene.get("voice", "en-GB-ThomasNeural")
                    })

                self.job.update_status("ASSETS_SOURCED", assets_data=sourced_scenes)
                status = "ASSETS_SOURCED"

            # Step 7: Video Assembly
            if status == "ASSETS_SOURCED":
                print("==================================================")
                print("       BETA STEP 7: 90s BROADCAST RENDERING       ")
                print("==================================================")
                rec = self.job.get_record()
                assets = json.loads(rec["assets_data"])
                topic = json.loads(rec["topic_data"])

                out_video = PROJECT_ROOT / "output" / f"{self.job.job_id}_final.mp4"
                out_video.parent.mkdir(parents=True, exist_ok=True)
                rendered = False

                engine = preferred_engine or "remotion"

                if engine == "remotion":
                    try:
                        from stages.remotion_renderer import render_remotion_video
                        print("[Beta-Orchestrator] Rendering with Remotion Engine in beta/remotion...")
                        render_remotion_video(
                            assets=assets,
                            story_meta=topic,
                            output_path=out_video,
                            include_retro=True
                        )
                        rendered = True
                        print(f"[Beta-Orchestrator] Remotion master completed: {out_video}")
                    except Exception as rem_err:
                        print(f"[Beta-Orchestrator] Remotion render notice: {rem_err}. Falling back to FFmpeg assembler...")

                if not rendered:
                    from stages.video_assembler import assemble_video_ffmpeg
                    print("[Beta-Orchestrator] Rendering with FFmpeg Broadcast Assembler...")
                    assemble_video_ffmpeg(
                        scenes=assets,
                        output_mp4_path=out_video,
                        credit_source_name=topic["source"],
                        include_logo_outro=True,
                        story_headline=topic.get("headline"),
                        story_category=topic.get("category", "transfer_rumour")
                    )

                # Quality Assurance
                print("[Beta-Orchestrator] Running Beta Engine QA Suite...")
                qa_report_path = PROJECT_ROOT / "evidence" / f"{self.job.job_id}_qa_report.json"
                contact_sheet_path = PROJECT_ROOT / "evidence" / f"{self.job.job_id}_contact_sheet.jpg"
                qa_report = {}
                try:
                    from stages.qa_engine import EngineQASuite
                    qa_suite = EngineQASuite(PROJECT_ROOT)
                    total_expected_frames = round((sum(float(s.get("audio_duration_sec", 3.0)) for s in assets) + 1.40) * 30.0)
                    qa_report = qa_suite.run_full_qa(
                        video_path=Path(out_video),
                        props={
                            "scenes": assets,
                            "totalDurationInFrames": total_expected_frames,
                            "headline": topic.get("headline", ""),
                            "include_outro": True
                        },
                        output_report_path=qa_report_path,
                        contact_sheet_path=contact_sheet_path
                    )
                    print(f"[Beta-Orchestrator] QA Result: {qa_report.get('overall_status')} (Report: {qa_report_path.name})")
                except Exception as qae:
                    print(f"[Beta-Orchestrator] QA Suite notice: {qae}")

                # Retention Logging
                try:
                    from pipeline.retention_tracker import RetentionTracker
                    tracker = RetentionTracker()
                    script_data_obj = json.loads(rec["script_data"])
                    geom_info = qa_report.get("checks", {}).get("geometry", {})
                    dur_val = geom_info.get("duration_sec", 28.0)
                    tracker.log_video({
                        "video_id": self.job.job_id,
                        "story_category": topic.get("category", "general_news"),
                        "headline": topic.get("headline", ""),
                        "entities": topic.get("entities", {}),
                        "duration_sec": dur_val,
                        "hook_selected": script_data_obj.get("hook_options", {}).get("recommended", "hook_a"),
                        "hook_type": script_data_obj.get("hook_options", {}).get("recommended", "question_challenge"),
                        "hook_options": script_data_obj.get("hook_options", {}),
                        "script_word_count": len(script_data_obj.get("full_text", "").split()),
                        "visual_beats_count": len(assets),
                        "output_filename": Path(out_video).name,
                        "qa_report_summary": {
                            "status": qa_report.get("overall_status", "UNKNOWN"),
                            "lufs": qa_report.get("checks", {}).get("loudness", {}).get("integrated_lufs"),
                            "peak": qa_report.get("checks", {}).get("loudness", {}).get("true_peak_dbtp")
                        }
                    })
                except Exception as track_err:
                    print(f"[Beta-Orchestrator] Retention tracker notice: {track_err}")

                self.job.update_status("VIDEO_ASSEMBLED", video_path=str(out_video))
                status = "VIDEO_ASSEMBLED"

            # Step 8: Manual Review & Staging
            if status in ("VIDEO_ASSEMBLED", "VIDEO_APPROVAL_PENDING"):
                print("==================================================")
                print("       BETA STEP 8: PREVIEW & MANUAL REVIEW       ")
                print("==================================================")
                rec = self.job.get_record()
                video_path = rec["video_path"]
                print(f"[Beta-Orchestrator] Video ready for review: {video_path}")
                self.job.record_approval("VIDEO", "LOCAL_REVIEW_STAGED")
                self.job.update_status("VIDEO_APPROVED")
                status = "VIDEO_APPROVED"

            # Step 9: Safe Mock Publishing
            if status == "VIDEO_APPROVED":
                print("==================================================")
                print("       BETA STEP 9: PUBLISH SAFEKEEPER            ")
                print("==================================================")
                rec = self.job.get_record()
                topic = json.loads(rec["topic_data"])
                script_data = json.loads(rec["script_data"])

                from stages.youtube_uploader import upload_video_youtube
                receipt = upload_video_youtube(
                    video_path=Path(rec["video_path"]),
                    title=topic["headline"],
                    script_text=script_data.get("full_text", ""),
                    source_name=topic["source"],
                    source_url=topic.get("url", "https://bbc.com/sport/football"),
                    reliability_tier=topic["reliability_tier"],
                    allow_public=False
                )
                self.job.update_status("COMPLETED", youtube_id=receipt.get("video_id"))
                status = "COMPLETED"
                print(f"\n[Beta-Orchestrator] ✓ Beta Cycle Successfully Completed!")
                print(f"  • Output Master: {rec['video_path']}")
                print(f"  • Staged Receipt: {receipt.get('video_id')}")
                break

if __name__ == "__main__":
    orch = PipelineOrchestrator()
    orch.execute_pipeline()
