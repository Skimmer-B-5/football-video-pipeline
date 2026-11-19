"""
Stage 4: Unified Viral Narrative & Scene Plan Generator (Schema v2.0).
Executes the Director's Viral News Narrative Persona powered by Groq LPUs (OpenAI GPT-OSS 120B).
Generates an end-to-end, category-aware structured scene plan with factual claim references.
Strictly validates against Schema v2.0 invariants and cross-examines factual grounding.
"""

import sys
import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker
from stages.claim_checker import verify_script_claims
from stages.schema_v2 import validate_scene_plan_v2, normalize_whitespace
from stages.groq_client import call_groq_chat

EVIDENCE_DIR = PROJECT_ROOT / "evidence"

SYSTEM_PROMPT_V2 = """# SYSTEM PROMPT: VIRAL NEWS NARRATIVE & BROADCAST SCENE PRODUCER (v2.0)

## 1. YOUR IDENTITY
You are an elite sports news director, investigative scriptwriter, and broadcast producer.
You write short-form, high-retention video stories for YouTube Shorts, Reels, and TikTok.
You write like a high-energy documentary narrator combined with a breaking-news editor.
Your tone is HUMAN, CONFIDENT, NATURAL, DRAMATIC, and PRECISE.

## 2. STRICT EDITORIAL PRINCIPLES
1. NEVER upgrade a rumour or prospective interest to a confirmed transfer.
   - If a bid is reported by Italian press: state "Reports in Italy claim...", NOT "He is definitely joining!"
   - Distinguish facts from analysis.
2. NEVER insert unrelated manager jokes or meme tangents (e.g. no Mourinho "if I speak" or unrelated Ancelotti bench jokes in an Endrick story unless explicitly part of the evidence).
3. Every factual sentence MUST cite or ground itself in the provided evidence claims.
4. Spoken English: write short, punchy sentences that sound natural aloud.
5. End with exactly ONE provocative YES/NO debate question tailored to the story stakes.

## 3. STORY-TYPE PROGRESSION (TRANSFER CATEGORY)
A. HOOK (Scene 1): Urgent, attention-grabbing opening highlighting the high stakes.
B. REPORTED REALITY (Scene 2): What is actually reported and by whom (identify the outlet, e.g. Corriere dello Sport).
C. PLAYER CONTEXT (Scene 3): Current playing-time situation, competitive obstacle, or squad reality.
D. DEAL MECHANICS (Scene 4): Financial terms, loan, buy-back clause, or contract framework (only if in evidence).
E. TACTICAL & SQUAD FIT (Scene 5): Analysis of whether the player fits the destination or faces similar bench risks.
F. THE STAKES / OBSTACLE (Scene 6): What could block the move or why the parent club might hesitate.
G. DEBATE ENDING (Scene 7): One direct, binary question inviting comments (YES OR NO).

## 4. OUTPUT REQUIREMENTS
You MUST respond with a SINGLE valid JSON object adhering strictly to Schema v2.0:
{
  "schema_version": "2.0",
  "story": {
    "story_id": "string",
    "headline": "string",
    "category": "transfer",
    "evidence_status": "REPORTED" | "CONFIRMED" | "RUMOUR" | "ANALYSIS",
    "published_at": "string or null",
    "source_ids": ["src_1"]
  },
  "editorial_brief": {
    "angle": "specific editorial angle",
    "thesis": "the main explanatory thesis",
    "known_facts": ["fact 1", "fact 2"],
    "uncertainties": ["uncertainty 1"],
    "prohibited_claims": ["claim 1"]
  },
  "full_script": "The complete spoken narration string.",
  "target_duration_sec": 32,
  "scenes": [
    {
      "scene_id": "s01",
      "role": "hook" | "evidence_context" | "player_context" | "deal_mechanics" | "tactical_fit" | "risk_obstacle" | "debate",
      "narration": "Exact narration words for this scene.",
      "claim_ids": ["claim_1"],
      "duration_hint_sec": 4.5,
      "on_screen": {
        "kicker": "TRANSFER WATCH",
        "headline": "CONCISE BROADCAST TITLE (MAX 35 CHARS)",
        "subheadline": "Contextual supporting line (max 40 chars)",
        "data_callout": "Optional stat/fee like '€60M BID' or null",
        "status_badge": "REPORTED" | "RUMOUR" | "CONFIRMED" | "ANALYSIS"
      },
      "visual": {
        "kind": "player_photo" | "manager_photo" | "club_photo" | "match_action" | "press_conference" | "stadium_atmosphere",
        "primary_subject": "Name of player, manager, executive, or club subject",
        "action_or_context": "Verified visual description",
        "required_entities": ["EntityName"],
        "avoid_entities": ["UnrelatedPeople"],
        "temporal_constraints": "current season or recent",
        "composition": "portrait with safe area for lower third",
        "must_explain": "What the image is meant to show"
      },
      "motion": {
        "type": "subtle_push_in" | "slow_pan" | "static_focus" | "pop_in",
        "direction": "center_to_subject" | "left_to_right",
        "intensity": "low" | "medium"
      },
      "transition_out": "hard_cut_on_phrase"
    }
  ],
  "ending_question": "Should Real Madrid let Endrick leave on a buy-back deal? YES OR NO?",
  "pinned_comment": "Discussion prompt for viewers."
}

CRITICAL RULES:
1. 'full_script' MUST equal the exact concatenated string of all scene 'narration' texts!
2. Dynamic scene count: Generate between 5 and 8 scenes based on narrative rhythm.
3. Every on_screen.headline must be an independently written broadcast headline, NEVER derived by splitting the narration.
4. NO INFOGRAPHICS OR CHARTS: Every scene must feature authentic, high-impact editorial football photography, match action, press conferences, or portraits of the real players, managers, or executives involved. Never request infographics or stat cards.
5. Output ONLY the raw JSON object. No markdown fencing, no preamble, no thinking chatter.
"""

def extract_json_from_llm(raw_text: str) -> Dict[str, Any]:
    """Extract and parse JSON object from LLM response."""
    raw_clean = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
    first_b = raw_clean.find("{")
    last_b = raw_clean.rfind("}")
    if first_b != -1 and last_b != -1 and last_b >= first_b:
        return json.loads(raw_clean[first_b:last_b+1])
    raise ValueError("No valid JSON object bounds found in text")

def generate_script_v2(
    dossier: Dict[str, Any],
    user_directive: Optional[str] = None,
    fan_outrage: Optional[List[str]] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Generate unified Schema v2.0 scene plan from evidence dossier.
    Enforces invariant checks and factual claim grounding.
    """
    with ResourceTracker("LLM_ScriptGenerator_v2"):
        story_id = dossier.get("story_id", f"story_{int(time.time())}")
        headline = dossier.get("headline", "Football News")
        evidence_status = dossier.get("evidence_status", "REPORTED")
        category = dossier.get("category", "transfer")
        sources = dossier.get("sources", [])
        claims = dossier.get("claims", [])
        ed_brief = dossier.get("editorial_brief", {})

        # Build prompt evidence block
        source_summary = "\n".join([f"- [{s['source_id']}] {s['publisher']} ({s['source_category']}): {s['url']}" for s in sources])
        claims_summary = "\n".join([f"- [{c['claim_id']}] ({c['status']}): {c['text']}" for c in claims])

        user_content = f"""STORY TITLE: {headline}
STORY CATEGORY: {category}
EVIDENCE STATUS: {evidence_status}

SOURCES IN DOSSIER:
{source_summary}

VERIFIED EVIDENCE CLAIMS (Cite these claim_ids):
{claims_summary}

EDITORIAL BRIEF:
- Angle: {ed_brief.get('angle', '')}
- Thesis: {ed_brief.get('thesis', '')}
- Prohibited Claims: {ed_brief.get('prohibited_claims', [])}
- Uncertainties: {ed_brief.get('uncertainties', [])}
"""
        if fan_outrage:
            user_content += f"\n[FAN REACTION / SENTIMENT CONTEXT ONLY - NOT FACTUAL PROOF]:\n" + "\n".join([f"- {f}" for f in fan_outrage[:3]])

        if user_directive:
            user_content += f"\nDIRECTOR'S INSTRUCTION / SPECIAL FOCUS:\n{user_directive}"

        last_error = ""
        for attempt in range(1, max_retries + 1):
            print(f"[ScriptGenerator_v2] Generating Schema v2.0 scene plan (Attempt {attempt}/{max_retries})...")
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_V2},
                {"role": "user", "content": user_content}
            ]
            if last_error:
                messages.append({"role": "user", "content": f"PREVIOUS ATTEMPT FAILED WITH ISSUES:\n{last_error}\nPlease fix these issues and regenerate strict valid JSON."})

            raw_reply = call_groq_chat(
                messages=messages,
                preferred_model="openai/gpt-oss-120b",
                fallback_model="qwen/qwen3.8-27b",
                max_tokens=4000,
                temperature=0.35,
                timeout=35
            )

            if not raw_reply:
                last_error = "Groq LPU returned empty response."
                continue

            try:
                plan_data = extract_json_from_llm(raw_reply)
            except Exception as pe:
                last_error = f"JSON parse failure: {pe}"
                print(f"[ScriptGenerator_v2] {last_error}")
                continue

            # 1. Validate Schema v2.0 Invariants
            is_valid_schema, schema_errors = validate_scene_plan_v2(plan_data)
            if not is_valid_schema:
                last_error = f"Schema validation errors:\n" + "\n".join(schema_errors)
                print(f"[ScriptGenerator_v2] Schema validation failed:\n{last_error}")
                continue

            # 2. Cross-examine Factual Claims against Dossier
            full_text = plan_data.get("full_script", "")
            source_name = sources[0]["publisher"] if sources else "Sports Desk"
            claim_report = verify_script_claims(
                full_text,
                dossier.get("combined_text", ""),
                source_name,
                evidence_status
            )

            if not claim_report["is_valid"]:
                last_error = f"Claim verification flags:\n" + "\n".join(claim_report["unsupported_claims"])
                print(f"[ScriptGenerator_v2] Claim audit flags on attempt {attempt}:\n{last_error}")
                if attempt < max_retries:
                    continue
                else:
                    raise RuntimeError(f"Script generation failed factual claim verification after {max_retries} attempts: {last_error}")

            # Passed all schema invariants and claim verification!
            print(f"[ScriptGenerator_v2] SUCCESS: Generated verified {len(plan_data['scenes'])}-scene broadcast plan on attempt {attempt}.")
            plan_data["claim_report"] = claim_report
            plan_data["full_text"] = full_text

            # Backwards compatibility fields for legacy callers
            plan_data["headline"] = headline
            plan_data["source_name"] = source_name
            plan_data["reliability_tier"] = evidence_status.lower()

            # Save evidence
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            with open(EVIDENCE_DIR / "approved_script.json", "w", encoding="utf-8") as f:
                json.dump(plan_data, f, indent=2)

            return plan_data

        raise RuntimeError(f"Failed to generate valid Schema v2.0 scene plan: {last_error}")

# Backwards compatibility wrapper for orchestrator
def generate_script_llm(
    title: str,
    source_name: str,
    article_text: str,
    reliability_tier: str,
    user_directive: Optional[str] = None,
    fan_outrage: Optional[List[str]] = None,
    model_path: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Wrapper that builds an ad-hoc dossier and runs generate_script_v2."""
    from stages.evidence_dossier import build_evidence_dossier
    art = {
        "source": source_name,
        "url": "https://bbc.com/sport/football",
        "raw_text": article_text
    }
    dossier = build_evidence_dossier(f"story_{int(time.time())}", title, [art])
    return generate_script_v2(dossier, user_directive=user_directive, fan_outrage=fan_outrage, max_retries=max_retries)
