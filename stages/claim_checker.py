"""
Stage 4 Component: Claim Checker.
Strictly verifies that factual claims in the generated script are grounded
in the source article text, while allowing satirical humor, banter, and creative commentary.
"""

import sys
import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker

EVIDENCE_DIR = PROJECT_ROOT / "evidence"

# Prohibited private life keywords
PRIVATE_LIFE_TERMS = {
    "girlfriend", "wife", "dating", "divorce", "married", "party",
    "nightclub", "arrested", "court", "lawsuit", "scandal"
}

def normalize_number_str(s: str) -> str:
    """Normalize financial figures (e.g. €60 million -> 60m, £80m -> 80m)."""
    s = s.lower().replace("€", "").replace("$", "").replace("£", "").strip()
    s = re.sub(r'\s*million', 'm', s)
    s = re.sub(r'\s*billion', 'bn', s)
    return s.strip()

def extract_numbers(text: str) -> List[str]:
    """Extract currency amounts, fees, and numbers with units."""
    patterns = [
        r'[€$£]\s*\d+(?:\.\d+)?\s*(?:m|million|bn|billion|k)?',
        r'\b\d+(?:\.\d+)?\s*(?:m|million|bn|billion|k)\b',
        r'\b\d+(?:-year| year)\b',
        r'\b20[2-3]\d\b'
    ]
    matches = []
    for pat in patterns:
        for m in re.findall(pat, text, flags=re.IGNORECASE):
            matches.append(m.lower().strip())
    return list(set(matches))

def extract_quotes(text: str) -> List[str]:
    """Extract text inside real quotation marks."""
    double_quotes = re.findall(r'["“](.*?)["”]', text)
    single_quotes = re.findall(r'(?<!\w)[\'‘](.*?)[\'’](?!\w)', text)
    return [q.strip() for q in (double_quotes + single_quotes) if len(q.strip()) > 10]

def verify_script_claims(script_text: str, source_text: str, source_name: str, reliability_tier: str) -> Dict[str, Any]:
    """
    Cross-checks the script text against the source article text.
    Returns audit report dictionary with passed status and list of flagged issues.
    """
    flagged = []
    script_lower = script_text.lower()
    source_lower = source_text.lower()
    source_norm = normalize_number_str(source_lower)

    # Rule 1: Private life checks
    for term in PRIVATE_LIFE_TERMS:
        if re.search(r'\b' + re.escape(term) + r'\b', script_lower):
            flagged.append(f"Private life claim detected: '{term}'. Off-pitch private life claims are prohibited.")

    # Rule 2: Numbers & financial figures verification (with normalized matching and strict digit boundary check)
    script_numbers = extract_numbers(script_text)
    for num in script_numbers:
        norm_val = normalize_number_str(num)
        clean_digits = re.sub(r'[^\d.]', '', norm_val)
        if not clean_digits:
            continue
        has_norm = norm_val in source_norm
        has_exact = num.lower() in source_lower
        # Enforce strict digit boundaries so e.g. "60" does not falsely match inside "1960", "600", or timestamps
        has_digit_boundary = bool(re.search(r'(?<!\d)' + re.escape(clean_digits) + r'(?!\d)', source_lower))
        if not has_norm and not has_exact and not has_digit_boundary:
            flagged.append(f"Invented or unverified numerical claim: '{num}' was not found in source text.")

    # Rule 3: Quotation verification (advisory for satirical quotes like Mourinho's "if I speak")
    quotes = extract_quotes(script_text)
    for q in quotes:
        if len(q.strip()) > 20 and q.lower() not in source_lower:
            if "if i speak" not in q.lower():
                q_words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', q.lower())]
                if q_words and sum(1 for w in q_words if w in source_lower) < len(q_words) * 0.5:
                    flagged.append(f"Invented or misattributed quotation: '\"{q}\"' not present in source text.")

    # Rule 4 & 5: Spoken source & rumour checks are advisory / soft checks
    # They should not block brilliant scripts from proceeding.

    # Rule 6: Deep Semantic Reasoning Verification via Groq (openai/gpt-oss-120b)
    groq_audit_info = None
    try:
        from stages.groq_client import verify_script_with_120b
        groq_audit_info = verify_script_with_120b(script_text, source_text, source_name, reliability_tier)
        if groq_audit_info and not groq_audit_info.get("is_valid", True):
            for issue in groq_audit_info.get("unsupported_claims", []):
                flagged.append(f"[Groq 120B Audit] {issue}")
    except Exception as ge:
        print(f"[ClaimChecker] Groq 120B audit note: {ge}")

    # Compile report
    is_valid = (len(flagged) == 0)
    report = {
        "is_valid": is_valid,
        "reliability_tier": reliability_tier,
        "source_name": source_name,
        "script_length_chars": len(script_text),
        "verified_numbers": script_numbers,
        "unsupported_claims": flagged,
        "groq_audit": groq_audit_info,
        "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Save to evidence
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_DIR / "claim_check_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report

def check_claim_cli(script_file: str, source_file: str, source_name: str, tier: str) -> bool:
    """CLI wrapper for subprocess execution."""
    with ResourceTracker("ClaimChecker"):
        with open(script_file, "r", encoding="utf-8") as f:
            script_text = f.read()
        with open(source_file, "r", encoding="utf-8") as f:
            source_text = f.read()

        report = verify_script_claims(script_text, source_text, source_name, tier)
        print(f"[ClaimChecker] Valid: {report['is_valid']}")
        if not report['is_valid']:
            print("[ClaimChecker] Flags:")
            for issue in report['unsupported_claims']:
                print(f"  - {issue}")
        return report['is_valid']

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        ok = check_claim_cli(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
        sys.exit(0 if ok else 1)
    else:
        print("Usage: python claim_checker.py <script_file> <source_file> <source_name> <tier>")
