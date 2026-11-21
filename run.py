"""
CLI Dispatcher for FS 30 — Paper-Cut Football Shorts Pipeline.
Executes the complete end-to-end 8-stage pipeline per FS30 Master Prompt Pack:
  1. fetch_story
  2. write_script
  3. plan_frames
  4. fetch_assets
  5. synthesize_voice
  6. captions
  7. render
  8. preview_and_approve
"""

import argparse
import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from fs30.config import load_config, get_run_dir
from fs30.stage1_fetch_story import fetch_story
from fs30.stage2_write_script import write_script
from fs30.stage3_plan_frames import plan_frames
from fs30.stage4_fetch_assets import fetch_assets
from fs30.stage5_synthesize_voice import synthesize_all_scenes
from fs30.stage6_captions import generate_all_captions
from fs30.stage7_render import render_full_video
from fs30.stage8_telegram import send_approval_request

def setup_logger(run_dir: Path):
    log_file = run_dir / "log.txt"
    
    def log(msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{ts}] {msg}"
        print(formatted)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
            
    return log

def main():
    # Pre-process /new command-line shorthand
    if len(sys.argv) > 1 and sys.argv[1] in ["/new", "new"]:
        sys.argv.pop(1)
        if len(sys.argv) > 1 and sys.argv[1] in ["news", "story"]:
            mode_choice = sys.argv.pop(1)
            sys.argv.extend(["--mode", mode_choice])

    parser = argparse.ArgumentParser(description="FS 30 Video Engine CLI (/new dispatcher)")
    parser.add_argument("--mode", type=str, choices=["news", "story"], default="news", help="Pipeline mode: 'news' (90s reporter) or 'story' (Vox documentary)")
    parser.add_argument("--story", type=str, help="Pasted story text or path to story text file")
    parser.add_argument("--url", type=str, help="URL to football news article")
    parser.add_argument("--run", type=str, help="Run ID for runs/<run_id>/", default=None)
    parser.add_argument(
        "--stage",
        type=str,
        choices=["fetch_story", "write_script", "plan_frames", "fetch_assets", "synthesize_voice", "captions", "render", "telegram"],
        help="Execute single stage alone (news mode)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Stop after plan_frames and print formatted plan")
    parser.add_argument("--skip-telegram", action="store_true", help="Skip Telegram upload step")

    args = parser.parse_args()

    t_start = time.time()
    run_id = args.run or f"run_{time.strftime('%Y%m%d_%H%M%S')}"
    run_dir = get_run_dir(run_id)
    log = setup_logger(run_dir)
    config = load_config()

    log("===========================================================================")
    log(f"  FS 30 FOOTBALL VIDEO ENGINE | MODE: {args.mode.upper()} | RUN: {run_id}")
    log("===========================================================================")

    # ROUTING: Story Pipeline vs News Pipeline
    if args.mode == "story":
        from fs30.story_pipeline.runner import run_story_pipeline
        src = args.url or args.story
        result = run_story_pipeline(story_input=src, run_dir=run_dir, log_func=log)
        return

    # NEWS PIPELINE (90s Aesthetic News Reporter - Unmodified)

    # Handle isolated single stage execution
    if args.stage:
        if args.stage == "fetch_story":
            src = args.url or args.story
            if not src:
                log("Error: --url or --story is required for fetch_story")
                sys.exit(1)
            fetch_story(src, run_dir, log_func=log)

        elif args.stage == "write_script":
            story_file = run_dir / "story.json"
            if not story_file.exists():
                log(f"Error: {story_file} not found. Run fetch_story first.")
                sys.exit(1)
            with open(story_file, "r", encoding="utf-8") as f:
                story_data = json.load(f)
            write_script(story_data, run_dir, config=config, log_func=log)

        elif args.stage == "plan_frames":
            script_file = run_dir / "script.json"
            if not script_file.exists():
                log(f"Error: {script_file} not found. Run write_script first.")
                sys.exit(1)
            with open(script_file, "r", encoding="utf-8") as f:
                script_data = json.load(f)
            plan_frames(script_data, run_dir, config=config, dry_run=args.dry_run, log_func=log)

        elif args.stage == "fetch_assets":
            plan_file = run_dir / "plan.json"
            if not plan_file.exists():
                log(f"Error: {plan_file} not found. Run plan_frames first.")
                sys.exit(1)
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            fetch_assets(plan_data, run_dir, log_func=log)

        elif args.stage == "synthesize_voice":
            plan_file = run_dir / "plan.json"
            script_file = run_dir / "script.json"
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            with open(script_file, "r", encoding="utf-8") as f:
                script_data = json.load(f)
            synthesize_all_scenes(script_data, plan_data, run_dir, config=config, log_func=log)

        elif args.stage == "captions":
            plan_file = run_dir / "plan.json"
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            generate_all_captions(plan_data, run_dir, log_func=log)

        elif args.stage == "render":
            plan_file = run_dir / "plan.json"
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            assets_dir = run_dir / "assets"
            resolved_assets = {f.stem: f for f in assets_dir.glob("*.png")}
            audio_dir = run_dir / "audio"
            audio_results = {}
            for sc in plan_data.get("scenes", []):
                sid = sc.get("id")
                audio_results[sid] = {
                    "audio_path": audio_dir / f"scene_{sid}.wav",
                    "duration": sc.get("est_seconds", 4.0)
                }
            caption_files = generate_all_captions(plan_data, run_dir, log_func=log)
            render_full_video(plan_data, resolved_assets, audio_results, caption_files, run_dir, log_func=log)

        elif args.stage == "telegram":
            master_mp4 = run_dir / "final_fs30_master.mp4"
            with open(run_dir / "story.json", "r", encoding="utf-8") as f:
                story_data = json.load(f)
            with open(run_dir / "script.json", "r", encoding="utf-8") as f:
                script_data = json.load(f)
            send_approval_request(master_mp4, story_data, script_data, run_id, config=config, log_func=log)

        log(f"✓ Single stage '{args.stage}' completed.")
        return

    # Full End-to-End Pipeline Execution
    src = args.url or args.story
    if not src:
        if (run_dir / "story.json").exists():
            log(f"Re-using existing story.json in {run_dir}")
            with open(run_dir / "story.json", "r", encoding="utf-8") as f:
                story_data = json.load(f)
        else:
            log("Error: Must provide --story or --url")
            sys.exit(1)
    else:
        story_data = fetch_story(src, run_dir, log_func=log)

    # Stage 2: Write Script (re-use if existing run specified without new story)
    script_file = run_dir / "script.json"
    if not src and script_file.exists():
        log(f"Re-using existing validated script.json in {run_dir}")
        with open(script_file, "r", encoding="utf-8") as f:
            script_data = json.load(f)
    else:
        script_data = write_script(story_data, run_dir, config=config, log_func=log)

    # Stage 3: Plan Frames
    plan_file = run_dir / "plan.json"
    if not src and plan_file.exists():
        log(f"Re-using existing validated plan.json in {run_dir}")
        with open(plan_file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    else:
        plan_data = plan_frames(script_data, run_dir, config=config, dry_run=args.dry_run, log_func=log)

    if args.dry_run:
        log("Dry run requested. Stopping after plan_frames.")
        return

    # Stage 4: Fetch Assets + Cutout Quality Gate
    resolved_assets = fetch_assets(plan_data, run_dir, log_func=log)

    # Stage 5: Synthesize Voice (Qwen3-TTS Calm Narrative)
    audio_results = synthesize_all_scenes(script_data, plan_data, run_dir, config=config, log_func=log)

    # Stage 6: Captions (Paper-style cards in safe zone)
    caption_files = generate_all_captions(plan_data, run_dir, log_func=log)

    # Stage 7: Render 1080x1920 2.5D Paper-Cut Video
    master_mp4 = render_full_video(plan_data, resolved_assets, audio_results, caption_files, run_dir, log_func=log)

    # Stage 8: Telegram Approval
    tel_result = None
    if not args.skip_telegram:
        tel_result = send_approval_request(master_mp4, story_data, script_data, run_id, config=config, log_func=log)

    total_time = time.time() - t_start

    # Final telemetry report
    report = {
        "run_id": run_id,
        "status": "COMPLETED",
        "story_headline": story_data.get("headline"),
        "script_title": script_data.get("title"),
        "word_count": script_data.get("word_count"),
        "scenes_count": len(plan_data.get("scenes", [])),
        "assets_count": len(resolved_assets),
        "total_render_duration_sec": sum(sc.get("est_seconds", 0) for sc in plan_data.get("scenes", [])) + 2.0,
        "execution_time_sec": round(total_time, 2),
        "telegram_delivery": tel_result,
        "master_video_path": str(master_mp4.resolve())
    }
    with open(run_dir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    log("===========================================================================")
    log(f"  ✓ COMPLETE FS 30 PIPELINE MASTERED SUCCESSFULLY!")
    log(f"  • Video: {master_mp4}")
    log(f"  • Duration: {report['total_render_duration_sec']:.1f}s | Size: {master_mp4.stat().st_size // 1024} KB")
    log(f"  • Total Pipeline Time: {total_time:.1f}s")
    log("===========================================================================")

if __name__ == "__main__":
    main()
