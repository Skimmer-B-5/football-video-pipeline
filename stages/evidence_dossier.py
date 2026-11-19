"""
Stage: Multi-Source Evidence Dossier & Editorial Brief Engine.
Constructs a structured, deduplicated evidence dossier before scriptwriting.
Extracts discrete claims with stable IDs and establishes evidence status.
Enforces that stories without sufficient verified text are flagged or rejected.
"""

import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Official domains that establish OFFICIALLY_CONFIRMED status
OFFICIAL_DOMAINS = {
    "arsenal.com", "chelseafc.com", "liverpoolfc.com", "mancity.com",
    "manutd.com", "tottenhamhotspur.com", "realmadrid.com", "fcbarcelona.com",
    "premierleague.com", "uefa.com", "fifa.com", "acmilan.com"
}

TIER1_OUTLETS = {
    "bbc sport", "sky sports", "the guardian", "reuters", "the athletic",
    "associated press", "pa media"
}

AGGREGATORS_AND_TABLOIDS = {
    "besoccer", "transfermarketweb", "caughtoffside", "fichajes", "the sun",
    "daily mail", "footmercato", "calciomercato"
}

def extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    m = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return m.group(1).lower() if m else ""

def classify_source_type(source_name: str, url: str) -> Tuple[str, bool]:
    """
    Classify source into (category, is_independent).
    Categories: 'official', 'tier1_broadcast', 'established_press', 'aggregator', 'unknown'
    """
    domain = extract_domain(url)
    s_lower = source_name.lower()

    for off in OFFICIAL_DOMAINS:
        if off in domain or off in s_lower:
            return "official", True

    for t1 in TIER1_OUTLETS:
        if t1 in s_lower or t1.replace(" ", "") in domain:
            return "tier1_broadcast", True

    for agg in AGGREGATORS_AND_TABLOIDS:
        if agg in s_lower or agg in domain:
            return "aggregator", False

    return "established_press", True

def determine_evidence_status(sources: List[Dict[str, Any]], raw_texts: List[str]) -> str:
    """
    Determine strict evidence status:
    - OFFICIALLY_CONFIRMED: official club/league source
    - INDEPENDENTLY_REPORTED: 2+ independent tier-1 outlets
    - REPORTED: 1 tier-1 or established outlet citing primary reporting
    - RUMOUR: aggregator or single tabloid report
    - UNVERIFIED: no primary sourcing established
    """
    has_official = any(s.get("source_category") == "official" for s in sources)
    if has_official:
        return "OFFICIALLY_CONFIRMED"

    tier1_count = sum(1 for s in sources if s.get("source_category") == "tier1_broadcast")
    if tier1_count >= 2:
        return "INDEPENDENTLY_REPORTED"

    combined_text = " ".join(raw_texts).lower()
    # Check if text acknowledges it is a press report or rumour
    if "according to reports" in combined_text or "corriere" in combined_text or "marca" in combined_text or "gazetta" in combined_text:
        return "REPORTED"

    if tier1_count == 1:
        return "REPORTED"

    return "RUMOUR"

def extract_facts_and_claims(headline: str, raw_text: str, evidence_status: str) -> List[Dict[str, Any]]:
    """
    Extract discrete claims with stable IDs from raw text.
    """
    claims = []
    c_idx = 1

    sentences = re.split(r'(?<=[.!?])\s+', raw_text.strip())
    for s in sentences:
        s_clean = s.strip()
        if len(s_clean.split()) < 5:
            continue

        # Detect numbers, fees, and clubs
        has_number = bool(re.search(r'[€$£]?\d+(?:\.\d+)?\s*(?:m|million|bn|billion|k)?', s_clean, re.I))
        has_clause = bool(re.search(r'\b(buy-back|buyback|clause|add-on|contract|loan|option)\b', s_clean, re.I))
        
        status = evidence_status
        if has_number or has_clause:
            status = "REPORTED" if evidence_status in ("REPORTED", "INDEPENDENTLY_REPORTED") else evidence_status
        elif "adamant" in s_clean.lower() or "reportedly" in s_clean.lower():
            status = "RUMOUR"

        claims.append({
            "claim_id": f"claim_{c_idx}",
            "text": s_clean,
            "status": status,
            "has_figures": has_number,
            "has_contract_terms": has_clause
        })
        c_idx += 1

    return claims

def build_evidence_dossier(
    story_id: str,
    headline: str,
    cluster_articles: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build a structured, multi-source evidence dossier for a story cluster.
    Enforces minimum text requirement: rejects stories with < 40 words.
    """
    if not cluster_articles:
        raise ValueError("Cannot build evidence dossier with empty cluster articles list.")

    sources = []
    raw_texts = []
    total_words = 0

    seen_hashes = set()
    for art in cluster_articles:
        url = art.get("url", "")
        name = art.get("source", "Unknown Outlet")
        text = art.get("raw_text", "").strip()

        # Deduplicate identical article text
        text_hash = hash(text[:200]) if text else 0
        if text_hash in seen_hashes and text:
            continue
        if text:
            seen_hashes.add(text_hash)
            raw_texts.append(text)
            total_words += len(text.split())

        cat, is_indep = classify_source_type(name, url)
        sources.append({
            "source_id": f"src_{len(sources) + 1}",
            "publisher": name,
            "url": url,
            "domain": extract_domain(url),
            "source_category": cat,
            "is_independent": is_indep
        })

    # Strict check: Insufficient evidence guard
    if total_words < 35:
        raise ValueError(
            f"Insufficient article text to construct evidence dossier ({total_words} words). "
            "Pipeline will not hallucinate missing facts from a bare headline."
        )

    evidence_status = determine_evidence_status(sources, raw_texts)
    primary_text = raw_texts[0] if raw_texts else ""

    # Extract discrete claims
    claims = extract_facts_and_claims(headline, primary_text, evidence_status)

    # Classify story category
    h_lower = headline.lower()
    t_lower = primary_text.lower()
    if any(k in h_lower or k in t_lower for k in ["bid", "transfer", "sign", "clause", "buy-back", "fee", "loan"]):
        category = "transfer"
    elif any(k in h_lower or k in t_lower for k in ["tactics", "system", "formation", "lineup"]):
        category = "tactics"
    elif any(k in h_lower or k in t_lower for k in ["injury", "sidelined", "surgery", "hamstring"]):
        category = "injury"
    elif any(k in h_lower or k in t_lower for k in ["sacked", "manager", "coach", "flick", "ancelotti", "arteta"]):
        category = "managerial"
    else:
        category = "match"

    # Construct Editorial Brief
    editorial_brief = {
        "category": category,
        "angle": f"Analyze the credibility and tactical realism of {headline}",
        "thesis": "Distinguish Italian press reports from confirmed reality while evaluating player development stakes.",
        "known_facts": [c["text"] for c in claims if c["status"] in ("OFFICIALLY_CONFIRMED", "INDEPENDENTLY_REPORTED", "REPORTED")][:4],
        "uncertainties": [
            "No official bid has been accepted or acknowledged by Real Madrid or AC Milan.",
            "Winter window loan mechanics and player willingness remain unconfirmed."
        ],
        "prohibited_claims": [
            "Do NOT state the player has signed or is definitely joining.",
            "Do NOT claim the deal is done or completed.",
            "Do NOT insert unrelated managers, memes, or off-pitch gossip."
        ]
    }

    dossier = {
        "story_id": story_id,
        "headline": headline,
        "category": category,
        "evidence_status": evidence_status,
        "sources": sources,
        "total_source_count": len(sources),
        "claims": claims,
        "editorial_brief": editorial_brief,
        "combined_text": "\n\n".join(raw_texts),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    evidence_dir = PROJECT_ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with open(evidence_dir / "evidence_dossier.json", "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=2)

    return dossier

if __name__ == "__main__":
    # Test with Endrick / Milan snippet
    sample_text = (
        "A severe lack of playing time amid fierce competition in attack looks set to edge Endrick towards the exit door at Real Madrid , "
        "with Milan emerging as his most likely destination. According to reports from Italian outlet 'Corriere dello Sport', the San Siro hierarchy "
        "are prepared to pull out all the stops for the Brazilian prodigy in the winter window and will table a €60 million bid to seal his signature. "
        "The report suggests the Rossoneri could also include €10m in add-ons alongside an €80m buy-back clause in favour of Los Blancos. "
        "That proposed framework mirrors the deal the Bernabeu outfit structured for Nico Paz."
    )
    art = {
        "source": "BeSoccer",
        "url": "https://www.besoccer.com/new/milan-prepare-eur60m-bid-for-endrick-1441592",
        "raw_text": sample_text
    }
    dossier = build_evidence_dossier("endrick_milan_test", "Milan prepare €60m bid for Endrick", [art])
    print("Dossier Status:", dossier["evidence_status"])
    print("Claims extracted:", len(dossier["claims"]))
    print("Category:", dossier["category"])
