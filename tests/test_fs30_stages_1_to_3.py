"""
Test Suite for FS 30 Pipeline: Stages 1 to 3.
Exercises:
1. Stage 1 story fetching and parsing.
2. Stage 2 script generation with deliberate validation failure and successful retry recovery.
3. Stage 3 frame planning with deliberate validation failure, animation sanitization, and successful retry.
"""

import unittest
import shutil
import json
from pathlib import Path

from fs30.config import PROJECT_ROOT, get_run_dir
from fs30.stage1_fetch_story import fetch_story
from fs30.stage2_write_script import write_script, validate_script
from fs30.stage3_plan_frames import plan_frames, validate_plan, sanitize_and_log_animations

SAMPLE_STORY_TEXT = """
SOURCE NAME: The Guardian
PUBLISHED: 2026-11-20
HEADLINE: Luis Suarez in new shocking controversy
ARTICLE TEXT:
Luis Suarez has once again stunned the football world with another unbelievable chapter in his career.
Former Liverpool striker Luis Suarez has been involved in high-stakes controversy spanning his career from Ajax to England.
According to The Guardian, football governing bodies have reviewed the complete disciplinary history.
Liverpool officials stood by the Uruguayan forward during numerous intense Premier League campaigns.
The legacy remains a chilling divide between sublime goalscoring genius and moments of pure madness on the pitch.
"""

class TestFS30Stages1To3(unittest.TestCase):
    def setUp(self):
        self.test_run_id = "test_run_unit_001"
        self.run_dir = get_run_dir(self.test_run_id)

    def tearDown(self):
        if self.run_dir.exists():
            shutil.rmtree(self.run_dir)

    def test_stage1_fetch_story(self):
        """Verify Stage 1 correctly parses and saves story.json."""
        story = fetch_story(SAMPLE_STORY_TEXT, self.run_dir)
        self.assertEqual(story["source_name"], "The Guardian")
        self.assertEqual(story["headline"], "Luis Suarez in new shocking controversy")
        self.assertTrue((self.run_dir / "story.json").exists())

    def test_stage2_retry_on_deliberate_validation_failure(self):
        """
        Verify Stage 2 detects deliberate validation failure (e.g., contains digits, wrong word count)
        and successfully recovers on retry when error feedback is provided.
        """
        story = fetch_story(SAMPLE_STORY_TEXT, self.run_dir)

        call_count = 0
        def mocked_llm(system_prompt, user_prompt, log_func=print):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Deliberate failure: contains digit '10', quotes, and wrong word count
                return {
                    "title": "Suarez Career Controversy",
                    "certainty": "confirmed",
                    "beats": [
                        {"beat": "hook", "narration": "Luis Suarez stunned the world with 10 match bans."},
                        {"beat": "context", "narration": "His journey was filled with unbelievable drama."},
                        {"beat": "source", "narration": "According to The Guardian reporters."},
                        {"beat": "detail", "narration": "He served heavy suspensions across Europe."},
                        {"beat": "outlook", "narration": "His complex football legacy remains split forever."}
                    ],
                    "pronunciation_hints": {},
                    "word_count": 40
                }
            else:
                # Clean recovery: exactly 74 words, no digits, no quotes, source in source beat, <=16 words/sentence
                b1 = "Luis Suarez left an unforgettable mark on modern football with his breathtaking and controversial skill."
                b2 = "From Ajax to Liverpool, shocking flashpoints repeatedly overshadowed his extraordinary and undisputed natural attacking brilliance."
                b3 = "According to The Guardian, English football authorities handed down severe unprecedented punishments and heavy suspensions."
                b4 = "He captured thirty one league goals without a single penalty kick during that magnificent final season."
                b5 = "Supporters worldwide remain divided forever between his scoring genius and unpredictable temper on the pitch."
                total_words = len((f"{b1} {b2} {b3} {b4} {b5}").split())
                return {
                    "title": "Luis Suarez Career Breakdown",
                    "certainty": "confirmed",
                    "beats": [
                        {"beat": "hook", "narration": b1},
                        {"beat": "context", "narration": b2},
                        {"beat": "source", "narration": b3},
                        {"beat": "detail", "narration": b4},
                        {"beat": "outlook", "narration": b5}
                    ],
                    "pronunciation_hints": {"Suarez": "SWAH-rez"},
                    "word_count": total_words
                }

        script = write_script(story, self.run_dir, llm_func=mocked_llm)
        self.assertEqual(call_count, 2, "LLM should have been called twice (1 failure + 1 retry)")
        self.assertTrue(70 <= script["word_count"] <= 85)
        self.assertTrue((self.run_dir / "script.json").exists())

    def test_stage3_retry_and_sanitization(self):
        """
        Verify Stage 3 catches invalid scene count / mismatched narration,
        recovers on retry, and properly sanitizes unknown animation keywords.
        """
        # Valid 74-word script
        b1 = "Luis Suarez left an unforgettable mark on modern football with his breathtaking and controversial skill."
        b2 = "From Ajax to Liverpool, shocking flashpoints repeatedly overshadowed his extraordinary and undisputed natural attacking brilliance."
        b3 = "According to The Guardian, English football authorities handed down severe unprecedented punishments and heavy suspensions."
        b4 = "He captured thirty one league goals without a single penalty kick during that magnificent final season."
        b5 = "Supporters worldwide remain divided forever between his scoring genius and unpredictable temper on the pitch."
        script = {
            "title": "Luis Suarez Career Breakdown",
            "certainty": "confirmed",
            "beats": [
                {"beat": "hook", "narration": b1},
                {"beat": "context", "narration": b2},
                {"beat": "source", "narration": b3},
                {"beat": "detail", "narration": b4},
                {"beat": "outlook", "narration": b5}
            ],
            "pronunciation_hints": {"Suarez": "SWAH-rez"},
            "word_count": len((f"{b1} {b2} {b3} {b4} {b5}").split())
        }

        call_count = 0
        def mocked_llm(system_prompt, user_prompt, log_func=print):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Deliberate failure: only 3 scenes (expected 6 to 9)
                return {
                    "palette": {"accent1": "#C8102E", "accent2": "#00B2A9", "accent3": "#F6EB61", "paper": "#F4EFE6"},
                    "assets": [{"id": "a1", "type": "photo", "search_query": "Suarez", "fallback_query": "Suarez photo"}],
                    "scenes": [
                        {"id": 1, "beat": "hook", "narration": b1, "layers": [{"z": 0, "role": "background", "asset": "a1"}]}
                    ]
                }
            else:
                # Clean recovery: 6 scenes covering script exactly
                return {
                    "palette": {"accent1": "#C8102E", "accent2": "#00B2A9", "accent3": "#F6EB61", "paper": "#F4EFE6"},
                    "assets": [
                        {"id": "a1", "type": "photo", "search_query": "Anfield stadium", "fallback_query": "stadium", "subject_alt": "none"},
                        {"id": "a2", "type": "cutout", "search_query": "Luis Suarez portrait", "fallback_query": "Suarez Liverpool", "subject_alt": "jersey_silhouette"}
                    ],
                    "scenes": [
                        {
                            "id": 1, "beat": "hook", "narration": b1, "est_seconds": 3.7,
                            "camera": {"move": "push_in", "intensity": "low"}, "transition_out": "paper_wipe",
                            "layers": [
                                {"z": 0, "role": "background", "asset": "a1"},
                                {"z": 1, "role": "paper_shape", "shape": "torn_strip", "color": "accent1", "enter": "slide_in_left", "enter_delay": 0.0, "idle": "none", "exit": "none"},
                                {"z": 2, "role": "subject", "asset": "a2", "enter": "pop_in", "enter_delay": 0.3, "idle": "float", "exit": "none"},
                                {"z": 3, "role": "text_card", "text": "GOAL MACHINE", "enter": "drop_in", "enter_delay": 0.6, "idle": "none", "exit": "none"}
                            ]
                        },
                        {
                            "id": 2, "beat": "context", "narration": "From Ajax to Liverpool,", "est_seconds": 1.5,
                            "camera": {"move": "drift_left", "intensity": "low"}, "transition_out": "torn_slide",
                            "layers": [
                                {"z": 0, "role": "background", "asset": "a1"},
                                {"z": 1, "role": "paper_shape", "shape": "ticket", "color": "accent2", "enter": "fade_magical", "enter_delay": 0.0, "idle": "none", "exit": "none"} # Unknown anim to test sanitization
                            ]
                        },
                        {
                            "id": 3, "beat": "context", "narration": "shocking flashpoints repeatedly overshadowed his extraordinary and undisputed natural attacking brilliance.", "est_seconds": 3.7,
                            "camera": {"move": "pull_out", "intensity": "low"}, "transition_out": "page_flip",
                            "layers": [
                                {"z": 0, "role": "background", "asset": "a1"},
                                {"z": 1, "role": "text_card", "text": "ENDLESS TURMOIL", "enter": "tear_in", "enter_delay": 0.2, "idle": "none", "exit": "none"}
                            ]
                        },
                        {
                            "id": 4, "beat": "source", "narration": b3, "est_seconds": 4.1,
                            "camera": {"move": "drift_right", "intensity": "low"}, "transition_out": "paper_wipe",
                            "layers": [
                                {"z": 0, "role": "background", "asset": "a1"},
                                {"z": 1, "role": "paper_shape", "shape": "banner", "color": "accent3", "enter": "unfold", "enter_delay": 0.0, "idle": "none", "exit": "none"}
                            ]
                        },
                        {
                            "id": 5, "beat": "detail", "narration": b4, "est_seconds": 4.8,
                            "camera": {"move": "static_breathe", "intensity": "low"}, "transition_out": "torn_slide",
                            "layers": [
                                {"z": 0, "role": "background", "asset": "a1"},
                                {"z": 1, "role": "subject", "asset": "a2", "enter": "drop_in", "enter_delay": 0.2, "idle": "pulse", "exit": "none"}
                            ]
                        },
                        {
                            "id": 6, "beat": "outlook", "narration": b5, "est_seconds": 4.1,
                            "camera": {"move": "push_in", "intensity": "low"}, "transition_out": "cut",
                            "layers": [
                                {"z": 0, "role": "background", "asset": "a1"},
                                {"z": 1, "role": "text_card", "text": "GENIUS OR MADNESS?", "enter": "pop_in", "enter_delay": 0.0, "idle": "none", "exit": "none"}
                            ]
                        }
                    ]
                }

        plan = plan_frames(script, self.run_dir, dry_run=True, llm_func=mocked_llm)
        self.assertEqual(call_count, 2, "Stage 3 should have retried after initial failure")
        self.assertEqual(len(plan["scenes"]), 6)
        # Verify unknown animation 'fade_magical' was sanitized to 'none'
        self.assertEqual(plan["scenes"][1]["layers"][1]["enter"], "none")
        self.assertTrue((self.run_dir / "plan.json").exists())

if __name__ == "__main__":
    unittest.main()
