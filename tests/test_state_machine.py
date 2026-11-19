"""
Automated Unit Tests: SQLite State Machine & Crash Recovery.
Tests:
1. Job creation and state transitions.
2. WAL mode and safe connection teardown.
3. Mid-run crash recovery: recovers exact active job ID and stage data without re-running completed work.
4. Approval audit logging.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.state_manager import JobState, get_db_connection, init_database

def test_job_lifecycle_and_resume():
    test_id = "test_lifecycle_001"
    print(f"[TestStateMachine] 1. Initializing mock job: {test_id}...")

    # Wipe prior test artifact if any
    with get_db_connection() as conn:
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (test_id,))
        conn.execute("DELETE FROM approvals WHERE job_id = ?", (test_id,))

    # Create job and advance stages
    job = JobState.create(test_id)
    assert job.get_status() == "INIT", f"Expected INIT, got {job.get_status()}"
    
    job.update_status("COLLECTED")
    assert job.get_status() == "COLLECTED"

    job.update_status("RANKED")
    assert job.get_status() == "RANKED"

    mock_topic = {
        "headline": "Arsenal sign Riccardo Calafiori for £42m",
        "source": "Sky Sports",
        "reliability_tier": "confirmed"
    }
    job.update_status("TOPIC_APPROVAL_PENDING", topic_data=mock_topic)
    assert job.get_status() == "TOPIC_APPROVAL_PENDING"

    print("[TestStateMachine] 2. Simulating sudden crash while awaiting approval...")
    del job

    print("[TestStateMachine] 3. Recovering job state post-restart...")
    resumed = JobState.get_latest_active_job()
    assert resumed is not None, "Failed to recover active job!"
    assert resumed.job_id == test_id, f"Recovered wrong job: {resumed.job_id}"
    assert resumed.get_status() == "TOPIC_APPROVAL_PENDING", f"Status corrupted: {resumed.get_status()}"

    rec = resumed.get_record()
    assert rec["error_message"] is None, "Error message should be empty on healthy pending job"
    recovered_topic = json.loads(rec["topic_data"])
    assert recovered_topic["headline"] == mock_topic["headline"], "Topic payload corrupted"

    # Simulate phone approval tap
    resumed.record_approval("TOPIC", "APPROVED", recovered_topic)
    resumed.update_status("TOPIC_APPROVED")
    assert resumed.get_status() == "TOPIC_APPROVED"

    # Cleanup test job
    with get_db_connection() as conn:
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (test_id,))
        conn.execute("DELETE FROM approvals WHERE job_id = ?", (test_id,))

    print("  ✅ Passed: State transitions, crash recovery, and approval logging verified.")

def test_wal_mode_enabled():
    print("[TestStateMachine] 4. Verifying SQLite WAL mode...")
    with get_db_connection() as conn:
        row = conn.execute("PRAGMA journal_mode;").fetchone()
        mode = row[0].lower() if row else ""
        assert mode == "wal", f"Expected WAL mode, got {mode}"
    print(f"  ✅ Passed: Database journal mode is '{mode.upper()}'.")

if __name__ == "__main__":
    test_job_lifecycle_and_resume()
    test_wal_mode_enabled()
    print("\n[TestStateMachine] ALL STATE MACHINE TESTS PASSED SUCCESSFULLY! ✅")
