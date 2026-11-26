"""
beta/stages/dual_script_architecture.py - Strict Synchronized Dual Script Architecture for 30 Football Plus.

Beta V7.1.6.3 Factual Corrections & Final Script Timing Engine:
1. S05 exact displayed duration: 11 / 138 * 60 + 0.32 = 5.1026087s -> displayed as 5.10s.
2. Unrounded cumulative time tracking: master duration is 30.15s.
3. Updated S01: "Milan have made their move, but Mourinho wants him to stay." (5.28s secrecy > 4s).
4. Updated S02: "Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses." (16 tokens).
5. Updated S03: "Reports cite eighty to eighty-five million repurchase figures, but nothing is agreed." (13 tokens, no agreed clause).
6. Updated S04: "Now a left-leg muscle injury complicates matters, with no official return date." (13 tokens, official Nov 23 medical bulletin).
7. S04 Image Key: match action / archival file material; indoor rehabilitation on Nov 23 documented.
8. Image rights status: PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION across all beats.
9. S03 visual: restrained data overlay over dominant football photography (no standalone card).
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def expand_spoken_tokens(text: str) -> List[str]:
    """
    Extracts pronunciation-expanded spoken tokens by splitting compound words
    and stripping punctuation so that duration is calculated on actual speech tokens.
    """
    clean = re.sub(r'[\.,\?!\"“”\']', '', text)
    tokens = []
    for word in clean.split():
        if '-' in word:
            parts = word.split('-')
            tokens.extend([p for p in parts if p])
        else:
            tokens.append(word)
    return tokens


def calculate_spoken_duration_exact(text: str, wpm: float = 138.0) -> Tuple[int, int, float, float]:
    """
    V7.1.6.3 Timing Engine: Calculates exact unrounded duration and displayed rounded duration
    strictly from pronunciation-expanded spoken tokens and pause allowances.
    Formula: duration = (spoken_tokens / configured_wpm * 60) + pause_allowances
    Pause allowances: 0.18s per comma/dash, 0.32s per period/question mark.
    """
    words = text.strip().split()
    written_words = len(words)
    spoken_tokens = expand_spoken_tokens(text)
    token_count = len(spoken_tokens)

    base_speech_sec = (token_count / wpm) * 60.0
    comma_count = text.count(",") + text.count("—")
    period_count = text.count(".") + text.count("?") + text.count("!")
    pause_sec = (comma_count * 0.18) + (period_count * 0.32)

    exact_unrounded = base_speech_sec + pause_sec
    displayed_rounded = round(exact_unrounded, 2)
    return written_words, token_count, exact_unrounded, displayed_rounded


def calculate_spoken_duration(text: str, wpm: float = 138.0) -> Tuple[int, int, float]:
    """Backwards compatibility wrapper returning (written_words, token_count, displayed_duration)."""
    w, t, _, disp = calculate_spoken_duration_exact(text, wpm)
    return w, t, disp


class DualScriptDirector:
    """Produces and synchronizes Script A (Dialogue) and Script B (Image Key)."""

    def generate_endrick_dual_scripts(
        self,
        story_id: str = "endrick_milan",
        run_id: str = "run_v7_1",
        script_version: str = "v7.1.6.3"
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Creates synchronized Script A (Dialogue Screenplay) and Script B (Image Key Screenplay).
        """
        meta = {
            "story_id": story_id,
            "run_id": run_id,
            "script_version": script_version,
            "headline": "MILAN PLOT ENDRICK MOVE AS MOURINHO RESISTS EXIT",
            "source": "Cadena SER / Corriere dello Sport / TNT Sports Brazil / Real Madrid Official",
            "reliability_tier": "REPORTED_AND_OFFICIAL",
            "category": "transfer_and_squad_update",
            "primary_subject": "Endrick",
            "player_age": 20,
            "date_of_birth": "2006-07-21",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "opening_candidates": [
                {
                    "candidate_id": "OPENING_OPT_1_FORMAL_MOVE_MOURINHO_RESISTS",
                    "text": "Milan have made their move, but Mourinho wants him to stay.",
                    "written_words": 11,
                    "spoken_tokens": 11,
                    "secrecy_duration_sec": 5.28,
                    "status": "SELECTED_STRONGEST",
                    "evaluation": "Reflects the stronger reported status (Milan presenting an offer close to €70M per Nov 23 SER report) while concealing Endrick's name and face for 5.28s (>4s threshold)."
                },
                {
                    "candidate_id": "OPENING_OPT_2_WINTER_MOVE_SER",
                    "text": "Milan are pushing for a winter deal, but Mourinho resists.",
                    "written_words": 10,
                    "spoken_tokens": 10,
                    "secrecy_duration_sec": 4.85,
                    "status": "ALTERNATIVE",
                    "evaluation": "Concise, but slightly less active than 'made their move'."
                },
                {
                    "candidate_id": "OPENING_OPT_3_MADRID_RESOLVE",
                    "text": "Milan have presented a winter offer, yet Mourinho wants him to stay.",
                    "written_words": 12,
                    "spoken_tokens": 12,
                    "secrecy_duration_sec": 5.72,
                    "status": "ALTERNATIVE",
                    "evaluation": "Accurate, but higher token count."
                }
            ],
            "asset_tracking_schema": [
                "exact_source_url",
                "asset_id",
                "creator_or_photographer",
                "license_terms",
                "required_attribution",
                "retrieval_date",
                "local_filename",
                "sha256",
                "permitted_usage_and_restrictions"
            ]
        }

        # Raw scene data definitions - V7.1.6.3 Reconciled Package (62 words, 64 spoken tokens, 30.15s)
        scenes_data = [
            {
                "beat_id": "S01",
                "dialogue": "Milan have made their move, but Mourinho wants him to stay.",
                "narrative_purpose": "Anonymous broadcast hook reflecting reported formal proposal from Milan versus Mourinho's desire to retain him, strictly concealing Endrick's name and face (5.28s secrecy > 4s).",
                "fact_ids": ["CLAIM_ENDRICK_04_CADENA_SER_NOV23_FORMAL_OFFER", "CLAIM_ENDRICK_05_CADENA_SER_NOV24_MOURINHO_RESISTANCE"],
                "pronunciation_guidance": "Milan: [mee-LAHN]. Mourinho: [moo-REEN-yoh]. Made their move: punchy opening cadence.",
                "secrecy_requirements": {
                    "player_name_hidden": True,
                    "face_revealed": False,
                    "opening_window_sec": 4.0
                },
                "on_screen": {
                    "kicker": "● TRANSFER REPORT",
                    "headline": "MILAN MAKE MOVE",
                    "subheadline": "MOURINHO WANTS STAY",
                    "status_badge": "REPORTED"
                },
                "image_key": {
                    "visual_narrative_objective": "Establish institutional transfer stakes and financial scale without revealing player face (strict 4-second secrecy policy).",
                    "exact_visual_description": "Evening architectural photograph of the Estadio Santiago Bernabéu, showing the illuminated exterior metallic facade and modern stadium structure under night floodlights. Institutional context with face concealed.",
                    "intended_subject": "Estadio Santiago Bernabéu Exterior Night",
                    "club": "Real Madrid",
                    "event_and_date": "Stadium Architecture / 2024-2026",
                    "shot_type": "Architectural Wide / Night Stadium Atmosphere",
                    "search_queries": [
                        "Estadio Santiago Bernabeu exterior night floodlights",
                        "Santiago Bernabeu stadium architectural exterior"
                    ],
                    "required_visible_elements": [
                        "Santiago Bernabéu metallic facade and floodlights",
                        "Clean architectural framing",
                        "Cinematic night illumination"
                    ],
                    "banned_visual_elements": [
                        "Endrick face (banned in Beat 1)",
                        "Bruno Fernandes",
                        "Manchester United branding",
                        "Watermarks or ticker bars"
                    ],
                    "face_visibility_requirement": "BANNED_OR_CONCEALED (Mandatory 4s opening secrecy rule)",
                    "composition_requirements": "Subject detail centered in [300, 1100], avoiding upper bezel and lower thirds.",
                    "opencv_framing_instructions": "Center crop 9:16 vertical, preserve architectural scale and vertical lighting.",
                    "rights_status": "PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION",
                    "archival_or_contextual_allowed": True
                }
            },
            {
                "beat_id": "S02",
                "dialogue": "Italian reports put Milan's package for Endrick at sixty million fixed, plus ten in potential bonuses.",
                "narrative_purpose": "Subject identity reveal explicitly naming Endrick in narration and attributing Italian reporting (Corriere dello Sport, Nov 16), making the fixed (€60M) and variable (+€10M in potential bonuses) portions unambiguous as an exploratory package.",
                "fact_ids": ["CLAIM_ENDRICK_01_AGE", "CLAIM_ENDRICK_06_CORRIERE_NOV16_PACKAGE_AND_BUYBACK"],
                "pronunciation_guidance": "Endrick: [EN-drick]. Sixty million fixed: deliberate numerical articulation.",
                "secrecy_requirements": {
                    "player_name_hidden": False,
                    "face_revealed": True,
                    "opening_window_sec": 0.0
                },
                "on_screen": {
                    "kicker": "● PROPOSED PACKAGE",
                    "headline": "ENDRICK TARGETED",
                    "subheadline": "€60M FIXED + €10M BONUSES",
                    "status_badge": "PROPOSAL"
                },
                "image_key": {
                    "visual_narrative_objective": "Reveal Endrick in recognisable Real Madrid context matching the spoken reveal.",
                    "exact_visual_description": "Recognisable portrait of 20-year-old Endrick wearing the official Real Madrid white kit at his Santiago Bernabéu presentation, facing the camera with eyes, hairline, and facial expression clear.",
                    "intended_subject": "Endrick (Felipe Moreira de Sousa, age 20)",
                    "club": "Real Madrid",
                    "event_and_date": "Real Madrid Official Presentation / July 2024",
                    "shot_type": "Official Presentation Medium Portrait",
                    "search_queries": [
                        "Endrick Real Madrid presentation portrait",
                        "Endrick holding Real Madrid white kit"
                    ],
                    "required_visible_elements": [
                        "Endrick recognizable facial features",
                        "Real Madrid white kit or official backdrop",
                        "Clear head and chin within safe framing"
                    ],
                    "banned_visual_elements": [
                        "Brazil Seleção jersey (replaced per V7.1.1)",
                        "Palmeiras jersey",
                        "Bruno Fernandes",
                        "Pochettino",
                        "Severed forehead/chin"
                    ],
                    "face_visibility_requirement": "MANDATORY_PROMINENT (Full face visible, upper third)",
                    "composition_requirements": "Face center strictly in upper-third safe zone: y in [260, 780], x in [420, 660] with 10% headroom.",
                    "opencv_framing_instructions": "Detect face, center horizontally, place eyes at 30% from top of 9:16 frame with headroom.",
                    "rights_status": "PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION",
                    "archival_or_contextual_allowed": False
                }
            },
            {
                "beat_id": "S03",
                "dialogue": "Reports cite eighty to eighty-five million repurchase figures, but nothing is agreed.",
                "narrative_purpose": "Attribute the €80M (Corriere dello Sport) and €85M (TNT Sports Brazil) buy-back figures to differing press reports, explicitly establishing that no buy-back clause has been agreed between clubs.",
                "fact_ids": ["CLAIM_ENDRICK_06_CORRIERE_NOV16_PACKAGE_AND_BUYBACK", "CLAIM_ENDRICK_07_TNT_SPORTS_BUYBACK_FIGURE"],
                "pronunciation_guidance": "Eighty to eighty-five million: deliberate measured cadence. Repurchase: [ree-PUR-chuhs].",
                "secrecy_requirements": {
                    "player_name_hidden": False,
                    "face_revealed": True,
                    "opening_window_sec": 0.0
                },
                "on_screen": {
                    "kicker": "● DEAL CLAUSE",
                    "headline": "€80M–€85M REPURCHASE",
                    "subheadline": "REPORTED • NOT AGREED",
                    "status_badge": "UNAGREED"
                },
                "image_key": {
                    "visual_narrative_objective": "Explain the reported transfer figures (€60M fixed + €10M bonuses; separate €80M and €85M buy-back figures reported by different outlets, with no agreed clause) using a restrained data overlay integrated with relevant football photography. Photography remains dominant without standalone rectangular card styling.",
                    "exact_visual_description": "Relevant authentic football photography (Estadio Santiago Bernabéu or pitchside context) as the dominant background, integrated with a restrained typography data overlay presenting the €60M fixed + €10M bonuses proposal, differing €80M / €85M reported buy-back figures, and prominent NOT AGREED status. Restrained 1990s/2000s football-news graphic language without CRT gimmicks, excessive boxes, or generic AI styling.",
                    "intended_subject": "Transfer Context & Authentic Football Photography with Restrained Data Overlay",
                    "club": "Real Madrid / AC Milan",
                    "event_and_date": "Editorial Analysis / November 2026",
                    "shot_type": "Contextual Football Photography with Graphic Typography Overlay",
                    "search_queries": [
                        "Santiago Bernabeu stadium match pitch floodlights",
                        "San Siro Giuseppe Meazza pitchside architectural"
                    ],
                    "required_visible_elements": [
                        "Dominant authentic football photography base",
                        "Restrained data overlay: €60M fixed + €10M bonuses",
                        "Differing €80M and €85M reported buy-back figures",
                        "Prominent NOT AGREED status indicator",
                        "Established typography tokens (Barlow Condensed / Inter / IBM Plex Mono)"
                    ],
                    "banned_visual_elements": [
                        "Large standalone solid rectangular infographic card",
                        "CRT scanlines or retro television gimmicks",
                        "Cluttered dashboard boxes",
                        "Generic AI futuristic styling"
                    ],
                    "face_visibility_requirement": "NOT_APPLICABLE (Stadium / Pitch Photography with Overlay)",
                    "composition_requirements": "Photography dominant across full 1080x1920 canvas; data overlay integrated in safe margins [y: 350-1150].",
                    "opencv_framing_instructions": "Preserve 9:16 vertical proportion and photographic depth.",
                    "rights_status": "PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION",
                    "archival_or_contextual_allowed": True
                }
            },
            {
                "beat_id": "S04",
                "dialogue": "Now a left-leg muscle injury complicates matters, with no official return date.",
                "narrative_purpose": "Factual inclusion of the November 23 official Real Madrid medical bulletin (abductor of left leg, pending evolution, no official return date), using safer spoken phrasing without speculative recovery estimates.",
                "fact_ids": ["CLAIM_ENDRICK_02_MEDICAL_BULLETIN", "CLAIM_ENDRICK_03_INDOOR_TRAINING"],
                "pronunciation_guidance": "Left-leg muscle injury: neutral factual delivery. Complicates matters: clear articulation.",
                "secrecy_requirements": {
                    "player_name_hidden": False,
                    "face_revealed": True,
                    "opening_window_sec": 0.0
                },
                "on_screen": {
                    "kicker": "● MEDICAL BULLETIN",
                    "headline": "LEFT-LEG MUSCLE INJURY",
                    "subheadline": "NO OFFICIAL RETURN DATE",
                    "status_badge": "OFFICIAL"
                },
                "image_key": {
                    "visual_narrative_objective": "Depict Endrick in genuine Real Madrid squad context using verified match competition or archival file material, explicitly clarifying that he is not depicted participating in current outdoor training (as official November 23 club reports confirm he worked indoors inside the facilities).",
                    "exact_visual_description": "Verified competitive match action photograph of Endrick in official Real Madrid kit at the Estadio Santiago Bernabéu (La Liga competitive match action, August 25, 2024 vs Real Valladolid), in competitive athletic movement. Clearly designated as past file material and not depicting his November 2026 indoor rehabilitation condition.",
                    "intended_subject": "Endrick in Real Madrid Competitive Match Action (August 25, 2024 vs Real Valladolid - File Action)",
                    "club": "Real Madrid",
                    "event_and_date": "La Liga Matchday 2 / August 25, 2024",
                    "shot_type": "Competitive Match Action Medium Shot",
                    "search_queries": [
                        "Endrick Real Madrid debut goal Valladolid August 2024",
                        "Endrick Real Madrid match action Santiago Bernabeu"
                    ],
                    "required_visible_elements": [
                        "Endrick in official Real Madrid white match kit",
                        "Competitive match action at the Santiago Bernabéu",
                        "Clear designation as past match action / file photo",
                        "Focused athletic intensity"
                    ],
                    "banned_visual_elements": [
                        "Implication of outdoor squad training on Nov 23 (he trained indoors)",
                        "Palmeiras jersey",
                        "Bruno Fernandes",
                        "Pochettino"
                    ],
                    "face_visibility_requirement": "VISIBLE (Action profile or three-quarters view)",
                    "composition_requirements": "Face in y in [280, 820], action dynamic intact.",
                    "opencv_framing_instructions": "Focus crop around player maintaining competitive pitch action.",
                    "rights_status": "PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION",
                    "archival_or_contextual_allowed": True
                }
            },
            {
                "beat_id": "S05",
                "dialogue": "Will Mourinho keep the Brazilian or will Milan force a compromise?",
                "narrative_purpose": "Closing editorial question driving viewer reflection on the central managerial tension without clichés.",
                "fact_ids": ["CLAIM_ENDRICK_05_CADENA_SER_NOV24_MOURINHO_RESISTANCE"],
                "pronunciation_guidance": "Mourinho: [moo-REEN-yoh]. Force a compromise: measured closing inflection.",
                "secrecy_requirements": {
                    "player_name_hidden": False,
                    "face_revealed": True,
                    "opening_window_sec": 0.0
                },
                "on_screen": {
                    "kicker": "● THE VERDICT",
                    "headline": "MOURINHO OR MILAN?",
                    "subheadline": "SANCTION OR RETAIN",
                    "status_badge": "EDITORIAL"
                },
                "image_key": {
                    "visual_narrative_objective": "Atmospheric stadium closing shot showing the actual San Siro matchday/evening atmosphere.",
                    "exact_visual_description": "Authentic matchday stadium photograph of the Stadio Giuseppe Meazza (San Siro) in Milan, showcasing the iconic red girders, illuminated pitch and stadium tiers under evening sky.",
                    "intended_subject": "Stadio Giuseppe Meazza (San Siro) Evening Matchday",
                    "club": "AC Milan",
                    "event_and_date": "Serie A Matchday / 2024-2026",
                    "shot_type": "Stadium Matchday / Evening Atmospheric",
                    "search_queries": [
                        "San Siro stadium matchday evening floodlights",
                        "Stadio Giuseppe Meazza San Siro match atmosphere"
                    ],
                    "required_visible_elements": [
                        "Iconic San Siro architectural features (spiral towers, red girders)",
                        "Evening stadium illumination",
                        "Authentic matchday setting"
                    ],
                    "banned_visual_elements": [
                        "Daytime generic training pitch",
                        "Bruno Fernandes",
                        "Pochettino",
                        "Watermarks"
                    ],
                    "face_visibility_requirement": "OPTIONAL (Full stadium depth allowed)",
                    "composition_requirements": "Center area open for on-screen discussion callout.",
                    "opencv_framing_instructions": "Vertical 9:16 crop emphasizing stadium grandeur.",
                    "rights_status": "PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION",
                    "archival_or_contextual_allowed": True
                }
            }
        ]

        # V7.1.6.3 Timing Engine: Derive cumulative boundaries strictly from unrounded values
        unrounded_current_time = 0.0
        script_a_beats = []
        script_b_beats = []

        for idx, sc in enumerate(scenes_data):
            w_cnt, t_cnt, exact_dur, disp_dur = calculate_spoken_duration_exact(sc["dialogue"])
            start_disp = round(unrounded_current_time, 2)
            unrounded_current_time += exact_dur
            end_disp = round(unrounded_current_time, 2)

            # S05 display duration is strictly 5.10s (exact: 11/138*60 + 0.32 = 5.1026087s)
            # Master duration derived from unrounded sum: 30.1460870s -> 30.15s
            script_a_beats.append({
                "beat_id": sc["beat_id"],
                "spoken_dialogue": sc["dialogue"],
                "narrative_purpose": sc["narrative_purpose"],
                "fact_claim_ids": sc["fact_ids"],
                "pronunciation_guidance": sc["pronunciation_guidance"],
                "estimated_duration_sec": disp_dur,
                "start_time_sec": start_disp,
                "end_time_sec": end_disp,
                "written_word_count": w_cnt,
                "spoken_token_count": t_cnt,
                "word_count": w_cnt,  # Backward compatibility
                "secrecy_requirements": sc["secrecy_requirements"],
                "on_screen_graphics": sc["on_screen"]
            })

            ik = sc["image_key"]
            script_b_beats.append({
                "beat_id": sc["beat_id"],
                "dialogue_reference": sc["beat_id"],
                "dialogue_snippet": sc["dialogue"][:50] + "...",
                "allocated_duration_sec": disp_dur,
                "start_time_sec": start_disp,
                "end_time_sec": end_disp,
                "spoken_token_count": t_cnt,
                "visual_narrative_objective": ik.get("visual_narrative_objective", ""),
                "exact_image_description": ik.get("exact_visual_description", ik.get("exact_image_description", ik.get("image_visual_description", ""))),
                "intended_subject": ik.get("intended_subject", ""),
                "club": ik.get("club", ""),
                "event_and_date": ik.get("event_and_date", ""),
                "shot_type": ik.get("shot_type", ""),
                "search_queries": ik.get("search_queries", []),
                "required_visible_elements": ik.get("required_visible_elements", []),
                "banned_visual_elements": ik.get("banned_visual_elements", []),
                "face_visibility_requirement": ik.get("face_visibility_requirement", ""),
                "composition_requirements": ik.get("composition_requirements", ""),
                "opencv_framing_instructions": ik.get("opencv_framing_instructions", ""),
                "rights_status": ik.get("rights_status", "PENDING_ASSET_SELECTION_AND_LICENSE_VERIFICATION"),
                "archival_or_contextual_allowed": ik.get("archival_or_contextual_allowed", True)
            })

        total_words = sum(b["written_word_count"] for b in script_a_beats)
        total_tokens = sum(b["spoken_token_count"] for b in script_a_beats)
        total_duration = round(unrounded_current_time, 2)

        script_a = {
            "metadata": {
                **meta,
                "deliverable": "SCRIPT_A_DIALOGUE_SCREENPLAY",
                "total_written_words": total_words,
                "total_spoken_tokens": total_tokens,
                "total_spoken_words": total_words,  # Backward compatibility
                "total_duration_sec": total_duration,
                "target_wpm": 138.0
            },
            "full_spoken_narration": " ".join(b["spoken_dialogue"] for b in script_a_beats),
            "beats": script_a_beats
        }

        script_b = {
            "metadata": {
                **meta,
                "deliverable": "SCRIPT_B_IMAGE_KEY_SCREENPLAY",
                "total_visual_beats": len(script_b_beats),
                "total_written_words": total_words,
                "total_spoken_tokens": total_tokens,
                "total_duration_sec": total_duration
            },
            "image_beats": script_b_beats
        }

        return script_a, script_b

    def format_telegram_message_a_dialogue(self, script_a: Dict[str, Any]) -> str:
        """Formats Message A — Dialogue Screenplay for Telegram."""
        meta = script_a["metadata"]
        candidates = meta.get("opening_candidates", [])
        lines = [
            f"🎬 <b>MESSAGE A — DIALOGUE SCREENPLAY (V7.1.6.3)</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━",
            f"📰 <b>Headline:</b> {meta['headline']}",
            f"📌 <b>Source:</b> {meta['source']} ({meta['reliability_tier']})",
            f"⏱️ <b>Narration Timing:</b> {meta['total_duration_sec']}s ({meta['total_written_words']} written words | {meta['total_spoken_tokens']} spoken tokens @ 138 WPM)",
            f"━━━━━━━━━━━━━━━━━━━━━━\n",
            f"🎯 <b>OPENING HOOK EVALUATION:</b>\n"
        ]

        for cand in candidates:
            status_emoji = "⭐ <b>[SELECTED]</b>" if cand["status"] == "SELECTED_STRONGEST" else "• [ALT]"
            lines.append(
                f"{status_emoji} <i>\"{cand['text']}\"</i>\n"
                f"   ↳ {cand['written_words']} words ({cand['spoken_tokens']} spoken tokens) | {cand['secrecy_duration_sec']}s name & face concealed\n"
                f"   ↳ <i>{cand['evaluation']}</i>\n"
            )

        lines.extend([
            f"🎙️ <b>FULL REVISED SPOKEN SCRIPT:</b>",
            f"<i>\"{script_a['full_spoken_narration']}\"</i>\n",
            f"📋 <b>BEAT-BY-BEAT TIMELINE & TOKEN COUNTS:</b>"
        ])

        for b in script_a["beats"]:
            sec = " [4s+ Opening Secrecy Active]" if b["secrecy_requirements"]["player_name_hidden"] else ""
            lines.append(
                f"<b>[{b['beat_id']} | {b['start_time_sec']}s–{b['end_time_sec']}s ({b['estimated_duration_sec']}s | {b['written_word_count']}w / {b['spoken_token_count']}t)]</b>{sec}\n"
                f"🗣️ <i>\"{b['spoken_dialogue']}\"</i>\n"
                f"🎯 <b>Role:</b> {b['narrative_purpose']}\n"
                f"📺 <b>Graphics:</b> {b['on_screen_graphics']['headline']} — {b['on_screen_graphics']['subheadline']}\n"
            )

        return "\n".join(lines)

    def format_telegram_message_b_image_key(self, script_b: Dict[str, Any]) -> str:
        """Formats Message B — Image Key Screenplay for Telegram."""
        meta = script_b["metadata"]
        lines = [
            f"🖼️ <b>MESSAGE B — IMAGE KEY SCREENPLAY (V7.1.6.3)</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━",
            f"🎯 <b>Visual Production Blueprint</b>",
            f"📌 <b>Story:</b> {meta['headline']}",
            f"⏱️ <b>Total Visual Beats:</b> {meta['total_visual_beats']} ({meta['total_duration_sec']}s | {meta.get('total_spoken_tokens', 64)} spoken tokens)",
            f"━━━━━━━━━━━━━━━━━━━━━━\n",
            f"📋 <b>PROPOSED IMAGE DESCRIPTIONS:</b>\n"
        ]

        for b in script_b["image_beats"]:
            lines.append(
                f"<b>━━━━━━━━ BEAT {b['beat_id']} ({b['allocated_duration_sec']}s | {b.get('spoken_token_count', 0)} tokens) ━━━━━━━━</b>\n"
                f"🗣️ <b>Dialogue:</b> <i>\"{b['dialogue_snippet']}\"</i>\n"
                f"🎯 <b>Narrative Goal:</b> {b['visual_narrative_objective']}\n"
                f"📷 <b>Visual to Search:</b>\n{b['exact_image_description']}\n"
                f"🔍 <b>Search Queries:</b>\n• \"{b['search_queries'][0]}\"\n• \"{b['search_queries'][1]}\"\n"
                f"👤 <b>Face Rule:</b> {b['face_visibility_requirement']}\n"
                f"📐 <b>Framing:</b> {b['opencv_framing_instructions']}\n"
                f"📋 <b>Rights Status:</b> {b['rights_status']}\n"
                f"🚫 <b>Banned:</b> {', '.join(b['banned_visual_elements'][:3])}\n"
            )

        return "\n".join(lines)
