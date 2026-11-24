"""
beta/stages/asset_ledger.py
V7.1.6.7 Asset Integrity, Provenance & Story-Level Isolation Ledger.

Maintains an immutable ledger for every visual asset utilized in a production run:
- Local asset ID (ast_<shot_id>_<sha256[:8]>)
- SHA256 cryptographic hash of image bytes
- Source platform & provenance URL
- Rights metadata (e.g. editorial_public_archive, licensed_editorial_wire)
- Story-level workspace isolation
- Crop & framing audit scores (sharpness variance, safe zone compliance)
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class StoryAssetLedger:
    def __init__(self, workspace_manifest_dir: Path, story_id: str):
        self.manifest_dir = workspace_manifest_dir
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.story_id = story_id
        self.ledger_file = self.manifest_dir / "asset_ledger.json"
        self.assets: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        if self.ledger_file.exists():
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    self.assets = json.load(f).get("assets", {})
            except Exception:
                self.assets = {}

    def record_asset(
        self,
        shot_id: str,
        scene_id: str,
        primary_entity: str,
        file_path: Path,
        source_url: str,
        source_platform: str,
        crop_audit: Dict[str, Any],
        rights_status: str = "editorial_public_archive"
    ) -> Dict[str, Any]:
        """Registers an asset in the isolated ledger with cryptographic hash and provenance."""
        if not file_path.exists():
            return {}

        file_hash = sha256_of_file(file_path)
        asset_id = f"ast_{shot_id}_{file_hash[:8]}"

        record = {
            "asset_id": asset_id,
            "story_id": self.story_id,
            "shot_id": shot_id,
            "scene_id": scene_id,
            "primary_entity": primary_entity,
            "local_path": str(file_path.as_posix()),
            "file_size_bytes": file_path.stat().st_size,
            "sha256": file_hash,
            "source_url": source_url,
            "source_platform": source_platform,
            "rights_status": rights_status,
            "resolution": crop_audit.get("effective_crop_res", "1080x1920"),
            "blur_variance": crop_audit.get("blur_variance"),
            "scale_factor": crop_audit.get("scale_factor"),
            "safe_zone_compliant": crop_audit.get("safe_zone_compliant", True),
            "timestamp_iso": datetime.now(timezone.utc).isoformat()
        }

        self.assets[asset_id] = record
        self.save()
        return record

    def save(self):
        data = {
            "story_id": self.story_id,
            "total_assets": len(self.assets),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "assets": self.assets
        }
        with open(self.ledger_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """Validates that all assets in the ledger exist and match their SHA256 hashes."""
        discrepancies = []
        for aid, meta in self.assets.items():
            p = Path(meta["local_path"])
            if not p.exists():
                discrepancies.append(f"Missing asset file for {aid}: {p}")
                continue
            curr_hash = sha256_of_file(p)
            if curr_hash != meta["sha256"]:
                discrepancies.append(f"SHA256 mismatch for {aid}: expected {meta['sha256']}, got {curr_hash}")

        return (len(discrepancies) == 0, discrepancies)
