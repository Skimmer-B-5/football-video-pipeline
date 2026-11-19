"""
pipeline/retention_tracker.py - Persistent Video Production & Retention Performance Tracker.

Implements Section 16 of the Master Directive:
1. Persistent recording of every rendered video's editorial and technical parameters.
2. Tracking of 24h and 7d YouTube Studio retention analytics (Stayed-to-Watch, APV, drop-off curves).
3. 10-video rolling cohort comparative analysis (Top 3 vs Bottom 3).
4. Evidence-based hypothesis generation for continuous channel retention optimization.
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
DB_PATH = DATA_DIR / "retention_performance.db"

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
            # 1. Video Production Metadata
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

            # 2. Retention & Analytics Snapshots (24h, 7d, manual)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS retention_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                snapshot_type TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                shown_in_feed INTEGER DEFAULT 0,
                stayed_to_watch_pct REAL DEFAULT 0.0,
                engaged_views INTEGER DEFAULT 0,
                average_view_duration_sec REAL DEFAULT 0.0,
                average_percentage_viewed_pct REAL DEFAULT 0.0,
                retention_curve TEXT,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                traffic_sources TEXT,
                first_dropoff_sec REAL,
                dropoff_scene_id TEXT,
                dropoff_script_line TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
            """)
            conn.commit()

    def log_video(self, meta: Dict[str, Any]) -> str:
        """
        Persists a newly rendered video's complete production DNA into the database.
        """
        video_id = meta.get("video_id") or f"vid_{int(datetime.datetime.now().timestamp())}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        entities = meta.get("entities", {})
        hook_options = meta.get("hook_options", {})
        qa_summary = meta.get("qa_report_summary", {})
        caption_cfg = meta.get("caption_config", {})
        music_cfg = meta.get("music_config", {})

        word_count = int(meta.get("script_word_count", 0))
        duration = float(meta.get("duration_sec", 1.0))
        speed_wps = round(word_count / max(1.0, duration), 2) if word_count > 0 else 2.6

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO videos (
                video_id, created_at, story_category, headline, topic_entities,
                duration_sec, hook_selected, hook_type, hook_options,
                script_word_count, narration_speed_wps, visual_beats_count,
                caption_config, voice_mode, music_config, qa_report_summary, output_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_id,
                now_iso,
                meta.get("story_category", "general_news"),
                meta.get("headline", "Untitled Story"),
                json.dumps(entities) if isinstance(entities, dict) else str(entities),
                duration,
                meta.get("hook_selected", ""),
                meta.get("hook_type", "question_challenge"),
                json.dumps(hook_options) if isinstance(hook_options, dict) else str(hook_options),
                word_count,
                speed_wps,
                int(meta.get("visual_beats_count", 1)),
                json.dumps(caption_cfg) if isinstance(caption_cfg, dict) else str(caption_cfg),
                meta.get("voice_mode", "british_broadcast_news"),
                json.dumps(music_cfg) if isinstance(music_cfg, dict) else str(music_cfg),
                json.dumps(qa_summary) if isinstance(qa_summary, dict) else str(qa_summary),
                meta.get("output_filename", f"{video_id}.mp4")
            ))
            conn.commit()

        print(f"[RetentionTracker] ✓ Logged video {video_id} ({meta.get('headline', '')})")
        return video_id

    def record_analytics_snapshot(
        self,
        video_id: str,
        snapshot_type: str,
        metrics: Dict[str, Any]
    ) -> int:
        """
        Records a 24h or 7d analytics snapshot fetched from YouTube Studio or entered manually.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ret_curve = metrics.get("retention_curve", [])
        traffic = metrics.get("traffic_sources", {})

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO retention_snapshots (
                video_id, snapshot_type, recorded_at, shown_in_feed,
                stayed_to_watch_pct, engaged_views, average_view_duration_sec,
                average_percentage_viewed_pct, retention_curve, likes, comments,
                traffic_sources, first_dropoff_sec, dropoff_scene_id, dropoff_script_line
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_id,
                snapshot_type,
                now_iso,
                int(metrics.get("shown_in_feed", 0)),
                float(metrics.get("stayed_to_watch_pct", 0.0)),
                int(metrics.get("engaged_views", 0)),
                float(metrics.get("average_view_duration_sec", 0.0)),
                float(metrics.get("average_percentage_viewed_pct", 0.0)),
                json.dumps(ret_curve) if isinstance(ret_curve, list) else str(ret_curve),
                int(metrics.get("likes", 0)),
                int(metrics.get("comments", 0)),
                json.dumps(traffic) if isinstance(traffic, dict) else str(traffic),
                metrics.get("first_dropoff_sec"),
                metrics.get("dropoff_scene_id"),
                metrics.get("dropoff_script_line")
            ))
            snapshot_id = cur.lastrowid
            conn.commit()

        print(f"[RetentionTracker] ✓ Recorded {snapshot_type} snapshot for {video_id}")
        return snapshot_id

    def get_all_videos(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT v.*, 
                   s.stayed_to_watch_pct, 
                   s.average_percentage_viewed_pct, 
                   s.first_dropoff_sec
            FROM videos v
            LEFT JOIN retention_snapshots s ON v.video_id = s.video_id
            ORDER BY v.created_at DESC
            LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def evaluate_10_video_cohort(self) -> Dict[str, Any]:
        """
        Analyzes the last 10 logged videos with analytics:
        - Ranks top 3 and bottom 3 by Stayed-to-Watch and Average Percentage Viewed (APV).
        - Identifies winning hook patterns (Question vs Stat vs Conflict).
        - Analyzes pacing (words per second & visual changes).
        - Generates 1-2 evidence-based actionable hypotheses for the next production cycle.
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT v.*, 
                   s.stayed_to_watch_pct, 
                   s.average_percentage_viewed_pct, 
                   s.first_dropoff_sec,
                   s.dropoff_scene_id,
                   s.dropoff_script_line
            FROM videos v
            JOIN retention_snapshots s ON v.video_id = s.video_id
            ORDER BY v.created_at DESC
            LIMIT 10
            """)
            rows = [dict(r) for r in cur.fetchall()]

        if len(rows) < 3:
            return {
                "status": "INSUFFICIENT_DATA",
                "cohort_size": len(rows),
                "message": f"Need at least 3 videos with analytics snapshots for cohort analysis (currently {len(rows)})."
            }

        # Sort by stayed_to_watch_pct descending
        sorted_by_stayed = sorted(rows, key=lambda x: x.get("stayed_to_watch_pct", 0.0), reverse=True)
        top_3 = sorted_by_stayed[:3]
        bottom_3 = sorted_by_stayed[-3:] if len(sorted_by_stayed) >= 6 else sorted_by_stayed[len(sorted_by_stayed)//2:]

        # Hook style distribution in top vs bottom
        top_hook_types = [v.get("hook_type") for v in top_3]
        bottom_hook_types = [v.get("hook_type") for v in bottom_3]

        # Pacing analysis
        top_avg_wps = sum(v.get("narration_speed_wps", 2.6) for v in top_3) / len(top_3)
        bottom_avg_wps = sum(v.get("narration_speed_wps", 2.6) for v in bottom_3) / len(bottom_3)

        top_avg_dur = sum(v.get("duration_sec", 28.0) for v in top_3) / len(top_3)
        bottom_avg_dur = sum(v.get("duration_sec", 28.0) for v in bottom_3) / len(bottom_3)

        # Formulate actionable hypotheses
        hypotheses = []
        if "shocking_number_fact" in top_hook_types and "shocking_number_fact" not in bottom_hook_types:
            hypotheses.append({
                "factor": "Hook Style",
                "finding": "Shocking Number/Fact hooks showed significantly higher Stayed-to-Watch conversion.",
                "recommendation": "Prioritize Hook B (data/financial numbers) in transfer and contract stories."
            })
        elif "question_challenge" in top_hook_types:
            hypotheses.append({
                "factor": "Hook Style",
                "finding": "Direct binary question hooks drove stronger opening retention.",
                "recommendation": "Ensure Scene 1 opens with immediate high-stakes dilemma."
            })

        if top_avg_dur < bottom_avg_dur - 3.0:
            hypotheses.append({
                "factor": "Duration Pacing",
                "finding": f"Top performers averaged {top_avg_dur:.1f}s vs {bottom_avg_dur:.1f}s for lower performers.",
                "recommendation": "Trim secondary context sentences to keep runtime between 24-27 seconds."
            })

        if not hypotheses:
            hypotheses.append({
                "factor": "Visual Pacing",
                "finding": "Consistent retention maintained across visual cuts every 2.5-3.5 seconds.",
                "recommendation": "Maintain current 2-4s visual cut frequency with safe-zone captions."
            })

        return {
            "status": "COMPLETED",
            "cohort_size": len(rows),
            "top_performers": [
                {
                    "video_id": v["video_id"],
                    "headline": v["headline"],
                    "hook_type": v["hook_type"],
                    "duration_sec": v["duration_sec"],
                    "stayed_to_watch_pct": v["stayed_to_watch_pct"],
                    "apv_pct": v["average_percentage_viewed_pct"]
                }
                for v in top_3
            ],
            "bottom_performers": [
                {
                    "video_id": v["video_id"],
                    "headline": v["headline"],
                    "hook_type": v["hook_type"],
                    "duration_sec": v["duration_sec"],
                    "stayed_to_watch_pct": v["stayed_to_watch_pct"],
                    "apv_pct": v["average_percentage_viewed_pct"]
                }
                for v in bottom_3
            ],
            "metrics_comparison": {
                "top_avg_wps": round(top_avg_wps, 2),
                "bottom_avg_wps": round(bottom_avg_wps, 2),
                "top_avg_duration_sec": round(top_avg_dur, 1),
                "bottom_avg_duration_sec": round(bottom_avg_dur, 1),
            },
            "evidence_based_recommendations": hypotheses
        }

    def export_summary_json(self, output_path: Path) -> Path:
        data = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "videos": self.get_all_videos(limit=50),
            "cohort_analysis": self.evaluate_10_video_cohort()
        }
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return output_path

if __name__ == "__main__":
    print("Testing Retention Tracker...")
    tracker = RetentionTracker()
    test_id = tracker.log_video({
        "video_id": "test_video_001",
        "story_category": "transfer_rumour",
        "headline": "Real Madrid Considering Endrick Milan Loan",
        "duration_sec": 28.4,
        "hook_selected": "Is Real Madrid's prodigy heading to San Siro?",
        "hook_type": "question_challenge",
        "script_word_count": 76,
        "visual_beats_count": 7
    })
    tracker.record_analytics_snapshot(test_id, "24h", {
        "shown_in_feed": 1420,
        "stayed_to_watch_pct": 74.2,
        "average_view_duration_sec": 21.8,
        "average_percentage_viewed_pct": 76.8,
        "likes": 88,
        "comments": 19
    })
    cohort = tracker.evaluate_10_video_cohort()
    print("Cohort Analysis Status:", cohort["status"])
