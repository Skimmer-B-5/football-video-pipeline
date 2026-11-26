"""
test_pipeline_core.py - Core Verification Suite for Promoted Main Broadcast Pipeline.
Verifies root layout resolution, database paths, uploader safety defaults, and Remotion setup.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_main_root_resolution():
    """Verify that PROJECT_ROOT points cleanly to the promoted main repository root."""
    assert (PROJECT_ROOT / "config" / "config.yaml").exists()
    assert (PROJECT_ROOT / "run_pipeline.py").exists()
    assert (PROJECT_ROOT / "run_telegram_broadcast_service.py").exists()

def test_pipeline_import_resolution():
    """Verify that importing pipeline and stages resolves cleanly at root."""
    from pipeline.state_manager import PROJECT_ROOT as SM_ROOT, DB_PATH
    assert SM_ROOT.resolve() == PROJECT_ROOT.resolve()
    assert DB_PATH.resolve() == (PROJECT_ROOT / "data" / "news.db").resolve()

def test_state_manager_database():
    """Verify state manager creates and queries data/news.db cleanly."""
    from pipeline.state_manager import JobState, init_database
    init_database()
    assert (PROJECT_ROOT / "data" / "news.db").exists()

    job = JobState.create()
    assert len(job.job_id) >= 4
    assert job.get_status() == "INIT"

    job.update_status("TESTING_CORE")
    assert job.get_status() == "TESTING_CORE"

def test_retention_tracker_database():
    """Verify retention tracker writes to data/retention.db cleanly."""
    from pipeline.retention_tracker import RetentionTracker, DB_PATH
    assert DB_PATH.resolve() == (PROJECT_ROOT / "data" / "retention.db").resolve()
    tracker = RetentionTracker()
    vid_id = tracker.log_video({
        "video_id": "main_test_001",
        "story_category": "test",
        "headline": "Test Core Headline",
        "duration_sec": 28.5
    })
    assert vid_id == "main_test_001"
    assert (PROJECT_ROOT / "data" / "retention.db").exists()

def test_youtube_uploader_private_default():
    """Verify youtube_uploader defaults to private and runs mock receipt when unconfigured."""
    from stages.youtube_uploader import upload_video_youtube
    test_dummy = PROJECT_ROOT / "output" / "dummy_test.mp4"
    test_dummy.parent.mkdir(parents=True, exist_ok=True)
    test_dummy.write_text("dummy video content", encoding="utf-8")

    receipt = upload_video_youtube(
        video_path=test_dummy,
        title="Test Safe Video",
        script_text="Test script text",
        source_name="Test Source",
        source_url="https://test.com",
        reliability_tier="confirmed",
        allow_public=False
    )
    assert receipt["privacy_status"] == "private"
    assert receipt["status"] in ("MOCK_VERIFIED", "UPLOADED")
    if test_dummy.exists():
        test_dummy.unlink()

def test_remotion_directory_structure():
    """Verify remotion directory has package.json and both main & experiment compositions."""
    rem_dir = PROJECT_ROOT / "remotion"
    assert (rem_dir / "package.json").exists()
    assert (rem_dir / "src" / "FootballShort.tsx").exists()
    assert (rem_dir / "src" / "DocumentaryPaperShort.tsx").exists()
    assert (rem_dir / "src" / "design" / "tokens.ts").exists()

if __name__ == "__main__":
    print("Running main pipeline core tests...")
    test_main_root_resolution()
    test_pipeline_import_resolution()
    test_state_manager_database()
    test_retention_tracker_database()
    test_youtube_uploader_private_default()
    test_remotion_directory_structure()
    print("✓ All main pipeline core tests passed successfully!")
