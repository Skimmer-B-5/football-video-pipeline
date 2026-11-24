"""
test_beta_pipeline.py - Verification suite for beta pipeline isolation.
Ensures zero pollution of production state, correct module resolution,
and independent database/storage operation.
"""

import os
import sys
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BETA_ROOT.parent

# Set beta as sys.path[0]
if str(BETA_ROOT) not in sys.path:
    sys.path.insert(0, str(BETA_ROOT))

def test_beta_root_resolution():
    """Verify that BETA_ROOT points to the beta subdirectory."""
    assert BETA_ROOT.name == "beta"
    assert (BETA_ROOT / "config" / "config.yaml").exists()
    assert (BETA_ROOT / "run_beta.py").exists()

def test_pipeline_import_isolation():
    """Verify that importing pipeline and stages resolves within beta/."""
    from pipeline.state_manager import PROJECT_ROOT, DB_PATH
    assert PROJECT_ROOT.resolve() == BETA_ROOT.resolve()
    assert DB_PATH.resolve() == (BETA_ROOT / "data" / "beta_news.db").resolve()

def test_state_manager_database_isolation():
    """Verify state manager creates and queries beta/data/beta_news.db only."""
    from pipeline.state_manager import JobState, get_db_connection, init_database
    init_database()
    assert (BETA_ROOT / "data" / "beta_news.db").exists()
    
    # Create test job
    job = JobState.create()
    assert job.job_id.startswith("beta_")
    assert job.get_status() == "INIT"
    
    job.update_status("TESTING_ISOLATION")
    assert job.get_status() == "TESTING_ISOLATION"

def test_retention_tracker_isolation():
    """Verify retention tracker writes to beta/data/beta_retention.db."""
    from pipeline.retention_tracker import RetentionTracker, DB_PATH
    assert DB_PATH.resolve() == (BETA_ROOT / "data" / "beta_retention.db").resolve()
    tracker = RetentionTracker()
    vid_id = tracker.log_video({
        "video_id": "beta_test_001",
        "story_category": "test",
        "headline": "Test Isolation Headline",
        "duration_sec": 28.5
    })
    assert vid_id == "beta_test_001"
    assert (BETA_ROOT / "data" / "beta_retention.db").exists()

def test_youtube_uploader_safety_gate():
    """Verify that beta youtube_uploader is a strict offline mock."""
    from stages.youtube_uploader import upload_video_youtube
    test_dummy = BETA_ROOT / "output" / "dummy_test.mp4"
    test_dummy.parent.mkdir(parents=True, exist_ok=True)
    test_dummy.write_text("dummy video content", encoding="utf-8")
    
    receipt = upload_video_youtube(
        video_path=test_dummy,
        title="Test Safe Video",
        script_text="Test script text",
        source_name="Test Source",
        source_url="https://test.com",
        reliability_tier="confirmed",
        allow_public=True # Should still be ignored and mocked
    )
    assert receipt["status"] == "MOCK_VERIFIED"
    assert receipt["video_id"].startswith("BETA_STAGED_")
    if test_dummy.exists():
        test_dummy.unlink()

def test_remotion_directory_structure():
    """Verify remotion directory has package.json and src/ design tokens."""
    rem_dir = BETA_ROOT / "remotion"
    assert (rem_dir / "package.json").exists()
    assert (rem_dir / "src" / "FootballShort.tsx").exists()
    assert (rem_dir / "src" / "design" / "tokens.ts").exists()

if __name__ == "__main__":
    print("Running beta isolation tests...")
    test_beta_root_resolution()
    test_pipeline_import_isolation()
    test_state_manager_database_isolation()
    test_retention_tracker_isolation()
    test_youtube_uploader_safety_gate()
    test_remotion_directory_structure()
    print("✓ All beta isolation tests passed successfully!")
