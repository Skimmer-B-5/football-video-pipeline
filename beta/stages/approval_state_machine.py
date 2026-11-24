"""
beta/stages/approval_state_machine.py - Explicit Persisted Approval State Machine for Beta Pipeline.

Fulfills Beta V7.1 Mandate:
"The complete workflow must use explicit persisted states:
STORY_SELECTED -> DUAL_SCRIPT_GENERATED -> SCRIPT_REVIEW_PENDING -> SCRIPT_APPROVED
-> IMAGE_PROCUREMENT -> QWEN_VL_RANKING -> OPENCV_CROP_OPTIMISATION
-> VISUAL_REVIEW_PENDING -> VISUALS_APPROVED -> VOICE_AUDITION_PENDING
-> VOICE_APPROVED -> RENDER_READY -> VIDEO_RENDERED -> FINAL_QA -> DELIVERY.
An approval must apply only to the exact version reviewed.
Any material change to the dialogue, image key or visual manifest invalidates downstream approvals.
Do not use Telegram message delivery as a substitute for human approval.
Do not render while any approval state is pending."
"""

import os
import sys
import json
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class PipelineState(str, Enum):
    STORY_SELECTED = "STORY_SELECTED"
    DUAL_SCRIPT_GENERATED = "DUAL_SCRIPT_GENERATED"
    SCRIPT_REVIEW_PENDING = "SCRIPT_REVIEW_PENDING"
    SCRIPT_APPROVED = "SCRIPT_APPROVED"
    IMAGE_PROCUREMENT = "IMAGE_PROCUREMENT"
    QWEN_VL_RANKING = "QWEN_VL_RANKING"
    OPENCV_CROP_OPTIMISATION = "OPENCV_CROP_OPTIMISATION"
    VISUAL_REVIEW_PENDING = "VISUAL_REVIEW_PENDING"
    VISUALS_APPROVED = "VISUALS_APPROVED"
    VOICE_AUDITION_PENDING = "VOICE_AUDITION_PENDING"
    VOICE_APPROVED = "VOICE_APPROVED"
    RENDER_READY = "RENDER_READY"
    VIDEO_RENDERED = "VIDEO_RENDERED"
    FINAL_QA = "FINAL_QA"
    DELIVERY = "DELIVERY"
    REJECTED = "REJECTED"


VALID_TRANSITIONS = {
    PipelineState.STORY_SELECTED: [PipelineState.DUAL_SCRIPT_GENERATED, PipelineState.REJECTED],
    PipelineState.DUAL_SCRIPT_GENERATED: [PipelineState.DUAL_SCRIPT_GENERATED, PipelineState.SCRIPT_REVIEW_PENDING, PipelineState.REJECTED],
    PipelineState.SCRIPT_REVIEW_PENDING: [PipelineState.SCRIPT_APPROVED, PipelineState.DUAL_SCRIPT_GENERATED, PipelineState.REJECTED],
    PipelineState.SCRIPT_APPROVED: [PipelineState.IMAGE_PROCUREMENT, PipelineState.SCRIPT_REVIEW_PENDING, PipelineState.REJECTED],
    PipelineState.IMAGE_PROCUREMENT: [PipelineState.QWEN_VL_RANKING, PipelineState.REJECTED],
    PipelineState.QWEN_VL_RANKING: [PipelineState.OPENCV_CROP_OPTIMISATION, PipelineState.IMAGE_PROCUREMENT, PipelineState.REJECTED],
    PipelineState.OPENCV_CROP_OPTIMISATION: [PipelineState.VISUAL_REVIEW_PENDING, PipelineState.IMAGE_PROCUREMENT, PipelineState.REJECTED],
    PipelineState.VISUAL_REVIEW_PENDING: [PipelineState.VISUALS_APPROVED, PipelineState.OPENCV_CROP_OPTIMISATION, PipelineState.IMAGE_PROCUREMENT, PipelineState.REJECTED],
    PipelineState.VISUALS_APPROVED: [PipelineState.VOICE_AUDITION_PENDING, PipelineState.VISUAL_REVIEW_PENDING, PipelineState.REJECTED],
    PipelineState.VOICE_AUDITION_PENDING: [PipelineState.VOICE_APPROVED, PipelineState.VOICE_AUDITION_PENDING, PipelineState.REJECTED],
    PipelineState.VOICE_APPROVED: [PipelineState.RENDER_READY, PipelineState.VOICE_AUDITION_PENDING, PipelineState.REJECTED],
    PipelineState.RENDER_READY: [PipelineState.VIDEO_RENDERED, PipelineState.REJECTED],
    PipelineState.VIDEO_RENDERED: [PipelineState.FINAL_QA, PipelineState.REJECTED],
    PipelineState.FINAL_QA: [PipelineState.DELIVERY, PipelineState.RENDER_READY, PipelineState.REJECTED],
    PipelineState.DELIVERY: [PipelineState.SCRIPT_APPROVED, PipelineState.SCRIPT_REVIEW_PENDING, PipelineState.IMAGE_PROCUREMENT, PipelineState.STORY_SELECTED],
    PipelineState.REJECTED: [PipelineState.STORY_SELECTED]
}


class ApprovalStateMachine:
    """Manages and persists approval transitions with strict validation."""

    def __init__(self, workspace_state_file: Path, story_id: str, run_id: str):
        self.state_file = workspace_state_file
        self.story_id = story_id
        self.run_id = run_id
        self._load_or_initialize()

    def _load_or_initialize(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self.current_state = PipelineState(data.get("current_state", PipelineState.STORY_SELECTED))
                self.script_version = data.get("script_version", "v7.1")
                self.script_approved_by = data.get("script_approved_by")
                self.visuals_approved_by = data.get("visuals_approved_by")
                self.voice_approved_by = data.get("voice_approved_by")
                self.history = data.get("history", [])
                return
            except Exception:
                pass

        self.current_state = PipelineState.STORY_SELECTED
        self.script_version = "v7.1"
        self.script_approved_by = None
        self.visuals_approved_by = None
        self.voice_approved_by = None
        self.history = []
        self._persist("Initial state initialized")

    def _persist(self, reason: str):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "story_id": self.story_id,
            "run_id": self.run_id,
            "current_state": self.current_state.value,
            "script_version": self.script_version,
            "script_approved_by": self.script_approved_by,
            "visuals_approved_by": self.visuals_approved_by,
            "voice_approved_by": self.voice_approved_by,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_transition_reason": reason,
            "history": self.history
        }
        self.state_file.write_text(json.dumps(record, indent=2), encoding="utf-8")

    def transition_to(
        self,
        new_state: PipelineState,
        actor: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Transitions state, validating against allowed transitions."""
        allowed = VALID_TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed:
            raise ValueError(
                f"[INVALID STATE TRANSITION] Cannot move from {self.current_state.value} to {new_state.value}. Allowed: {[s.value for s in allowed]}"
            )

        old_state = self.current_state
        self.current_state = new_state
        entry = {
            "from": old_state.value,
            "to": new_state.value,
            "actor": actor,
            "reason": reason,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "metadata": metadata or {}
        }
        self.history.append(entry)

        if new_state == PipelineState.SCRIPT_APPROVED:
            self.script_approved_by = actor
        elif new_state == PipelineState.VISUALS_APPROVED:
            self.visuals_approved_by = actor
        elif new_state == PipelineState.VOICE_APPROVED:
            self.voice_approved_by = actor

        self._persist(reason)
        return True

    def invalidate_downstream_on_script_change(self, new_script_version: str, actor: str):
        """If script changes, immediately invalidates all visual, voice, and render approvals!"""
        self.script_version = new_script_version
        self.script_approved_by = None
        self.visuals_approved_by = None
        self.voice_approved_by = None
        self.current_state = PipelineState.DUAL_SCRIPT_GENERATED
        entry = {
            "from": "ANY",
            "to": PipelineState.DUAL_SCRIPT_GENERATED.value,
            "actor": actor,
            "reason": f"Script invalidated due to content modification (version {new_script_version})",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        self.history.append(entry)
        self._persist("Downstream invalidated due to script change")

    def assert_render_permitted(self):
        """Strict guard preventing rendering unless all approvals are locked."""
        if self.current_state != PipelineState.RENDER_READY:
            raise ValueError(
                f"[RENDER BLOCKED] Current state is '{self.current_state.value}'. Rendering requires 'RENDER_READY' with explicit Script, Visuals, and Voice approvals."
            )
        if not self.script_approved_by:
            raise ValueError("[RENDER BLOCKED] Script approval missing.")
        if not self.visuals_approved_by:
            raise ValueError("[RENDER BLOCKED] Visuals approval missing.")
        if not self.voice_approved_by:
            raise ValueError("[RENDER BLOCKED] Voice approval missing.")
        return True
