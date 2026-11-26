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

try:
    from stages.groq_client import call_groq_chat
    from pipeline.neural_instructions import StoryDossier, CONFIGURED_LLM_MODEL, CONFIGURED_LLM_FALLBACK
    from stages.fact_checker import FactChecker
except ModuleNotFoundError:
    from stages.groq_client import call_groq_chat
    from pipeline.neural_instructions import StoryDossier, CONFIGURED_LLM_MODEL, CONFIGURED_LLM_FALLBACK
    from stages.fact_checker import FactChecker

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
    use_club_crest: bool = False
    prefer_landscape: bool = False
    layout_preference: str = "auto"


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
        - For scenes S01..S06: derives 1-sentence image description and action search query.
        - For scene S07 (or any choice beat with 'or' / 'and'): derives TWO image descriptions to show both parts.
        - Blocks obsolete/former managers from FactChecker across all queries and avoid_terms.
        """
        dossier = FactChecker.audit_and_enrich_dossier(dossier)
        suitor_mgr = dossier.pursuing_manager or FactChecker.get_verified_manager(dossier.pursuing_club)
        suitor_std = dossier.pursuing_stadium or FactChecker.get_verified_stadium(dossier.pursuing_club)
        curr_std = dossier.current_stadium or FactChecker.get_verified_stadium(dossier.current_club)
        cat_low = (getattr(dossier, "story_category", "") or "").lower()
        obsolete_terms = (
            FactChecker.get_obsolete_managers(dossier.current_club) +
            FactChecker.get_obsolete_managers(dossier.pursuing_club)
        )
        base_avoid = [
            "street", "sidewalk", "streetline", "empty bench", "empty dugout",
            "drawing", "cartoon", "static portrait", "match preview", "lineup", "news18",
            "conference hall", "empty chairs", "score prediction"
        ] + obsolete_terms

        # Vary which 1 beat showcases dual stacked landscape split (Top from Left + Bottom from Right) per story
        dual_seed = sum(ord(ch) for ch in (dossier.story_id or "news")) % 3
        dual_split_scene = ["S04", "S06", "S02"][dual_seed]
        if cat_low == "managerial_change" and dual_split_scene == "S02":
            dual_split_scene = "S04"

        specs: List[EditorialShotSpec] = []
        shot_counter = 1

        print(f"\n[LLMVisualDirector] Directing visual shots via {self.preferred_model} for {len(screenplay_scenes)} scenes...")

        def _sanitize_obsolete(text_val: str, fallback_val: str) -> str:
            low = (text_val or "").lower()
            for obs in obsolete_terms:
                if obs and obs in low:
                    print(f"[LLMVisualDirector] Blocked stale entity '{obs}' in visual spec -> substituting '{fallback_val}'")
                    return fallback_val
            return text_val or fallback_val

        def _normalize_entity(raw_ent: str, fallback_ent: str) -> str:
            ent = _sanitize_obsolete(raw_ent, fallback_ent)
            low = ent.lower()
            for canon in [dossier.protagonist_name, dossier.current_manager, suitor_mgr, curr_std, suitor_std]:
                if canon and canon.lower() in low:
                    return canon
            return ent

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

                # Part 1 Shot (Selling club protagonist / match action — NEVER tiny boxed card)
                p1_default_ent = dossier.current_manager if cat_low == "managerial_change" else dossier.protagonist_name
                p1_entity = _normalize_entity(choice_data["part1_entity"], p1_default_ent)
                if cat_low != "managerial_change" and dossier.protagonist_name.lower() in p1_entity.lower():
                    p1_entity = dossier.protagonist_name
                p1_query = _sanitize_obsolete(choice_data["part1_query"].replace('"', ''), f"{p1_entity} {dossier.current_club} match action")
                p1_desc = _sanitize_obsolete(choice_data["part1_description"], f"{p1_entity} in dynamic action for {dossier.current_club}.")
                specs.append(EditorialShotSpec(
                    shot_id=f"{sid}_shot1",
                    scene_id=sid,
                    index=shot_counter,
                    role="choice_part1_home",
                    primary_entity=p1_entity,
                    club_affiliation=dossier.current_club,
                    crop_strategy="managerial" if ("manager" in p1_entity.lower() or dossier.current_manager.lower() in p1_entity.lower()) else "match_action",
                    search_queries=[
                        f"{p1_query}",
                        f"{p1_entity} {dossier.current_club} match action",
                        f"{dossier.protagonist_name} {dossier.current_club} celebration"
                    ],
                    avoid_terms=list(base_avoid),
                    required_context=p1_desc,
                    layout_preference="split_duel"
                ))
                shot_counter += 1

                # Part 2 Shot: For player-transfer destination debates, feature Pursuing Club Stadium + Transparent Crest Overlay
                # so viewers immediately see the suitor club identity (never an unlabelled face!)
                use_suitor_emblem = (cat_low != "managerial_change") and bool(dossier.pursuing_club) and ("rival" not in dossier.pursuing_club.lower())
                if use_suitor_emblem:
                    p2_entity = suitor_std
                    p2_query = f"{suitor_std} {dossier.pursuing_club} stadium floodlights night"
                    p2_desc = f"{suitor_std} floodlit matchnight stadium featuring transparent {dossier.pursuing_club} crest."
                    p2_strat = "tactical"
                else:
                    p2_entity = _normalize_entity(choice_data["part2_entity"], suitor_mgr)
                    p2_query = _sanitize_obsolete(choice_data["part2_query"].replace('"', ''), f"{suitor_mgr} {dossier.pursuing_club} touchline")
                    p2_desc = _sanitize_obsolete(choice_data["part2_description"], f"{suitor_mgr} directing tactical instructions for {dossier.pursuing_club}.")
                    p2_strat = "managerial" if (suitor_mgr.lower() in p2_entity.lower() or "coach" in p2_entity.lower() or "manager" in p2_entity.lower()) else "tactical"
                specs.append(EditorialShotSpec(
                    shot_id=f"{sid}_shot2",
                    scene_id=sid,
                    index=shot_counter,
                    role="choice_part2_suitor",
                    primary_entity=p2_entity,
                    club_affiliation=dossier.pursuing_club,
                    crop_strategy=p2_strat,
                    search_queries=[
                        f"{p2_query}",
                        f"{suitor_std} {dossier.pursuing_club} stadium pitch night",
                        f"{suitor_std} matchday floodlights"
                    ] if use_suitor_emblem else [
                        f"{p2_query}",
                        f"{suitor_mgr} {dossier.pursuing_club} touchline coach",
                        f"{suitor_std} {dossier.pursuing_club} floodlights matchday"
                    ],
                    avoid_terms=list(base_avoid) + ["conference hall", "empty chairs"],
                    required_context=p2_desc,
                    use_club_crest=use_suitor_emblem,
                    layout_preference="split_duel"
                ))
                shot_counter += 1

            elif sid == dual_split_scene and sid != "S01":
                # Dual Landscape Split Beat: 2 distinct horizontal images (Top slides from Left + Bottom slides from Right)
                print(f"  [{sid}] Assigning animated Dual-Landscape Split Beat (Top-from-Left + Bottom-from-Right)...")
                single_data = self.describe_single_scene(sid, narration, dossier)
                e1 = _normalize_entity(single_data["primary_entity"], dossier.protagonist_name)
                q1 = _sanitize_obsolete(single_data["search_query"].replace('"', ''), f"{e1} {dossier.current_club} match action")
                e2 = dossier.current_manager if (e1.lower() != dossier.current_manager.lower()) else curr_std
                q2 = f"{dossier.current_manager} {dossier.current_club} touchline match" if e2 == dossier.current_manager else f"{curr_std} {dossier.current_club} floodlights night"
                specs.append(EditorialShotSpec(
                    shot_id=f"{sid}_shot1",
                    scene_id=sid,
                    index=shot_counter,
                    role=f"scene_{sid.lower()}_split_top",
                    primary_entity=e1,
                    club_affiliation=dossier.current_club,
                    crop_strategy="match_action" if dossier.protagonist_name.lower() in e1.lower() else "tactical",
                    search_queries=[q1, f"{dossier.protagonist_name} {dossier.current_club} match action"],
                    avoid_terms=list(base_avoid),
                    required_context=single_data.get("image_description") or f"{e1} top landscape frame",
                    prefer_landscape=True,
                    layout_preference="dual_landscape_split",
                ))
                shot_counter += 1
                specs.append(EditorialShotSpec(
                    shot_id=f"{sid}_shot2",
                    scene_id=sid,
                    index=shot_counter,
                    role=f"scene_{sid.lower()}_split_bottom",
                    primary_entity=e2,
                    club_affiliation=dossier.current_club,
                    crop_strategy="managerial" if e2 == dossier.current_manager else "tactical",
                    search_queries=[q2, f"{dossier.current_club} players training pitch matchday"],
                    avoid_terms=list(base_avoid),
                    required_context=f"Complementary bottom landscape shot featuring {e2}.",
                    prefer_landscape=True,
                    layout_preference="dual_landscape_split",
                ))
                shot_counter += 1

            else:
                print(f"  [{sid}] Asking {self.preferred_model} for 1-sentence image description...")
                single_data = self.describe_single_scene(sid, narration, dossier)
                default_ent = curr_std if sid == "S01" else dossier.protagonist_name
                entity = _normalize_entity(single_data["primary_entity"], default_ent)
                q = _sanitize_obsolete(single_data["search_query"].replace('"', ''), f"{entity} {dossier.current_club} match action")
                desc = _sanitize_obsolete(single_data["image_description"], f"{entity} during high-intensity match action.")

                # Narrative-locked diversity rules (never misroute current club "united" onto suitor club!)
                mgr_last = (dossier.current_manager or "").split()[-1].lower() if dossier.current_manager else ""
                purs_low = (dossier.pursuing_club or "").lower()
                curr_low = (dossier.current_club or "").lower()
                prot_last = (dossier.protagonist_name or "").split()[-1].lower()
                use_crest_single = False

                if sid != "S01" and mgr_last and len(mgr_last) > 3 and mgr_last in narr_lower:
                    entity = dossier.current_manager
                    q = f"{dossier.current_manager} {dossier.current_club} touchline manager"
                    desc = f"{dossier.current_manager} giving touchline instructions for {dossier.current_club}."
                elif sid != "S01" and purs_low and purs_low in narr_lower and prot_last not in narr_lower and curr_low not in narr_lower:
                    entity = suitor_std
                    q = f"{suitor_std} {dossier.pursuing_club} stadium floodlights night"
                    desc = f"{suitor_std} illuminated with transparent {dossier.pursuing_club} badge."
                    use_crest_single = ("rival" not in purs_low and "suitor" not in purs_low)

                # Determine crop strategy and avoid list based on entity and scene
                if sid == "S01":
                    if dossier.protagonist_name.lower() in entity.lower():
                        entity = curr_std
                        q = f"{curr_std} {dossier.current_club} floodlights matchday"
                    crop_strat = "managerial" if dossier.current_manager.lower() in entity.lower() else "tactical"
                    club_affil = dossier.current_club
                    avoid = [dossier.protagonist_name] + list(base_avoid)
                elif "manager" in entity.lower() or dossier.current_manager.lower() in entity.lower() or suitor_mgr.lower() in entity.lower():
                    crop_strat = "managerial"
                    club_affil = dossier.pursuing_club if suitor_mgr.lower() in entity.lower() else dossier.current_club
                    avoid = list(base_avoid)
                elif dossier.protagonist_name.lower() in entity.lower():
                    crop_strat = "match_action"
                    club_affil = dossier.current_club
                    avoid = ["unrelated player"] + list(base_avoid)
                elif dossier.pursuing_club.lower() in entity.lower() or suitor_std.lower() in entity.lower():
                    crop_strat = "tactical"
                    club_affil = dossier.pursuing_club
                    avoid = list(base_avoid)
                    if sid == "S03":
                        use_crest_single = True
                else:
                    crop_strat = "match_action"
                    club_affil = dossier.current_club
                    avoid = list(base_avoid)

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
                        f"{entity} {club_affil} match action" if crop_strat != "tactical" else f"{entity} {club_affil} matchday floodlights",
                        f"{entity} {club_affil} tackle" if crop_strat == "match_action" else f"{entity} {club_affil} stadium night"
                    ],
                    avoid_terms=avoid,
                    required_context=desc,
                    use_club_crest=use_crest_single,
                ))
                shot_counter += 1

        print(f"[LLMVisualDirector] Successfully planned {len(specs)} shots for story timeline.")
        return specs
