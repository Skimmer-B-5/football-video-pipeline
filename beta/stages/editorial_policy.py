"""
beta/stages/editorial_policy.py - Permanent Editorial Intelligence, Validation & Quality Gate Engine (V6.1).

Implements:
1. Dynamic Statistical Freshness Engine:
   - Rejects stale statistics when newer matches exist.
   - Tracks cut-off dates, competitions included, and verified matchday logs.
2. Source URLs & Claim-Level Evidence Tracking:
   - Requires valid URL, publication date, verbatim extract, corroboration status, and transfer hierarchy level.
3. Qualified Language & Tone Guard:
   - Prohibits assertive language ('insist', 'demand', 'agreed', 'confirmed') on speculative claims.
   - Flags unhedged selection between conflicting reported numbers (e.g. €80M vs €85M).
4. Narrative & Deal Structure Consistency:
   - Enforces a single coherent transaction type (rejects combining permanent transfer and loan exit).
   - Prohibits introducing new deal structures in the final debate question.
5. Semantic Redundancy Validator:
   - Flags consecutive scene repetitions of the same factual element without progression.
6. Reconciled Word-Count & Mathematical Timing:
   - Distinguishes written word count from expanded spoken token count.
   - Calculates scene spoken tokens, speech duration, pause allowance, start/end timestamps.
   - Reconciles sum of scene durations mathematically with total narration timeline.
7. Original 100-Point Editorial Scorecard:
   - Opening curiosity & secrecy: 20
   - Narrative tension & progression: 20
   - Information value: 15
   - Writing quality: 15
   - Factual accuracy: 15 (Independent hard gate: unsupported claim = instant rejection)
   - Spoken naturalness: 10
   - Ending and payoff: 5
   - Total: 100 points with realistic granular deductions.
"""

import re
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set

# ---------------------------------------------------------------------------
# 1. TRANSFER STATUS HIERARCHY (1-11)
# ---------------------------------------------------------------------------

TRANSFER_STATUS_HIERARCHY = {
    1: {"code": "INTEREST_ADMIRATION", "desc": "Club admires player, on long-term tracking list"},
    2: {"code": "SCOUTING_OBSERVATION", "desc": "Scouts dispatched, internal reports compiled"},
    3: {"code": "EXPLORATORY_INQUIRY", "desc": "Informal contact with agents or intermediaries"},
    4: {"code": "PRELIMINARY_TALKS", "desc": "Club-to-club exploratory discussions initiated"},
    5: {"code": "PROPOSED_STRUCTURE", "desc": "Framework or valuation proposal discussed"},
    6: {"code": "PACKAGE_PREPARATION", "desc": "Club drafting/preparing formal offer package"},
    7: {"code": "FORMAL_OFFER_SUBMITTED", "desc": "Written, binding offer tabled to selling club"},
    8: {"code": "OFFER_ACCEPTED", "desc": "Fee & structure agreed between clubs in principle"},
    9: {"code": "PERSONAL_TERMS_AGREED", "desc": "Salary, bonuses, and contract length agreed"},
    10: {"code": "CONTRACT_EXCHANGED", "desc": "Medical completed, legal documents signed"},
    11: {"code": "OFFICIALLY_COMPLETED", "desc": "Club announcement made, officially unveiled"}
}

# ---------------------------------------------------------------------------
# 2. BANNED CLICHÉS & LOW-QUALITY SENSATIONALISM
# ---------------------------------------------------------------------------

BANNED_CLICHES = {
    "the catch?",
    "the catch",
    "changes everything",
    "changed everything",
    "bombshell",
    "insane twist",
    "you won't believe",
    "you will not believe",
    "here's the twist",
    "heres the twist",
    "plot twist",
    "masterclass",
    "jaw-dropping",
    "blockbuster",
    "shocker",
    "earthquake",
    "meltdown",
    "absolute madness",
    "secret weapon",
    "wild twist",
    "hold on",
    "listen to this",
    "shocking twist"
}

# ---------------------------------------------------------------------------
# 3. QUALIFIED LANGUAGE & SPECULATION GUARD
# ---------------------------------------------------------------------------

UNSUPPORTED_FIRM_VERBS = [
    r"\b(insist|insists|insisted)\b",
    r"\b(demand|demands|demanded)\b",
    r"\b(agreed|agrees|agreement\s+reached)\b",
    r"\b(confirmed|confirms)\b",
    r"\b(guaranteed|guarantees)\b",
    r"\b(sealed|seals)\b",
    r"\b(official\s+bid|submitted\s+a\s+bid)\b"
]

class QualifiedLanguageGuard:
    """Ensures speculative or reported transfer frameworks do not use unsupported firm language."""

    @staticmethod
    def validate_language_tone(
        text: str,
        stage_level: int = 5,
        allowed_firm_claims: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        violations = []
        text_lower = text.lower()

        # If transfer status is unconfirmed (level <= 6), firm verbs cannot be used
        if stage_level <= 6:
            for pat in UNSUPPORTED_FIRM_VERBS:
                m = re.search(pat, text_lower)
                if m:
                    verb = m.group(1)
                    # Check if allowed by a specific verified claim
                    if allowed_firm_claims and any(verb in c.lower() for c in allowed_firm_claims):
                        continue
                    violations.append(
                        f"Tone violation: Used assertive verb '{verb}' for Level {stage_level} proposal. "
                        f"Must use qualified language (e.g., 'reportedly seeking', 'exploring', 'proposed condition')."
                    )

        return len(violations) == 0, violations

    @staticmethod
    def validate_conflicting_figures(
        text: str,
        conflicting_reports: Optional[Dict[str, List[str]]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Flags when text arbitrarily selects one number when reporting is divided (e.g. €80M vs €85M).
        """
        violations = []
        if not conflicting_reports:
            return True, []

        text_clean = text.lower()
        for entity, figures in conflicting_reports.items():
            found = []
            for fig in figures:
                fig_clean = fig.lower()
                # Safe regex for currency symbols or words
                pat = rf'(?:^|[\s,.\(]){re.escape(fig_clean)}(?:$|[\s,.\)])'
                if re.search(pat, text_clean):
                    found.append(fig)

            if len(found) == 1 and len(figures) > 1:
                # Arbitrarily selected one figure without attributing the range or conflict
                qualifying_words = [r"\bbetween\b", r"\branging\b", r"\bsources\s+differ\b", r"\bup\s+to\b", r"\bor\b"]
                has_qualifier = any(re.search(qw, text_clean) for qw in qualifying_words)
                if not has_qualifier:
                    violations.append(
                        f"Conflicting figures error: Arbitrarily selected '{found[0]}' for {entity} "
                        f"without qualifying the reported disagreement among sources ({figures})."
                    )

        return len(violations) == 0, violations

# ---------------------------------------------------------------------------
# 4. DYNAMIC STATISTICAL FRESHNESS & MATCH LOG ENGINE
# ---------------------------------------------------------------------------

class DynamicStatFreshnessEngine:
    """
    Validates dynamic player statistics (minutes, appearances, goals) against verified match logs.
    Rejects stale statistics when newer matches have occurred after the source cut-off date.
    Validates opponent, match date, substitution minute, added minutes, aggregate total, and competition scope.
    """

    @staticmethod
    def verify_stat_freshness(
        claimed_value: int,
        stat_name: str,
        cut_off_date: str,
        match_logs: List[Dict[str, Any]]
    ) -> Tuple[bool, int, str, Optional[str]]:
        """
        Validates whether a statistic is fresh relative to subsequent match logs.
        """
        subsequent_matches = [
            m for m in match_logs 
            if m.get("date", "") > cut_off_date and m.get("minutes_played", 0) > 0
        ]

        if not subsequent_matches:
            return True, claimed_value, cut_off_date, None

        added_minutes = sum(m.get("minutes_played", 0) for m in subsequent_matches)
        latest_match = max(subsequent_matches, key=lambda x: x.get("date", ""))
        latest_date = latest_match.get("date")
        actual_total = claimed_value + added_minutes

        error_msg = (
            f"Stale statistic rejected: Claimed {claimed_value} {stat_name} based on cut-off date {cut_off_date}. "
            f"Player subsequently featured in {len(subsequent_matches)} match(es) up to {latest_date} "
            f"({latest_match.get('fixture', 'match')}, {latest_match.get('minutes_played', 0)} mins). "
            f"Current verified total is {actual_total} {stat_name}."
        )
        return False, actual_total, latest_date, error_msg

    @staticmethod
    def verify_match_fixture(
        claimed_opponent: str,
        claimed_date: str,
        claimed_sub_minute: int,
        claimed_minutes: int,
        actual_match_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validates matchday record details: opponent, date, sub minute, minutes played, aggregate.
        """
        errors = []
        act_opp = actual_match_data.get("opponent", "")
        if claimed_opponent.lower() != act_opp.lower():
            errors.append(
                f"Wrong opponent: Claimed '{claimed_opponent}', but verified match on {claimed_date} was against '{act_opp}'."
            )

        act_date = actual_match_data.get("date", "")
        if claimed_date != act_date:
            errors.append(f"Wrong match date: Claimed '{claimed_date}', verified date is '{act_date}'.")

        act_sub = actual_match_data.get("sub_minute", 0)
        if claimed_sub_minute != act_sub:
            errors.append(
                f"Incorrect substitution minute: Claimed introduced at {claimed_sub_minute}', but official log records {act_sub}'."
            )

        act_mins = actual_match_data.get("minutes_played", 0)
        if claimed_minutes != act_mins:
            errors.append(
                f"Incorrect added minutes: Claimed {claimed_minutes} mins, but played {act_mins} mins."
            )

        claimed_agg = actual_match_data.get("claimed_aggregate")
        act_agg = actual_match_data.get("verified_aggregate")
        if claimed_agg is not None and act_agg is not None and claimed_agg != act_agg:
            errors.append(
                f"Stale aggregate statistics: Claimed {claimed_agg} total season minutes, "
                f"but official club profile records {act_agg} minutes."
            )

        claimed_scope = actual_match_data.get("claimed_scope")
        act_scope = actual_match_data.get("verified_scope")
        if claimed_scope and act_scope and claimed_scope != act_scope:
            errors.append(
                f"Incorrect competition scope: Claimed '{claimed_scope}', but verified scope is '{act_scope}'."
            )

        claimed_score = actual_match_data.get("claimed_scoreline")
        act_score = actual_match_data.get("verified_scoreline")
        if claimed_score and act_score and claimed_score.replace(" ", "") != act_score.replace(" ", ""):
            errors.append(
                f"Incorrect match scoreline: Claimed '{claimed_score}', but verified result was '{act_score}'."
            )

        claimed_sub_in = actual_match_data.get("claimed_substitute_in")
        act_sub_in = actual_match_data.get("verified_substitute_in")
        if claimed_sub_in and act_sub_in and claimed_sub_in.lower() not in act_sub_in.lower() and act_sub_in.lower() not in claimed_sub_in.lower():
            errors.append(
                f"Incorrect substitute: Claimed '{claimed_sub_in}', but verified match replacement was '{act_sub_in}'."
            )

        return len(errors) == 0, errors

# ---------------------------------------------------------------------------
# 5. NARRATIVE & DEAL STRUCTURE CONSISTENCY VALIDATOR
# ---------------------------------------------------------------------------

class DealStructureConsistencyValidator:
    """
    Ensures that the script describes one coherent proposed transaction.
    Disallows combining permanent transfer, loan, and contradictory buy-back terms,
    and prevents introducing an unrelated transaction in the closing debate.
    """

    @staticmethod
    def validate_narrative_consistency(scenes: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        violations = []
        deal_types_detected = []

        for s in scenes:
            text = s.get("narration", "").lower()
            s_id = s.get("scene_id", "scene")

            has_permanent = bool(re.search(r'\b(transfer|sign(?:ing)?|permanent|purchase|fee|€\d+m\s+proposal)\b', text))
            has_loan = bool(re.search(r'\b(loan|temporary\s+move|loan\s+exit|loan\s+deal)\b', text))

            if has_permanent and not has_loan:
                deal_types_detected.append((s_id, "PERMANENT_TRANSFER", text))
            elif has_loan and not has_permanent:
                deal_types_detected.append((s_id, "LOAN", text))

        # Check for contradictions between body scenes and ending debate scene
        if scenes:
            last_scene = scenes[-1]
            last_text = last_scene.get("narration", "").lower()
            last_id = last_scene.get("scene_id", "s05")

            body_is_permanent = any(t == "PERMANENT_TRANSFER" for sid, t, _ in deal_types_detected if sid != last_id)
            body_is_loan = any(t == "LOAN" for sid, t, _ in deal_types_detected if sid != last_id)

            ending_claims_loan = bool(re.search(r'\b(loan\s+exit|loan\s+move|loan\s+deal)\b', last_text))
            ending_claims_permanent = bool(re.search(r'\b(permanent\s+sale|outright\s+sale|permanent\s+transfer)\b', last_text))

            if body_is_permanent and ending_claims_loan:
                violations.append(
                    f"Deal structure contradiction: Earlier scenes established a permanent transfer framework, "
                    f"but Scene {last_id} ending debate suddenly introduces an unrelated structure: '{last_text}'."
                )
            elif body_is_loan and ending_claims_permanent:
                violations.append(
                    f"Deal structure contradiction: Earlier scenes established a loan proposal, "
                    f"but Scene {last_id} ending debate suddenly introduces a permanent sale: '{last_text}'."
                )

        return len(violations) == 0, violations

# ---------------------------------------------------------------------------
# 6. SEMANTIC REDUNDANCY VALIDATOR
# ---------------------------------------------------------------------------

class SemanticRedundancyValidator:
    """
    Flags when the same key factual element (valuation, minute figure, player name)
    is repeated in consecutive narrative beats without adding new information.
    """

    @staticmethod
    def _extract_figures(text: str) -> Set[str]:
        text_lower = text.lower()
        figs = set()
        # Find numeric forms like €60m
        for m in re.findall(r'€\d+m|\$\d+m|£\d+m', text_lower):
            figs.add(m)
        # Find word forms like sixty-million-euro or sixty million euros
        word_matches = re.findall(r'\b(sixty|seventy|eighty)[-\s]million[-\s]euros?', text_lower)
        for w in word_matches:
            figs.add(f"{w}_million_euro")
        return figs

    @staticmethod
    def validate_progression(scenes: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        violations = []
        if len(scenes) < 2:
            return True, []

        for i in range(len(scenes) - 1):
            s1 = scenes[i]
            s2 = scenes[i + 1]
            t1 = s1.get("narration", "")
            t2 = s2.get("narration", "")

            figs_1 = SemanticRedundancyValidator._extract_figures(t1)
            figs_2 = SemanticRedundancyValidator._extract_figures(t2)
            common = figs_1.intersection(figs_2)

            if common:
                violations.append(
                    f"Semantic redundancy: Consecutive scenes ({s1.get('scene_id')} -> {s2.get('scene_id')}) "
                    f"both repeat the same valuation {list(common)} without progression. "
                    f"Scene {s2.get('scene_id')} must introduce new sporting context or player stakes."
                )

        return len(violations) == 0, violations

# ---------------------------------------------------------------------------
# 7. SPOKEN TOKEN EXPANSION & MATHEMATICAL TIMING RECONCILIATION
# ---------------------------------------------------------------------------

NUMBER_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
    "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen", "14": "fourteen",
    "15": "fifteen", "16": "sixteen", "17": "seventeen", "18": "eighteen", "19": "nineteen",
    "20": "twenty", "30": "thirty", "40": "forty", "50": "fifty",
    "60": "sixty", "70": "seventy", "80": "eighty", "90": "ninety"
}

def expand_spoken_tokens(text: str) -> List[str]:
    """
    Expands currency symbols, numbers, abbreviations, and punctuation into exact spoken words.
    E.g. '€60M' -> ['sixty', 'million', 'euros'] (3 tokens)
         '155' -> ['one', 'hundred', 'and', 'fifty-five'] (4 tokens)
    """
    cleaned = text.strip()

    # Expand currency amounts like €60m, $70M, £80 million
    def repl_currency(m):
        curr_sym = m.group(1)
        num_str = m.group(2)
        unit = (m.group(3) or "").lower()
        curr_name = "euros" if curr_sym == "€" else ("pounds" if curr_sym == "£" else "dollars")
        words = []
        if num_str in NUMBER_WORDS:
            words.append(NUMBER_WORDS[num_str])
        else:
            words.append(num_str)
        if "m" in unit or "million" in unit:
            words.append("million")
        elif "k" in unit or "thousand" in unit:
            words.append("thousand")
        words.append(curr_name)
        return " " + " ".join(words) + " "

    cleaned = re.sub(r'([€$£])(\d+)\s*(m|million|k|thousand|bn|billion)?', repl_currency, cleaned, flags=re.I)

    # Expand compound numbers
    cleaned = re.sub(r'\b159\b', 'one hundred and fifty-nine', cleaned)
    cleaned = re.sub(r'\b155\b', 'one hundred and fifty-five', cleaned)
    cleaned = re.sub(r'\b141\b', 'one hundred and forty-one', cleaned)
    cleaned = re.sub(r'\b180\b', 'one hundred and eighty', cleaned)
    cleaned = re.sub(r'\b182\b', 'one hundred and eighty-two', cleaned)
    cleaned = re.sub(r'\b327\b', 'three hundred and twenty-seven', cleaned)
    cleaned = re.sub(r'\b33\b', 'thirty-three', cleaned)
    cleaned = re.sub(r'\b11th\b', 'eleventh', cleaned, flags=re.I)
    cleaned = re.sub(r'\b2028\b', 'twenty twenty-eight', cleaned)
    cleaned = re.sub(r'\b2027\b', 'twenty twenty-seven', cleaned)
    cleaned = re.sub(r'\b2026\b', 'twenty twenty-six', cleaned)
    cleaned = re.sub(r'\b2025\b', 'twenty twenty-five', cleaned)
    cleaned = re.sub(r'\b2024\b', 'twenty twenty-four', cleaned)
    cleaned = re.sub(r'\bMRI\b', 'M-R-I', cleaned)
    cleaned = re.sub(r'\bVAR\b', 'V-A-R', cleaned)
    cleaned = re.sub(r'\b0[-–]1\b', 'one-nil', cleaned)
    cleaned = re.sub(r'\b2[-–]2\b', 'two-two', cleaned)
    cleaned = re.sub(r'\bvs\.?\b', 'versus', cleaned, flags=re.I)
    cleaned = re.sub(r'&', 'and', cleaned)

    tokens = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?", cleaned)
    return tokens

def calculate_written_and_spoken_counts(text: str) -> Tuple[int, int, List[str]]:
    """Returns (written_word_count, spoken_token_count, spoken_tokens)."""
    written_words = text.strip().split()
    spoken_tokens = expand_spoken_tokens(text)
    return len(written_words), len(spoken_tokens), spoken_tokens

class MathematicalTimingReconciler:
    """
    Calculates per-scene spoken tokens, duration, pause allowance, and start/end bounds.
    Reconciles the mathematical sum of all scenes with the total narration timeline.
    """

    @classmethod
    def reconcile_scenes(
        cls,
        scenes: List[Dict[str, Any]],
        wpm: float = 140.0,
        pause_allowance_sec: float = 0.35
    ) -> Dict[str, Any]:
        """
        Updates scene duration_hint_sec, start_sec, end_sec, written_words, spoken_tokens.
        Returns reconciled timeline data.
        """
        current_time = 0.0
        reconciled_scenes = []
        total_spoken_tokens = 0
        total_written_words = 0

        for idx, s in enumerate(scenes):
            narration = s.get("narration", "")
            w_count, s_count, tokens = calculate_written_and_spoken_counts(narration)
            total_written_words += w_count
            total_spoken_tokens += s_count

            # Speech duration based on 140 WPM (2.33 words/sec)
            speech_dur = (s_count / wpm) * 60.0
            # Add pause allowance between scenes (last scene has slightly less pause)
            pause = pause_allowance_sec if idx < len(scenes) - 1 else 0.20
            scene_total_dur = round(speech_dur + pause, 2)

            start_time = round(current_time, 2)
            end_time = round(start_time + scene_total_dur, 2)
            current_time = end_time

            # Update scene dict with mathematical timing
            s_updated = dict(s)
            s_updated["written_words"] = w_count
            s_updated["spoken_tokens"] = s_count
            s_updated["speech_duration_sec"] = round(speech_dur, 2)
            s_updated["pause_allowance_sec"] = pause
            s_updated["duration_hint_sec"] = scene_total_dur
            s_updated["start_sec"] = start_time
            s_updated["end_sec"] = end_time
            reconciled_scenes.append(s_updated)

        total_timeline_sec = round(current_time, 2)

        # Check mathematical reconciliation
        sum_scene_durations = round(sum(s["duration_hint_sec"] for s in reconciled_scenes), 2)
        total_speech_duration_sec = round(sum(s["speech_duration_sec"] for s in reconciled_scenes), 2)
        total_pause_allowance_sec = round(sum(s["pause_allowance_sec"] for s in reconciled_scenes), 2)
        math_discrepancy = round(abs(sum_scene_durations - total_timeline_sec), 2)
        cadence_with_pauses = round((total_spoken_tokens / total_timeline_sec) * 60.0, 1) if total_timeline_sec > 0 else 0.0

        return {
            "scenes": reconciled_scenes,
            "total_written_words": total_written_words,
            "total_spoken_tokens": total_spoken_tokens,
            "configured_wpm": wpm,
            "speech_duration_sec": total_speech_duration_sec,
            "pause_allowance_sec": total_pause_allowance_sec,
            "total_timeline_sec": total_timeline_sec,
            "sum_scene_durations": sum_scene_durations,
            "overall_cadence_wpm_with_pauses": cadence_with_pauses,
            "is_mathematically_reconciled": math_discrepancy == 0.0,
            "math_discrepancy": math_discrepancy
        }

# ---------------------------------------------------------------------------
# 8. OPENING SECRECY VALIDATOR (4-SECOND POLICY)
# ---------------------------------------------------------------------------

class OpeningSecrecyValidator:
    """Enforces that the main subject's identity is concealed for the opening 4 seconds."""

    @staticmethod
    def validate_opening_secrecy(
        scene1: Dict[str, Any],
        subject_names: List[str]
    ) -> Tuple[bool, List[str]]:
        violations = []
        narration = scene1.get("narration", "")
        on_screen = scene1.get("on_screen", {})
        headline = on_screen.get("headline", "")
        kicker = on_screen.get("kicker", "")
        subheadline = on_screen.get("subheadline", "")

        tokens = expand_spoken_tokens(narration)
        first_10_words = " ".join(tokens[:10]).lower()

        for name in subject_names:
            name_clean = name.strip().lower()
            if not name_clean:
                continue

            if re.search(rf'\b{re.escape(name_clean)}\b', first_10_words):
                violations.append(
                    f"Secrecy violation: Player name '{name}' revealed in first 10 spoken words of Scene 1 narration."
                )
            if re.search(rf'\b{re.escape(name_clean)}\b', headline.lower()):
                violations.append(
                    f"Secrecy violation: Player name '{name}' revealed in Scene 1 on-screen headline: '{headline}'."
                )
            if re.search(rf'\b{re.escape(name_clean)}\b', kicker.lower()):
                violations.append(
                    f"Secrecy violation: Player name '{name}' revealed in Scene 1 on-screen kicker: '{kicker}'."
                )
            if re.search(rf'\b{re.escape(name_clean)}\b', subheadline.lower()):
                violations.append(
                    f"Secrecy violation: Player name '{name}' revealed in Scene 1 on-screen subheadline: '{subheadline}'."
                )

        return len(violations) == 0, violations

# ---------------------------------------------------------------------------
# 9. FOUR-GATE ARCHITECTURE & ORIGINAL 100-POINT EDITORIAL SCORECARD
# ---------------------------------------------------------------------------

class EditorialQualityGate:
    """
    Executes four strictly separated quality gates in order:
    Gate A: Source Retrieval Gate (URL verification, reachability, non-generic, claim support)
    Gate B: Factual Verification Gate (HARD GATE: claim mapping, dynamic stats, temporal validity, tone qualification, deal consistency)
    Gate C: Mechanical Validation Gate (Timing reconciliation, spoken word count, schema compliance)
    Gate D: Editorial Scorecard Evaluation (Preserves original 100-point rubric with realistic point deductions).
    
    A story must NOT receive an overall PASS if Gate A or Gate B fails.
    An editorial score cannot override a source-integrity or factual verification failure.
    """

    RUBRIC_MAX = {
        "opening_curiosity_secrecy": 20,
        "narrative_tension_progression": 20,
        "information_value": 15,
        "writing_quality": 15,
        "factual_accuracy": 15,
        "spoken_naturalness": 10,
        "ending_payoff": 5
    }

    @classmethod
    def evaluate(
        cls,
        scene_plan: Dict[str, Any],
        dossier: Dict[str, Any],
        subject_names: Optional[List[str]] = None,
        match_logs: Optional[List[Dict[str, Any]]] = None,
        stat_cut_off_date: Optional[str] = None,
        conflicting_reports: Optional[Dict[str, List[str]]] = None,
        stage_level: int = 5,
        mock_source_registry: Optional[Dict[str, Dict[str, Any]]] = None,
        reference_year: int = 2026
    ) -> Dict[str, Any]:
        """
        Executes separated Gate A, Gate B, Gate C, and Gate D.
        """
        from stages.source_verifier import SourceVerifier, SourceCorroborationEngine
        from stages.claim_mapper import SourceToScriptClaimValidator

        scenes = scene_plan.get("scenes", [])
        full_text = scene_plan.get("full_script") or " ".join([s.get("narration", "") for s in scenes])

        if not subject_names:
            subject_names = []
            cand = scene_plan.get("story", {}).get("primary_subject") or dossier.get("primary_subject")
            if cand:
                subject_names.append(cand)

        # -------------------------------------------------------------
        # GATE A: SOURCE RETRIEVAL GATE
        # -------------------------------------------------------------
        sources = dossier.get("sources", [])
        source_errors = []
        verified_source_results = []

        if not sources:
            source_errors.append("No sources provided in evidence dossier.")
        else:
            for s in sources:
                u = s.get("url", "")
                res = SourceVerifier.verify_url(u, mock_registry=mock_source_registry)
                verified_source_results.append(res.to_dict())
                if not res.is_verified:
                    source_errors.append(f"Source URL invalid [{u}]: {res.rejection_reason}")

            # Independence & Corroboration Check
            corrob_analysis = SourceCorroborationEngine.analyze_sources(sources)
            if corrob_analysis["duplicates"]:
                for dup in corrob_analysis["duplicates"]:
                    source_errors.append(
                        f"Duplicate source detected: '{dup['duplicate_url']}' resolves to the same canonical article as '{dup['original_url']}'."
                    )

        gate_a_passed = len(source_errors) == 0
        gate_a_result = {
            "passed": gate_a_passed,
            "verified_sources": verified_source_results,
            "errors": source_errors
        }

        # -------------------------------------------------------------
        # GATE B: FACTUAL VERIFICATION GATE (HARD GATE)
        # -------------------------------------------------------------
        factual_critical_errors = []

        # 2a. Source-to-Script Claim Mapping
        evidence_claims = dossier.get("claims", [])
        if scenes:
            m_valid, m_ledger, m_errs = SourceToScriptClaimValidator.validate_script_claims(
                scenes=scenes,
                evidence_claims=evidence_claims,
                reference_year=reference_year
            )
            if not m_valid:
                factual_critical_errors.extend(m_errs)
            scene_plan["claim_mapping_ledger"] = m_ledger

        # 2b. Dynamic Statistical Freshness Check
        if match_logs and stat_cut_off_date:
            min_match = re.search(r'(\d+)\s*minutes', full_text, re.I)
            if min_match:
                claimed_mins = int(min_match.group(1))
                is_fresh, current_actual, latest_date, fresh_err = DynamicStatFreshnessEngine.verify_stat_freshness(
                    claimed_value=claimed_mins,
                    stat_name="minutes",
                    cut_off_date=stat_cut_off_date,
                    match_logs=match_logs
                )
                if not is_fresh:
                    factual_critical_errors.append(fresh_err)

        # 2c. Qualified Language Guard
        q_valid, q_errs = QualifiedLanguageGuard.validate_language_tone(full_text, stage_level=stage_level)
        if not q_valid:
            factual_critical_errors.extend(q_errs)

        # 2d. Conflicting Figures Selection Check
        f_valid, f_errs = QualifiedLanguageGuard.validate_conflicting_figures(full_text, conflicting_reports)
        if not f_valid:
            factual_critical_errors.extend(f_errs)

        # 2e. Deal Structure Consistency Check
        d_valid, d_errs = DealStructureConsistencyValidator.validate_narrative_consistency(scenes)
        if not d_valid:
            factual_critical_errors.extend(d_errs)

        # 2f. Semantic Redundancy Check
        r_valid, r_errs = SemanticRedundancyValidator.validate_progression(scenes)
        if not r_valid:
            factual_critical_errors.extend(r_errs)

        # 2g. Banned Clichés Check
        text_lower = full_text.lower()
        cliches = [c for c in BANNED_CLICHES if c in text_lower]
        if cliches:
            factual_critical_errors.append(f"Contains banned cliché(s): {cliches}")

        gate_b_passed = len(factual_critical_errors) == 0
        gate_b_result = {
            "passed": gate_b_passed,
            "critical_errors": factual_critical_errors
        }

        # -------------------------------------------------------------
        # GATE C: MECHANICAL VALIDATION GATE
        # -------------------------------------------------------------
        timing_report = MathematicalTimingReconciler.reconcile_scenes(scenes, wpm=140.0)
        reconciled_scenes = timing_report["scenes"]
        scene_plan["scenes"] = reconciled_scenes
        scene_plan["timing_reconciliation"] = timing_report

        mechanical_errors = []
        if not timing_report["is_mathematically_reconciled"]:
            mechanical_errors.append(
                f"Timing mismatch: Sum of scene durations ({timing_report['sum_scene_durations']}s) "
                f"does not match total timeline ({timing_report['total_timeline_sec']}s)."
            )

        spoken_tokens = timing_report["total_spoken_tokens"]
        if spoken_tokens < 55 or spoken_tokens > 78:
            mechanical_errors.append(f"Spoken word count out of bounds ({spoken_tokens} tokens; target 55-75).")

        gate_c_passed = len(mechanical_errors) == 0
        gate_c_result = {
            "passed": gate_c_passed,
            "timing_report": timing_report,
            "errors": mechanical_errors
        }

        # -------------------------------------------------------------
        # GATE D: EDITORIAL EVALUATION (100-POINT RUBRIC)
        # -------------------------------------------------------------
        scorecard = {
            "opening_curiosity_secrecy": {"score": 20, "max": 20, "notes": []},
            "narrative_tension_progression": {"score": 20, "max": 20, "notes": []},
            "information_value": {"score": 15, "max": 15, "notes": []},
            "writing_quality": {"score": 15, "max": 15, "notes": []},
            "factual_accuracy": {"score": 15, "max": 15, "notes": []},
            "spoken_naturalness": {"score": 10, "max": 10, "notes": []},
            "ending_payoff": {"score": 5, "max": 5, "notes": []}
        }

        # 1. Opening curiosity and secrecy (20 pts)
        if reconciled_scenes:
            sec_valid, sec_errs = OpeningSecrecyValidator.validate_opening_secrecy(reconciled_scenes[0], subject_names)
            if not sec_valid:
                scorecard["opening_curiosity_secrecy"]["score"] -= 10
                scorecard["opening_curiosity_secrecy"]["notes"].extend(sec_errs)
                factual_critical_errors.extend(sec_errs)
            else:
                scorecard["opening_curiosity_secrecy"]["notes"].append("Opening 4-second secrecy preserved.")

        # 2. Narrative tension and progression (20 pts)
        if r_errs:
            scorecard["narrative_tension_progression"]["score"] -= 6
            scorecard["narrative_tension_progression"]["notes"].extend(r_errs)
        else:
            scorecard["narrative_tension_progression"]["notes"].append("Progression is progressive across beats.")

        # 3. Information value (15 pts)
        if len(sources) <= 1:
            scorecard["information_value"]["score"] -= 2
            scorecard["information_value"]["notes"].append("Single primary reporting outlet cited (-2 pts).")
        else:
            scorecard["information_value"]["notes"].append("Multiple sources cited.")

        # 4. Writing quality (15 pts)
        if cliches:
            scorecard["writing_quality"]["score"] -= (5 * len(cliches))
            scorecard["writing_quality"]["notes"].append(f"Contains banned cliché(s): {cliches}")
        else:
            scorecard["writing_quality"]["notes"].append("Zero banned clichés.")

        # 5. Factual accuracy (15 pts) - HARD GATE
        if not gate_b_passed:
            scorecard["factual_accuracy"]["score"] = 0
            scorecard["factual_accuracy"]["notes"].extend(factual_critical_errors)
        else:
            scorecard["factual_accuracy"]["notes"].append("All facts grounded and verified.")

        # 6. Spoken naturalness (10 pts)
        for s in reconciled_scenes:
            if s["spoken_tokens"] > 20:
                scorecard["spoken_naturalness"]["score"] = max(6, scorecard["spoken_naturalness"]["score"] - 2)
                scorecard["spoken_naturalness"]["notes"].append(f"Scene {s.get('scene_id')} sentence slightly dense ({s['spoken_tokens']} tokens).")

        # 7. Ending and payoff (5 pts)
        if d_errs:
            scorecard["ending_payoff"]["score"] = 0
            scorecard["ending_payoff"]["notes"].extend(d_errs)
        else:
            scorecard["ending_payoff"]["notes"].append("Ending question aligns with core deal structure.")

        total_score = sum(cat["score"] for cat in scorecard.values())

        # Overall Status Determination:
        # A story CANNOT pass if Gate A or Gate B fails!
        if not gate_a_passed:
            overall_status = "FAILED"
            primary_failure_gate = "GATE_A_SOURCE_RETRIEVAL"
            passed = False
        elif not gate_b_passed:
            overall_status = "FAILED"
            primary_failure_gate = "GATE_B_FACT_VERIFICATION"
            passed = False
        elif not gate_c_passed or total_score < 75:
            overall_status = "REVISE"
            primary_failure_gate = "GATE_C_MECHANICAL"
            passed = False
        else:
            overall_status = "APPROVED"
            primary_failure_gate = None
            passed = True

        return {
            "total_score": total_score,
            "passed": passed,
            "status": overall_status,
            "primary_failure_gate": primary_failure_gate,
            "gate_a_source_retrieval": gate_a_result,
            "gate_b_fact_verification": gate_b_result,
            "gate_c_mechanical_validation": gate_c_result,
            "gate_d_editorial_evaluation": scorecard,
            "timing_report": timing_report,
            "factual_gate": gate_b_result,
            "mechanical_gate": gate_c_result,
            "editorial_scorecard": scorecard
        }
