"""
run_beta.py - Isolated CLI Dispatcher for 30 Football Plus Beta Pipeline.

Executes within the isolated beta/ sandbox:
- Zero production database pollution (uses beta/data/beta_news.db).
- Zero production output overwriting (saves to beta/output/).
- Zero YouTube publishing (staged safely for local inspection).
- Independent configuration and state tracking.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path

# Lock beta/ as the primary import root
BETA_ROOT = Path(__file__).resolve().parent
if str(BETA_ROOT) not in sys.path:
    sys.path.insert(0, str(BETA_ROOT))

# Load beta-specific environment variables if present
beta_env = BETA_ROOT / ".env"
if beta_env.exists():
    with open(beta_env, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

os.environ["BETA_ACTIVE"] = "1"

# Ensure all essential beta directories exist
for d in ["data", "data/audio", "data/images", "logs", "output", "evidence", "cache"]:
    (BETA_ROOT / d).mkdir(parents=True, exist_ok=True)

from pipeline.state_manager import JobState, init_database
from pipeline.orchestrator import PipelineOrchestrator

def setup_beta_logger(job_id: str):
    logs_dir = BETA_ROOT / "logs"
    log_file = logs_dir / f"{job_id}.log"
    
    def log(msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{ts}][BETA] {msg}"
        print(formatted)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
            
    return log

def main():
    parser = argparse.ArgumentParser(description="30 Football Plus — Isolated Beta Pipeline Runner")
    parser.add_argument("--story", type=str, help="Pasted news story text or headline")
    parser.add_argument("--url", type=str, help="Direct news article URL")
    parser.add_argument("--auto", action="store_true", help="Auto-select top ranked story from feeds")
    parser.add_argument("--job", type=str, default=None, help="Specific job ID to resume or assign")
    parser.add_argument("--dry-run", action="store_true", help="Stop after script and frame planning")
    parser.add_argument("--engine", type=str, choices=["remotion", "ffmpeg"], default="remotion", help="Video render engine (default: remotion)")
    parser.add_argument(
        "--stage",
        type=str,
        choices=["collector", "ranker", "script", "sourcing", "audio", "render", "qa", "all"],
        default="all",
        help="Execute a specific stage in isolation"
    )

    args = parser.parse_args()

    t_start = time.time()
    init_database()

    job = JobState(args.job) if args.job else JobState.create()
    log = setup_beta_logger(job.job_id)

    log("===========================================================================")
    log(f"  30 FOOTBALL PLUS | ISOLATED BETA PIPELINE | JOB: {job.job_id}")
    log(f"  • Root: {BETA_ROOT}")
    log(f"  • Render Engine: {args.engine.upper()} | Stage: {args.stage.upper()}")
    log(f"  • Production Safe: YES (Zero production writes, zero YouTube publish)")
    log("===========================================================================")

    orch = PipelineOrchestrator(job=job)

    if args.stage == "all":
        orch.execute_pipeline(
            custom_story=args.story,
            custom_url=args.url,
            dry_run=args.dry_run,
            preferred_engine=args.engine
        )
    elif args.stage == "collector":
        from stages.collector import poll_all_feeds
        poll_all_feeds()
        log("✓ Collector completed.")
    elif args.stage == "ranker":
        from stages.ranker import run_ranking_pipeline
        run_ranking_pipeline()
        log("✓ Ranker completed.")
    elif args.stage == "script":
        from stages.script_generator import generate_script_llm
        title = args.story or "Real Madrid Agree Terms for Trent Alexander-Arnold"
        res = generate_script_llm(title=title, source_name="Beta Direct", article_text=title, reliability_tier="confirmed")
        out_f = BETA_ROOT / "evidence" / f"{job.job_id}_script.json"
        out_f.write_text(json.dumps(res, indent=2), encoding="utf-8")
        log(f"✓ Script generated and saved to {out_f.name}")
    elif args.stage == "qa":
        out_vid = BETA_ROOT / "output" / f"{job.job_id}_final.mp4"
        if out_vid.exists():
            from stages.qa_engine import EngineQASuite
            qa = EngineQASuite(BETA_ROOT)
            rep = qa.run_full_qa(out_vid, {}, BETA_ROOT / "evidence" / f"{job.job_id}_qa.json")
            log(f"✓ QA completed: {rep.get('overall_status')}")
        else:
            log(f"Cannot run QA: {out_vid} not found.")

    total_t = round(time.time() - t_start, 2)
    log(f"Beta run completed in {total_t}s.")

if __name__ == "__main__":
    main()
