"""
Persistent SQLite State Manager.
Ensures that all stages and Telegram human-in-the-loop approvals are persisted.
If interrupted or killed mid-run, resuming picks up exactly where the pipeline left off.
"""

import sqlite3
import json
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "news.db"

@contextmanager
def get_db_connection():
    """Thread-safe context manager enforcing WAL mode, busy timeout, and deterministic connection closing."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=10000;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize articles and jobs schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Articles store
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                published_at TEXT,
                raw_text TEXT,
                scraped_at TEXT,
                cluster_id INTEGER,
                reliability_tier TEXT,
                ranking_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'NEW'
            )
        """)
        
        # Pipeline jobs store
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                topic_id INTEGER,
                topic_data TEXT,
                script_data TEXT,
                assets_data TEXT,
                video_path TEXT,
                youtube_id TEXT,
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (topic_id) REFERENCES articles(id)
            )
        """)
        
        # Approvals log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                approval_type TEXT NOT NULL, -- 'TOPIC' or 'SCRIPT' or 'VIDEO'
                decision TEXT NOT NULL,       -- 'APPROVED', 'EDITED', 'REJECTED'
                payload TEXT,
                decided_at TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """)
        conn.commit()

class JobState:
    def __init__(self, job_id: str):
        self.job_id = job_id
        init_database()

    @classmethod
    def create(cls, job_id: Optional[str] = None) -> "JobState":
        init_database()
        if not job_id:
            job_id = f"job_{time.strftime('%Y%m%d_%H%M%S')}"
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (job_id, "INIT", now, now)
            )
            conn.commit()
        return cls(job_id)

    @classmethod
    def get_latest_active_job(cls) -> Optional["JobState"]:
        init_database()
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT job_id FROM jobs WHERE status NOT IN ('COMPLETED', 'REJECTED', 'SKIPPED', 'SCRIPT_REJECTED', 'VIDEO_REJECTED', 'ARCHIVED', 'CANCELLED', 'FAILED', 'QUOTA_EXHAUSTED') ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if row:
                return cls(row["job_id"])
        return None

    def get_record(self) -> Dict[str, Any]:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (self.job_id,)).fetchone()
            return dict(row) if row else {}

    def get_status(self) -> str:
        rec = self.get_record()
        return rec.get("status", "UNKNOWN")

    def update_status(self, status: str, **kwargs):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        fields = ["status = ?", "updated_at = ?"]
        params = [status, now]

        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            if isinstance(v, (dict, list)):
                params.append(json.dumps(v))
            else:
                params.append(v)

        params.append(self.job_id)
        query = f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?"
        with get_db_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    def record_approval(self, approval_type: str, decision: str, payload: Optional[Any] = None):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO approvals (job_id, approval_type, decision, payload, decided_at) VALUES (?, ?, ?, ?, ?)",
                (self.job_id, approval_type, decision, json.dumps(payload) if payload else None, now)
            )
            conn.commit()
