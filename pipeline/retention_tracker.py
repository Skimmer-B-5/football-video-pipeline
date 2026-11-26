"""
# PROVENANCE: Copied from pipeline/retention_tracker.py and adapted for beta runtime isolation.
pipeline/retention_tracker.py - Beta Video Production & Retention Performance Tracker.
Tracks parameters and performance metrics into beta/data/retention.db.
"""

import os
import json
import sqlite3
import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "retention.db"

class RetentionTracker:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                story_category TEXT NOT NULL,
                headline TEXT NOT NULL,
                topic_entities TEXT,
                duration_sec REAL NOT NULL,
                hook_selected TEXT NOT NULL,
                hook_type TEXT NOT NULL,
                hook_options TEXT,
                script_word_count INTEGER NOT NULL,
                narration_speed_wps REAL NOT NULL,
                visual_beats_count INTEGER NOT NULL,
                caption_config TEXT,
                voice_mode TEXT,
                music_config TEXT,
                qa_report_summary TEXT,
                output_filename TEXT
            )
            """)
            conn.commit()

    def log_video(self, video_data: Dict[str, Any]) -> str:
        vid = video_data.get("video_id") or f"beta_vid_{int(datetime.datetime.now().timestamp())}"
        now_iso = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO videos (
                video_id, created_at, story_category, headline, topic_entities,
                duration_sec, hook_selected, hook_type, hook_options, script_word_count,
                narration_speed_wps, visual_beats_count, caption_config, voice_mode,
                music_config, qa_report_summary, output_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vid,
                now_iso,
                video_data.get("story_category", "unknown"),
                video_data.get("headline", ""),
                json.dumps(video_data.get("entities", {})),
                float(video_data.get("duration_sec", 0.0)),
                video_data.get("hook_selected", "default"),
                video_data.get("hook_type", "default"),
                json.dumps(video_data.get("hook_options", {})),
                int(video_data.get("script_word_count", 0)),
                float(video_data.get("narration_speed_wps", 2.6)),
                int(video_data.get("visual_beats_count", 0)),
                json.dumps(video_data.get("caption_config", {})),
                video_data.get("voice_mode", "jeff_stelling"),
                json.dumps(video_data.get("music_config", {})),
                json.dumps(video_data.get("qa_report_summary", {})),
                video_data.get("output_filename", "")
            ))
            conn.commit()
        return vid
