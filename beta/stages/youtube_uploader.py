"""
# PROVENANCE: Replaces stages/youtube_uploader.py in the isolated beta pipeline.
# STRICT ISOLATION DIRECTIVE: Beta pipeline NEVER publishes to production YouTube.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("BetaYouTubeMock")

def format_description(
    story_title: str,
    script_text: str,
    source_name: str,
    source_url: str,
    reliability_tier: str
) -> str:
    return (
        f"{story_title}\n\n"
        f"30 FOOTBALL PLUS [BETA PREVIEW]\n"
        f"Source: {source_name} ({reliability_tier.upper()})\n\n"
        f"#shorts #football #soccer #premierleague #transfers"
    )

def upload_video_youtube(
    video_path: Path,
    title: str,
    script_text: str,
    source_name: str,
    source_url: str,
    reliability_tier: str,
    allow_public: bool = False
) -> Dict[str, Any]:
    """
    STRICT BETA SAFETY GATE:
    Always returns a local staged receipt. Zero network requests made to YouTube API.
    """
    print("[Beta-Safety] YouTube automatic upload is STRICTLY DISABLED in beta pipeline.")
    print(f"[Beta-Safety] Master video saved locally: {video_path}")
    
    mock_id = f"BETA_STAGED_{int(time.time())}"
    return {
        "status": "MOCK_VERIFIED",
        "video_id": mock_id,
        "local_path": str(video_path),
        "url": f"https://local-beta-preview/{mock_id}",
        "privacy": "private_staged",
        "message": "Beta video staged locally in beta/output. Production publishing skipped."
    }
