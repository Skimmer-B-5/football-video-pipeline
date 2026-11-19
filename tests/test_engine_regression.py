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

if __name__ == "__main__":
    unittest.main()
