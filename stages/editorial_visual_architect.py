"""
beta/stages/editorial_visual_architect.py
Node 2: Editorial Visual Architect for the 16-Shot Editorial Timeline.
Translates the StoryDossier and 5-Beat Dual-Script into a strictly curated
16-shot visual specification adhering to V7.1.6.7 Broadcast Rules:
- Enforces identity concealment during S01 (stadium facade, manager, pitch atmosphere).
- Enforces authentic protagonist imagery for S02 reveal, S04 medical/complication, and S05 verdict.
- BANS generic third-party player photos, empty grass aerials, and unrelated football clutter.
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class EditorialShotSpec:
    shot_id: str             # e.g. "S01_shot1"
    scene_id: str            # e.g. "S01"
    index: int               # 1..16
    role: str                # "stadium_facade", "manager_touchline", "protagonist_reveal", etc.
    primary_entity: str      # Exact entity name e.g. "Calvin Bassey", "Marco Silva", "Craven Cottage"
    club_affiliation: str    # e.g. "Fulham", "Manchester United"
    crop_strategy: str       # "portrait", "match_action", "celebration", "managerial", "tactical"
    search_queries: List[str]# Exact targeted search queries in priority order
    avoid_terms: List[str]   # Explicit terms to disqualify (e.g. "Manchester United player in red")
    required_context: str    # What the shot must corroborate
    allow_fallback_crest: bool = False # Allow high-res crest card if genuine photo unavailable

class EditorialVisualArchitect:
    """Plans the 16-shot visual timeline ensuring perfect corroboration with the broadcast news."""

    @staticmethod
    def plan_16_shots(dossier) -> List[EditorialShotSpec]:
        p = dossier.protagonist_name
        curr = dossier.current_club
        purs = dossier.pursuing_club
        mgr = dossier.current_manager

        specs: List[EditorialShotSpec] = [
            # -------------------------------------------------------------
            # S01: THE HOOK & CONCEALMENT (3 Shots)
            # Must conceal protagonist identity for >= 4 seconds!
            # -------------------------------------------------------------
            EditorialShotSpec(
                shot_id="S01_shot1",
                scene_id="S01",
                index=1,
                role="stadium_floodlights_opening",
                primary_entity=f"{curr} stadium matchday",
                club_affiliation=curr,
                crop_strategy="tactical",
                search_queries=[
                    f"{curr} stadium floodlights matchday night atmosphere",
                    f"{curr} Craven Cottage pitch floodlights matchday" if "fulham" in curr.lower() else f"{curr} stadium match night crowd",
                    f"{curr} stadium packed stands night"
                ],
                avoid_terms=[p, "street", "sidewalk", "streetline", "panorama", "brick wall", "road", "bench", "dugout", "empty grass", "aerial field", "drawing", "cartoon", "vecteezy"],
                required_context="Grand cinematic matchday stadium under floodlights packed with crowd for opening frame",
                allow_fallback_crest=True
            ),
            EditorialShotSpec(
                shot_id="S01_shot2",
                scene_id="S01",
                index=2,
                role="manager_intense_touchline",
                primary_entity=mgr,
                club_affiliation=curr,
                crop_strategy="managerial",
                search_queries=[
                    f'"{mgr}" manager passionate touchline {curr}',
                    f'"{mgr}" manager press conference interview {curr}',
                    f'"{mgr}" manager serious touchline instructions'
                ],
                avoid_terms=[p, "bench empty", "dugout empty", "sideline bench", "playing football", "as a player", "street"],
                required_context="Current manager directing tactics or reacting on touchline with intense expression"
            ),
            EditorialShotSpec(
                shot_id="S01_shot3",
                scene_id="S01",
                index=3,
                role="pitch_match_tension",
                primary_entity=f"{curr} match",
                club_affiliation=curr,
                crop_strategy="match_action",
                search_queries=[
                    f"{curr} Premier League match battle action pitch",
                    f"{curr} football match night floodlights duel",
                    f"{curr} vs {purs} competitive match action"
                ],
                avoid_terms=["cartoon", "fifa", "ea fc", "stadium seats empty", "vecteezy", "stock", "clipart", "illustration"],
                required_context="High-intensity match play setting the competitive stakes"
            ),

            # -------------------------------------------------------------
            # S02: THE DRAMATIC REVEAL (3 Shots)
            # Explicitly names protagonist. Visuals MUST corroborate protagonist!
            # -------------------------------------------------------------
            EditorialShotSpec(
                shot_id="S02_shot1",
                scene_id="S02",
                index=4,
                role="protagonist_reveal_portrait",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="portrait",
                search_queries=[
                    f"{p} {curr} portrait",
                    f"{p} {curr} official photo",
                    f"{p} {curr} headshot",
                    f"{p} football portrait"
                ],
                avoid_terms=["multiple players", "fan drawing", "stat card", "fifa card"],
                required_context="Direct, high-definition portrait of the protagonist"
            ),
            EditorialShotSpec(
                shot_id="S02_shot2",
                scene_id="S02",
                index=5,
                role="protagonist_celebration",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="celebration",
                search_queries=[
                    f"{p} celebration {curr}",
                    f"{p} match celebration",
                    f"{p} goal celebration passion"
                ],
                avoid_terms=["crowd slice", "blurry action", "fan selfie"],
                required_context="Protagonist celebrating in club colours"
            ),
            EditorialShotSpec(
                shot_id="S02_shot3",
                scene_id="S02",
                index=6,
                role="protagonist_match_action",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="match_action",
                search_queries=[
                    f"{p} {curr} match action",
                    f"{p} pitch action focus",
                    f"{p} premier league match"
                ],
                avoid_terms=["substitute bench empty", "cartoon"],
                required_context="Protagonist executing competitive play on the pitch"
            ),

            # -------------------------------------------------------------
            # S03: TRANSFER FIGURES & CLAUSES (4 Shots)
            # Numbers, negotiation, suitor interest. NO generic red shirts!
            # -------------------------------------------------------------
            EditorialShotSpec(
                shot_id="S03_shot1",
                scene_id="S03",
                index=7,
                role="suitor_stadium_exterior",
                primary_entity=f"{purs} stadium",
                club_affiliation=purs,
                crop_strategy="tactical",
                search_queries=[
                    f"{purs} Old Trafford stadium exterior facade" if "man" in purs.lower() else f"{purs} stadium exterior facade",
                    f"{purs} stadium entrance night",
                    f"{purs} boardroom executive entrance"
                ],
                avoid_terms=[p, "crowd selfie", "fan drawing", "aerial grass"],
                required_context="The pursuing heavyweight club headquarters establishing the destination",
                allow_fallback_crest=True
            ),
            EditorialShotSpec(
                shot_id="S03_shot2",
                scene_id="S03",
                index=8,
                role="protagonist_match_dominance",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="match_action",
                search_queries=[
                    f"{p} match action {curr}",
                    f"{p} premier league match",
                    f"{p} defensive clearance"
                ],
                avoid_terms=["unrelated player", "fifa card"],
                required_context="Protagonist displaying the elite quality justifying the transfer fee"
            ),
            EditorialShotSpec(
                shot_id="S03_shot3",
                scene_id="S03",
                index=9,
                role="manager_negotiation_reaction",
                primary_entity=mgr,
                club_affiliation=curr,
                crop_strategy="managerial",
                search_queries=[
                    f"{mgr} press conference {curr}",
                    f"{mgr} manager interview serious",
                    f"{mgr} touchline reaction"
                ],
                avoid_terms=[p, "playing football"],
                required_context="Current club manager addressing transfer speculation"
            ),
            EditorialShotSpec(
                shot_id="S03_shot4",
                scene_id="S03",
                index=10,
                role="protagonist_contract_focus",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="portrait",
                search_queries=[
                    f"{p} presentation suit",
                    f"{p} media portrait {curr}",
                    f"{p} official profile photo"
                ],
                avoid_terms=["blurry crowd", "stat graphic"],
                required_context="Professional editorial portrait supporting contract discussion"
            ),

            # -------------------------------------------------------------
            # S04: THE COMPLICATION / MEDICAL (3 Shots)
            # Physical bulletin, medical, or squad friction.
            # -------------------------------------------------------------
            EditorialShotSpec(
                shot_id="S04_shot1",
                scene_id="S04",
                index=11,
                role="protagonist_frustration_walking",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="portrait",
                search_queries=[
                    f"{p} walking off pitch serious",
                    f"{p} frustrated match reaction",
                    f"{p} pitch reaction"
                ],
                avoid_terms=["laughing", "smiling", "fan selfie"],
                required_context="Protagonist displaying serious emotion or walking off pitch"
            ),
            EditorialShotSpec(
                shot_id="S04_shot2",
                scene_id="S04",
                index=12,
                role="manager_tactical_concern",
                primary_entity=mgr,
                club_affiliation=curr,
                crop_strategy="managerial",
                search_queries=[
                    f"{mgr} press conference serious",
                    f"{mgr} manager concerned touchline",
                    f"{mgr} talking to players"
                ],
                avoid_terms=[p, "laughing"],
                required_context="Manager expressing tactical concern or medical update"
            ),
            EditorialShotSpec(
                shot_id="S04_shot3",
                scene_id="S04",
                index=13,
                role="protagonist_training_fitness",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="match_action",
                search_queries=[
                    f"{p} training session {curr}",
                    f"{p} fitness drill running",
                    f"{p} training ground pitch"
                ],
                avoid_terms=["aerial pitch", "empty field", "unrelated squad"],
                required_context="Protagonist training or undergoing fitness assessment"
            ),

            # -------------------------------------------------------------
            # S05: THE VERDICT & CLOSING DEBATE (3 Shots)
            # High-impact closing argument.
            # -------------------------------------------------------------
            EditorialShotSpec(
                shot_id="S05_shot1",
                scene_id="S05",
                index=14,
                role="protagonist_verdict_portrait",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="portrait",
                search_queries=[
                    f"{p} close up portrait hd",
                    f"{p} serious face portrait",
                    f"{p} official headshot {curr}"
                ],
                avoid_terms=["multiple players", "blurry background"],
                required_context="High-impact intense close-up of the protagonist"
            ),
            EditorialShotSpec(
                shot_id="S05_shot2",
                scene_id="S05",
                index=15,
                role="matchday_head_to_head",
                primary_entity=f"{curr} matchday",
                club_affiliation=curr,
                crop_strategy="tactical",
                search_queries=[
                    f"{curr} stadium floodlights night match",
                    f"{curr} vs {purs} premier league matchday",
                    f"{curr} match atmosphere fans"
                ],
                avoid_terms=["empty seats", "fifa card"],
                required_context="Electric stadium atmosphere setting up the fan debate",
                allow_fallback_crest=True
            ),
            EditorialShotSpec(
                shot_id="S05_shot3",
                scene_id="S05",
                index=16,
                role="protagonist_final_determination",
                primary_entity=p,
                club_affiliation=curr,
                crop_strategy="celebration",
                search_queries=[
                    f"{p} match passion celebration",
                    f"{p} determined pitch walk",
                    f"{p} match action celebration"
                ],
                avoid_terms=["blurry", "substitute bench"],
                required_context="Protagonist with resolute expression driving the closing debate"
            )
        ]
        return specs
