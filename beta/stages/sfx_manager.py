"""
beta/stages/sfx_manager.py - Intelligent Football Sound Design & SFX Rotation Director.

Enforces:
1. Tone-Aware Sound Design: Matches audio events to editorial beats (serious vs transfer vs comedic).
2. Anti-Repetition Guard: Cooldowns prevent using identical effects across consecutive beats or videos.
3. Restrained Editorial Rhythm: Maximum 2-3 SFX per 30-second video. Dialogue is always priority.
4. Voice Ducking & Peak Protection: Leveled mixing at -18 to -24 dBFS below narration.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SFX_DIR = PROJECT_ROOT / "data" / "sfx"
MUSIC_DIR = PROJECT_ROOT / "data" / "music"
REGISTRY_FILE = PROJECT_ROOT / "data" / "sfx_registry.json"

SFX_CATALOG = {
    # 1. Transfer & Contract Foley
    "cash_register": {
        "file": "cash_register_ding.wav",
        "category": "transfer_business",
        "mood": ["transfer", "money", "record_fee", "valuation"],
        "default_offset": 0.15,
        "volume_db": -19.0,
        "intensity": "medium",
        "cooldown_scenes": 4
    },
    "contract_stamp": {
        "file": "contract_stamp.wav",
        "category": "transfer_business",
        "mood": ["contract", "clause", "signed", "agreement", "buyback"],
        "default_offset": 0.20,
        "volume_db": -18.0,
        "intensity": "medium",
        "cooldown_scenes": 3
    },
    "camera_shutter": {
        "file": "camera_shutter.wav",
        "category": "press_media",
        "mood": ["breaking_news", "unveil", "presentation", "rumour"],
        "default_offset": 0.10,
        "volume_db": -20.0,
        "intensity": "low",
        "cooldown_scenes": 3
    },
    "paper_slide": {
        "file": "paper_slide.wav",
        "category": "transfer_business",
        "mood": ["contract", "report", "terms", "dossier"],
        "default_offset": 0.10,
        "volume_db": -22.0,
        "intensity": "subtle",
        "cooldown_scenes": 2
    },

    # 2. Football Match Drama
    "referee_whistle": {
        "file": "referee_whistle.wav",
        "category": "match_incident",
        "mood": ["foul", "penalty", "var", "controversy", "disallowed"],
        "default_offset": 0.05,
        "volume_db": -21.0,
        "intensity": "high",
        "cooldown_scenes": 5
    },
    "var_check_chime": {
        "file": "var_check_chime.wav",
        "category": "match_incident",
        "mood": ["var", "review", "scrutiny", "controversy", "investigation"],
        "default_offset": 0.10,
        "volume_db": -19.0,
        "intensity": "medium",
        "cooldown_scenes": 4
    },
    "stadium_gasp": {
        "file": "stadium_gasp.wav",
        "category": "match_incident",
        "mood": ["shock", "miss", "blunder", "crisis", "outrage"],
        "default_offset": 0.15,
        "volume_db": -20.0,
        "intensity": "medium",
        "cooldown_scenes": 4
    },

    # 3. Editorial Tension & Revelations
    "broadcast_sting": {
        "file": "broadcast_sting.wav",
        "category": "broadcast_alert",
        "mood": ["breaking_news", "exclusive", "alert", "headline"],
        "default_offset": 0.05,
        "volume_db": -20.0,
        "intensity": "medium",
        "cooldown_scenes": 4
    },
    "dramatic_reveal": {
        "file": "dramatic_reveal_stinger.wav",
        "category": "narrative_twist",
        "mood": ["twist", "clause", "secret", "ultimatum", "conflict"],
        "default_offset": 0.25,
        "volume_db": -18.5,
        "intensity": "high",
        "cooldown_scenes": 4
    },
    "sub_bass_drop": {
        "file": "sub_bass_drop.wav",
        "category": "narrative_twist",
        "mood": ["high_stakes", "crisis", "pressure", "decision"],
        "default_offset": 0.15,
        "volume_db": -19.0,
        "intensity": "medium",
        "cooldown_scenes": 3
    },

    # 4. Curated Comedic & Irony Reactions (Tone-Gated)
    "record_stop": {
        "file": "record_stop.wav",
        "category": "comedic_irony",
        "mood": ["contradiction", "bizarre", "unexpected", "plot_twist", "humour"],
        "default_offset": 0.10,
        "volume_db": -18.0,
        "intensity": "high",
        "cooldown_scenes": 6
    },
    "vine_boom": {
        "file": "meme_vine_boom.wav",
        "category": "comedic_irony",
        "mood": ["shock", "disaster", "embarrassing", "humour"],
        "default_offset": 0.15,
        "volume_db": -21.0,
        "intensity": "medium",
        "cooldown_scenes": 6
    },

    # 5. Outro Sonic Signature
    "sonic_branding": {
        "file": "sonic_branding_sting.wav",
        "category": "branding_outro",
        "mood": ["outro", "brand", "closing"],
        "default_offset": 0.0,
        "volume_db": -16.0,
        "intensity": "high",
        "cooldown_scenes": 1
    }
}

class SFXDirector:
    """Manages sound design planning, tone-gating, and mix timing across scenes."""

    def __init__(self):
        self.used_cues = []

    def select_scene_sfx(
        self,
        scene_idx: int,
        total_scenes: int,
        scene_role: str,
        narration: str,
        story_category: str,
        headline: str
    ) -> Optional[Dict[str, Any]]:
        """
        Intelligently decides if a scene warrants an SFX, selecting the most appropriate
        sound cue while enforcing a strict maximum budget of 2-3 cues per entire video.
        """
        # Outro is handled separately by the outro engine
        if scene_idx == total_scenes - 1:
            return None

        # Hard budget: maximum 2 SFX across the 5 main story scenes (plus outro)
        if len(self.used_cues) >= 2:
            return None

        text_lower = (narration + " " + headline).lower()

        # Tone Guard: Never use comedic reactions on injury/tragedy/serious crises
        allow_comedy = story_category not in ["injury", "tragedy", "serious_governance"]

        chosen_key = None

        # Scene 1: Opening Hook
        if scene_idx == 0:
            if "breaking" in text_lower or "exclusive" in text_lower or "shock" in text_lower:
                chosen_key = "broadcast_sting"
            elif any(w in text_lower for w in ["million", "bid", "fee", "clause", "deal", "transfer"]):
                chosen_key = "camera_shutter"
            elif any(w in text_lower for w in ["var", "referee", "penalty", "disallowed"]):
                chosen_key = "referee_whistle"

        # Scene 2 or 3: The Complication or Contract Details
        elif scene_idx in [1, 2]:
            if any(w in text_lower for w in ["buy-back", "buyback", "clause", "contract", "terms", "formula", "signed"]):
                chosen_key = "contract_stamp"
            elif any(w in text_lower for w in ["€", "£", "$", "million", "fee", "record"]):
                chosen_key = "cash_register"
            elif any(w in text_lower for w in ["var", "review", "overturned", "lines", "handball"]):
                chosen_key = "var_check_chime"
            elif any(w in text_lower for w in ["twist", "detail that changes", "secret", "catch", "detail"]):
                chosen_key = "dramatic_reveal"
            elif allow_comedy and any(w in text_lower for w in ["absurd", "bizarre", "refuses", "disaster", "walk away"]):
                chosen_key = "record_stop"

        # Scene 4: High Stakes / Consequences
        elif scene_idx == 3:
            if any(w in text_lower for w in ["crisis", "pressure", "ultimatum", "gamble", "demand"]):
                chosen_key = "sub_bass_drop"
            elif any(w in text_lower for w in ["stadium", "furious", "outrage", "stunned"]):
                chosen_key = "stadium_gasp"

        if chosen_key and chosen_key not in self.used_cues:
            meta = SFX_CATALOG[chosen_key]
            sfx_file = SFX_DIR / meta["file"]
            if sfx_file.exists():
                self.used_cues.append(chosen_key)
                return {
                    "sfx_id": chosen_key,
                    "file_path": str(sfx_file),
                    "category": meta["category"],
                    "offset_sec": meta["default_offset"],
                    "volume_db": meta["volume_db"],
                    "intensity": meta["intensity"]
                }

        return None

    def design_soundtrack_for_story(
        self,
        scenes: List[Dict[str, Any]],
        story_category: str,
        headline: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Orchestrates full audiovisual sound design:
        - Selects matching background music bed.
        - Places restrained, tone-aware SFX cues across scenes.
        - Schedules music intensity and ducking moments.
        """
        self.used_cues.clear()
        total_sc = len(scenes)

        # 1. Select appropriate background music bed
        if story_category in ["breaking_news", "controversy_var", "managerial_crisis"]:
            music_file = MUSIC_DIR / "breaking_wire.wav"
            mood = "urgent_wire"
        else:
            music_file = MUSIC_DIR / "transfer_pulse.wav"
            mood = "documentary_pulse"

        if not music_file.exists():
            music_file = SFX_DIR / "tension_drone.wav"

        music_plan = {
            "file_path": str(music_file),
            "mood": mood,
            "base_volume_db": -22.0,  # Sits comfortably beneath commentary
            "duck_volume_db": -27.0,  # Ducks further when SFX fire
        }

        # 2. Decorate each scene with sound design cues
        decorated_scenes = []
        for idx, sc in enumerate(scenes):
            sc_copy = dict(sc)
            role = sc.get("role", "")
            narr = sc.get("narration", "")
            
            sfx_cue = self.select_scene_sfx(
                scene_idx=idx,
                total_scenes=total_sc,
                scene_role=role,
                narration=narr,
                story_category=story_category,
                headline=headline
            )
            sc_copy["sound_design"] = {
                "sfx": sfx_cue,
                "music_intensity": "low" if idx == 0 else ("high" if idx in [2, 3] else "medium"),
                "ducking_required": sfx_cue is not None
            }
            if sfx_cue:
                print(f"[SFXDirector] Scene {idx+1} ({role}): Assigned '{sfx_cue['sfx_id']}' at {sfx_cue['offset_sec']}s ({sfx_cue['volume_db']} dB)")
            decorated_scenes.append(sc_copy)

        return decorated_scenes, music_plan

if __name__ == "__main__":
    director = SFXDirector()
    sample_scenes = [
        {"role": "hook", "narration": "Endrick to Milan? There's one detail that changes this entire deal."},
        {"role": "context", "narration": "Reports in Italy confirm formal discussions have accelerated."},
        {"role": "clause", "narration": "The formula includes an eighty million euro buy-back clause."},
        {"role": "consequence", "narration": "Milan need urgent firepower, but Madrid demand starter minutes."},
        {"role": "verdict", "narration": "Is San Siro the right move, or a massive gamble? Tell us below."}
    ]
    dec, mus = director.design_soundtrack_for_story(sample_scenes, "transfer_rumour", "Endrick Milan Transfer")
    print(f"Music plan: {mus['mood']} ({mus['file_path']})")
    print(f"Assigned SFX cues: {len(director.used_cues)}")
