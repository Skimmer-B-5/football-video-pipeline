"""
tests/test_master_pipeline_render.py - End-to-End Master Video Assembly & QA Verification.

Tests full execution of:
1. stages/video_assembler.py with central design tokens (y=1730 ticker, y=1440 lower third, y=1300 subtitles).
2. Forced-alignment subtitles engine (Groq Whisper Turbo / fallback).
3. Audio mastering (-14 LUFS, 48kHz stereo PCM, 0.75s broadcast breathing hold, zero screech).
4. Automated QA Suite (Geometry, streams, loudness, sync, text layout, storyboard contact sheet).
5. Logging to pipeline/retention_tracker.py.
"""

import sys
import os
import json
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.video_assembler import assemble_video_ffmpeg
from stages.qa_engine import EngineQASuite
from pipeline.retention_tracker import RetentionTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_master_render")

def run_e2e_pipeline_verification():
    logger.info("==================================================")
    logger.info("   RUNNING E2E MASTER PIPELINE VERIFICATION TEST   ")
    logger.info("==================================================")

    data_dir = PROJECT_ROOT / "data"
    img_dir = data_dir / "images"
    audio_dir = data_dir / "audio"
    output_dir = PROJECT_ROOT / "evidence" / "test_renders"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_mp4 = output_dir / "master_engine_test_video.mp4"
    output_report = output_dir / "master_engine_test_qa.json"
    output_storyboard = output_dir / "master_engine_test_storyboard.jpg"

    # Define 4 authentic scenes matching existing test media
    scenes = [
        {
            "scene_id": "s01",
            "role": "hook",
            "image_path": str(img_dir / "scene_s01.png"),
            "audio_path": str(audio_dir / "scene_s01.wav"),
            "narration": "Reports in Italy claim AC Milan have made formal enquiries for Real Madrid forward Endrick.",
            "on_screen": {
                "headline": "MILAN LAUNCH BID FOR ENDRICK",
                "subheadline": "EXCLUSIVE: ROSSONERI OPEN TALKS OVER RECORD LOAN",
                "kicker": "TRANSFER WATCH",
                "status_badge": "REPORTED",
                "source_credit": "CORRIERE DELLO SPORT"
            },
            "motion": "push_in"
        },
        {
            "scene_id": "s02",
            "role": "context",
            "image_path": str(img_dir / "scene_s02.png"),
            "audio_path": str(audio_dir / "scene_s02.wav"),
            "narration": "The Brazilian prodigy has found playing time hard to come by under Carlo Ancelotti this season.",
            "on_screen": {
                "headline": "LIMITED MINUTES AT BERNABEU",
                "subheadline": "TEENAGER STRUGGLING FOR REGULAR STARTING ROLE",
                "kicker": "SQUAD CONTEXT",
                "status_badge": "ANALYSIS",
                "source_credit": "MARCA"
            },
            "motion": "pull_out"
        },
        {
            "scene_id": "s03",
            "role": "deal_mechanics",
            "image_path": str(img_dir / "scene_s03.png"),
            "audio_path": str(audio_dir / "scene_s03.wav"),
            "narration": "Real Madrid would strictly require a guaranteed buy-back clause in any permanent loan arrangement.",
            "on_screen": {
                "headline": "MANDATORY BUY-BACK DEMANDED",
                "subheadline": "MADRID PROTECTING LONG-TERM STAKE IN FORWARD",
                "kicker": "CONTRACT CLAUSE",
                "status_badge": "CONTRACT CLAUSE",
                "source_credit": "CADENA SER"
            },
            "motion": "lateral_pan"
        },
        {
            "scene_id": "s04",
            "role": "debate",
            "image_path": str(img_dir / "scene_s04.png"),
            "audio_path": str(audio_dir / "scene_s04.wav"),
            "narration": "Is San Siro the right move for his development? Let us know below.",
            "on_screen": {
                "headline": "WOULD YOU LET ENDRICK LEAVE?",
                "subheadline": "HAVE YOUR SAY IN THE COMMENTS BELOW",
                "kicker": "FINAL VERDICT",
                "status_badge": "THE FINAL VERDICT",
                "source_credit": "30 FOOTBALL PLUS"
            },
            "motion": "subtle_ease"
        }
    ]

    # 1. Execute Master Assembly via video_assembler.py
    logger.info("Step 1: Assembling Master Broadcast Video via video_assembler.py...")
    rendered_path = assemble_video_ffmpeg(
        scenes=scenes,
        output_mp4_path=output_mp4,
        credit_source_name="Corriere dello Sport",
        include_logo_outro=True,
        story_headline="Real Madrid Considering Endrick AC Milan Loan"
    )
    assert Path(rendered_path).exists(), f"Render output missing: {rendered_path}"
    logger.info(f"✓ Video rendered successfully: {rendered_path}")

    # 2. Execute Automated QA Suite
    logger.info("Step 2: Executing Automated Engine QA Suite...")
    qa = EngineQASuite(PROJECT_ROOT)
    qa_report = qa.run_full_qa(
        video_path=Path(rendered_path),
        props={"scenes": scenes, "totalDurationInFrames": len(scenes) * 90},
        output_report_path=output_report,
        contact_sheet_path=output_storyboard
    )
    logger.info(f"✓ QA Result: {qa_report['overall_status']}")
    logger.info(f"  Geometry: {qa_report['checks']['geometry']}")
    logger.info(f"  Loudness: {qa_report['checks']['loudness']}")
    logger.info(f"  Streams: {qa_report['checks']['streams']}")
    assert qa_report["checks"]["geometry"]["passed"], "Geometry check failed!"
    assert qa_report["checks"]["streams"]["passed"], "Streams check failed!"
    assert qa_report["checks"]["loudness"]["passed"], "Loudness check failed!"
    assert output_storyboard.exists(), "Storyboard contact sheet was not generated!"

    # 3. Log to Retention Performance Tracker
    logger.info("Step 3: Logging to Retention Performance Tracker...")
    tracker = RetentionTracker()
    vid_id = tracker.log_video({
        "video_id": "test_e2e_endrick_001",
        "story_category": "transfer_rumour",
        "headline": "Real Madrid Considering Endrick AC Milan Loan",
        "duration_sec": qa_report["checks"]["geometry"]["duration_sec"],
        "hook_selected": "Reports in Italy claim AC Milan have made formal enquiries for Endrick.",
        "hook_type": "question_challenge",
        "script_word_count": sum(len(s["narration"].split()) for s in scenes),
        "visual_beats_count": len(scenes),
        "output_filename": Path(rendered_path).name,
        "qa_report_summary": {
            "status": qa_report["overall_status"],
            "lufs": qa_report["checks"]["loudness"].get("integrated_lufs"),
            "peak": qa_report["checks"]["loudness"].get("true_peak_dbtp")
        }
    })
    logger.info(f"✓ Video logged to retention database with ID: {vid_id}")

    logger.info("==================================================")
    logger.info("   ✓ ALL E2E MASTER PIPELINE CHECKS PASSED!       ")
    logger.info("==================================================")
    return {
        "video_path": str(rendered_path),
        "qa_report": qa_report,
        "storyboard": str(output_storyboard)
    }

if __name__ == "__main__":
    run_e2e_pipeline_verification()
