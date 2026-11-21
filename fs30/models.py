"""
Data structures and type definitions for FS 30 Pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Allowed tokens from Part 1 & Part 3 specifications
ALLOWED_BEATS = ["hook", "context", "source", "detail", "outlook"]

ALLOWED_ENTER = [
    "pop_in", "slide_in_left", "slide_in_right", "slide_in_up",
    "drop_in", "unfold", "tear_in", "none"
]

ALLOWED_IDLE = ["wobble", "float", "pulse", "none"]

ALLOWED_EXIT = ["slide_out", "fold_away", "none"]

ALLOWED_TRANSITIONS = ["paper_wipe", "torn_slide", "page_flip", "cut"]

ALLOWED_CAMERA_MOVES = [
    "push_in", "pull_out", "drift_left", "drift_right", "drift_up", "static_breathe"
]

ALLOWED_CAMERA_INTENSITIES = ["low", "medium"]

ALLOWED_PAPER_SHAPES = [
    "torn_strip", "circle", "arrow", "burst", "banner",
    "scribble_underline", "ticket", "jersey_silhouette"
]

ALLOWED_LAYER_ROLES = ["background", "subject", "paper_shape", "text_card", "foreground"]

@dataclass
class Story:
    source_name: str
    date: str
    headline: str
    article_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "date": self.date,
            "headline": self.headline,
            "article_text": self.article_text
        }

@dataclass
class ScriptBeat:
    beat: str
    narration: str

@dataclass
class Script:
    title: str
    certainty: str
    beats: List[ScriptBeat]
    pronunciation_hints: Dict[str, str] = field(default_factory=dict)
    word_count: int = 0

    def full_narration(self) -> str:
        return " ".join(b.narration for b in self.beats)
