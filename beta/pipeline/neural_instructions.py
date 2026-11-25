"""
beta/pipeline/neural_instructions.py
V7.1.6.7 Consolidated Master Architecture Specification & Neural Instructions.
Defines the authoritative target architecture for future football-news video productions.

Key Architectural Guarantees:
1. Voice Architecture: Qwen3-TTS CustomVoice (Ryan) as default production voice; Base cloning only with authorized reference.
2. Runtime Separation: Main 5-beat story (~30s) and branded outro (5-6s) tracked and recorded separately.
3. Anonymity: Minimum 4.0s identity concealment window enforced in S01.
4. Visual Architecture: 16-shot target timeline (3-4 distinct shots per beat) with exact mathematical frame reconciliation.
5. Narration: Natural-language delivery guidelines (conjunctions as editorial guidance, not rigid rules) with voice auditioning.
6. Subtitles: Speech-aligned timing from generated audio instead of fixed frame delay.
7. CRT Rendering: Analog phosphor treatment applied predominantly to footage/background; foreground typography remains crisp.
8. Vision Inspection: Multi-gate validation (OpenCV face/safe-zone [240, 1250], metadata, VLM semantic advisory, human review).
9. Asset Integrity: Exact provenance, SHA256 hashes, local asset IDs, and per-story directory isolation.
10. Model Configuration: Configurable, version-pinned LLM/VLM identifiers with runtime execution logging.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# ==============================================================================
# MODEL CONFIGURATION & VERSION PINNING (POINT 10)
# ==============================================================================

CONFIGURED_LLM_MODEL = os.environ.get("BETA_LLM_MODEL", "openai/gpt-oss-120b")
CONFIGURED_LLM_FALLBACK = os.environ.get("BETA_LLM_FALLBACK", "qwen/qwen3.8-27b")
CONFIGURED_VLM_MODEL = os.environ.get("BETA_VLM_MODEL", "meta-llama/llama-3.2-11b-vision-instruct")


@dataclass
class StoryDossier:
    """Standardized input dossier for any football story passing through the pipeline."""
    story_id: str
    protagonist_name: str
    current_club: str
    current_manager: str
    pursuing_club: str
    reported_base_fee: str
    reported_bonuses: str
    reported_buyback: Optional[str] = None
    complication: str = ""
    reporting_sources: List[str] = field(default_factory=list)
    headline_kicker: str = "● TRANSFER WATCH"
    main_headline: str = ""
    ticker_text: str = ""
    pursuing_manager: str = ""
    current_stadium: str = ""
    pursuing_stadium: str = ""
    fan_reactions: List[str] = field(default_factory=list)
    raw_article_text: str = ""
    story_category: str = "transfer_rumour"
    hero_image_url: Optional[str] = None
    candidate_images: List[str] = field(default_factory=list)
    article_urls: List[str] = field(default_factory=list)


# ==============================================================================
# NEURAL NODE 1: BROADCAST SCREENPLAY & DUAL-SCRIPT ENGINE (LLM) (POINTS 2, 3, 5, 10)
# ==============================================================================

SCREENPLAY_SYSTEM_PROMPT = """You are an elite British sports news television editor producing an energetic, high-tension 1990s television football-news broadcast short for 'THIS IS FOOTBALL IN 30 SECONDS'.

Your job is to transform a verified Story Dossier into a synchronized 8-Scene Broadcast Screenplay (7 news scenes + 1 ending card):
1. Spoken Narration: Written for an original British sports-presenter voice design (mature male baritone, fast-paced 145 WPM cadence, punchy, authoritative delivery).
2. On-Screen Graphics Directives: Kickers, Headlines, Subheadlines, and Status Badges.

### 8-SCENE NARRATIVE ARCHITECTURE (STRICT 30-SECOND DURATION ENVELOPE):

TOTAL STORY WORD BUDGET: STRICTLY 56–62 SPOKEN WORDS ACROSS S01..S07.
AT 145 WORDS PER MINUTE, ~58 WORDS EQUALS ~25 SECONDS STORY + 5 SECONDS OUTRO = ~30 SECONDS MASTER VIDEO.
EVERY SCENE MUST BE A SHORT, CRISP, PUNCHY SENTENCE (7–9 WORDS).

1. S01 — THE HOOK & CONCEALMENT (7–9 WORDS | MINIMUM 4.0-SECOND IDENTITY CONCEALMENT):
   - Strict Anonymity: The protagonist's name MUST NOT appear in S01 spoken narration or on-screen text.
   - Word Count: Strictly 7–9 spoken words. The audio engine enforces >= 4.0s duration via acoustic air padding.
   - Establish club tension, stadium pressure, or managerial conflict without revealing the player's identity.

2. S02 — THE DRAMATIC REVEAL (7–9 WORDS):
   - Explicitly name the protagonist in the opening beat.
   - Use natural conjunction attack (e.g., "And — ") for an energetic vocal pickup.

3. S03 — THE SUITOR MOVE & INTEREST (7–9 WORDS):
   - Name the pursuing club / suitor actively circling or bidding.

4. S04 — PROPOSED PACKAGE & VALUATION (7–9 WORDS):
   - State the reported transfer fee or contract figure.

5. S05 — MANAGERIAL RESISTANCE (7–9 WORDS):
   - Introduce the manager's firm stance or board resistance.

6. S06 — PLAYER PERSPECTIVE & SQUAD STATUS (7–9 WORDS):
   - Cover the player's contract situation, agent stance, or squad reality.

7. S07 — THE CLOSING DILEMMA WITH "OR" / "AND" CHOICE (8–10 WORDS):
   - Frame the ultimate debate question with an "OR" / "AND" choice between the two sides:
     (e.g., "Will Silva keep his defensive anchor, or will United force the move?")
   - This dual-part choice triggers two distinct visual corroborations on screen.

8. OUTRO — BRANDED ENDING CARD (12–14 WORDS):
   - Fixed sign-off: "Either way — this is football in thirty seconds. Follow for daily transfer updates."
   - Scene 8 is the branded graphic ident (4.8–5.2s).

### OUTPUT JSON SCHEMA:
{
  "story_id": string,
  "master_headline": string,
  "ticker_text": string,
  "scenes": [
    {
      "scene_id": "S01",
      "spoken_narration": string,
      "on_screen": {
        "kicker": string,
        "headline": string,
        "subheadline": string,
        "status_badge": "REPORTED" | "OFFICIAL" | "PROPOSAL" | "UNAGREED" | "DEVELOPING"
      }
    },
    ... (S02, S03, S04, S05, S06, S07, outro)
  ]
}
"""


# ==============================================================================
# NEURAL NODE 2: 16-SHOT EDITORIAL VISUAL ARCHITECT (POINTS 4, 9)
# ==============================================================================

VISUAL_ARCHITECT_PROMPT = """You are a television broadcast visual director designing a 16-shot vertical (9:16) timeline for a 1990s television football news report.

### 16-SHOT TIMELINE TARGET (3–4 DISTINCT SHOTS PER BEAT):
1. S01 (3 shots — Concealment): Current club stadium facade -> Manager touchline/tactical bench -> High-intensity match tension. (Protagonist 100% concealed).
2. S02 (3 shots — Reveal): Protagonist official portrait -> Goal celebration in club colours -> Match action dominance.
3. S03 (4 shots — Figures & Clauses): Suitor stadium exterior headquarters -> Protagonist match dominance -> Manager press conference reaction -> Contract/data presentation card.
4. S04 (3 shots — Complication): Protagonist frustration/walking off pitch -> Manager tactical concern -> Protagonist training/fitness drill.
5. S05 (3 shots — Verdict): Protagonist verdict close-up -> Matchday clash/floodlit atmosphere -> Protagonist final determination.

### ASSET DIVERSITY & INTEGRITY REQUIREMENTS:
- Every shot must use genuinely distinct visual material or meaningful editorial detail shots. Repetitive crops or minor zooms of the same photograph are strictly prohibited.
- Shot durations within each scene must sum exactly to the scene's master frame count.
"""


# ==============================================================================
# NEURAL NODE 3: VISION FRAMING & MULTI-GATE QUALITY INSPECTION (POINTS 7, 8, 9)
# ==============================================================================

VISION_INSPECTION_SPEC = {
    "gates": [
        {
            "gate": "A_METADATA_AND_RIGHTS",
            "description": "Verifies source archive provenance, editorial licensing status, SHA256 integrity, and subject metadata heuristics."
        },
        {
            "gate": "B_OPENCV_COMPLIANCE",
            "criteria": {
                "resolution_floor": "iw >= 540 and ih >= 540",
                "laplacian_blur_threshold": 45.0,  # Scale-invariant normalized Laplacian variance
                "safe_zone_y": [240, 1250],        # Y range in 1080x1920 safe from HUD bug (<240) and lower-third (>1250)
                "headroom_ratio": "<= 0.30",       # Face height <= 30% of crop height
                "multi_face_edge_check": True      # Rejects crops where a secondary face intersects the left/right crop border
            }
        },
        {
            "gate": "C_VLM_SEMANTIC_ADVISORY",
            "description": "Vision-Language Model advisory review evaluating semantic relevance and composition. VLM output is strictly an advisory semantic check; it NEVER certifies legal rights, identity, or event chronology by itself."
        },
        {
            "gate": "D_HUMAN_IN_THE_LOOP_REVIEW",
            "description": "Interactive Telegram approval before rendering; user may review, reject, or request regeneration."
        }
    ]
}


# ==============================================================================
# NEURAL NODE 4: VOICE ARCHITECTURE SPECIFICATION (POINTS 1, 2, 5)
# ==============================================================================

VOICE_ARCHITECTURE_SPEC = {
    # 1. Primary Default Production Voice: Original British Sports-Presenter Design
    "production_voice": {
        "engine": "Qwen3-TTS 0.6B CustomVoice",
        "speaker": "Ryan",
        "voice_design_profile": "Original British Sports Presenter",
        "attributes": {
            "register": "Mid-to-low warm baritone",
            "accent": "British English (Received Pronunciation / standard broadcast)",
            "pacing_wpm": 138.0,
            "tone": "Conversational broadcast authority, restrained excitement, articulate consonants",
            "instruct_prompt": (
                "A mature British male sports correspondent delivering breaking football transfer news "
                "from the television studio desk. Measured, authoritative, calm baritone with natural conversational pauses, "
                "clear British pronunciation, and restrained emphasis."
            )
        },
        "hyperparameters": {
            "temperature": 0.65,
            "repetition_penalty": 1.10,
            "language": "English",
            "non_streaming_mode": True
        }
    },

    # 2. Reference-Audio Voice Cloning Mode (Strictly Conditional)
    "clone_voice": {
        "engine": "Qwen3-TTS 0.6B Base",
        "authorization_requirement": "Strictly requires documented authorization, consent, and verified licensing for the reference recording.",
        "usage_policy": "Base voice cloning is ONLY enabled when a properly authorized reference voice is explicitly configured. Jeff Stelling or any other public broadcaster MUST NOT be cloned without appropriate authorization.",
        "fallback_behavior": "If no authorized reference audio is provided, automatically fall back to the production Qwen3-TTS CustomVoice (Ryan) sports-presenter design."
    },

    # 3. Analog Vocal Mastering Chain
    "analog_vocal_chain": {
        "highpass_hz": 80,
        "lowpass_hz": 11500,
        "presence_eq_hz": 3000,
        "presence_eq_gain_db": 2.2,
        "compand": "attacks=0.02:decays=0.15:points=-60/-60|-24/-16|-12/-8|0/-3",
        "loudnorm_i": -14.0,
        "loudnorm_tp": -1.0,
        "loudnorm_lra": 7.0,
        "sample_rate_hz": 48000,
        "channels": "stereo"
    },

    # 4. Pacing & Transition Rules
    "pacing_rules": {
        "whoosh_effects": False,          # STRICTLY FORBIDDEN
        "marker_wipes": False,            # STRICTLY FORBIDDEN
        "s01_minimum_duration_sec": 4.0,  # Strict 4.0-second identity concealment
        "lead_pause_sec": 0.12,           # Natural studio breath pause
        "tail_pause_sec": 0.22            # Clean settling time
    }
}


# ==============================================================================
# RETRO CRT RENDERING SPECIFICATION (POINT 7)
# ==============================================================================

CRT_RENDERING_SPEC = {
    "layer_separation": {
        "background_media": {
            "treatment": "Analog CRT phosphor bloom, subtle RGB fringing, restrained 1.5% phosphor shimmer, authentic scanlines",
            "blur_filter": "Subtle broadcast softening only; NO heavy gaussian blurring",
            "plastic_frame": False  # NO fake television monitor bezel frames
        },
        "foreground_graphics": {
            "treatment": "Direct pixel rendering for typography, TopHUD bug, lower-third cards, and rolling ticker",
            "crispness": "100% sharp vector/text rendering; exempt from heavy analog distortion to maintain complete legibility"
        }
    }
}
