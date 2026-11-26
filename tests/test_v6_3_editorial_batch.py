"""
beta/tests/test_v6_3_editorial_batch.py - Production Batch Generation & 4-Gate Quality Verification (V6.3.1 Corrected).

Implements:
1. Story 1 (Bruno Fernandes): Personal decision -> Club crisis -> Contract context -> Leadership implication.
2. Story 2 (David Raya): Match incident -> Injury uncertainty -> Immediate replacement (Kepa) -> Title implications.
3. Story 3 (Brighton): Expensive opposition -> Unexpected result (0-1) -> Recruitment method -> Sporting outcome.
4. Exact timing reporting: Word count, spoken tokens, pure speech duration at 140 WPM, pause allowance, total timeline duration.
5. All 4 gates active: Gate A (Live HTTP), Gate B (Fact verification), Gate C (Mechanical math), Gate D (100-pt rubric).
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stages.source_verifier import SourceVerifier, SourceCorroborationEngine
from stages.claim_mapper import SourceToScriptClaimValidator
from stages.editorial_policy import (
    EditorialQualityGate,
    OpeningSecrecyValidator,
    MathematicalTimingReconciler,
    calculate_written_and_spoken_counts,
    expand_spoken_tokens
)

# ---------------------------------------------------------------------------
# THREE VERIFIED PRODUCTION STORIES (NOVEMBER 21-22, 2026)
# ---------------------------------------------------------------------------

STORY_1_BRUNO = {
    "story_id": "v6_3_1_story_1_bruno_contract",
    "headline": "Bruno Fernandes puts Manchester United contract negotiations on hold",
    "category": "contract_negotiation",
    "primary_subject": "Bruno Fernandes",
    "event_date": "2026-11-22",
    "publication_date": "2026-11-22",
    "narrative_structure": "personal_decision -> club_crisis -> contract_context -> leadership_implication",
    "why_it_matters": (
        "Manchester United club captain Bruno Fernandes has taken the rare step of freezing contract negotiations "
        "despite receiving an official extension offer from the club. With United second-bottom after their worst start in "
        "forty years and new manager Mauricio Pochettino taking charge against Liverpool, the captain's decision to postpone "
        "personal financial discussions prioritizes the club's on-pitch crisis."
    ),
    "sources": [
        {
            "publisher": "The Guardian",
            "url": "https://www.theguardian.com/football/2026/nov/22/bruno-fernandes-reveals-talks-over-new-manchester-united-contract-are-on-hold",
            "published_at": "2026-11-22"
        },
        {
            "publisher": "Sky Sports",
            "url": "https://www.skysports.com/football/news/13614990/bruno-fernandes-man-utd-captain-confirms-contract-offer-but-says-negotiations-are-on-hold",
            "published_at": "2026-11-22"
        }
    ],
    "evidence_status": "CONFIRMED",
    "claims": [
        {
            "claim_id": "claim_1",
            "text": "Bruno Fernandes confirmed in an interview that Manchester United offered him a new contract, but he put discussions on hold.",
            "published_at": "2026-11-22"
        },
        {
            "claim_id": "claim_2",
            "text": "Fernandes stated discussions were paused because the club must focus on climbing out of the bottom two, dismissing rumors of wage demands.",
            "published_at": "2026-11-22"
        },
        {
            "claim_id": "claim_3",
            "text": "Manchester United hold a club option extending Fernandes's contract until June 2028.",
            "published_at": "2026-11-22"
        },
        {
            "claim_id": "claim_4",
            "text": "Mauricio Pochettino takes charge of his first Manchester United match against Liverpool with United second-bottom.",
            "published_at": "2026-11-22"
        }
    ],
    "hook_candidates": [
        {
            "id": "hook_a",
            "archetype": "personal_decision",
            "spoken_text": "A Premier League captain has chosen to freeze his own contract extension.",
            "headline": "CONTRACT FREEZE",
            "subheadline": "TALKS PUT ON HOLD",
            "kicker": "CAPTAIN'S STANCE"
        },
        {
            "id": "hook_b",
            "archetype": "financial_postponement",
            "spoken_text": "While Manchester United battle relegation, one star player is refusing to discuss a pay rise.",
            "headline": "TALKS POSTPONED",
            "subheadline": "MONEY PUT ASIDE",
            "kicker": "OLD TRAFFORD SHOCK"
        },
        {
            "id": "hook_c",
            "archetype": "dressing_room_focus",
            "spoken_text": "Before facing Liverpool, Manchester United's captain made an unexpected boardroom decision.",
            "headline": "BOARDROOM SURPRISE",
            "subheadline": "SURVIVAL FOCUS",
            "kicker": "CRISIS STANCE"
        }
    ],
    "selected_hook_id": "hook_a",
    "scenes": [
        {
            "scene_id": "s01",
            "role": "personal_decision",
            "narration": "A Premier League captain has chosen to freeze his own contract extension.",
            "claim_ids": ["claim_1"],
            "on_screen": {
                "headline": "CONTRACT FREEZE",
                "subheadline": "TALKS PUT ON HOLD",
                "kicker": "CAPTAIN'S STANCE",
                "status_badge": "CONFIRMED"
            },
            "visual": {
                "kind": "tunnel_photo",
                "primary_subject": "Old Trafford Tunnel",
                "search_entity": "Manchester United",
                "search_context": "Old Trafford players tunnel matchday atmosphere",
                "composition": "wide cinematic safe area",
                "must_explain": "Establishes personal decision and boardroom tension without showing player face."
            },
            "motion": {"type": "subtle_push_in"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s02",
            "role": "club_crisis",
            "narration": "Bruno Fernandes paused negotiations, refusing to discuss personal terms while Manchester United sit second-bottom.",
            "claim_ids": ["claim_1", "claim_2"],
            "on_screen": {
                "headline": "BRUNO FERNANDES",
                "subheadline": "TALKS ON HOLD",
                "kicker": "SECOND-BOTTOM",
                "status_badge": "CONFIRMED"
            },
            "visual": {
                "kind": "player_photo",
                "primary_subject": "Bruno Fernandes",
                "search_entity": "Bruno Fernandes",
                "search_context": "Bruno Fernandes captain armband portrait",
                "composition": "portrait safe area",
                "must_explain": "First reveal of Bruno Fernandes matching the narrative name drop."
            },
            "motion": {"type": "slow_pan_right"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s03",
            "role": "contract_context",
            "narration": "United hold an option until twenty twenty-eight, while the Portuguese midfielder dismissed rumors of wage demands.",
            "claim_ids": ["claim_2", "claim_3"],
            "on_screen": {
                "headline": "OPTION TO 2028",
                "subheadline": "WAGE RUMORS DISMISSED",
                "kicker": "CONTRACT CONTEXT",
                "status_badge": "CONFIRMED"
            },
            "visual": {
                "kind": "tactical_graphics",
                "primary_subject": "Contract Extension Graphic",
                "search_entity": "Old Trafford Executive",
                "search_context": "Manchester United boardroom desk documents",
                "composition": "editorial split safe area",
                "must_explain": "Visualizes contract extension option to 2028 and dismissed wage demand rumors."
            },
            "motion": {"type": "subtle_push_in"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s04",
            "role": "leadership_implication",
            "narration": "With Mauricio Pochettino arriving, will this crisis stance rally the dressing room, or leave his future uncertain?",
            "claim_ids": ["claim_2", "claim_4"],
            "on_screen": {
                "headline": "THE FINAL VERDICT",
                "subheadline": "HAVE YOUR SAY",
                "kicker": "POCHETTINO ERA",
                "status_badge": "DEBATE"
            },
            "visual": {
                "kind": "manager_photo",
                "primary_subject": "Mauricio Pochettino",
                "search_entity": "Mauricio Pochettino",
                "search_context": "Mauricio Pochettino manager touchline Anfield preview",
                "composition": "portrait dynamic safe area",
                "must_explain": "Closes with Pochettino's arrival and the debate over Fernandes's leadership stance."
            },
            "motion": {"type": "slow_zoom_out"},
            "transition_out": "hard_cut_on_phrase"
        }
    ]
}

STORY_2_RAYA = {
    "story_id": "v6_3_1_story_2_raya_injury",
    "headline": "Arteta sweats over David Raya after goalkeeper suffers shoulder injury",
    "category": "tactical_analysis",
    "primary_subject": "David Raya",
    "event_date": "2026-11-21",
    "publication_date": "2026-11-21",
    "narrative_structure": "match_incident -> injury_uncertainty -> immediate_replacement -> title_implications",
    "why_it_matters": (
        "Arsenal hold a six-point lead atop the Premier League, but their primary defensive anchor David Raya was forced off "
        "close to tears with a shoulder injury during their 2-2 draw at Newcastle. With Raya having kept seven clean sheets "
        "in ten league games and undergoing an MRI scan, Mikel Arteta had to call on Kepa Arrizabalaga as title pressure mounts."
    ),
    "sources": [
        {
            "publisher": "The Guardian",
            "url": "https://www.theguardian.com/football/2026/nov/21/david-raya-shoulder-injury-arsenal-newcastle-mikel-arteta",
            "published_at": "2026-11-21"
        },
        {
            "publisher": "The Guardian (Match Report)",
            "url": "https://www.theguardian.com/football/2026/nov/21/newcastle-arsenal-premier-league-match-report",
            "published_at": "2026-11-21"
        },
        {
            "publisher": "Premier League Official Squad",
            "url": "https://www.premierleague.com/en/clubs/3/arsenal/squad?se=418",
            "published_at": "2026-11-21"
        }
    ],
    "evidence_status": "REPORTED",
    "claims": [
        {
            "claim_id": "claim_1",
            "text": "David Raya was forced off with a shoulder injury during Arsenal's 2-2 draw at Newcastle following an accidental collision with William Osula.",
            "published_at": "2026-11-21"
        },
        {
            "claim_id": "claim_2",
            "text": "Raya was helped off in evident pain close to tears, with Mikel Arteta confirming the goalkeeper will undergo an MRI scan with prognosis unknown.",
            "published_at": "2026-11-21"
        },
        {
            "claim_id": "claim_3",
            "text": "Kepa Arrizabalaga replaced David Raya in goal, with Raya having kept seven clean sheets in Arsenal's opening ten Premier League games.",
            "published_at": "2026-11-21"
        },
        {
            "claim_id": "claim_4",
            "text": "Arsenal remain six points clear at the top of the Premier League ahead of Brighton and Manchester City.",
            "published_at": "2026-11-21"
        }
    ],
    "hook_candidates": [
        {
            "id": "hook_a",
            "archetype": "match_incident",
            "spoken_text": "A second-half collision at St James' Park has disrupted Arsenal's title momentum.",
            "headline": "TITLE RACE ALARM",
            "subheadline": "ST JAMES' COLLISION",
            "kicker": "INJURY BLOW"
        },
        {
            "id": "hook_b",
            "archetype": "defensive_anchor_loss",
            "spoken_text": "Arsenal's six-point lead is suddenly vulnerable after a devastating goalkeeper setback.",
            "headline": "LEAD VULNERABLE",
            "subheadline": "GOALKEEPER SCARE",
            "kicker": "EMIRATES WORRY"
        },
        {
            "id": "hook_c",
            "archetype": "arteta_dilemma",
            "spoken_text": "Mikel Arteta faces an agonizing medical wait after an accidental clash in Newcastle.",
            "headline": "ARTETA SWEATING",
            "subheadline": "AGONY IN NEWCASTLE",
            "kicker": "SCAN PENDING"
        }
    ],
    "selected_hook_id": "hook_a",
    "scenes": [
        {
            "scene_id": "s01",
            "role": "match_incident",
            "narration": "A second-half collision at St James' Park has disrupted Arsenal's title momentum.",
            "claim_ids": ["claim_1", "claim_4"],
            "on_screen": {
                "headline": "TITLE RACE ALARM",
                "subheadline": "ST JAMES' COLLISION",
                "kicker": "INJURY BLOW",
                "status_badge": "DEVELOPING"
            },
            "visual": {
                "kind": "tactical_hud",
                "primary_subject": "Premier League Table",
                "search_entity": "Arsenal",
                "search_context": "Emirates Stadium tactical board six points clear",
                "composition": "wide cinematic safe area",
                "must_explain": "Establishes title race jeopardy without revealing goalkeeper face prematurely."
            },
            "motion": {"type": "subtle_push_in"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s02",
            "role": "injury_uncertainty",
            "narration": "David Raya was helped off close to tears with a shoulder problem, awaiting an MRI assessment.",
            "claim_ids": ["claim_1", "claim_2"],
            "on_screen": {
                "headline": "DAVID RAYA",
                "subheadline": "AWAITING MRI SCAN",
                "kicker": "SHOULDER PROBLEM",
                "status_badge": "REPORTED"
            },
            "visual": {
                "kind": "player_photo",
                "primary_subject": "David Raya",
                "search_entity": "David Raya",
                "search_context": "David Raya goalkeeper kit gloves focused expression",
                "composition": "portrait safe area",
                "must_explain": "First reveal of David Raya matching the narration name drop."
            },
            "motion": {"type": "slow_pan_right"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s03",
            "role": "immediate_replacement",
            "narration": "Kepa Arrizabalaga stepped in, replacing a goalkeeper who kept seven clean sheets in ten league games.",
            "claim_ids": ["claim_3"],
            "on_screen": {
                "headline": "KEPA CALLED UP",
                "subheadline": "7 CLEAN SHEETS IN 10",
                "kicker": "REPLACEMENT IN GOAL",
                "status_badge": "REPORTED"
            },
            "visual": {
                "kind": "player_photo",
                "primary_subject": "Kepa Arrizabalaga",
                "search_entity": "Kepa Arrizabalaga",
                "search_context": "Kepa Arrizabalaga Arsenal goalkeeper kit gloves",
                "composition": "portrait safe area",
                "must_explain": "Visualizes Kepa Arrizabalaga entering as Arsenal's matchday replacement."
            },
            "motion": {"type": "subtle_push_in"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s04",
            "role": "title_implications",
            "narration": "With Arsenal six points clear, can Kepa secure the title lead during this medical uncertainty?",
            "claim_ids": ["claim_3", "claim_4"],
            "on_screen": {
                "headline": "THE FINAL VERDICT",
                "subheadline": "HAVE YOUR SAY",
                "kicker": "TITLE DEBATE",
                "status_badge": "DEBATE"
            },
            "visual": {
                "kind": "manager_photo",
                "primary_subject": "Mikel Arteta",
                "search_entity": "Mikel Arteta",
                "search_context": "Mikel Arteta touchline dugout anxious rain",
                "composition": "portrait dynamic safe area",
                "must_explain": "Arteta in dugout contemplating title lead defense under goalkeeper uncertainty."
            },
            "motion": {"type": "slow_zoom_out"},
            "transition_out": "hard_cut_on_phrase"
        }
    ]
}

STORY_3_BRIGHTON = {
    "story_id": "v6_3_1_story_3_brighton_recruitment",
    "headline": "How Brighton's data-led recruitment stunned Manchester City at the Etihad",
    "category": "tactical_analysis",
    "primary_subject": "Fabian Hurzeler",
    "event_date": "2026-10-31",
    "publication_date": "2026-11-21",
    "narrative_structure": "expensive_opposition -> unexpected_result -> recruitment_method -> sporting_outcome",
    "why_it_matters": (
        "Brighton defeated Manchester City 0-1 at the Etihad Stadium, with three-million-pound signing Yasin Ayari outperforming "
        "City's £327m midfield. Under thirty-three-year-old manager Fabian Hürzeler, the Seagulls sit second in the Premier League, "
        "proving that combining algorithmic talent identification with rigorous character vetting can outperform sovereign-backed spending."
    ),
    "sources": [
        {
            "publisher": "Manchester City Official Result",
            "url": "https://www.mancity.com/matchday/fixtures/mens/2026/premier-league/man-city-v-brighton-31-oct-2026",
            "published_at": "2026-10-31"
        },
        {
            "publisher": "BBC Sport (Ayari)",
            "url": "https://www.bbc.co.uk/sport/football/articles/c20gyeeexgro",
            "published_at": "2026-11-01"
        },
        {
            "publisher": "BBC Sport (City Midfield)",
            "url": "https://www.bbc.co.uk/sport/football/articles/cve8rkd8r302o",
            "published_at": "2026-10-31"
        },
        {
            "publisher": "Premier League Official (Hürzeler)",
            "url": "https://www.premierleague.com/en/managers/53902/fabian-hurzeler",
            "published_at": "2026-11-22"
        },
        {
            "publisher": "The Guardian",
            "url": "https://www.theguardian.com/football/2026/nov/21/brighton-rocking-premier-league-elite-title-challenge",
            "published_at": "2026-11-21"
        }
    ],
    "evidence_status": "REPORTED",
    "claims": [
        {
            "claim_id": "claim_1",
            "text": "Manchester City fielded a £327m midfield against Brighton at the Etihad Stadium.",
            "published_at": "2026-10-31"
        },
        {
            "claim_id": "claim_2",
            "text": "Brighton defeated Manchester City 0-1 at the Etihad on 31 October 2026, with £3.5m signing Yasin Ayari scoring in the 11th minute.",
            "published_at": "2026-10-31"
        },
        {
            "claim_id": "claim_3",
            "text": "Brighton's recruitment model pairs proprietary data analytics with human scouting and character vetting to find coachable talent.",
            "published_at": "2026-11-21"
        },
        {
            "claim_id": "claim_4",
            "text": "Under thirty-three-year-old manager Fabian Hürzeler, Brighton sit second in the Premier League, having scored more goals than any division rival.",
            "published_at": "2026-11-21"
        }
    ],
    "hook_candidates": [
        {
            "id": "hook_a",
            "archetype": "expensive_opposition",
            "spoken_text": "Facing City's three-hundred-million-pound midfield, Brighton proved expenditure does not guarantee victory.",
            "headline": "£327M EXPENSE",
            "subheadline": "ETIHAD TEST",
            "kicker": "FINANCIAL GAP"
        },
        {
            "id": "hook_b",
            "archetype": "unexpected_upset",
            "spoken_text": "Manchester City were stunned at home by an opponent that spends a fraction of their budget.",
            "headline": "ETIHAD SHOCK",
            "subheadline": "0-1 UPSET",
            "kicker": "BUDGET TRIUMPH"
        },
        {
            "id": "hook_c",
            "archetype": "recruitment_revolution",
            "spoken_text": "While rival clubs spend hundreds of millions, Brighton's recruitment model is quietly conquering the league.",
            "headline": "DATA SCOUTING",
            "subheadline": "SMART RECRUITMENT",
            "kicker": "SEAGULLS MODEL"
        }
    ],
    "selected_hook_id": "hook_a",
    "scenes": [
        {
            "scene_id": "s01",
            "role": "expensive_opposition",
            "narration": "Facing City's three-hundred-million-pound midfield, Brighton proved expenditure does not guarantee victory.",
            "claim_ids": ["claim_1"],
            "on_screen": {
                "headline": "£327M EXPENSE",
                "subheadline": "ETIHAD MIDFIELD",
                "kicker": "FINANCIAL GAP",
                "status_badge": "REPORTED"
            },
            "visual": {
                "kind": "action_photo",
                "primary_subject": "Etihad Stadium Midfield",
                "search_entity": "Manchester City",
                "search_context": "Manchester City midfield Etihad stadium match action",
                "composition": "wide action safe area",
                "must_explain": "Establishes City's £327m midfield without cheapening the visual contrast."
            },
            "motion": {"type": "subtle_push_in"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s02",
            "role": "unexpected_result",
            "narration": "The Seagulls secured a historic one-nil win, with three-million-pound recruit Yasin Ayari scoring in the eleventh minute.",
            "claim_ids": ["claim_2"],
            "on_screen": {
                "headline": "0-1 AT THE ETIHAD",
                "subheadline": "AYARI 11TH MIN GOAL",
                "kicker": "HISTORIC VICTORY",
                "status_badge": "CONFIRMED"
            },
            "visual": {
                "kind": "player_action",
                "primary_subject": "Yasin Ayari",
                "search_entity": "Yasin Ayari",
                "search_context": "Yasin Ayari Brighton goal celebration Etihad stadium",
                "composition": "action safe area",
                "must_explain": "Celebrates Yasin Ayari's 11th-minute winner at the Etihad."
            },
            "motion": {"type": "slow_pan_right"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s03",
            "role": "recruitment_method",
            "narration": "Brighton's model pairs data analytics with character vetting, finding coachable talent to replace major sales.",
            "claim_ids": ["claim_3"],
            "on_screen": {
                "headline": "DATA AND VETTING",
                "subheadline": "COACHABILITY METRICS",
                "kicker": "SEAGULLS MODEL",
                "status_badge": "ANALYSIS"
            },
            "visual": {
                "kind": "tactical_graphics",
                "primary_subject": "Analytics Dashboard",
                "search_entity": "Tony Bloom",
                "search_context": "Brighton recruitment analytics room screens",
                "composition": "editorial split safe area",
                "must_explain": "Visualizes data analytics alongside character interview dossiers."
            },
            "motion": {"type": "subtle_push_in"},
            "transition_out": "hard_cut_on_phrase"
        },
        {
            "scene_id": "s04",
            "role": "sporting_outcome",
            "narration": "With thirty-three-year-old Fabian Hürzeler guiding them to second place, can this development system genuinely sustain a title challenge?",
            "claim_ids": ["claim_4"],
            "on_screen": {
                "headline": "THE FINAL VERDICT",
                "subheadline": "HAVE YOUR SAY",
                "kicker": "TITLE TILT?",
                "status_badge": "DEBATE"
            },
            "visual": {
                "kind": "manager_photo",
                "primary_subject": "Fabian Hurzeler",
                "search_entity": "Fabian Hurzeler",
                "search_context": "Fabian Hurzeler technical area celebration Amex",
                "composition": "portrait safe area",
                "must_explain": "Highlights Hürzeler's guidance taking Brighton to second place."
            },
            "motion": {"type": "slow_zoom_out"},
            "transition_out": "hard_cut_on_phrase"
        }
    ]
}

BATCH_STORIES = [STORY_1_BRUNO, STORY_2_RAYA, STORY_3_BRIGHTON]

def run_v6_3_1_batch():
    print("=" * 80)
    print("BETA V6.3.1: CORRECTED EDITORIAL BATCH RUN WITH 4-GATE VERIFICATION")
    print("=" * 80)

    results = []
    for idx, story in enumerate(BATCH_STORIES, 1):
        print(f"\n--- Processing Story {idx}: {story['headline']} ---")
        print(f" Narrative Structure: {story['narrative_structure']}")

        # 1. Source verification
        for src in story["sources"]:
            u = src["url"]
            res = SourceVerifier.verify_url(u)
            print(f" Source URL: {u[:65]}...")
            print(f"  -> HTTP: {res.http_status} | Canonical: {res.canonical_url[:60]}... | Verified: {res.is_verified}")

        # 2. Timing calculation
        full_text = " ".join(s["narration"] for s in story["scenes"])
        w_cnt, s_cnt, tokens = calculate_written_and_spoken_counts(full_text)
        timing = MathematicalTimingReconciler.reconcile_scenes(story["scenes"], wpm=140.0, pause_allowance_sec=0.35)

        print(f" Timing Report:")
        print(f"  * Written Words: {w_cnt}")
        print(f"  * Spoken Tokens: {s_cnt}")
        print(f"  * Configured WPM: {timing['configured_wpm']}")
        print(f"  * Speech Duration (at 140 WPM): {timing['speech_duration_sec']}s")
        print(f"  * Pause Allowance: {timing['pause_allowance_sec']}s")
        print(f"  * Total Expected Timeline: {timing['total_timeline_sec']}s (Sum scenes: {timing['sum_scene_durations']}s)")
        print(f"  * Overall Cadence with Pauses: {timing['overall_cadence_wpm_with_pauses']} WPM")
        print(f"  * Reconciled Math: {timing['is_mathematically_reconciled']}")

        scene_plan = {
            "schema_version": "2.0",
            "story": {
                "story_id": story["story_id"],
                "headline": story["headline"],
                "category": story["category"],
                "primary_subject": story["primary_subject"],
                "event_date": story["event_date"],
                "publication_date": story["publication_date"],
                "source": story["sources"][0]["publisher"],
                "reliability_tier": story["evidence_status"]
            },
            "why_it_matters": story["why_it_matters"],
            "narrative_structure": story["narrative_structure"],
            "hook_candidates": story["hook_candidates"],
            "selected_hook": story["selected_hook_id"],
            "full_script": full_text,
            "written_word_count": w_cnt,
            "spoken_token_count": s_cnt,
            "configured_wpm": timing["configured_wpm"],
            "speech_duration_sec": timing["speech_duration_sec"],
            "pause_allowance_sec": timing["pause_allowance_sec"],
            "target_duration_sec": timing["total_timeline_sec"],
            "overall_cadence_wpm_with_pauses": timing["overall_cadence_wpm_with_pauses"],
            "scenes": timing["scenes"]
        }

        # 3. 4-Gate Quality Evaluation
        dossier = {
            "sources": story["sources"],
            "claims": story["claims"],
            "primary_subject": story["primary_subject"]
        }
        subj_list = [story["primary_subject"]] if "Bruno" in story["primary_subject"] or "Raya" in story["primary_subject"] else []
        stage_lvl = 11 if story["evidence_status"].upper() in ["CONFIRMED", "OFFICIALLY_CONFIRMED"] else 5

        q_eval = EditorialQualityGate.evaluate(
            scene_plan=scene_plan,
            dossier=dossier,
            subject_names=subj_list,
            stage_level=stage_lvl,
            reference_year=2026
        )

        scene_plan["quality_gate_report"] = q_eval

        print(f" Quality Gate Results:")
        print(f"  * Gate A (Source Retrieval): {'PASSED' if q_eval['gate_a_source_retrieval']['passed'] else 'FAILED'}")
        print(f"  * Gate B (Fact Verification): {'PASSED' if q_eval['gate_b_fact_verification']['passed'] else 'FAILED'}")
        print(f"  * Gate C (Mechanical Validation): {'PASSED' if q_eval['gate_c_mechanical_validation']['passed'] else 'FAILED'}")
        print(f"  * Gate D Editorial Score: {q_eval['total_score']}/100")
        print(f"  * Overall Gate Status: {q_eval['status']}")
        for crit, data in q_eval["gate_d_editorial_evaluation"].items():
            print(f"     - {crit}: {data['score']}/{data['max']} -> {data['notes']}")

        results.append(scene_plan)

    out_file = PROJECT_ROOT / "evidence" / "v6_3_1_editorial_batch_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Successfully executed corrected V6.3.1 batch and saved to {out_file}")

if __name__ == "__main__":
    run_v6_3_1_batch()
