"""
Automated Unit Tests: Script Grounding & Claim Checker.
Tests:
1. Rejection of prohibited off-pitch private life claims.
2. Rejection of hallucinated financial transfer fees.
3. Digit boundary check: ensures numbers like "60" do NOT match inside years like "1960" or timestamps.
4. Detection of invented / misattributed quotations.
5. Acceptance of valid, grounded scripts with accurate numbers and citations.
"""

import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.claim_checker import verify_script_claims

def test_negative_claim_detection():
    print("[TestClaimChecker] 1. Testing negative claim detection...")
    source_article_text = (
        "Chelsea have finalized the transfer of winger Pedro Neto from Wolverhampton Wanderers. "
        "The deal is valued at £54 million with add-ons. Neto agreed personal terms and completed his medical on Friday."
    )
    source_name = "BBC Sport"
    tier = "confirmed"

    # Hallucinated script with 3 deliberate violations
    bad_script = (
        "Chelsea have smashed their record by signing Pedro Neto for an unbelievable £150 million. "
        "According to BBC Sport, Neto told reporters: 'I always dreamed of playing in Siberia and making history.' "
        "He immediately celebrated at a nightclub party with his new girlfriend. "
        "This story is confirmed."
    )

    report = verify_script_claims(bad_script, source_article_text, source_name, tier)
    assert not report["is_valid"], "Script with deliberate false claims was improperly accepted!"
    assert any("150" in f for f in report["unsupported_claims"]), "Failed to flag invented £150m fee"
    assert any("private life" in f.lower() or "girlfriend" in f.lower() or "nightclub" in f.lower() for f in report["unsupported_claims"]), "Failed to flag private life claim"
    assert any("quotation" in f.lower() or "siberia" in f.lower() for f in report["unsupported_claims"]), "Failed to flag invented quotation"
    print("  ✅ Passed: All deliberate hallucinations detected and rejected.")

def test_digit_boundary_enforcement():
    print("[TestClaimChecker] 2. Testing digit boundary check (e.g. 60 vs 1960)...")
    source_with_year = "Real Madrid won the European Cup in 1960 after defeating Eintracht Frankfurt."
    
    # Script claims 60 million euros, but article only mentions the year 1960
    script_with_fee = "Real Madrid are offering €60 million to seal the transfer immediately."
    
    report = verify_script_claims(script_with_fee, source_with_year, "Marca", "rumour")
    assert not report["is_valid"], "Failed digit boundary test: 60 was falsely matched inside 1960!"
    assert any("60" in f for f in report["unsupported_claims"]), "Missing 60m unverified flag"
    print("  ✅ Passed: Digit boundary enforced. 60 inside 1960 is strictly rejected.")

def test_grounded_script_passes():
    print("[TestClaimChecker] 3. Testing grounded script verification...")
    source_text = (
        "Arsenal have agreed a £42 million deal with Bologna for defender Riccardo Calafiori. "
        "Personal terms are on a five-year contract until 2029."
    )
    good_script = (
        "Arsenal have made their defensive move! "
        "According to Sky Sports, a £42 million deal is agreed with Bologna for Riccardo Calafiori. "
        "He signs a five-year contract until 2029. "
        "Will he transform Arteta's defense? YES OR NO? Comment below!"
    )
    report = verify_script_claims(good_script, source_text, "Sky Sports", "confirmed")
    # Rule 1-3 should pass cleanly
    unsupported_factual = [u for u in report["unsupported_claims"] if not u.startswith("[Groq 120B Audit]")]
    assert len(unsupported_factual) == 0, f"Grounded claims unexpectedly flagged: {unsupported_factual}"
    print("  ✅ Passed: Grounded script passed all factual claim rules.")

if __name__ == "__main__":
    test_negative_claim_detection()
    test_digit_boundary_enforcement()
    test_grounded_script_passes()
    print("\n[TestClaimChecker] ALL CLAIM CHECKER TESTS PASSED SUCCESSFULLY! ✅")
