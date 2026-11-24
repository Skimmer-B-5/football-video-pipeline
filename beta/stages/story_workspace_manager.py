"""
beta/stages/story_workspace_manager.py - Strict Story Workspace Isolation & Asset Security Engine.

Fulfills Beta V7.1 Mandate:
"Create independent story workspaces.
Asset resolution must require an exact story and scene match.
Never load an image merely because it is named scene_1.png.
Never use an unscoped latest-session fallback.
Never copy previous story photographs into a new story workspace automatically.
Make cross-story contamination impossible."
"""

import os
import sys
import json
import time
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ContaminationError(Exception):
    """Raised when an asset violates story, run, scene, or hash isolation rules."""
    pass


class GateViolationError(Exception):
    """Raised when an operation is attempted without the required prior approval."""
    pass


@dataclass
class AssetMetadata:
    story_id: str
    run_id: str
    script_version: str
    scene_id: str
    asset_id: str
    candidate_id: str
    source_url: str
    source_page_url: str
    original_filename: str
    sha256: str
    publication_date: str
    event_date: str
    approval_status: str  # PENDING, APPROVED, REJECTED, PROVISIONAL
    subject_category: str
    intended_subject: str
    relative_path: str


class StoryWorkspace:
    """
    Encapsulates a strictly isolated filesystem workspace for a specific story run.
    Structure:
    beta/workspaces/<story_id>/<run_id>/
        ├── scripts/
        │   ├── dialogue_script.json
        │   └── image_key_script.json
        ├── assets/
        │   ├── candidates/
        │   ├── approved/
        │   └── rejected/
        ├── crops/
        ├── voice/
        ├── telegram/
        ├── manifests/
        └── state/
            └── approval_state.json
    """

    def __init__(self, story_id: str, run_id: Optional[str] = None):
        self.story_id = story_id.strip().lower()
        self.run_id = run_id or f"run_{int(time.time())}"
        self.base_dir = PROJECT_ROOT / "workspaces" / self.story_id / self.run_id

        # Subdirectories
        self.scripts_dir = self.base_dir / "scripts"
        self.assets_dir = self.base_dir / "assets"
        self.candidates_dir = self.assets_dir / "candidates"
        self.approved_dir = self.assets_dir / "approved"
        self.rejected_dir = self.assets_dir / "rejected"
        self.crops_dir = self.base_dir / "crops"
        self.voice_dir = self.base_dir / "voice"
        self.telegram_dir = self.base_dir / "telegram"
        self.manifests_dir = self.base_dir / "manifests"
        self.state_dir = self.base_dir / "state"

        self._ensure_structure()

    def _ensure_structure(self):
        for d in [
            self.scripts_dir,
            self.candidates_dir,
            self.approved_dir,
            self.rejected_dir,
            self.crops_dir,
            self.voice_dir,
            self.telegram_dir,
            self.manifests_dir,
            self.state_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        h = hashlib.sha256()
        h.update(file_path.read_bytes())
        return h.hexdigest()

    def register_candidate_asset(
        self,
        scene_id: str,
        source_file: Path,
        source_url: str,
        source_page_url: str,
        intended_subject: str,
        subject_category: str,
        publication_date: str = "2026-11-20",
        event_date: str = "2026-11-20",
        script_version: str = "v7.1"
    ) -> AssetMetadata:
        """Copies an acquired image into candidates/ and creates its strict metadata ledger."""
        if not source_file.exists():
            raise FileNotFoundError(f"Source candidate file missing: {source_file}")

        # Compute hash before copying
        file_sha = self.compute_sha256(source_file)
        ext = source_file.suffix.lower()
        candidate_id = f"cand_{scene_id}_{file_sha[:10]}"
        asset_id = f"{self.story_id}_{scene_id}_{candidate_id}"
        dest_filename = f"{candidate_id}{ext}"
        dest_path = self.candidates_dir / dest_filename

        shutil.copy2(str(source_file), str(dest_path))

        meta = AssetMetadata(
            story_id=self.story_id,
            run_id=self.run_id,
            script_version=script_version,
            scene_id=scene_id,
            asset_id=asset_id,
            candidate_id=candidate_id,
            source_url=source_url,
            source_page_url=source_page_url,
            original_filename=source_file.name,
            sha256=file_sha,
            publication_date=publication_date,
            event_date=event_date,
            approval_status="PENDING",
            subject_category=subject_category,
            intended_subject=intended_subject,
            relative_path=str(dest_path.relative_to(self.base_dir))
        )

        meta_file = self.candidates_dir / f"{candidate_id}.json"
        meta_file.write_text(json.dumps(asdict(meta), indent=2), encoding="utf-8")
        return meta

    def approve_scene_crop(
        self,
        scene_id: str,
        crop_file: Path,
        parent_candidate: AssetMetadata,
        qwen_rank: float,
        crop_verdict: str
    ) -> AssetMetadata:
        """Moves an approved crop into approved/ and certifies its manifest entry."""
        if not crop_file.exists():
            raise FileNotFoundError(f"Crop file missing: {crop_file}")

        # Check candidate ownership
        self.validate_asset(parent_candidate, expected_scene_id=scene_id)

        crop_sha = self.compute_sha256(crop_file)
        dest_filename = f"{scene_id}_approved_{crop_sha[:8]}.png"
        dest_path = self.approved_dir / dest_filename
        shutil.copy2(str(crop_file), str(dest_path))

        approved_meta = AssetMetadata(
            story_id=self.story_id,
            run_id=self.run_id,
            script_version=parent_candidate.script_version,
            scene_id=scene_id,
            asset_id=f"{self.story_id}_{scene_id}_approved",
            candidate_id=parent_candidate.candidate_id,
            source_url=parent_candidate.source_url,
            source_page_url=parent_candidate.source_page_url,
            original_filename=dest_filename,
            sha256=crop_sha,
            publication_date=parent_candidate.publication_date,
            event_date=parent_candidate.event_date,
            approval_status="APPROVED",
            subject_category=parent_candidate.subject_category,
            intended_subject=parent_candidate.intended_subject,
            relative_path=str(dest_path.relative_to(self.base_dir))
        )

        meta_file = self.approved_dir / f"{scene_id}_approved.json"
        data = asdict(approved_meta)
        data["qwen_rank"] = qwen_rank
        data["crop_verdict"] = crop_verdict
        meta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Update run visual manifest
        self.update_visual_manifest(scene_id, approved_meta)
        return approved_meta

    def update_visual_manifest(self, scene_id: str, meta: AssetMetadata):
        manifest_path = self.manifests_dir / "visual_asset_manifest.json"
        manifest = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = {}

        manifest["story_id"] = self.story_id
        manifest["run_id"] = self.run_id
        manifest["script_version"] = meta.script_version
        manifest["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        scenes = manifest.get("scenes", {})
        scenes[scene_id] = asdict(meta)
        manifest["scenes"] = scenes

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def get_visual_manifest(self) -> Dict[str, Any]:
        manifest_path = self.manifests_dir / "visual_asset_manifest.json"
        if not manifest_path.exists():
            return {}
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def validate_asset(self, asset: AssetMetadata, expected_scene_id: Optional[str] = None) -> bool:
        """
        Enforces Section 1.3:
        current_story_id == asset.story_id
        current_run_id == asset.run_id
        current_scene_id == asset.scene_id
        manifest_sha256 == actual_file_sha256
        """
        if asset.story_id != self.story_id:
            raise ContaminationError(
                f"[STORY CONTAMINATION] Asset story_id '{asset.story_id}' does not match workspace '{self.story_id}'"
            )
        if asset.run_id != self.run_id:
            raise ContaminationError(
                f"[RUN CONTAMINATION] Asset run_id '{asset.run_id}' does not match workspace run '{self.run_id}'"
            )
        if expected_scene_id and asset.scene_id != expected_scene_id:
            raise ContaminationError(
                f"[SCENE MISMATCH] Asset scene_id '{asset.scene_id}' does not match requested scene '{expected_scene_id}'"
            )

        asset_file = self.base_dir / asset.relative_path
        if not asset_file.exists():
            raise FileNotFoundError(f"[MISSING ASSET] File does not exist at {asset_file}")

        actual_sha = self.compute_sha256(asset_file)
        if actual_sha != asset.sha256:
            raise ContaminationError(
                f"[HASH INTEGRITY FAILURE] SHA256 mismatch for {asset.original_filename}: expected {asset.sha256}, got {actual_sha}"
            )

        return True

    def resolve_scene_asset(self, scene_id: str) -> Tuple[Path, AssetMetadata]:
        """
        Resolves the approved asset for a scene.
        Strictly forbids unscoped fallbacks or reading other folders!
        """
        manifest = self.get_visual_manifest()
        scenes = manifest.get("scenes", {})
        if scene_id not in scenes:
            raise ContaminationError(f"Scene '{scene_id}' has no approved asset in manifest for {self.story_id}:{self.run_id}")

        meta_dict = scenes[scene_id]
        meta = AssetMetadata(**{k: v for k, v in meta_dict.items() if k in AssetMetadata.__annotations__})

        self.validate_asset(meta, expected_scene_id=scene_id)
        asset_file = self.base_dir / meta.relative_path
        return asset_file, meta
