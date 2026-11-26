"""
# PROVENANCE: Copied from pipeline/state_manager.py and adapted for beta runtime isolation.
Persistent SQLite State Manager for Beta Pipeline.
Ensures that all stages and human-in-the-loop approvals are persisted in beta/data/news.db.
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
    """Initialize articles and jobs schema inside beta database."""
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
                hero_image_url TEXT,
                category TEXT,
                scraped_at TEXT,
                cluster_id INTEGER,
                reliability_tier TEXT,
                ranking_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'NEW'
            )
        """)

        # Idempotent schema migrations for existing news.db databases
        for col_def in ("hero_image_url TEXT", "category TEXT"):
            try:
                cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_def}")
            except sqlite3.OperationalError:
                pass
        
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
                approvals TEXT
            )
        """)
        conn.commit()

class JobState:
    def __init__(self, job_id: str):
        self.job_id = job_id
        init_database()

    @classmethod
    def create(cls) -> "JobState":
        init_database()
        job_id = f"job_{int(time.time())}"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, status, created_at, updated_at, approvals) VALUES (?, ?, ?, ?, ?)",
                (job_id, "INIT", now_str, now_str, json.dumps({}))
            )
        return cls(job_id)

    @classmethod
    def get_latest_active_job(cls) -> Optional["JobState"]:
        init_database()
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT job_id FROM jobs WHERE status NOT IN ('COMPLETED', 'FAILED', 'CANCELLED', 'ARCHIVED', 'SKIPPED') ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if row:
                return cls(row["job_id"])
        return None

    def get_status(self) -> str:
        with get_db_connection() as conn:
            row = conn.execute("SELECT status FROM jobs WHERE job_id = ?", (self.job_id,)).fetchone()
            return row["status"] if row else "UNKNOWN"

    def get_record(self) -> Dict[str, Any]:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (self.job_id,)).fetchone()
            return dict(row) if row else {}

    def update_status(self, new_status: str, **kwargs):
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        updates = ["status = ?", "updated_at = ?"]
        params = [new_status, now_str]

        for k, v in kwargs.items():
            updates.append(f"{k} = ?")
            params.append(json.dumps(v) if isinstance(v, (dict, list)) else v)

        params.append(self.job_id)
        query = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?"
        with get_db_connection() as conn:
            conn.execute(query, params)

    def record_approval(self, stage: str, status: str, payload: Optional[Dict[str, Any]] = None):
        rec = self.get_record()
        approvals = json.loads(rec.get("approvals") or "{}")
        approvals[stage] = {
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "payload": payload or {}
        }
        self.update_status(self.get_status(), approvals=approvals)
