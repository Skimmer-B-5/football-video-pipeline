"""
beta/tests/test_editorial_intelligence.py - Automated Editorial Intelligence & Regression Test Suite (V6.2).

Comprehensive verification of:
1. Dynamic statistical freshness: Rejects stale statistics after subsequent matches.
2. Match fixture validation: Regressions for wrong opponent (Celta Vigo vs Leganés), date,
   substitution minute (70' vs 76'), added minutes (20 vs 14), aggregate total (159 vs 155),
   and competition scope (All Competitions vs League Only).
3. Conflicting transfer fees (€60M vs €70M) and buy-back options (€80M vs €85M).
4. Deal structure consistency (permanent vs loan contradiction, ending question alignment).
5. Unsupported firm language guard ('insist', 'demand', 'agreed', 'confirmed').
6. Semantic redundancy between consecutive beats.
7. Spoken word expansion accuracy (including 159, currencies, abbreviations).
8. Mathematical timing reconciliation (scene durations sum strictly equals total narration timeline).
9. Opening 4-second secrecy (name concealed in first 10 spoken words and on-screen graphics).
10. Historical temporal relevance rejection (Guardiola 2024 extension cannot validate 2026 news).
11. Matchday participation contradiction rejection (Ødegaard started vs Newcastle on Nov 21).
12. Historical sanction conflation rejection (Everton 2024 deductions vs 2026 news).
13. Real URL verification & generic homepage rejection.
14. Duplicate source URL and syndication detection.
15. Four-gate architecture strict separation (Gate A and Gate B failure prevents overall PASS).
16. Source-to-script claim mapping validation (unreferenced claims, manager attribution, minutes).
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path so 'beta' package is importable
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
PROJECT_ROOT = TEST_DIR.parent

from stages.editorial_policy import (
    expand_spoken_tokens,
    calculate_written_and_spoken_counts,
    BANNED_CLICHES,
    OpeningSecrecyValidator,
    QualifiedLanguageGuard,
    DynamicStatFreshnessEngine,
    DealStructureConsistencyValidator,
    SemanticRedundancyValidator,
    MathematicalTimingReconciler,
    EditorialQualityGate
)
from stages.source_verifier import SourceVerifier, SourceCorroborationEngine
from stages.claim_mapper import SourceToScriptClaimValidator
from stages.hook_engine import CuriosityHookEngine


class TestEditorialIntelligence(unittest.TestCase):

    def setUp(self):
        self.sample_headline = "Milan prepare €60m bid for Endrick"
        self.sample_text = (
            "A lack of playing time amid fierce competition looks set to edge Endrick towards the exit door at Real Madrid "
            "with Milan emerging as his most likely destination. According to reports from Italian outlet Corriere dello Sport, "
            "the San Siro hierarchy are preparing a sixty million euro proposal. Real Madrid reportedly favor an eighty million buy-back option."
        )
        self.sources = [{
            "publisher": "Corriere dello Sport",
            "url": "https://www.corrieredellosport.it/news/calcio/calciomercato/milan/2026/11/10/endrick",
            "published_at": "2026-11-10"
        }]
        # Verified match log for Endrick on November 21, 2026:
        # Real Madrid 2–1 Celta Vigo, introduced at 70' for Mbappé, 20 minutes played, season total 159 minutes.
        self.match_logs_nov21 = [
            {
                "date": "2026-11-21",
                "fixture": "Real Madrid 2-1 Celta Vigo",
                "opponent": "Celta Vigo",
                "sub_minute": 70,
                "minutes_played": 20
            }
        ]

    def test_01_stale_statistics_after_subsequent_match(self):
        """Test 1: Rejects 139 minutes based on Nov 10 report when player featured for 20 mins on Nov 21."""
        claimed_value = 139
        cut_off_date = "2026-11-10"

        is_fresh, current_total, latest_date, err = DynamicStatFreshnessEngine.verify_stat_freshness(
            claimed_value=claimed_value,
            stat_name="minutes",
            cut_off_date=cut_off_date,
            match_logs=self.match_logs_nov21
        )
        self.assertFalse(is_fresh, "Failed to flag stale minutes after subsequent matchday!")
        self.assertEqual(current_total, 159, f"Expected 159 minutes (139+20), got {current_total}")
        self.assertEqual(latest_date, "2026-11-21")
        self.assertIn("Stale statistic rejected", err)

    def test_02_match_fixture_validation_regressions(self):
        """Test 2: Verifies all Section 4 matchday regression checks."""
        verified_match_data = {
            "opponent": "Celta Vigo",
            "date": "2026-11-21",
            "sub_minute": 70,
            "minutes_played": 20,
            "verified_aggregate": 159,
            "verified_scope": "All Competitions (La Liga & Champions League)"
        }

        # 2a. Wrong opponent regression (Leganés vs Celta Vigo)
        valid_opp, errs_opp = DynamicStatFreshnessEngine.verify_match_fixture(
            claimed_opponent="Leganés",
            claimed_date="2026-11-21",
            claimed_sub_minute=70,
            claimed_minutes=20,
            actual_match_data=verified_match_data
        )
        self.assertFalse(valid_opp)
        self.assertTrue(any("Wrong opponent" in e for e in errs_opp))

        # 2b. Wrong substitution minute regression (76' vs 70')
        valid_sub, errs_sub = DynamicStatFreshnessEngine.verify_match_fixture(
            claimed_opponent="Celta Vigo",
            claimed_date="2026-11-21",
            claimed_sub_minute=76,
            claimed_minutes=20,
            actual_match_data=verified_match_data
        )
        self.assertFalse(valid_sub)
        self.assertTrue(any("Incorrect substitution minute" in e for e in errs_sub))

        # 2c. Wrong added minutes regression (14 mins vs 20 mins)
        valid_min, errs_min = DynamicStatFreshnessEngine.verify_match_fixture(
            claimed_opponent="Celta Vigo",
            claimed_date="2026-11-21",
            claimed_sub_minute=70,
            claimed_minutes=14,
            actual_match_data=verified_match_data
        )
        self.assertFalse(valid_min)
        self.assertTrue(any("Incorrect added minutes" in e for e in errs_min))

        # 2d. Wrong aggregate total regression (155 vs 159)
        data_wrong_agg = dict(verified_match_data, claimed_aggregate=155)
        valid_agg, errs_agg = DynamicStatFreshnessEngine.verify_match_fixture(
            claimed_opponent="Celta Vigo",
            claimed_date="2026-11-21",
            claimed_sub_minute=70,
            claimed_minutes=20,
            actual_match_data=data_wrong_agg
        )
        self.assertFalse(valid_agg)
        self.assertTrue(any("Stale aggregate statistics" in e for e in errs_agg))

        # 2e. Wrong competition scope regression ("La Liga only" vs All Comps)
        data_wrong_scope = dict(verified_match_data, claimed_scope="La Liga only")
        valid_scope, errs_scope = DynamicStatFreshnessEngine.verify_match_fixture(
            claimed_opponent="Celta Vigo",
            claimed_date="2026-11-21",
            claimed_sub_minute=70,
            claimed_minutes=20,
            actual_match_data=data_wrong_scope
        )
        self.assertFalse(valid_scope)
        self.assertTrue(any("Incorrect competition scope" in e for e in errs_scope))

        # 2f. All correct parameters pass cleanly
        data_all_correct = dict(
            verified_match_data,
            claimed_aggregate=159,
            claimed_scope="All Competitions (La Liga & Champions League)"
        )
        valid_all, errs_all = DynamicStatFreshnessEngine.verify_match_fixture(
            claimed_opponent="Celta Vigo",
            claimed_date="2026-11-21",
            claimed_sub_minute=70,
            claimed_minutes=20,
            actual_match_data=data_all_correct
        )
        self.assertTrue(valid_all, f"Correct match fixture data falsely rejected: {errs_all}")
        self.assertEqual(len(errs_all), 0)

    def test_03_conflicting_transfer_fees(self):
        """Test 3: Flags arbitrary selection when outlets differ between €60M and €70M."""
        text_arbitrary = "Milan are preparing a €60M proposal to sign the forward."
        conflicts = {"base_fee": ["€60M", "€70M"]}

        is_valid, errs = QualifiedLanguageGuard.validate_conflicting_figures(
            text=text_arbitrary,
            conflicting_reports=conflicts
        )
        self.assertFalse(is_valid, "Failed to catch unhedged selection between conflicting fees!")
        self.assertTrue(any("Arbitrarily selected" in e for e in errs))

        # Qualified text should pass
        text_qualified = "Milan are exploring a valuation ranging between €60M and €70M."
        is_valid_q, errs_q = QualifiedLanguageGuard.validate_conflicting_figures(
            text=text_qualified,
            conflicting_reports=conflicts
        )
        self.assertTrue(is_valid_q, f"Qualified text was falsely rejected: {errs_q}")

    def test_04_different_reported_buyback_figures(self):
        """Test 4: Flags unhedged selection when buy-back reports differ between €80M and €85M."""
        text_arbitrary = "Madrid reportedly favor an €80M buy-back option."
        conflicts = {"buyback": ["€80M", "€85M"]}

        is_valid, errs = QualifiedLanguageGuard.validate_conflicting_figures(
            text=text_arbitrary,
            conflicting_reports=conflicts
        )
        self.assertFalse(is_valid, "Failed to catch unhedged buy-back number selection!")
        self.assertTrue(any("Arbitrarily selected" in e for e in errs))

    def test_05_loan_versus_permanent_transfer_contradiction(self):
        """Test 5: Disallows describing a €60M permanent transfer and calling it a loan in the ending."""
        bad_scenes_perm_then_loan = [
            {"scene_id": "s01", "narration": "A sixty-million-euro transfer framework is emerging."},
            {"scene_id": "s02", "narration": "Milan are preparing a permanent purchase proposal."},
            {"scene_id": "s03", "narration": "Madrid favor an eighty million buy-back option."},
            {"scene_id": "s04", "narration": "With only one hundred and fifty-nine minutes under Mourinho, Serie A is tempting."},
            {"scene_id": "s05", "narration": "Should Madrid sanction a protected loan exit, or keep him in Spain?"}
        ]
        is_valid, errs = DealStructureConsistencyValidator.validate_narrative_consistency(bad_scenes_perm_then_loan)
        self.assertFalse(is_valid, "Failed to catch permanent vs loan contradiction!")
        self.assertTrue(any("Deal structure contradiction" in e for e in errs))

        bad_scenes_loan_then_perm = [
            {"scene_id": "s01", "narration": "A loan proposal is being prepared with an option to buy."},
            {"scene_id": "s02", "narration": "The club want an initial six-month loan spell."},
            {"scene_id": "s03", "narration": "Wage contributions have been agreed in principle."},
            {"scene_id": "s04", "narration": "First team minutes are urgently required."},
            {"scene_id": "s05", "narration": "Should the club accept an outright permanent sale without a buyback?"}
        ]
        is_valid_l, errs_l = DealStructureConsistencyValidator.validate_narrative_consistency(bad_scenes_loan_then_perm)
        self.assertFalse(is_valid_l, "Failed to catch loan vs permanent sale contradiction!")

    def test_06_unsupported_firm_language(self):
        """Test 6: Prohibits assertive verbs ('insist', 'demand', 'agreed', 'confirmed') on proposals."""
        bad_text = "Madrid insist on an eighty million euro buy-back clause that Milan confirmed."
        is_valid, errs = QualifiedLanguageGuard.validate_language_tone(bad_text, stage_level=5)
        self.assertFalse(is_valid, "Failed to catch firm assertive language on speculative proposal!")
        self.assertGreaterEqual(len(errs), 2, "Should catch both 'insist' and 'confirmed'.")

        good_text = "Madrid reportedly favor an eighty million euro buy-back option, mirroring the Nico Paz deal."
        is_valid_g, errs_g = QualifiedLanguageGuard.validate_language_tone(good_text, stage_level=5)
        self.assertTrue(is_valid_g, f"Qualified text was falsely flagged: {errs_g}")

    def test_07_repeated_facts_across_scenes_semantic_redundancy(self):
        """Test 7: Flags consecutive scenes repeating the same fee without new information."""
        redundant_scenes = [
            {"scene_id": "s01", "narration": "A sixty-million-euro transfer framework is emerging with Milan."},
            {"scene_id": "s02", "narration": "Milan are preparing a sixty million euro bid to sign the forward."}
        ]
        is_valid, errs = SemanticRedundancyValidator.validate_progression(redundant_scenes)
        self.assertFalse(is_valid, "Failed to catch semantic redundancy across consecutive beats!")
        self.assertTrue(any("Semantic redundancy" in e for e in errs))

    def test_08_spoken_word_expansion_accuracy(self):
        """Test 8: Verifies exact token count expansion for numbers, currencies, and abbreviations."""
        text = "€60M in 2026 for 159 minutes vs AC Milan."
        w_count, s_count, tokens = calculate_written_and_spoken_counts(text)

        self.assertEqual(w_count, 9, f"Written word count expected 9, got {w_count}")
        # Expected expansion:
        # €60M -> sixty million euros (3)
        # in (1)
        # 2026 -> twenty twenty-six (2)
        # for (1)
        # 159 -> one hundred and fifty-nine (4)
        # minutes (1)
        # vs -> versus (1)
        # AC (1)
        # Milan (1)
        # Total = 3 + 1 + 2 + 1 + 4 + 1 + 1 + 1 + 1 = 15 spoken tokens
        self.assertEqual(s_count, 15, f"Spoken token count expected 15, got {s_count}. Tokens: {tokens}")
        self.assertIn("sixty", tokens)
        self.assertIn("euros", tokens)
        self.assertIn("fifty-nine", tokens)
        self.assertIn("versus", tokens)

    def test_09_scene_duration_totals_agree_with_narration_timeline(self):
        """Test 9: Scene duration sum must mathematically equal the total narration timeline."""
        scenes = [
            {"scene_id": "s01", "narration": "A sixty-million-euro transfer framework is emerging, with Madrid setting one unexpected condition."},
            {"scene_id": "s02", "narration": "That player is Endrick, as Milan explore a winter move to Serie A."},
            {"scene_id": "s03", "narration": "Madrid reportedly favor an eighty-million-euro buy-back option, mirroring the Nico Paz deal."},
            {"scene_id": "s04", "narration": "With only one hundred and fifty-nine minutes under Mourinho, Serie A minutes are tempting."},
            {"scene_id": "s05", "narration": "Should Madrid sanction a transfer with a buy-back option, or keep Endrick in Spain?"}
        ]
        timing = MathematicalTimingReconciler.reconcile_scenes(scenes, wpm=140.0)

        self.assertTrue(timing["is_mathematically_reconciled"], "Timeline is not mathematically reconciled!")
        self.assertEqual(timing["math_discrepancy"], 0.0)
        self.assertEqual(timing["sum_scene_durations"], timing["total_timeline_sec"])

        prev_end = 0.0
        for s in timing["scenes"]:
            self.assertEqual(s["start_sec"], prev_end)
            prev_end = s["end_sec"]
        self.assertEqual(prev_end, timing["total_timeline_sec"])

    def test_10_opening_secrecy_enforcement(self):
        """Test 10: Player name must NOT appear in Scene 1 narration first 10 words or on-screen graphics."""
        good_scene = {
            "narration": "A sixty-million-euro transfer framework is emerging, with Madrid setting one unexpected condition.",
            "on_screen": {
                "headline": "€60M TRANSFER FRAMEWORK",
                "kicker": "TRANSFER WATCH",
                "subheadline": "SAN SIRO PROPOSAL"
            }
        }
        is_valid, errors = OpeningSecrecyValidator.validate_opening_secrecy(good_scene, ["Endrick"])
        self.assertTrue(is_valid, f"Good scene was falsely rejected: {errors}")
        self.assertEqual(len(errors), 0)

        bad_scene = {
            "narration": "Endrick is facing a sixty-million-euro transfer framework at Real Madrid.",
            "on_screen": {
                "headline": "ENDRICK TO MILAN",
                "kicker": "TRANSFER WATCH",
                "subheadline": "SAN SIRO PROPOSAL"
            }
        }
        is_valid_b, errors_b = OpeningSecrecyValidator.validate_opening_secrecy(bad_scene, ["Endrick"])
        self.assertFalse(is_valid_b, "Failed to catch player name in first 10 words and headline!")
        self.assertGreaterEqual(len(errors_b), 2)

    def test_11_historical_temporal_relevance_rejection(self):
        """Test 11: Rejects using a historical 2024 contract extension to validate a 2026 news claim."""
        scenes = [
            {"scene_id": "s01", "narration": "Manchester City have reached an agreement in principle on a one-year contract extension.", "claim_ids": ["claim_pep_2024"]}
        ]
        # Claim dated November 2024
        evidence_claims = [
            {
                "claim_id": "claim_pep_2024",
                "text": "Pep Guardiola signs a one-year contract extension with Manchester City.",
                "published_at": "2024-11-20"
            }
        ]
        is_valid, _, errors = SourceToScriptClaimValidator.validate_script_claims(
            scenes=scenes,
            evidence_claims=evidence_claims,
            reference_year=2026
        )
        self.assertFalse(is_valid, "Failed to reject historical 2024 claim for 2026 news!")
        self.assertTrue(any("Temporal irrelevance error" in e for e in errors))

    def test_12_matchday_participation_contradiction_rejection(self):
        """Test 12: Rejects Martin Ødegaard injury claim when match logs confirm matchday participation."""
        # Story claims Ødegaard is sidelined with fresh ankle ligament strain
        story_text = "Martin Odegaard faces several weeks on the sidelines following a confirmed medial ligament strain."
        
        # Actual match log records full appearance on Nov 21, 2026 vs Newcastle
        match_log_ode = [
            {
                "date": "2026-11-21",
                "fixture": "Arsenal vs Newcastle",
                "minutes_played": 90,
                "status": "started_and_completed"
            }
        ]
        
        # Verify freshness rejects injury claim because player started and played full 90 mins on Nov 21
        is_fresh, current_mins, latest_date, err = DynamicStatFreshnessEngine.verify_stat_freshness(
            claimed_value=0, # Claiming 0 active availability
            stat_name="injury_absence",
            cut_off_date="2026-11-20",
            match_logs=match_log_ode
        )
        self.assertFalse(is_fresh)
        self.assertIn("Player subsequently featured", err)

    def test_13_historical_sanction_conflation_rejection(self):
        """Test 13: Rejects conflating 2024 Everton PSR points deductions (10 to 6) with 2026 news."""
        scenes = [
            {
                "scene_id": "s01",
                "narration": "An independent appeals board has reduced Everton's points deduction from ten points to six.",
                "claim_ids": ["claim_everton_2024"]
            }
        ]
        evidence_claims = [
            {
                "claim_id": "claim_everton_2024",
                "text": "Everton points deduction reduced from 10 to 6 points on appeal.",
                "published_at": "2024-02-26"
            }
        ]
        is_valid, _, errors = SourceToScriptClaimValidator.validate_script_claims(
            scenes=scenes,
            evidence_claims=evidence_claims,
            reference_year=2026
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("Temporal irrelevance error" in e for e in errors))

    def test_14_real_url_verification_and_generic_homepage_rejection(self):
        """Test 14: Verifies rejection of generic homepages and placeholder domains."""
        # Generic homepage rejection
        res_bbc = SourceVerifier.verify_url("https://www.bbc.com/sport/football")
        self.assertFalse(res_bbc.is_verified)
        self.assertTrue(res_bbc.is_generic_homepage)
        self.assertIn("Generic homepage URL rejected", res_bbc.rejection_reason)

        res_marca = SourceVerifier.verify_url("https://marca.com/futbol")
        self.assertFalse(res_marca.is_verified)
        self.assertTrue(res_marca.is_generic_homepage)

        # Placeholder rejection
        res_ph = SourceVerifier.verify_url("http://example.com/test-article")
        self.assertFalse(res_ph.is_verified)
        self.assertTrue(res_ph.is_placeholder)

        # Valid article URL using mock registry
        mock_reg = {
            "https://www.bbc.co.uk/sport/football/articles/c04992525e9o": {
                "http_status": 200,
                "title": "Arsenal vs Newcastle: Odegaard starts at Emirates",
                "publisher": "BBC Sport",
                "published_date": "2026-11-21",
                "article_text": "Martin Odegaard captained the side, starting in midfield alongside Declan Rice."
            }
        }
        res_valid = SourceVerifier.verify_url("https://www.bbc.co.uk/sport/football/articles/c04992525e9o", mock_registry=mock_reg)
        self.assertTrue(res_valid.is_verified)
        self.assertEqual(res_valid.title, "Arsenal vs Newcastle: Odegaard starts at Emirates")

    def test_15_duplicate_and_syndication_detection(self):
        """Test 15: Flags duplicate source URLs that resolve to identical canonical targets."""
        sources = [
            {"publisher": "The Athletic", "url": "https://theathletic.com/football/article-12345?utm_source=twitter"},
            {"publisher": "The Athletic Copy", "url": "https://theathletic.com/football/article-12345?utm_source=newsletter"}
        ]
        analysis = SourceCorroborationEngine.analyze_sources(sources)
        self.assertEqual(len(analysis["duplicates"]), 1)
        self.assertFalse(analysis["is_independent_corroboration"])

    def test_16_four_gate_strict_separation_enforcement(self):
        """Test 16: Confirms that Gate A or Gate B failure prevents an overall PASS regardless of score."""
        scene_plan = {
            "schema_version": "2.0",
            "story": {"primary_subject": "Endrick"},
            "scenes": [
                {"scene_id": "s01", "narration": "A sixty-million-euro transfer framework is emerging with Milan.", "claim_ids": ["claim_1"]}
            ]
        }
        
        # Test 16a: Gate A failure (invalid source URL)
        bad_dossier_a = {
            "sources": [{"url": "https://www.bbc.com/sport/football"}], # Generic homepage -> Gate A failure
            "claims": [{"claim_id": "claim_1", "text": "Milan explore €60M transfer.", "published_at": "2026-11-21"}]
        }
        eval_a = EditorialQualityGate.evaluate(scene_plan, bad_dossier_a)
        self.assertFalse(eval_a["gate_a_source_retrieval"]["passed"])
        self.assertFalse(eval_a["passed"])
        self.assertEqual(eval_a["status"], "FAILED")

        # Test 16b: Gate B failure (unreferenced claim)
        bad_dossier_b = {
            "sources": [{"url": "https://corrieredellosport.it/news/calcio/calciomercato/milan/2026/11/10/endrick"}],
            "claims": [] # Missing claims -> Gate B failure
        }
        mock_reg = {
            "https://corrieredellosport.it/news/calcio/calciomercato/milan/2026/11/10/endrick": {
                "http_status": 200, "title": "Endrick Milan proposal", "article_text": "Milan propose €60M."
            }
        }
        eval_b = EditorialQualityGate.evaluate(scene_plan, bad_dossier_b, mock_source_registry=mock_reg)
        self.assertTrue(eval_b["gate_a_source_retrieval"]["passed"])
        self.assertFalse(eval_b["gate_b_fact_verification"]["passed"])
        self.assertFalse(eval_b["passed"])
        self.assertEqual(eval_b["status"], "FAILED")

    def test_17_source_to_script_claim_mapping_validations(self):
        """Test 17: Validates manager attribution, statistical minutes, and unreferenced claims."""
        # 17a. Manager attribution mismatch (Ancelotti vs Mourinho)
        scenes_mgr_err = [
            {"scene_id": "s01", "narration": "Endrick has struggled for minutes under Ancelotti this season.", "claim_ids": ["claim_m"]}
        ]
        claims_mgr = [
            {"claim_id": "claim_m", "text": "Endrick has played limited minutes under José Mourinho at Real Madrid.", "published_at": "2026-11-21"}
        ]
        valid_m, _, errs_m = SourceToScriptClaimValidator.validate_script_claims(scenes_mgr_err, claims_mgr)
        self.assertFalse(valid_m)
        self.assertTrue(any("Manager attribution error" in e for e in errs_m))

        # 17b. Statistical minutes mismatch (141 vs 159)
        scenes_min_err = [
            {"scene_id": "s01", "narration": "With only one hundred and forty-one minutes under Mourinho, Serie A is tempting.", "claim_ids": ["claim_stat"]}
        ]
        claims_stat = [
            {"claim_id": "claim_stat", "text": "Endrick has played 159 minutes under Mourinho this season.", "published_at": "2026-11-21"}
        ]
        valid_s, _, errs_s = SourceToScriptClaimValidator.validate_script_claims(scenes_min_err, claims_stat)
        self.assertFalse(valid_s)
        self.assertTrue(any("Statistical minutes mismatch" in e for e in errs_s))

        # 17c. Aligned claims pass
        scenes_aligned = [
            {"scene_id": "s01", "narration": "With only one hundred and fifty-nine minutes under Mourinho, Serie A minutes are tempting.", "claim_ids": ["claim_stat"]}
        ]
        valid_ok, ledger_ok, errs_ok = SourceToScriptClaimValidator.validate_script_claims(scenes_aligned, claims_stat)
        self.assertTrue(valid_ok, f"Aligned claim falsely rejected: {errs_ok}")
        self.assertEqual(len(errs_ok), 0)

    def test_18_bruno_contract_pause_vs_rejected_overseas_offers(self):
        """Test 18: Rejects claiming formally rejected overseas bids when source only reports dismissing wage demand rumors."""
        bad_scenes = [
            {"scene_id": "s01", "narration": "Bruno Fernandes rejected lucrative moves abroad to stay at Old Trafford.", "claim_ids": ["claim_b"]}
        ]
        claims = [
            {"claim_id": "claim_b", "text": "Bruno Fernandes dismissed rumors of wage demands and stated he put contract discussions on hold.", "published_at": "2026-11-22"}
        ]
        valid, _, errs = SourceToScriptClaimValidator.validate_script_claims(bad_scenes, claims)
        self.assertFalse(valid)
        self.assertTrue(any("Unverified transfer rejection" in e for e in errs))

    def test_19_raya_goalkeeper_replacement_kepa_vs_neto(self):
        """Test 19: Rejects claiming Neto replaced Raya when official match record confirms Kepa Arrizabalaga came on."""
        bad_scenes = [
            {"scene_id": "s01", "narration": "Mikel Arteta had to turn to backup keeper Neto following the injury.", "claim_ids": ["claim_r"]}
        ]
        claims = [
            {"claim_id": "claim_r", "text": "Kepa Arrizabalaga replaced David Raya in the second half of the 2-2 draw at Newcastle.", "published_at": "2026-11-21"}
        ]
        valid, _, errs = SourceToScriptClaimValidator.validate_script_claims(bad_scenes, claims)
        self.assertFalse(valid)
        self.assertTrue(any("Goalkeeper substitution error" in e for e in errs))

    def test_20_raya_pending_diagnosis_vs_asserted_severe_injury(self):
        """Test 20: Rejects asserting severe injury or 'in tears' before medical MRI diagnosis."""
        bad_scenes = [
            {"scene_id": "s01", "narration": "David Raya was in tears following a severe shoulder injury at Newcastle.", "claim_ids": ["claim_diag"]}
        ]
        claims = [
            {"claim_id": "claim_diag", "text": "David Raya was helped off close to tears with a shoulder injury, awaiting an MRI scan with prognosis unknown.", "published_at": "2026-11-21"}
        ]
        valid, _, errs = SourceToScriptClaimValidator.validate_script_claims(bad_scenes, claims)
        self.assertFalse(valid)
        self.assertTrue(any("Injury severity exaggeration" in e for e in errs))

    def test_21_brighton_scoreline_0_1_vs_2_1(self):
        """Test 21: Rejects asserting 2-1 scoreline when verified match result was 0-1."""
        bad_scenes = [
            {"scene_id": "s01", "narration": "Brighton stunned Manchester City in a two-one victory at the Etihad.", "claim_ids": ["claim_score"]}
        ]
        claims = [
            {"claim_id": "claim_score", "text": "Brighton defeated Manchester City 0-1 at the Etihad Stadium thanks to Yasin Ayari's early goal.", "published_at": "2026-11-21"}
        ]
        valid, _, errs = SourceToScriptClaimValidator.validate_script_claims(bad_scenes, claims)
        self.assertFalse(valid)
        self.assertTrue(any("Match scoreline error" in e for e in errs))

    def test_22_hurzeler_age_accuracy(self):
        """Test 22: Rejects claiming Fabian Hürzeler is 31 years old when his verified age is 33."""
        bad_scenes = [
            {"scene_id": "s01", "narration": "Guided by thirty-one-year-old manager Fabian Hurzeler.", "claim_ids": ["claim_age"]}
        ]
        claims = [
            {"claim_id": "claim_age", "text": "Fabian Hürzeler is 33 years old, born February 26, 1993.", "published_at": "2026-11-21"}
        ]
        valid, _, errs = SourceToScriptClaimValidator.validate_script_claims(bad_scenes, claims)
        self.assertFalse(valid)
        self.assertTrue(any("Manager age error" in e for e in errs))

    def test_23_ayari_fee_vs_unsupported_salary(self):
        """Test 23: Rejects claiming unsupported weekly salary of £10k/week."""
        bad_scenes = [
            {"scene_id": "s01", "narration": "Ayari was signed for a weekly salary of ten thousand pounds a week.", "claim_ids": ["claim_fee"]}
        ]
        claims = [
            {"claim_id": "claim_fee", "text": "Brighton paid £3.5m to sign Yasin Ayari from AIK.", "published_at": "2026-11-21"}
        ]
        valid, _, errs = SourceToScriptClaimValidator.validate_script_claims(bad_scenes, claims)
        self.assertFalse(valid)
        self.assertTrue(any("Unsupported salary claim" in e for e in errs))

    def test_24_data_led_recruitment_vs_pure_algorithm(self):
        """Test 24: Rejects portraying recruitment as pure algorithms without character vetting and coachability."""
        bad_scenes = [
            {"scene_id": "s01", "narration": "Brighton rely solely on algorithms without human scouting.", "claim_ids": ["claim_rec"]}
        ]
        claims = [
            {"claim_id": "claim_rec", "text": "Brighton's recruitment model combines proprietary data analytics with human scouting and character vetting.", "published_at": "2026-11-21"}
        ]
        valid, _, errs = SourceToScriptClaimValidator.validate_script_claims(bad_scenes, claims)
        self.assertFalse(valid)
        self.assertTrue(any("Recruitment model oversimplification" in e for e in errs))

    def test_25_speaking_duration_calculations_vs_configured_wpm(self):
        """Test 25: Mathematical timing strictly separates pure speech duration from pause allowances."""
        scenes = [
            {"scene_id": "s01", "narration": "A Premier League captain has chosen to freeze his own contract extension."},
            {"scene_id": "s02", "narration": "Bruno Fernandes paused negotiations, refusing to discuss personal terms while Manchester United sit second-bottom."}
        ]
        timing = MathematicalTimingReconciler.reconcile_scenes(scenes, wpm=140.0, pause_allowance_sec=0.35)
        self.assertEqual(timing["configured_wpm"], 140.0)
        self.assertGreater(timing["speech_duration_sec"], 0.0)
        self.assertGreater(timing["pause_allowance_sec"], 0.0)
        expected_speech = round((timing["total_spoken_tokens"] / 140.0) * 60.0, 2)
        self.assertEqual(timing["speech_duration_sec"], expected_speech)
        self.assertEqual(timing["total_timeline_sec"], round(timing["speech_duration_sec"] + timing["pause_allowance_sec"], 2))
        self.assertTrue(timing["is_mathematically_reconciled"])

    def test_26_image_procurement_watermark_rejection(self):
        """Test 26: Rejects watermarked stock agencies (Alamy, Getty, Shutterstock) and invalid domains."""
        from stages.image_procurement_engine import DISQUALIFIED_DOMAINS
        test_urls = [
            "https://c8.alamy.com/comp/2S7DY69/players-walk-out.jpg",
            "https://media.gettyimages.com/id/1841165125/photo/bruno.jpg",
            "https://editorial01.shutterstock.com/preview-440/bruno.jpg"
        ]
        for u in test_urls:
            is_bad = any(d in u.lower() for d in DISQUALIFIED_DOMAINS)
            self.assertTrue(is_bad, f"URL {u} should have been disqualified as a stock watermark domain")

    def test_27_opencv_focal_framing_safe_zone(self):
        """Test 27: OpenCV focal framing positions face within vertical safe zone [260, 1100]."""
        import numpy as np
        import cv2
        from stages.image_procurement_engine import OpenCVFocalFramingEngine

        framing = OpenCVFocalFramingEngine(target_w=1080, target_h=1920)
        # Create synthetic test canvas with mock face region
        canvas = np.zeros((800, 1200, 3), dtype=np.uint8)
        canvas[200:400, 500:700] = (150, 150, 150)
        cropped, meta = framing.frame_and_crop(canvas)
        self.assertEqual(cropped.shape, (1920, 1080, 3))
        self.assertIn("crop_box", meta)
        self.assertIn("final_subj_box", meta)

    def test_28_action_subject_focal_bias_not_blind_center(self):
        """Test 28: SubjectDetector applies focal bias / contour analysis, avoiding blind geometric centering."""
        import numpy as np
        from stages.image_procurement_engine import SubjectDetector

        detector = SubjectDetector()
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Foreground sports subject placed off-center in upper-left
        img[100:300, 200:450] = (255, 255, 255)
        det = detector.detect(img)
        self.assertNotEqual(det["method"], "BLIND_GEOMETRIC_CENTER")
        # Focal center should not be exact midpoint (640, 360)
        cx, cy = det["center"]
        self.assertTrue(cx != 640 or cy != 360)

    def test_29_v6_4_approved_script_refinements_and_timing(self):
        """Test 29: Verifies V6.4 approved script refinements and decoupled timing in 25-32s window."""
        bruno_narration = [
            "A Premier League captain has chosen to freeze his own contract extension.",
            "Bruno Fernandes put his own contract talks on hold, refusing to discuss personal terms while Manchester United sit second-bottom.",
            "United hold a club extension option until June twenty twenty-eight, while the midfielder dismissed rumors of wage demands.",
            "With Mauricio Pochettino arriving, will this crisis stance rally the dressing room, or leave his future uncertain?"
        ]
        full_bruno = " ".join(bruno_narration)
        self.assertIn("put his own contract talks on hold", full_bruno)
        self.assertIn("June twenty twenty-eight", full_bruno)

        timing_bruno = MathematicalTimingReconciler.reconcile_scenes(
            [{"scene_id": f"s0{i+1}", "narration": n} for i, n in enumerate(bruno_narration)],
            wpm=140.0,
            pause_allowance_sec=0.35
        )
        self.assertGreaterEqual(timing_bruno["total_timeline_sec"], 25.0)
        self.assertLessEqual(timing_bruno["total_timeline_sec"], 32.0)

        # Raya script checks
        raya_narration = [
            "A second-half collision at St James' Park has disrupted Arsenal's title momentum.",
            "David Raya was helped off close to tears with a shoulder problem, awaiting an MRI assessment.",
            "Kepa Arrizabalaga stepped in, replacing a goalkeeper who kept seven clean sheets in ten league games.",
            "With Arsenal six points clear atop the Premier League, can Kepa safeguard their title charge, or has this Newcastle setback cracked the race wide open?"
        ]
        full_raya = " ".join(raya_narration)
        self.assertIn("St James' Park", full_raya)
        self.assertNotIn("Emirates Stadium", full_raya)

        # Brighton script checks
        brighton_narration = [
            "Facing City's three-hundred-million-pound midfield, Brighton proved expenditure does not guarantee victory.",
            "The Seagulls secured a historic one-nil win, with three point five million pound recruit Yasin Ayari scoring in the eleventh minute.",
            "Brighton's model pairs data analytics with character vetting, finding coachable talent to replace major sales.",
            "With thirty-three-year-old Fabian Hürzeler guiding them to second place, can this development system genuinely sustain a title challenge?"
        ]
        full_brighton = " ".join(brighton_narration)
        self.assertIn("three point five million pound", full_brighton)
        self.assertIn("thirty-three-year-old", full_brighton)

    def test_30_background_spectator_rejection(self):
        """Test 30: Validates rejection of blurred background spectator faces (Laplacian var < 20.0)."""
        import numpy as np
        import cv2
        from stages.semantic_image_procurement import EnhancedSubjectDetector

        detector = EnhancedSubjectDetector()
        # Create heavily blurred face ROI representing background spectator in crowd
        blurred_roi = cv2.GaussianBlur(np.ones((60, 60), dtype=np.uint8) * 128, (19, 19), 6.0)
        sharpness = detector._eval_face_sharpness(blurred_roi)
        self.assertLess(sharpness, 20.0, "Blurred crowd spectator face must have Laplacian sharpness < 20.0")

        # Sharp high-contrast foreground face ROI
        sharp_roi = np.zeros((60, 60), dtype=np.uint8)
        cv2.circle(sharp_roi, (30, 30), 20, 255, -1)
        sharp_sharpness = detector._eval_face_sharpness(sharp_roi)
        self.assertGreaterEqual(sharp_sharpness, 20.0, "Foreground sharp face ROI must have sharpness >= 20.0")

    def test_31_shirt_only_image_rejection(self):
        """Test 31: Validates rejection of flat jerseys/shirts with skin ratio < 0.008."""
        import io
        from PIL import Image
        from stages.semantic_image_procurement import SceneVisualSpec, SemanticVisualVerifier

        spec = SceneVisualSpec(
            scene_id="s02",
            role="club_crisis",
            intended_subject="Bruno Fernandes",
            club="Manchester United",
            event_context="Captain in match action",
            relevant_date="2026-11-22",
            required_visual_elements=["footballer", "face", "red_shirt"],
            banned_visual_elements=["shirt_only", "product_photo"],
            allowed_asset_types=["PLAYER_CONTEXTUAL_PHOTO"],
            search_queries=["Bruno Fernandes Manchester United"]
        )

        # Create red jersey laydown image with NO human skin pixels
        img = Image.new("RGB", (600, 600), color=(200, 10, 10))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        cand_meta = {
            "title": "Manchester United Home Shirt 2026",
            "url": "https://store.manutd.com/products/shirt.jpg",
            "page_url": "https://store.manutd.com"
        }

        passed, reason, _ = SemanticVisualVerifier.inspect_candidate(raw_bytes, cand_meta, spec)
        self.assertFalse(passed, "Shirt-only product photo must fail semantic inspection")
        self.assertIn("Shirt-only or inanimate object", reason)

    def test_32_temporal_provenance_mismatch(self):
        """Test 32: Validates rejection of older historical photos presented as current match action."""
        import io
        from PIL import Image
        from stages.semantic_image_procurement import SceneVisualSpec, SemanticVisualVerifier

        spec = SceneVisualSpec(
            scene_id="s01",
            role="match_action",
            intended_subject="David Raya",
            club="Arsenal",
            event_context="David Raya injury at St James' Park on 2026-11-21",
            relevant_date="2026-11-21",
            required_visual_elements=["goalkeeper", "match_action"],
            banned_visual_elements=["old_2023_match"],
            allowed_asset_types=["EXACT_EVENT_PHOTO"],
            search_queries=["David Raya Newcastle injury"]
        )

        img = Image.new("RGB", (600, 600), color=(120, 140, 180))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        # Older 2023 asset path
        cand_meta = {
            "title": "David Raya in action for Arsenal",
            "url": "https://cdn.arsenal.com/uploads/2023/10/david-raya-action.jpg",
            "page_url": "https://arsenal.com/news/2023"
        }

        passed, reason, _ = SemanticVisualVerifier.inspect_candidate(raw_bytes, cand_meta, spec)
        self.assertFalse(passed, "Historical 2023 asset must be rejected when EXACT_EVENT_PHOTO required for 2026")
        self.assertIn("Temporal mismatch", reason)

    def test_33_filename_subject_conflict(self):
        """Test 33: Validates rejection when URL filename contains PaulBarber but intended subject is Tony Bloom."""
        import io
        from PIL import Image
        from stages.semantic_image_procurement import SceneVisualSpec, SemanticVisualVerifier

        spec = SceneVisualSpec(
            scene_id="s03",
            role="recruitment_method",
            intended_subject="Tony Bloom",
            club="Brighton & Hove Albion",
            event_context="Brighton Chairman Tony Bloom executive feature",
            relevant_date="2026-11-21",
            required_visual_elements=["tony_bloom", "chairman"],
            banned_visual_elements=["paul_barber"],
            allowed_asset_types=["CLUB_CONTEXT_PHOTO"],
            search_queries=["Tony Bloom chairman Brighton"]
        )

        img = Image.new("RGB", (600, 600), color=(200, 200, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        cand_meta = {
            "title": "Brighton Executive Leadership",
            "url": "https://brightonandhovealbion.com/media/PaulBarber2_1_.jpg",
            "page_url": "https://brightonandhovealbion.com"
        }

        passed, reason, _ = SemanticVisualVerifier.inspect_candidate(raw_bytes, cand_meta, spec)
        self.assertFalse(passed, "Paul Barber filename must be rejected when Tony Bloom is intended subject")
        self.assertIn("PaulBarber vs Tony Bloom", reason)

    def test_34_no_fabricated_face_center_on_upper_body(self):
        """Test 34: Validates that UPPER_BODY and non-face detections strictly return face_center = None."""
        import numpy as np
        from stages.semantic_image_procurement import EnhancedSubjectDetector

        detector = EnhancedSubjectDetector()
        # Synthetic non-face image
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        img[150:450, 250:550] = (100, 150, 200)

        det = detector.detect(img)
        if not det["is_face"]:
            self.assertIsNone(det["face_center"], "Non-face detections must NEVER fabricate face_center coordinates")

    def test_35_effective_crop_resolution_rejection(self):
        """Test 35: Validates rejection when native crop resolution is too low or scale factor > 2.5x."""
        import numpy as np
        from stages.semantic_image_procurement import SceneVisualSpec, EffectiveResolutionCropValidator

        spec = SceneVisualSpec(
            scene_id="s01",
            role="scene",
            intended_subject="Player",
            club="Club",
            event_context="Context",
            relevant_date="2026-11-22",
            required_visual_elements=["player"],
            banned_visual_elements=[],
            allowed_asset_types=["PLAYER_CONTEXTUAL_PHOTO"],
            search_queries=[]
        )

        validator = EffectiveResolutionCropValidator(target_w=1080, target_h=1920)
        # Undersized image (350x200) requiring massive upscale
        low_res_img = np.zeros((200, 350, 3), dtype=np.uint8)
        low_res_img[20:180, 50:300] = (180, 180, 180)

        passed, crop_bgr, meta = validator.crop_and_validate(low_res_img, spec)
        self.assertFalse(passed, "Low resolution image requiring excessive upscale must be rejected")
        self.assertEqual(meta["decision"], "REJECTED")

    def test_36_generic_stadium_rejected_for_player_incident(self):
        """Test 36: Validates rejection of empty architectural stadium when player/walkout is required."""
        import io
        from PIL import Image
        from stages.semantic_image_procurement import SceneVisualSpec, SemanticVisualVerifier

        spec = SceneVisualSpec(
            scene_id="s01",
            role="personal_decision",
            intended_subject="Manchester United Players Tunnel Walkout",
            club="Manchester United",
            event_context="Players walking out of tunnel",
            relevant_date="2026-11-22",
            required_visual_elements=["tunnel", "walkout", "players"],
            banned_visual_elements=["empty_stands"],
            allowed_asset_types=["CLUB_CONTEXT_PHOTO"],
            search_queries=["Old Trafford tunnel"]
        )

        # Empty stadium simulation (green pitch, grey stands, no people/skin tone)
        img = Image.new("RGB", (800, 600), color=(50, 120, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        cand_meta = {
            "title": "Old Trafford Stadium Empty Blueprint",
            "url": "https://architecture.com/images/old-trafford-empty.jpg",
            "page_url": "https://architecture.com"
        }

        passed, reason, _ = SemanticVisualVerifier.inspect_candidate(raw_bytes, cand_meta, spec)
        self.assertFalse(passed, "Empty architectural stadium must be rejected when players/walkout are required")
        self.assertIn("Empty architectural stadium", reason)

    def test_37_rights_status_unverified(self):
        """Test 37: Validates that watermark-free web images are marked RIGHTS_UNVERIFIED / EDITORIAL_USE_ONLY, never RIGHTS_CLEARED."""
        from stages.semantic_image_procurement import evaluate_rights_status

        # Arbitrary web blog crawl
        status_web = evaluate_rights_status({"url": "https://randomblog.com/photo.jpg", "page_url": "https://randomblog.com"})
        self.assertEqual(status_web, "RIGHTS_UNVERIFIED")

        # Wikipedia / Wikimedia
        status_wiki = evaluate_rights_status({"url": "https://upload.wikimedia.org/wikipedia/commons/1/1a/photo.jpg", "page_url": "https://en.wikipedia.org"})
        self.assertEqual(status_wiki, "PUBLIC_DOMAIN")

        # Editorial news publisher
        status_news = evaluate_rights_status({"url": "https://theguardian.com/media/pic.jpg", "page_url": "https://theguardian.com/football"})
        self.assertEqual(status_news, "EDITORIAL_USE_ONLY")

        # Ensure absence of watermark never falsely returns RIGHTS_CLEARED
        self.assertNotEqual(status_web, "RIGHTS_CLEARED")
        self.assertNotEqual(status_news, "RIGHTS_CLEARED")

    def test_38_semantic_gatekeeper_overrides_technical_score(self):
        """Test 38: Validates that high visual quality cannot pass an asset if semantic verification fails."""
        import io
        from PIL import Image
        from stages.semantic_image_procurement import SceneVisualSpec, SemanticVisualVerifier

        spec = SceneVisualSpec(
            scene_id="s03",
            role="recruitment_method",
            intended_subject="Tony Bloom",
            club="Brighton & Hove Albion",
            event_context="Tony Bloom executive feature",
            relevant_date="2026-11-21",
            required_visual_elements=["tony_bloom", "chairman"],
            banned_visual_elements=["orlando_bloom"],
            allowed_asset_types=["CLUB_CONTEXT_PHOTO"],
            search_queries=["Tony Bloom chairman"],
            disqualified_entities=["orlando bloom", "orlando"]
        )

        # High resolution 4K image (3840x2160)
        img = Image.new("RGB", (3840, 2160), color=(180, 180, 180))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        raw_bytes = buf.getvalue()

        cand_meta = {
            "title": "Actor Orlando Bloom Attends Film Premiere",
            "url": "https://cinema.com/images/orlando_bloom_4k.jpg",
            "page_url": "https://cinema.com/news"
        }

        passed, reason, _ = SemanticVisualVerifier.inspect_candidate(raw_bytes, cand_meta, spec)
        self.assertFalse(passed, "4K image depicting disqualified entity Orlando Bloom must be strictly rejected")
        self.assertIn("disqualified entity", reason)

    def test_39_action_crop_rejection_when_contest_exceeds_9_16(self):
        """Test 39: ActionAwareCropper rejects when match contest width exceeds 9:16 vertical crop capacity."""
        import numpy as np
        from stages.action_aware_cropper import ActionAwareCropper
        from stages.semantic_image_procurement import SceneVisualSpec

        cropper = ActionAwareCropper(target_w=1080, target_h=1920)
        spec = SceneVisualSpec(
            scene_id="s01", role="match_incident", intended_subject="Midfield Contest",
            club="Brighton", event_context="Contest at Etihad", relevant_date="2026-10-31",
            required_visual_elements=["tackle"], banned_visual_elements=[],
            allowed_asset_types=["EXACT_EVENT_PHOTO"], search_queries=[]
        )

        # Landscape image 1920x1080 where two players contest across a wide span (750px > 607px max vertical width)
        img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        import cv2
        cv2.rectangle(img, (500, 300), (650, 700), (255, 255, 255), -1)
        cv2.rectangle(img, (1100, 300), (1250, 700), (255, 255, 255), -1)
        wide_contest = (500, 300, 750, 400)
        passed, crop, audit = cropper.crop_candidate(img, strategy="match_action", spec=spec, contest_box=wide_contest)
        self.assertFalse(passed, "Wide contest exceeding 9:16 vertical capacity must be rejected")
        self.assertIn("exceeds 9:16 vertical crop capacity", audit["reason"])

    def test_40_bruno_s03_reclassified_as_archival_contextual_portrait(self):
        """Test 40: Bruno Fernandes Portugal 2018 image must be reclassified from press-conference to archival portrait."""
        import json
        from pathlib import Path

        manifest_path = Path(__file__).resolve().parent.parent / "evidence" / "v6_4_2_scene_image_manifest.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        bruno_story = [s for s in manifest if s["story_id"] == "v6_4_2_story_1_bruno"][0]
        s03 = [sc for sc in bruno_story["scenes"] if sc["scene_id"] == "s03"][0]
        self.assertEqual(s03["asset_classification"], "ARCHIVAL_PHOTO")
        self.assertIn("Archival", s03["assessed_subject"])
        self.assertEqual(s03["overall_status"], "PROVISIONAL_REVIEW")

    def test_41_bruno_s04_labelled_as_archival_manager_portrait(self):
        """Test 41: Mauricio Pochettino November 2023 image is strictly labelled as archival, not current arrival footage."""
        import json
        from pathlib import Path

        manifest_path = Path(__file__).resolve().parent.parent / "evidence" / "v6_4_2_scene_image_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        bruno_story = [s for s in manifest if s["story_id"] == "v6_4_2_story_1_bruno"][0]
        s04 = [sc for sc in bruno_story["scenes"] if sc["scene_id"] == "s04"][0]
        self.assertEqual(s04["asset_classification"], "ARCHIVAL_PHOTO")
        self.assertIn("Archival Manager Portrait", s04["assessed_subject"])
        self.assertIn("Archival footage", s04["rejection_or_limitation_note"])

    def test_42_raya_s01_rejected_due_to_action_loss_in_crop(self):
        """Test 42: Raya S01 must be rejected as an injury incident illustration when vertical crop loses the collision."""
        import json
        from pathlib import Path

        manifest_path = Path(__file__).resolve().parent.parent / "evidence" / "v6_4_2_scene_image_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        raya_story = [s for s in manifest if s["story_id"] == "v6_4_2_story_2_raya"][0]
        s01 = [sc for sc in raya_story["scenes"] if sc["scene_id"] == "s01"][0]
        self.assertEqual(s01["overall_status"], "REJECTED_GAP")
        self.assertEqual(s01["gates"]["composition"], "FAIL")
        self.assertIn("vertical crop loses", s01["rejection_or_limitation_note"].lower())

    def test_43_brighton_s04_hurzeler_identity_verification_and_ayari_rejection(self):
        """Test 43: AyariBrighton03032026.jpeg is rejected for Fabian Hürzeler and replaced with verified Fabian Hürzeler portrait."""
        import json
        from pathlib import Path

        manifest_path = Path(__file__).resolve().parent.parent / "evidence" / "v6_4_2_scene_image_manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        brighton_story = [s for s in manifest if s["story_id"] == "v6_4_2_story_3_brighton"][0]
        s04 = [sc for sc in brighton_story["scenes"] if sc["scene_id"] == "s04"][0]
        self.assertNotIn("AyariBrighton", s04["provenance"]["url"])
        self.assertIn("Fabian_H%C3%BCrzeler", s04["provenance"]["url"])
        self.assertEqual(s04["overall_status"], "APPROVED")

    def test_44_rights_separation_and_vlm_reporting_transparency(self):
        """Test 44: EDITORIAL_USE_ONLY is strictly separated from commercial clearance and unverified assets."""
        from stages.semantic_image_procurement import evaluate_rights_status

        # Web crawl without licence
        status_web = evaluate_rights_status({"url": "https://unlicensed-blog.com/photo.jpg", "page_url": "https://unlicensed-blog.com"})
        self.assertEqual(status_web, "RIGHTS_UNVERIFIED")

        # News publisher
        status_news = evaluate_rights_status({"url": "https://theguardian.com/img.jpg", "page_url": "https://theguardian.com/football"})
        self.assertEqual(status_news, "EDITORIAL_USE_ONLY")
        self.assertNotEqual(status_news, "LICENSED_FOR_COMMERCIAL_REUSE")



if __name__ == "__main__":
    unittest.main(verbosity=2)
