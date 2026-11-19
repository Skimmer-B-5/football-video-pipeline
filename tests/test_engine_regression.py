"""
test_engine_regression.py - Comprehensive Regression Test Suite for 30 Football Plus Engine.

Verifies the engine across all 7 mandatory football story formats:
1. Transfer rumour
2. Official transfer announcement
3. Match result
4. Tactical analysis
5. Player comparison
6. Managerial controversy
7. Injury update

Ensures:
- Visual identity consistency across all 7 formats.
- Proper vertical infographic data structures.
- Lower-third formatting and safe margins.
- Clean headless Remotion composition.
"""

import os
import sys
import json
import logging
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.remotion_renderer import prepare_remotion_props
from stages.qa_engine import EngineQASuite

logger = logging.getLogger("test_regression")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 7 Distinct Story Definitions
STORY_PAYLOADS = [
    # 1. Transfer Rumour
    {
        "story": {
            "story_id": "rumour_wirtz_madrid",
            "headline": "Real Madrid prepare €150m Florian Wirtz bid",
            "kicker": "TRANSFER WATCH",
            "source": "BILD SPORT",
            "key_fact": "€130M FIXED + €20M ADD-ONS SOUGHT BY LEVERKUSEN",
            "ticker_text": "BILD: REAL MADRID TARGET FLORIAN WIRTZ ✦ LEVERKUSEN VALUATION €150M ✦ TALKS OPEN ✦"
        },
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "Real Madrid are preparing a sensational €150m transfer package for Bayer Leverkusen star Florian Wirtz.",
                "duration_sec": 4.5,
                "on_screen": {
                    "kicker": "TRANSFER WATCH",
                    "status_badge": "RUMOUR",
                    "data_callout": "€150M BID",
                    "headline": "MADRID PREPARE RECORD WIRTZ BID",
                    "subheadline": "LEVERKUSEN PLAYMAKER IDENTIFIED AS PRIMARY 2025 TARGET",
                    "source_credit": "BILD"
                },
                "visual": {
                    "kind": "transfer_fee_graphic",
                    "infographic_data": {
                        "transfer_fee": {
                            "guaranteed": "€130M",
                            "add_ons": "€20M",
                            "total_package": "€150M TOTAL",
                            "selling_club": "B. LEVERKUSEN",
                            "buying_club": "REAL MADRID",
                            "structure": "Fixed Base + Trophy Bonus Clauses"
                        }
                    }
                }
            }
        ]
    },

    # 2. Official Transfer Announcement
    {
        "story": {
            "story_id": "official_amorim_man_utd",
            "headline": "Ruben Amorim officially confirmed as Manchester United manager",
            "kicker": "BREAKING NEWS",
            "source": "MANCHESTER UNITED FC",
            "key_fact": "CONTRACT SIGNED UNTIL JUNE 2027",
            "ticker_text": "OFFICIAL: RUBEN AMORIM APPOINTED HEAD COACH ✦ €11M RELEASE CLAUSE PAID ✦ CONTRACT TO 2027 ✦"
        },
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "It is officially confirmed: Ruben Amorim has been appointed head coach of Manchester United.",
                "duration_sec": 4.2,
                "on_screen": {
                    "kicker": "BREAKING NEWS",
                    "status_badge": "OFFICIAL",
                    "data_callout": "SIGNED TO 2027",
                    "headline": "AMORIM CONFIRMED AT OLD TRAFFORD",
                    "subheadline": "SPORTING CP RELEASE CLAUSE TRIGGERED BY INEOS",
                    "source_credit": "CLUB STATEMENT"
                },
                "visual": {
                    "kind": "transfer_route_graphic",
                    "infographic_data": {
                        "transfer_route": {
                            "selling_club": "SPORTING CP",
                            "buying_club": "MANCHESTER UTD",
                            "player_name": "RUBEN AMORIM",
                            "transfer_status": "OFFICIAL",
                            "fee": "€11M BUYOUT"
                        }
                    }
                }
            }
        ]
    },

    # 3. Match Result
    {
        "story": {
            "story_id": "result_arsenal_psg",
            "headline": "Arsenal defeat Paris Saint-Germain 2-0 at Emirates Stadium",
            "kicker": "MATCH REPORT",
            "source": "CHAMPIONS LEAGUE",
            "key_fact": "HAVERTZ & SAKA ON THE SCORESHEET IN DOMINANT WIN",
            "ticker_text": "FULL TIME: ARSENAL 2-0 PARIS SG ✦ HAVERTZ 20' SAKA 35' ✦ CLEAN SHEET SECURED ✦"
        },
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "Arsenal delivered an authoritative European statement, cruising past Paris Saint-Germain with a two nil victory.",
                "duration_sec": 4.6,
                "on_screen": {
                    "kicker": "MATCH REPORT",
                    "status_badge": "FULL TIME",
                    "data_callout": "2-0 WIN",
                    "headline": "ARSENAL CRUISE PAST PARIS SG",
                    "subheadline": "FIRST HALF BLITZ SEALS COMMANDING CHAMPIONS LEAGUE POINTS",
                    "source_credit": "UEFA UCL"
                },
                "visual": {
                    "kind": "match_statistics_graphic",
                    "infographic_data": {
                        "match_statistics": {
                            "home_team": "ARSENAL",
                            "away_team": "PARIS SG",
                            "home_score": 2,
                            "away_score": 0,
                            "competition": "UEFA CHAMPIONS LEAGUE",
                            "stats": [
                                {"label": "POSSESSION", "home_val": "47%", "away_val": "53%"},
                                {"label": "SHOTS (TARGET)", "home_val": "6 (5)", "away_val": "10 (2)"},
                                {"label": "EXPECTED GOALS (xG)", "home_val": "1.82", "away_val": "0.64"},
                                {"label": "BIG CHANCES", "home_val": "3", "away_val": "1"}
                            ]
                        }
                    }
                }
            }
        ]
    },

    # 4. Tactical Analysis
    {
        "story": {
            "story_id": "tactics_slot_liverpool",
            "headline": "Tactical breakdown: Arne Slot's double pivot control at Liverpool",
            "kicker": "TACTICAL FOCUS",
            "source": "THE ATHLETIC",
            "key_fact": "GRAVENBERCH LEADING PREMIER LEAGUE INTERCEPTIONS",
            "ticker_text": "TACTICAL ANALYSIS: LIVERPOOL 4-2-3-1 SYSTEM ✦ HIGH PRESS TURNOVERS UP 34% ✦"
        },
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "Arne Slot has transformed Liverpool's midfield structure with a rigid four-two-three-one defensive framework.",
                "duration_sec": 4.8,
                "on_screen": {
                    "kicker": "TACTICAL FOCUS",
                    "status_badge": "TACTICAL",
                    "data_callout": "4-2-3-1 SYSTEM",
                    "headline": "SLOT'S MIDFIELD MASTERCLASS",
                    "subheadline": "RYAN GRAVENBERCH ANCHORS NEW ANFIELD CONTROL",
                    "source_credit": "TACTICAL LAB"
                },
                "visual": {
                    "kind": "tactical_formation_graphic",
                    "infographic_data": {
                        "tactical_formation": {
                            "formation": "4-2-3-1",
                            "team_name": "LIVERPOOL FC",
                            "manager": "ARNE SLOT",
                            "highlight_position": "DM",
                            "role_title": "DEEP-LYING CONTROLLER",
                            "role_description": "Dictates tempo and wins loose second balls in central midfield"
                        }
                    }
                }
            }
        ]
    },

    # 5. Player Comparison
    {
        "story": {
            "story_id": "compare_haaland_gyokeres",
            "headline": "Erling Haaland versus Viktor Gyokeres: The race for Europe's golden boot",
            "kicker": "HEAD TO HEAD",
            "source": "OPTA STATS",
            "key_fact": "GYOKERES AVERAGING A GOAL EVERY 68 MINUTES",
            "ticker_text": "STAT ATTACK: HAALAND 27 GOALS ✦ GYOKERES 32 GOALS ✦ EUROPE'S TOP PROLIFIC STRIKERS ✦"
        },
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "Europe's most devastating goalscorers compared: Erling Haaland and Viktor Gyökeres going head to head.",
                "duration_sec": 4.5,
                "on_screen": {
                    "kicker": "HEAD TO HEAD",
                    "status_badge": "COMPARISON",
                    "data_callout": "GOLDEN BOOT",
                    "headline": "HAALAND VS GYÖKERES COMPARED",
                    "subheadline": "THE NUMBERS BEHIND THE TWO MOST PROLIFIC STRIKERS",
                    "source_credit": "OPTA DATA"
                },
                "visual": {
                    "kind": "club_comparison_graphic",
                    "infographic_data": {
                        "club_comparison": {
                            "club_a": {"name": "HAALAND", "badge_color": "#48CAE4"},
                            "club_b": {"name": "GYÖKERES", "badge_color": "#06D6A0"},
                            "metrics": [
                                {"label": "TOTAL GOALS", "val_a": "27", "val_b": "32"},
                                {"label": "MINUTES PER GOAL", "val_a": "79'", "val_b": "68'"},
                                {"label": "EXPECTED GOALS (xG)", "val_a": "21.4", "val_b": "24.8"},
                                {"label": "SHOT CONVERSION", "val_a": "28%", "val_b": "31%"}
                            ]
                        }
                    }
                }
            }
        ]
    },

    # 6. Managerial Controversy
    {
        "story": {
            "story_id": "controversy_postecoglou_var",
            "headline": "Postecoglou fumes over disallowed stoppage-time winner",
            "kicker": "CONTROVERSY",
            "source": "SKY SPORTS",
            "key_fact": "PGMOL REVIEW SOUGHT FOLLOWING STOPPAGE-TIME RULING",
            "ticker_text": "BREAKING: POSTECOGLOU DEMANDS VAR TRANSPARENCY ✦ CRUCIAL CALL OVERTURNED ✦"
        },
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "Ange Postecoglou has unleashed on VAR officials after a controversial offside decision cost Spurs all three points.",
                "duration_sec": 4.4,
                "on_screen": {
                    "kicker": "CONTROVERSY",
                    "status_badge": "EXCLUSIVE",
                    "data_callout": "VAR DISPUTE",
                    "headline": "POSTECOGLOU HITS OUT AT VAR",
                    "subheadline": "SPURS BOSS LABELS CONTROVERSIAL CALL A DISGRACE",
                    "source_credit": "PRESS ROOM"
                },
                "visual": {
                    "kind": "player_profile_graphic",
                    "infographic_data": {
                        "player_profile": {
                            "player_name": "ANGE POSTECOGLOU",
                            "club": "TOTTENHAM HOTSPUR",
                            "nationality": "AUSTRALIA",
                            "age": 59,
                            "position": "MANAGER",
                            "market_value": "APPOINTED 2023",
                            "contract_until": "JUNE 2027",
                            "key_traits": ["HIGH PRESSING", "OUTSPOKEN", "DIRECT PLAY"]
                        }
                    }
                }
            }
        ]
    },

    # 7. Injury Update
    {
        "story": {
            "story_id": "injury_rodri_rehab",
            "headline": "Rodri begins advanced pitch rehabilitation following ACL surgery",
            "kicker": "INJURY BULLETIN",
            "source": "MANCHESTER CITY",
            "key_fact": "BALLOON D'OR WINNER AHEAD OF SCHEDULE IN GYM PROGRAM",
            "ticker_text": "MAN CITY BULLETIN: RODRI RECOVERY PROGRESS ✦ SURGERY SUCCESSFUL ✦ RETURN PROJECTED ✦"
        },
        "scenes": [
            {
                "scene_id": "s01",
                "role": "hook",
                "narration": "Manchester City have received a huge boost as Ballon d'Or winner Rodri begins pitch rehabilitation.",
                "duration_sec": 4.6,
                "on_screen": {
                    "kicker": "INJURY BULLETIN",
                    "status_badge": "UPDATE",
                    "data_callout": "STAGE 2 REHAB",
                    "headline": "RODRI ACCELERATES ACL RETURN",
                    "subheadline": "BALLON D'OR WINNER RESUMES LIGHT TRAINING AT CFA",
                    "source_credit": "MEDICAL REPORT"
                },
                "visual": {
                    "kind": "injury_timeline_graphic",
                    "infographic_data": {
                        "injury_timeline": {
                            "player_name": "RODRI",
                            "club": "MANCHESTER CITY",
                            "diagnosis": "ANTERIOR CRUCIATE LIGAMENT TEAR",
                            "matches_missed": 38,
                            "expected_return": "PRE-SEASON JULY 2025",
                            "status": "LIGHT PITCH WORK",
                            "progress_percentage": 50
                        }
                    }
                }
            }
        ]
    }
]

class TestEngineRegression(unittest.TestCase):
    def setUp(self):
        self.qa = EngineQASuite(PROJECT_ROOT)

    def test_all_seven_story_types_props_and_qa(self):
        """Validates that all 7 story formats generate valid, tokenized Remotion props passing QA checks."""
        for story_payload in STORY_PAYLOADS:
            story_id = story_payload["story"]["story_id"]
            logger.info(f"Testing Story Format: {story_id}")

            # 1. Prepare dynamic props
            props = prepare_remotion_props(story_payload, PROJECT_ROOT, fps=30.0)

            # Assert top-level keys
            self.assertIn("headline", props)
            self.assertIn("totalDurationInFrames", props)
            self.assertIn("scenes", props)
            self.assertIn("tickerText", props)
            self.assertIn("subtitles", props)
            self.assertGreater(props["totalDurationInFrames"], 0)
            self.assertGreaterEqual(len(props["scenes"]), 1)

            # 2. Text & Layout QA check
            layout_check = self.qa.verify_text_and_layout(props)
            self.assertTrue(
                layout_check["passed"],
                f"Layout QA failed for {story_id}: {layout_check['issues']}"
            )

            # 3. Subtitles cues generation check
            self.assertGreater(
                len(props["subtitles"]),
                0,
                f"Subtitles cue list is empty for {story_id}"
            )

            logger.info(f"✓ Story Format Passed: {story_id}")

    def test_design_tokens_consistency(self):
        """Verifies central layout coordinates, safe margins, and audio tokens meet broadcast standards."""
        from config.design_tokens import LAYOUT_TOKENS, COLOR_TOKENS, AUDIO_TOKENS, PACING_TOKENS

        # Ticker lowered to bottom safe area
        self.assertEqual(LAYOUT_TOKENS["ticker"]["y"], 1730)
        self.assertEqual(LAYOUT_TOKENS["ticker"]["height"], 110)
        self.assertEqual(LAYOUT_TOKENS["ticker"]["track_x"], 295)
        self.assertEqual(LAYOUT_TOKENS["ticker"]["track_width"], 785)

        # Subtitles safe zone
        self.assertEqual(LAYOUT_TOKENS["subtitles"]["y"], 1300)
        self.assertLess(LAYOUT_TOKENS["subtitles"]["y"], LAYOUT_TOKENS["lower_third"]["y"])

        # Lower-third anchor
        self.assertEqual(LAYOUT_TOKENS["lower_third"]["y"], 1440)
        self.assertEqual(LAYOUT_TOKENS["lower_third"]["height"], 200)

        # Audio mastering invariants (zero screech, -14 LUFS, 48kHz PCM)
        self.assertEqual(AUDIO_TOKENS["sample_rate"], 48000)
        self.assertEqual(AUDIO_TOKENS["channels"], 2)
        self.assertEqual(AUDIO_TOKENS["target_lufs"], -14.0)
        self.assertEqual(AUDIO_TOKENS["true_peak_ceiling"], -1.0)
        self.assertGreaterEqual(AUDIO_TOKENS["scene_final_hold_sec"], 0.70)

        # Cadence pacing bounds
        self.assertLessEqual(PACING_TOKENS["target_duration_min"], 24.0)
        self.assertGreaterEqual(PACING_TOKENS["target_duration_max"], 30.0)
        self.assertEqual(PACING_TOKENS["visual_beat_interval_sec"], (2.0, 4.0))

    def test_subtitles_engine_phrase_grouping_and_ass(self):
        """Verifies word-level grouping into rhythmic display cards and ASS safe-zone generation."""
        from stages.subtitles_engine import group_words_into_rhythmic_phrases, generate_ass_script
        import tempfile

        mock_words = [
            {"word": "Real", "start": 0.0, "end": 0.25},
            {"word": "Madrid", "start": 0.26, "end": 0.55},
            {"word": "have", "start": 0.56, "end": 0.75},
            {"word": "enquired", "start": 0.76, "end": 1.15},
            {"word": "about", "start": 1.16, "end": 1.35},
            {"word": "Endrick.", "start": 1.36, "end": 1.75}
        ]

        phrases = group_words_into_rhythmic_phrases(mock_words, max_words_per_phrase=3)
        self.assertGreater(len(phrases), 0)
        self.assertEqual(phrases[0]["words"][0]["word"], "Real")

        with tempfile.TemporaryDirectory() as td:
            ass_path = Path(td) / "test_subs.ass"
            generate_ass_script(phrases, ass_path, margin_v=620)
            self.assertTrue(ass_path.exists())
            content = ass_path.read_text(encoding="utf-8")
            self.assertIn("PlayResX: 1080", content)
            self.assertIn("PlayResY: 1920", content)
            self.assertIn("MarginV, Encoding", content)
            self.assertIn("620,1", content)
            self.assertIn("&H0066D1FF&", content)  # Brand Yellow Highlight

    def test_retention_tracker_cohort_evaluation(self):
        """Verifies logging video DNA, recording analytics snapshots, and cohort evaluation."""
        from pipeline.retention_tracker import RetentionTracker
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test_retention.db"
            tracker = RetentionTracker(db_path=db_path)

            # Log 3 sample videos
            for i in range(3):
                vid = tracker.log_video({
                    "video_id": f"reg_test_{i+1}",
                    "story_category": "transfer_rumour" if i == 0 else "governance",
                    "headline": f"Test Headline {i+1}",
                    "duration_sec": 27.5 + i,
                    "hook_selected": f"Hook text {i+1}",
                    "hook_type": "question_challenge" if i % 2 == 0 else "shocking_number_fact",
                    "script_word_count": 72 + i * 2,
                    "visual_beats_count": 7
                })
                tracker.record_analytics_snapshot(vid, "24h", {
                    "shown_in_feed": 1000 + i * 200,
                    "stayed_to_watch_pct": 72.0 + i * 3.0,
                    "average_percentage_viewed_pct": 75.0 + i * 2.0,
                    "likes": 50,
                    "comments": 10
                })

            cohort = tracker.evaluate_10_video_cohort()
            self.assertEqual(cohort["status"], "COMPLETED")
            self.assertEqual(cohort["cohort_size"], 3)
            self.assertGreater(len(cohort["top_performers"]), 0)
            self.assertGreater(len(cohort["evidence_based_recommendations"]), 0)

if __name__ == "__main__":
    unittest.main()
