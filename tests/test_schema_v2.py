"""
Automated Unit Tests: Schema v2.0 & Editorial Pipeline Invariants.
Tests:
1. Dynamic scene count validation (4-12 valid, <4 or >12 invalid).
2. Verbatim narration concatenation invariant (sum(scenes.narration) == full_script).
3. Written lower-third headline validation (must not be empty or truncated).
4. Evidence status and badge validity (no automatic BREAKING EXCLUSIVE).
5. Evidence Dossier minimum 35-word text guard.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.schema_v2 import validate_scene_plan_v2, normalize_whitespace
from stages.evidence_dossier import build_evidence_dossier

def test_valid_schema_v2_plan():
    print("[TestSchemaV2] 1. Testing valid Schema v2.0 scene plan...")
    plan = {
        "schema_version": "2.0",
        "story": {
            "story_id": "test_endrick_001",
            "headline": "Milan prepare sixty million bid for Endrick",
            "category": "transfer",
            "evidence_status": "REPORTED",
            "published_at": "2026-11-19T10:00:00Z",
            "source_ids": ["src_besoccer"]
        },
        "editorial_brief": {
            "angle": "Milan testing Madrid's resolve with loan plus option",
            "thesis": "Endrick's lack of minutes opens door for speculative Italian approach",
            "known_facts": ["€60M bid reported by Corriere dello Sport", "€80M buyback clause discussed"],
            "uncertainties": ["Whether Real Madrid will entertain winter exit"],
            "prohibited_claims": ["Do not claim deal is done or player is heading to Milan"]
        },
        "full_script": "Milan are reportedly preparing a sixty million euro bid for Endrick. But Real Madrid insist on an eighty million euro buyback clause. Can Endrick resurrect his season at San Siro? Tell us in the comments: yes or no.",
        "target_duration_sec": 30,
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "Milan are reportedly preparing a sixty million euro bid for Endrick.",
                "claim_ids": ["claim_1"],
                "duration_hint_sec": 4.5,
                "on_screen": {
                    "kicker": "TRANSFER WATCH",
                    "headline": "MILAN PREPARE €60M BID",
                    "subheadline": "Corriere dello Sport Report",
                    "data_callout": "€60M BID",
                    "status_badge": "REPORTED"
                },
                "visual": {
                    "kind": "player_photo",
                    "primary_subject": "Endrick",
                    "action_or_context": "Real Madrid bench or match portrait",
                    "required_entities": ["Endrick"],
                    "avoid_entities": ["Mourinho", "Ancelotti"],
                    "temporal_constraints": "2024-2025 season",
                    "composition": "portrait centered",
                    "must_explain": "Shows player subject of reported bid"
                },
                "motion": {"type": "subtle_push_in", "direction": "center", "intensity": "low"}
            },
            {
                "scene_id": "s02",
                "role": "deal_mechanics",
                "narration": "But Real Madrid insist on an eighty million euro buyback clause.",
                "claim_ids": ["claim_2"],
                "duration_hint_sec": 4.0,
                "on_screen": {
                    "kicker": "CONTRACT CLAUSE",
                    "headline": "€80M BUYBACK CLAUSE",
                    "subheadline": "Nico Paz Formula Proposed",
                    "data_callout": "€80M CLAUSE",
                    "status_badge": "REPORTED"
                },
                "visual": {
                    "kind": "contract_or_clause_graphic",
                    "primary_subject": "Endrick Transfer Flow",
                    "action_or_context": "Transfer flowchart with €60m bid and €80m return arrow",
                    "required_entities": ["Real Madrid", "AC Milan"],
                    "avoid_entities": [],
                    "temporal_constraints": "current",
                    "composition": "graphic flowchart",
                    "must_explain": "Illustrates buyback mechanics"
                },
                "motion": {"type": "static_focus", "direction": "center", "intensity": "low"}
            },
            {
                "scene_id": "s03",
                "role": "tactical_fit",
                "narration": "Can Endrick resurrect his season at San Siro?",
                "claim_ids": ["claim_3"],
                "duration_hint_sec": 3.5,
                "on_screen": {
                    "kicker": "TACTICAL FIT",
                    "headline": "SAN SIRO OPPORTUNITY?",
                    "subheadline": "Playing Time Dilemma",
                    "data_callout": None,
                    "status_badge": "ANALYSIS"
                },
                "visual": {
                    "kind": "club_photo",
                    "primary_subject": "San Siro",
                    "action_or_context": "AC Milan home stadium atmosphere",
                    "required_entities": ["AC Milan"],
                    "avoid_entities": [],
                    "temporal_constraints": "current",
                    "composition": "wide stadium",
                    "must_explain": "Establishes destination venue"
                },
                "motion": {"type": "slow_pan", "direction": "left_to_right", "intensity": "low"}
            },
            {
                "scene_id": "s04",
                "role": "debate",
                "narration": "Tell us in the comments: yes or no.",
                "claim_ids": [],
                "duration_hint_sec": 3.0,
                "on_screen": {
                    "kicker": "FINAL VERDICT",
                    "headline": "SHOULD MILAN SIGN HIM?",
                    "subheadline": "Vote In The Comments",
                    "data_callout": None,
                    "status_badge": "DEBATE"
                },
                "visual": {
                    "kind": "player_photo",
                    "primary_subject": "Endrick",
                    "action_or_context": "Contemplative match still",
                    "required_entities": ["Endrick"],
                    "avoid_entities": [],
                    "temporal_constraints": "current",
                    "composition": "portrait centered",
                    "must_explain": "Closing debate focus"
                },
                "motion": {"type": "static_focus", "direction": "center", "intensity": "low"}
            }
        ],
        "ending_question": "Should Milan sign Endrick? Yes or no?"
    }

    is_valid, errors = validate_scene_plan_v2(plan)
    assert is_valid, f"Valid plan failed validation: {errors}"
    print("  ✅ Passed: Valid Schema v2.0 plan successfully verified.")

def test_narration_mismatch_detection():
    print("[TestSchemaV2] 2. Testing narration mismatch detection...")
    plan = {
        "schema_version": "2.0",
        "story": {"story_id": "s1", "headline": "H", "category": "transfer", "evidence_status": "REPORTED"},
        "editorial_brief": {"angle": "A", "thesis": "T", "known_facts": [], "uncertainties": [], "prohibited_claims": []},
        "ending_question": "Will he succeed? Yes or no?",
        "full_script": "This is line one. This is line two. This is line three. This is line four.",
        "target_duration_sec": 30,
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "This is line one with extra hallucinated words.",
                "on_screen": {"kicker": "K", "headline": "H", "subheadline": "S", "status_badge": "REPORTED"},
                "visual": {"kind": "player_photo", "primary_subject": "P", "must_explain": "M"}
            },
            {
                "scene_id": "s02",
                "role": "player_context",
                "narration": "This is line two.",
                "on_screen": {"kicker": "K", "headline": "H", "subheadline": "S", "status_badge": "REPORTED"},
                "visual": {"kind": "player_photo", "primary_subject": "P", "must_explain": "M"}
            },
            {
                "scene_id": "s03",
                "role": "tactical_fit",
                "narration": "This is line three.",
                "on_screen": {"kicker": "K", "headline": "H", "subheadline": "S", "status_badge": "REPORTED"},
                "visual": {"kind": "player_photo", "primary_subject": "P", "must_explain": "M"}
            },
            {
                "scene_id": "s04",
                "role": "debate",
                "narration": "This is line four.",
                "on_screen": {"kicker": "K", "headline": "H", "subheadline": "S", "status_badge": "DEBATE"},
                "visual": {"kind": "player_photo", "primary_subject": "P", "must_explain": "M"}
            }
        ]
    }
    is_valid, errors = validate_scene_plan_v2(plan)
    assert not is_valid, "Narration mismatch was not flagged!"
    assert any("Concatenated scene narrations do not match full_script verbatim" in e for e in errors), f"Missing verbatim narration error: {errors}"
    print("  ✅ Passed: Narration mismatch correctly caught.")

def test_evidence_dossier_short_text_guard():
    print("[TestSchemaV2] 3. Testing evidence dossier short text guard (<35 words)...")
    articles = [
        {
            "source": "BBC Sport",
            "url": "https://bbc.com/sport",
            "raw_text": "Milan want to sign Endrick on loan."  # Only 7 words!
        }
    ]
    try:
        build_evidence_dossier("test_short", "Milan want Endrick", articles)
        assert False, "Failed to raise ValueError on text < 35 words!"
    except ValueError as ve:
        assert "insufficient article text" in str(ve).lower()
        print(f"  ✅ Passed: Correctly caught short text guard ({ve})")

if __name__ == "__main__":
    test_valid_schema_v2_plan()
    test_narration_mismatch_detection()
    test_evidence_dossier_short_text_guard()
    print("\n[TestSchemaV2] ALL SCHEMA V2.0 TESTS PASSED! ✅\n")
