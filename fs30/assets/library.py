"""
FS 30 Asset Subsystem: Managed Library & Picker API.
Handles SQLite querying, usage tracking, type/tag matching,
and prevents excessive re-use within a single video run.
"""

import sqlite3
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "assets" / "index.sqlite"

class AssetLibrary:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.usage_counts: Dict[str, int] = {}

    def get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def reset_usage(self):
        """Reset per-video usage tracking."""
        self.usage_counts.clear()

    def record_usage(self, asset_id: str):
        self.usage_counts[asset_id] = self.usage_counts.get(asset_id, 0) + 1

    def pick(
        self,
        role: str,
        tags: Optional[List[str]] = None,
        palette: Optional[Dict[str, str]] = None,
        exclude_ids: Optional[List[str]] = None,
        max_reuse: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        B8 Asset Picker API:
        Picks the best asset matching the role/type and optional tags,
        ensuring usage does not exceed max_reuse and excluding exclude_ids.
        """
        exclude_ids = exclude_ids or []
        tags = tags or []

        # Map semantic roles to asset types
        role_type_map = {
            "tape": "tape",
            "packing_tape": "tape",
            "scribble": "scribble",
            "arrow": "scribble",
            "starburst": "scribble",
            "doodle": "scribble",
            "paper_texture": "texture",
            "paper_multiply": "texture",
            "paper_crease": "texture",
            "glass_distortion": "overlay",
            "displacement_map": "overlay",
            "background_texture": "texture"
        }
        target_type = role_type_map.get(role, role)

        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM assets WHERE type = ?"
        params: List[Any] = [target_type]

        # Filter by pack preferences if role implies it
        if role == "paper_multiply":
            query += " AND pack = 'paper effects white'"
        elif role == "paper_crease":
            query += " AND pack = 'Paper effects black'"
        elif role == "background_texture":
            query += " AND pack IN ('paper effects white', 'Wrinkled Paper Textures')"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        # Filter out assets exceeding usage or in exclude_ids
        candidates = []
        for r in rows:
            a_id = r["id"]
            if a_id in exclude_ids:
                continue
            if self.usage_counts.get(a_id, 0) >= max_reuse:
                continue

            # Tag matching score
            r_tags = json.loads(r["tags"])
            tag_score = sum(1 for t in tags if t.lower() in [rt.lower() for rt in r_tags])
            
            candidates.append((tag_score, r))

        if not candidates:
            # Fallback: relax max_reuse if no candidate left
            candidates = [(0, r) for r in rows if r["id"] not in exclude_ids]
            if not candidates:
                return None

        # Sort by tag score descending, then shuffle top matches
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_score = candidates[0][0]
        best_matches = [c[1] for c in candidates if c[0] == top_score]
        chosen_row = random.choice(best_matches)

        chosen_dict = dict(chosen_row)
        chosen_dict["tags"] = json.loads(chosen_dict["tags"])
        
        self.record_usage(chosen_dict["id"])
        return chosen_dict

    def get_stats(self) -> Dict[str, Any]:
        """Returns total counts per type and pack."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT pack, COUNT(*), SUM(has_alpha) FROM assets GROUP BY pack")
        pack_stats = {row[0]: {"total": row[1], "has_alpha": row[2]} for row in cursor.fetchall()}
        
        cursor.execute("SELECT type, COUNT(*) FROM assets GROUP BY type")
        type_stats = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM assets")
        total = cursor.fetchone()[0]

        conn.close()
        return {
            "total_indexed": total,
            "packs": pack_stats,
            "types": type_stats
        }

# Global library singleton
library = AssetLibrary()
