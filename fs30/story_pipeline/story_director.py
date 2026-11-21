"""
Story Director for FS30 Story Pipeline.
Generates narrative scripts and synchronizes motion graphics layer specifications
(hero scale, torn-paper widgets, typography, desaturated backgrounds, tactical callouts).
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ArchivalWidgetPlan(BaseModel):
    widget_type: str = Field(..., description="'quote_card', 'match_ticket', 'newspaper_clipping', or 'evidence_tag'")
    primary_text: str = Field(..., description="Main quote, fixture, or newspaper headline")
    secondary_text: Optional[str] = Field(None, description="Attribution, date, or kicker")
    stamp_text: Optional[str] = Field(None, description="Red rubber stamp text (e.g. '7-MATCH BAN')")
    stamp_sub: Optional[str] = Field(None, description="Stamp sub-tag (e.g. 'KNVB SANCTION')")

class TacticalAnnotationPlan(BaseModel):
    enabled: bool = False
    target_description: Optional[str] = Field(None, description="What is being circled (e.g. 'bite mark on shoulder')")
    label: Optional[str] = Field(None, description="Callout text (e.g. 'TEETH MARKS')")

class StoryBeatPlan(BaseModel):
    beat_number: int
    duration_estimate: float = Field(..., description="Estimated spoken duration in seconds (typically 7-10s)")
    voiceover_text: str = Field(..., description="Benedict Cumberbatch delivery: articulate, measured, dramatic restraint")
    visual_headline: str = Field(..., description="Large bold display headline on torn paper banner (64pt+)")
    visual_kicker: str = Field(..., description="Eyebrow text above headline (date, competition, venue)")
    hero_subject_description: str = Field(..., description="Hero cutout to dominate 75% vertical frame")
    hero_cutout_key: str = Field(..., description="Identifier for asset matching")
    background_scene: str = Field(..., description="Stadium or venue backdrop (to be desaturated by 65%)")
    archival_widget: Optional[ArchivalWidgetPlan] = None
    tactical_annotation: Optional[TacticalAnnotationPlan] = None
    caption_words: List[str] = Field(..., description="Key spoken words for the bottom torn-paper ribbon")

class StoryPackage(BaseModel):
    story_id: str
    title: str
    era: str
    logline: str
    target_duration: float = Field(default=50.0, description="Target total video duration (45-60s)")
    narrator_voice_profile: str = "Benedict Cumberbatch (Conversational Scholar / Explanatory Classroom)"
    score_track: str = "Opportunity Walks (Kevin MacLeod, CC-BY 4.0)"
    beats: List[StoryBeatPlan]
    outro_headline: str = "THIS IS FOOTBALL IN 30s."
    outro_subtitle: str = "FOOTBALL STORIES EVERY WEEK."
    outro_cta: str = "FOLLOW FOR MORE."
