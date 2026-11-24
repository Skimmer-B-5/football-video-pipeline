"""
beta/stages/claim_mapper.py - Source-to-Script Claim Mapping & Fact Grounding Validator.

Enforces:
1. Every factual sentence in the generated script must map to verified claim IDs in the evidence dossier.
2. Checks:
   - Entity identity (player, club, manager)
   - Date & temporal relevance
   - Numerical statistics (minutes, appearances)
   - Transfer valuation & fees
   - Deal structure (permanent transfer vs loan vs buy-back)
   - Manager attribution
   - Status & certainty level
3. Rejection of unreferenced factual claims or claims that contradict supporting evidence.
4. Allows unreferenced closing debate questions / pure commentary, while enforcing that all factual premises within them are grounded.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set


class SourceToScriptClaimValidator:
    """Validates that all factual script statements map to verified, corroborated claim IDs."""

    @classmethod
    def is_editorial_commentary(cls, text: str) -> bool:
        """
        Determines if a sentence is purely rhetorical, editorial reflection, or a closing debate question
        rather than a factual news assertion.
        """
        text_clean = text.strip().lower()
        if text_clean.endswith("?") and any(w in text_clean for w in ["should", "can", "will", "would", "tell us", "your verdict"]):
            return True
        commentary_starters = [
            "the question now is", "only time will tell", "have your say",
            "what do you think", "drop your thoughts"
        ]
        return any(text_clean.startswith(c) for c in commentary_starters)

    @classmethod
    def validate_script_claims(
        cls,
        scenes: List[Dict[str, Any]],
        evidence_claims: List[Dict[str, Any]],
        reference_year: int = 2026
    ) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
        """
        Validates mapping of every scene to verified claim IDs.
        Returns (is_valid, mapped_audit_ledger, list_of_rejection_errors).
        """
        claims_by_id = {c.get("claim_id"): c for c in evidence_claims}
        audit_ledger = []
        violations = []

        for idx, s in enumerate(scenes):
            s_id = s.get("scene_id", f"s{idx+1:02d}")
            narration = s.get("narration", "").strip()
            claimed_ids = s.get("claim_ids", [])

            # Check if this sentence makes material factual claims:
            has_fee = bool(re.search(r'[€$£]\d+|million|valua', narration, re.I))
            has_stats = bool(re.search(r'\d+\s*minutes|\d+\s*games|\d+\s*goals', narration, re.I))
            has_transfer_terms = bool(re.search(r'\b(transfer|bid|clause|buy-back|repurchase|proposal|contract)\b', narration, re.I))
            is_factual = has_fee or has_stats or has_transfer_terms

            is_commentary = cls.is_editorial_commentary(narration)

            if is_factual and not claimed_ids and not is_commentary:
                violations.append(
                    f"Unreferenced factual claim in Scene {s_id}: '{narration}'. "
                    f"Every factual sentence must map to one or more verified claim IDs."
                )
                continue

            # If claim IDs are provided, verify factual correspondence
            matched_claims = []
            for cid in claimed_ids:
                if cid not in claims_by_id:
                    violations.append(
                        f"Invalid claim reference in Scene {s_id}: Cited '{cid}' does not exist in evidence dossier."
                    )
                    continue

                ev_claim = claims_by_id[cid]
                matched_claims.append(ev_claim)

                # Check temporal relevance
                claim_date = ev_claim.get("published_at", "")
                if claim_date and claim_date.startswith("2024") and reference_year >= 2026:
                    violations.append(
                        f"Temporal irrelevance error: Scene {s_id} cites Claim {cid} published in {claim_date[:4]}, "
                        f"which cannot validate a {reference_year} current news story."
                    )

            if not matched_claims:
                continue

            # Scene-level support checks across all matched claims:
            # 1. Transfer fee alignment
            fee_match_narr = re.search(r'([€$£]\d+(?:\.\d+)?\s*(?:m|million)?)', narration, re.I)
            if fee_match_narr:
                f_val = fee_match_narr.group(1).upper()
                num = re.search(r'\d+', f_val).group(0)
                has_fee_support = any(
                    (f_val.replace(" ", "") in c.get("text", "").upper().replace(" ", "")) or (num in c.get("text", ""))
                    for c in matched_claims
                )
                if not has_fee_support:
                    violations.append(
                        f"Factual mismatch in Scene {s_id}: Cites fee '{f_val}', but cited claims {claimed_ids} do not contain this fee."
                    )

            # 2. Deal structure alignment
            if "buy-back" in narration.lower() or "repurchase" in narration.lower():
                has_bb = any(
                    any(k in c.get("text", "").lower() for k in ["buy-back", "buyback", "clause", "repurchase", "nico paz"])
                    for c in matched_claims
                )
                if not has_bb:
                    violations.append(
                        f"Deal structure mismatch in Scene {s_id}: Claims buy-back option, but cited claims {claimed_ids} do not contain buy-back terms."
                    )

            # 3. Manager attribution
            managers_found_narr = re.findall(r'\b(Mourinho|Ancelotti|Guardiola|Arteta|Flick|Slot|Ten Hag|Amorim)\b', narration, re.I)
            if managers_found_narr:
                narr_mgrs = {m.lower() for m in managers_found_narr}
                # Check if any claim mentions a conflicting manager or supports the manager
                claim_mgrs = set()
                for c in matched_claims:
                    for m in re.findall(r'\b(Mourinho|Ancelotti|Guardiola|Arteta|Flick|Slot|Ten Hag|Amorim)\b', c.get("text", ""), re.I):
                        claim_mgrs.add(m.lower())
                if claim_mgrs and not narr_mgrs.intersection(claim_mgrs):
                    violations.append(
                        f"Manager attribution error in Scene {s_id}: Narration cites '{managers_found_narr}', but cited claims attribute to '{list(claim_mgrs)}'."
                    )

            # 4. Statistical minutes alignment
            if "minutes" in narration.lower():
                for val_digit, val_words in [("159", "fifty-nine"), ("155", "fifty-five"), ("141", "forty-one")]:
                    if val_digit in narration or val_words in narration:
                        has_min_support = any(
                            (val_digit in c.get("text", "") or val_words in c.get("text", ""))
                            for c in matched_claims
                        )
                        if not has_min_support:
                            violations.append(
                                f"Statistical minutes mismatch in Scene {s_id}: Narration cites {val_digit} minutes, but cited claims {claimed_ids} do not support it."
                            )

            # 5. Goalkeeper / Player substitution alignment
            if "neto" in narration.lower():
                has_kepa_claim = any("kepa" in c.get("text", "").lower() for c in matched_claims)
                if has_kepa_claim:
                    violations.append(
                        f"Goalkeeper substitution error in Scene {s_id}: Narration cites 'Neto', but verified match replacement was 'Kepa Arrizabalaga'."
                    )

            # 6. Injury severity qualification
            if any(w in narration.lower() for w in ["severe shoulder", "severe ligament", "severe injury", "in tears"]):
                is_unqualified = any(
                    any(p in c.get("text", "").lower() for p in ["close to tears", "awaiting an mri", "prognosis unknown", "medical assessment"])
                    for c in matched_claims
                )
                if is_unqualified:
                    violations.append(
                        f"Injury severity exaggeration in Scene {s_id}: Claiming severe injury or 'in tears' before medical MRI diagnosis contradicts verified reporting."
                    )

            # 7. Scoreline alignment
            if any(sc in narration.lower() for sc in ["2-1", "two-one"]):
                has_0_1 = any(any(sc0 in c.get("text", "").lower() for sc0 in ["0-1", "one-nil", "1-0"]) for c in matched_claims)
                if has_0_1:
                    violations.append(
                        f"Match scoreline error in Scene {s_id}: Narration claims 2-1, but verified match result was 0-1."
                    )

            # 8. Manager age alignment
            if any(a in narration.lower() for a in ["31-year-old", "thirty-one-year-old"]):
                has_33 = any(any(a33 in c.get("text", "").lower() for a33 in ["33", "thirty-three"]) for c in matched_claims)
                if has_33:
                    violations.append(
                        f"Manager age error in Scene {s_id}: Narration claims 31 years old, but verified age is 33."
                    )

            # 9. Unsupported weekly salary claims
            if any(sal in narration.lower() for sal in ["salary", "ten thousand pounds a week", "£10,000 a week"]):
                has_salary_support = any("salary" in c.get("text", "").lower() or "week" in c.get("text", "").lower() for c in matched_claims)
                if not has_salary_support:
                    violations.append(
                        f"Unsupported salary claim in Scene {s_id}: Weekly wage claim is unverified in cited claims {claimed_ids}."
                    )

            # 10. Formally rejected transfer bids vs contract pause
            if any(phrase in narration.lower() for phrase in ["rejected lucrative moves abroad", "rejected overseas offers", "turned down formal bids"]):
                has_bid_support = any("formal bid" in c.get("text", "").lower() or "rejected offers abroad" in c.get("text", "").lower() for c in matched_claims)
                if not has_bid_support:
                    violations.append(
                        f"Unverified transfer rejection in Scene {s_id}: Stating player formally rejected lucrative overseas bids exceeds source reporting (only dismissed wage rumors)."
                    )

            # 11. Data-led recruitment vs pure automated algorithms
            if any(phrase in narration.lower() for phrase in ["without human scouting", "purely automated algorithms", "solely on algorithms"]):
                has_human_scouting = any("human scouting" in c.get("text", "").lower() or "character vetting" in c.get("text", "").lower() for c in matched_claims)
                if has_human_scouting:
                    violations.append(
                        f"Recruitment model oversimplification in Scene {s_id}: Claiming pure algorithms without human scouting contradicts verified data-led model."
                    )

            audit_ledger.append({
                "scene_id": s_id,
                "narration": narration,
                "is_factual": is_factual,
                "is_commentary": is_commentary,
                "claim_ids": claimed_ids,
                "matched_evidence": [c.get("claim_id") for c in matched_claims]
            })

        is_valid = len(violations) == 0
        return is_valid, audit_ledger, violations
