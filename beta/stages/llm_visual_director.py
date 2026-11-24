"""
beta/stages/llm_visual_director.py
Node 2: LLM Visual Director (GPT OSS / Qwen 27B).
Translates an 8-scene broadcast screenplay into verified real-world visual specifications:
1. Ignores Scene 8 (Ending Card Outro).
2. For each story scene, asks GPT OSS (or Qwen 27B):
   "For a football channel, describe in one sentence the real-world photograph that should be shown here."
3. In positions of "OR" / "AND" choices (such as the closing dilemma S07), derives TWO distinct
   one-sentence image descriptions to visually corroborate both parts of the choice.
4. Derives targeted search queries from the descriptions for full-res image scraping.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from beta.stages.groq_client import call_groq_chat
from beta.pipeline.neural_instructions import StoryDossier, CONFIGURED_LLM_MODEL, CONFIGURED_LLM_FALLBACK
from beta.stages.fact_checker import FactChecker

@dataclass
class EditorialShotSpec:
    shot_id: str             # e.g. "S01_shot1", "S07_shot1"
    scene_id: str            # e.g. "S01", "S07"
    index: int               # Sequential index across timeline
    role: str                # e.g. "llm_scene_corroboration", "choice_part1", "choice_part2"
    primary_entity: str      # Exact entity name e.g. "Calvin Bassey", "Marco Silva", "Craven Cottage"
    club_affiliation: str    # e.g. "Fulham", "Manchester United"
    crop_strategy: str       # "portrait", "match_action", "celebration", "managerial", "tactical"
    search_queries: List[str]# Exact targeted search queries in priority order
    avoid_terms: List[str]   # Explicit terms to disqualify
    required_context: str    # One-sentence visual description from GPT OSS
    allow_fallback_crest: bool = True


class LLMVisualDirector:
    """Uses GPT OSS (or Qwen 27B) to visually direct every scene in the 8-scene broadcast."""

    def __init__(self, preferred_model: str = CONFIGURED_LLM_MODEL, fallback_model: str = CONFIGURED_LLM_FALLBACK):
        self.preferred_model = preferred_model
        self.fallback_model = fallback_model

    def describe_single_scene(self, scene_id: str, narration: str, dossier: StoryDossier) -> Dict[str, Any]:
        """Asks GPT OSS for a one-sentence real photograph description for a scene with dynamic action and verified facts."""
        is_s01 = (scene_id == "S01")
        suitor_mgr = FactChecker.get_verified_manager(dossier.pursuing_club)
        suitor_std = FactChecker.get_verified_stadium(dossier.pursuing_club)
        curr_std = FactChecker.get_verified_stadium(dossier.current_club)

        s01_guidance = (
            f"IMPORTANT FOR S01 (HOOK & CONCEALMENT): The protagonist's face/identity MUST NOT be shown yet. "
            f"Describe {dossier.current_club}'s stadium ({curr_std}) under floodlights, pitch atmosphere, or manager {dossier.current_manager} directing tactical play.\n"
            if is_s01 else ""
        )

        sys_prompt = (
            "You are the Visual Director for a top-tier football television news channel. "
            "Respond ONLY with a valid JSON object."
        )
        user_prompt = f"""Story Headline: {dossier.main_headline}
Scene ID: {scene_id}
Spoken Narration: "{narration}"
Protagonist: {dossier.protagonist_name}
Current Club: {dossier.current_club} (Manager: {dossier.current_manager}, Stadium: {curr_std})
Pursuing Club: {dossier.pursuing_club} (Current Manager: {suitor_mgr}, Stadium: {suitor_std})

{s01_guidance}For a football channel, describe in EXACTLY ONE sentence the real-world photograph that should be shown here to visually corroborate this scene.
Must be an authentic football photograph (match action, dynamic tackles, celebrations, training drills, stadium floodlights, press conference).
NO illustrations, NO drawings, NO empty benches or sidewalks.

EDITORIAL ACCURACY, DYNAMIC ACTION & FACT-CHECKING REQUIREMENTS:
1. FACT-CHECKED CLUB HEAD COACHES:
   - {dossier.current_club} head coach is: {dossier.current_manager}.
   - {dossier.pursuing_club} head coach is: {suitor_mgr}.
   NEVER use obsolete or incorrect coaches. If describing {dossier.pursuing_club}'s coach, use {suitor_mgr}.
2. MANDATE DYNAMIC ACTION PHOTOGRAPHY (NO STATIC STANDING POSES):
   - For players: NEVER describe a player just standing still or posing for a photo. Require dynamic match action: sliding tackles, aggressive sprinting, intense ball duels, passionate celebrations, or sharp training drills.
   - For managers: Describe animated touchline shouting, tactical hand signals, or intense press conference reactions.
3. SEARCH QUERY PRECISION:
   - Always include full names, club, and action: e.g. "{dossier.protagonist_name} {dossier.current_club} tackle match action", "{dossier.current_manager} {dossier.current_club} touchline tactical instructions", or "{suitor_mgr} {dossier.pursuing_club} coach press conference".
4. Accurate club kits: {dossier.protagonist_name} currently plays for {dossier.current_club}. Never put him in an opponent's kit.

Output JSON schema:
{{
  "image_description": "exactly one sentence describing the real action photograph",
  "search_query": "concise 4-6 word search query with action keywords to find this real photo",
  "primary_entity": "name of player, manager, or stadium"
}}"""

        raw = call_groq_chat(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            preferred_model=self.preferred_model,
            fallback_model=self.fallback_model,
            temperature=0.2,
            timeout=15
        )

        default_entity = f"{dossier.current_club} stadium matchday" if is_s01 else dossier.protagonist_name
        default_query = f"{dossier.current_club} stadium floodlights matchday" if is_s01 else f"{dossier.protagonist_name} {dossier.current_club} match"
        default_desc = f"A real matchday photograph corroborating {default_entity}."

        if raw:
            try:
                clean = re.sub(r'^```json\s*', '', raw.strip(), flags=re.MULTILINE)
                clean = re.sub(r'```$', '', clean.strip(), flags=re.MULTILINE)
                m = re.search(r'\{.*\}', clean, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    desc = parsed.get("image_description", "").strip() or default_desc
                    query = parsed.get("search_query", "").strip() or default_query
                    entity = parsed.get("primary_entity", "").strip() or default_entity
                    return {
                        "image_description": desc,
                        "search_query": query,
                        "primary_entity": entity
                    }
            except Exception as e:
                print(f"[LLMVisualDirector] Parse note ({e}), using default scene mapping.")

        return {
            "image_description": default_desc,
            "search_query": default_query,
            "primary_entity": default_entity
        }

    def describe_choice_scene(self, scene_id: str, narration: str, dossier: StoryDossier) -> Dict[str, Any]:
        """Asks GPT OSS for TWO distinct action photograph descriptions for an 'OR' / 'AND' choice scene with verified facts."""
        suitor_mgr = FactChecker.get_verified_manager(dossier.pursuing_club)
        suitor_std = FactChecker.get_verified_stadium(dossier.pursuing_club)
        curr_std = FactChecker.get_verified_stadium(dossier.current_club)

        sys_prompt = (
            "You are the Visual Director for a top-tier football television news channel. "
            "Respond ONLY with a valid JSON object."
        )
        user_prompt = f"""Story Headline: {dossier.main_headline}
Scene ID: {scene_id}
Spoken Narration: "{narration}"
Protagonist: {dossier.protagonist_name}
Current Club: {dossier.current_club} (Manager: {dossier.current_manager}, Stadium: {curr_std})
Pursuing Club: {dossier.pursuing_club} (Current Head Coach: {suitor_mgr}, Stadium: {suitor_std})

This football news scene presents an "OR" / "AND" choice between two sides of a transfer debate.
For a football channel, describe TWO distinct real-world photographs in exactly one sentence each to show the two parts:
1. Part 1 (First part of the choice): Describe in one sentence the action photograph for Part 1 ({dossier.protagonist_name} in match action for {dossier.current_club} or manager {dossier.current_manager} on touchline).
2. Part 2 (Second part of the choice): Describe in one sentence the photograph for Part 2 ({dossier.pursuing_club} head coach {suitor_mgr} in tactical press conference/touchline, or their iconic stadium {suitor_std} under lights).

DYNAMIC ACTION & SEARCH QUERY RULES:
- Never use generic terms like "coach", "manager", "football official", or "match".
- Mandate action: sliding tackle, duel, celebration, or passionate tactical instruction. NO static portraits.
- Always include full names and clubs: e.g. "{dossier.protagonist_name} {dossier.current_club} tackle match action", "{suitor_mgr} {dossier.pursuing_club} coach press conference", or "{suitor_std} matchday floodlights night".

Output JSON schema:
{{
  "part1_description": "one sentence describing real action photograph for Part 1",
  "part1_query": "concise 4-6 word search query for Part 1",
  "part1_entity": "primary entity for Part 1",
  "part2_description": "one sentence describing real action photograph for Part 2",
  "part2_query": "concise 4-6 word search query for Part 2",
  "part2_entity": "primary entity for Part 2"
}}"""

        raw = call_groq_chat(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            preferred_model=self.preferred_model,
            fallback_model=self.fallback_model,
            temperature=0.2,
            timeout=15
        )

        p1_desc = f"{dossier.current_manager} directing tactical instructions on the {dossier.current_club} touchline."
        p1_query = f"{dossier.current_manager} {dossier.current_club} manager touchline"
        p1_entity = dossier.current_manager

        p2_desc = f"{suitor_mgr} directing tactical preparations for {dossier.pursuing_club}."
        p2_query = f"{suitor_mgr} {dossier.pursuing_club} coach press conference"
        p2_entity = suitor_mgr

        if raw:
            try:
                clean = re.sub(r'^```json\s*', '', raw.strip(), flags=re.MULTILINE)
                clean = re.sub(r'```$', '', clean.strip(), flags=re.MULTILINE)
                m = re.search(r'\{.*\}', clean, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    return {
                        "part1_description": parsed.get("part1_description", p1_desc),
                        "part1_query": parsed.get("part1_query", p1_query),
                        "part1_entity": parsed.get("part1_entity", p1_entity),
                        "part2_description": parsed.get("part2_description", p2_desc),
                        "part2_query": parsed.get("part2_query", p2_query),
                        "part2_entity": parsed.get("part2_entity", p2_entity),
                    }
            except Exception as e:
                print(f"[LLMVisualDirector] Choice parse note ({e}), using default dual mapping.")

        return {
            "part1_description": p1_desc,
            "part1_query": p1_query,
            "part1_entity": p1_entity,
            "part2_description": p2_desc,
            "part2_query": p2_query,
            "part2_entity": p2_entity,
        }

    def plan_visual_timeline(self, screenplay_scenes: List[Dict[str, Any]], dossier: StoryDossier) -> List[EditorialShotSpec]:
        """
        Translates the 8-scene screenplay into shot specifications:
        - Skips Scene 8 (Ending Card Outro).
        - For scenes S01..S06: derives 1-sentence image description and search query.
        - For scene S07 (or any choice beat with 'or' / 'and'): derives TWO image descriptions to show both parts.
        """
        specs: List[EditorialShotSpec] = []
        shot_counter = 1

        print(f"\n[LLMVisualDirector] Directing visual shots via {self.preferred_model} for {len(screenplay_scenes)} scenes...")

        for sc in screenplay_scenes:
            sid = sc.get("scene_id", "")
            # Requirement: 1 scene is ending card -> don't bother
            if sid.lower() in ("outro", "s08", "scene_8"):
                print(f"  [{sid}] Ending card detected — skipping visual image scraping as instructed.")
                continue

            narration = sc.get("spoken_narration", "")
            narr_lower = narration.lower()

            # Detect if this scene represents an 'OR' / 'AND' choice (closing dilemma S07 or choice keywords)
            is_choice = (
                sid == "S07" or
                (" or " in narr_lower and "?" in narr_lower) or
                ("will " in narr_lower and " or " in narr_lower) or
                ("keep " in narr_lower and " or " in narr_lower)
            )

            if is_choice:
                print(f"  [{sid}] Detected 'OR' / 'AND' choice dilemma -> Generating 2 image descriptions for both parts...")
                choice_data = self.describe_choice_scene(sid, narration, dossier)

                # Part 1 Shot
                p1_query = choice_data["part1_query"].replace('"', '')
                specs.append(EditorialShotSpec(
                    shot_id=f"{sid}_shot1",
                    scene_id=sid,
                    index=shot_counter,
                    role="choice_part1_home",
                    primary_entity=choice_data["part1_entity"],
                    club_affiliation=dossier.current_club,
                    crop_strategy="managerial" if "manager" in choice_data["part1_entity"].lower() or dossier.current_manager.lower() in choice_data["part1_entity"].lower() else "match_action",
                    search_queries=[
                        f"{p1_query}",
                        f"{choice_data['part1_entity']} {dossier.current_club} match",
                        f"{choice_data['part1_entity']} press conference"
                    ],
                    avoid_terms=["street", "sidewalk", "streetline", "empty bench", "empty dugout", "drawing", "cartoon"],
                    required_context=choice_data["part1_description"]
                ))
                shot_counter += 1

                # Part 2 Shot
                p2_query = choice_data["part2_query"].replace('"', '')
                specs.append(EditorialShotSpec(
                    shot_id=f"{sid}_shot2",
                    scene_id=sid,
                    index=shot_counter,
                    role="choice_part2_suitor",
                    primary_entity=choice_data["part2_entity"],
                    club_affiliation=dossier.pursuing_club,
                    crop_strategy="tactical",
                    search_queries=[
                        f"{p2_query}",
                        f"Ruben Amorim {dossier.pursuing_club} coach" if "manchester united" in dossier.pursuing_club.lower() else f"{choice_data['part2_entity']} coach",
                        f"{dossier.pursuing_club} Old Trafford floodlights night" if "manchester united" in dossier.pursuing_club.lower() else f"{dossier.pursuing_club} stadium floodlights night"
                    ],
                    avoid_terms=["street", "sidewalk", "streetline", "empty bench", "empty dugout", "drawing", "cartoon"],
                    required_context=choice_data["part2_description"]
                ))
                shot_counter += 1

            else:
                print(f"  [{sid}] Asking {self.preferred_model} for 1-sentence image description...")
                single_data = self.describe_single_scene(sid, narration, dossier)
                q = single_data["search_query"].replace('"', '')
                entity = single_data["primary_entity"]

                # Determine crop strategy based on entity and scene
                if sid == "S01":
                    crop_strat = "tactical"
                    club_affil = dossier.current_club
                    avoid = [dossier.protagonist_name, "street", "sidewalk", "streetline", "empty bench", "empty dugout", "drawing", "cartoon"]
                elif "manager" in entity.lower() or dossier.current_manager.lower() in entity.lower():
                    crop_strat = "managerial"
                    club_affil = dossier.current_club
                    avoid = ["street", "sidewalk", "empty bench", "empty dugout", "drawing", "cartoon"]
                elif dossier.protagonist_name.lower() in entity.lower():
                    crop_strat = "portrait" if sid == "S02" else "match_action"
                    club_affil = dossier.current_club
                    avoid = ["unrelated player", "street", "sidewalk", "drawing", "cartoon"]
                elif dossier.pursuing_club.lower() in entity.lower():
                    crop_strat = "tactical"
                    club_affil = dossier.pursuing_club
                    avoid = ["street", "sidewalk", "drawing", "cartoon"]
                else:
                    crop_strat = "match_action"
                    club_affil = dossier.current_club
                    avoid = ["street", "sidewalk", "drawing", "cartoon"]

                specs.append(EditorialShotSpec(
                    shot_id=f"{sid}_shot1",
                    scene_id=sid,
                    index=shot_counter,
                    role=f"scene_{sid.lower()}_visual",
                    primary_entity=entity,
                    club_affiliation=club_affil,
                    crop_strategy=crop_strat,
                    search_queries=[
                        f"{q}",
                        f"{entity} {club_affil} match action",
                        f"{entity} {club_affil} training"
                    ],
                    avoid_terms=avoid,
                    required_context=single_data["image_description"]
                ))
                shot_counter += 1

        print(f"[LLMVisualDirector] Successfully planned {len(specs)} shots for story timeline.")
        return specs
