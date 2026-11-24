"""
beta/stages/scraped_story_adapter.py
Converts a scraped news article (from BBC, Sky, Guardian, BeSoccer, TransferMarketWeb)
into a structured StoryDossier ready for the V7.1.6.7 1990s Broadcast Pipeline.
Uses high-precision LLM entity extraction with rule-based fallback.
"""

import re
import json
from typing import Dict, Any, List
try:
    from pipeline.neural_instructions import StoryDossier
except ModuleNotFoundError:
    from beta.pipeline.neural_instructions import StoryDossier

try:
    from stages.groq_client import call_groq_chat
except ModuleNotFoundError:
    from beta.stages.groq_client import call_groq_chat

try:
    from stages.fact_checker import FactChecker
except ModuleNotFoundError:
    from beta.stages.fact_checker import FactChecker

KNOWN_PLAYERS = [
    "Endrick", "Bellingham", "Mbappe", "Vinicius", "Rodri", "Haaland", "Yamal",
    "Bastoni", "Gyokeres", "Gyökeres", "Davies", "Salah", "Alexander-Arnold",
    "Osimhen", "Leao", "Kvaratskhelia", "Musiala", "Wirtz", "Mainoo", "Alonso",
    "Bruno Fernandes", "Palmer", "Saka", "Foden", "De Bruyne", "Kane", "Gavi", "Pedri",
    "Bassey", "Calvin Bassey", "Nathan Collins", "Collins", "Kim Min-jae", "Min-jae",
    "Safonov", "Araujo", "Ronald Araujo", "Sesko", "Amorim", "Pochettino"
]

TOP_CLUBS = [
    "Manchester United", "Man United", "Man Utd", "MUFC", "Manchester City", "Man City", "MCFC",
    "Real Madrid", "Barcelona", "Arsenal", "Chelsea", "Liverpool", "Tottenham", "Spurs",
    "Bayern Munich", "Bayern", "Borussia Dortmund", "Dortmund", "Paris Saint-Germain", "PSG",
    "Juventus", "Inter Milan", "Inter", "AC Milan", "Milan", "Atletico Madrid", "Sporting CP",
    "Sporting", "Napoli", "Roma", "Aston Villa", "Newcastle", "Fulham", "Brentford",
    "Brighton", "West Ham", "Everton", "Wolves", "Crystal Palace"
]

CANONICAL_CLUBS = {
    "man utd": "Manchester United",
    "man united": "Manchester United",
    "mufc": "Manchester United",
    "man city": "Manchester City",
    "mcfc": "Manchester City",
    "spurs": "Tottenham",
    "barca": "Barcelona",
    "real": "Real Madrid",
    "bayern": "Bayern Munich",
    "dortmund": "Borussia Dortmund",
    "psg": "Paris Saint-Germain",
    "inter": "Inter Milan",
    "milan": "AC Milan"
}

def canonicalize_club(name: str) -> str:
    if not name:
        return "European Rivals"
    return CANONICAL_CLUBS.get(name.lower().strip(), name.strip())

def extract_entities_llm(headline: str, raw_text: str = "") -> Dict[str, str]:
    """Uses LLM to accurately extract football entities, club roles, and fees."""
    prompt = f"""Extract the football entities from this breaking news story.
HEADLINE: {headline}
TEXT: {raw_text[:600]}

Return ONLY valid JSON with these exact keys:
{{
  "protagonist_name": "Full name of the player or manager at the center of the story",
  "current_club": "The club the player currently belongs to (e.g. Fulham)",
  "current_manager": "Manager of current club (e.g. Marco Silva)",
  "pursuing_club": "The club trying to sign/bid for him (e.g. Manchester United)",
  "reported_base_fee": "Reported fee or clause if mentioned, else 'undisclosed'",
  "reported_bonuses": "Add-ons or bonuses if mentioned, else 'performance incentives'",
  "complication": "Key complication, injury, contract standoff, or rival interest"
}}
"""
    try:
        raw = call_groq_chat(
            system_prompt="You are an elite football transfer desk data analyst. Output ONLY valid JSON.",
            user_prompt=prompt,
            temperature=0.1,
            timeout=10
        )
        if raw:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
    except Exception as e:
        print(f"[StoryAdapter] LLM entity extraction note: {e}")
    return {}

def scraped_story_to_dossier(story: Dict[str, Any]) -> StoryDossier:
    """Extracts entities and facts from a scraped news story into a StoryDossier."""
    headline = story.get("headline", "Breaking Transfer Report")
    raw_text = story.get("raw_text") or headline
    source = story.get("source") or "Transfer Desk"

    # Try LLM extraction first
    llm_data = extract_entities_llm(headline, raw_text)
    if llm_data and llm_data.get("protagonist_name"):
        protagonist = llm_data["protagonist_name"]
        curr_club = canonicalize_club(llm_data.get("current_club"))
        purs_club = canonicalize_club(llm_data.get("pursuing_club"))
        manager = llm_data.get("current_manager") or "The Manager"
        base_fee = llm_data.get("reported_base_fee") or "an undisclosed fee"
        bonuses = llm_data.get("reported_bonuses") or "performance incentives"
        complication = llm_data.get("complication") or "contractual standoff and rival interest"

        # Prevent curr_club and purs_club from being identical if suitor is unknown
        if curr_club == purs_club:
            purs_club = "European Rivals"

        clean_id = re.sub(r'[^a-zA-Z0-9]+', '_', protagonist.lower()) + "_" + re.sub(r'[^a-zA-Z0-9]+', '_', curr_club.lower()[:8])
        clean_id = clean_id.strip('_')[:32]

        dossier = StoryDossier(
            story_id=clean_id,
            protagonist_name=protagonist,
            current_club=curr_club,
            current_manager=manager,
            pursuing_club=purs_club,
            reported_base_fee=base_fee,
            reported_bonuses=bonuses,
            reported_buyback="terms unresolved",
            complication=complication,
            reporting_sources=[source],
            headline_kicker="● BREAKING TRANSFER REPORT",
            main_headline=headline.upper(),
            ticker_text=f"{source.upper()}: {headline.upper()} ✦ 1990s TV BROADCAST DESK ✦"
        )
        return FactChecker.audit_and_enrich_dossier(dossier)

    # Fallback to rule-based parser
    detected_clubs = []
    for c in TOP_CLUBS:
        if re.search(r'\b' + re.escape(c) + r'\b', headline, re.IGNORECASE):
            canonical = canonicalize_club(c)
            if canonical not in detected_clubs:
                detected_clubs.append(canonical)

    protagonist = None
    for p in KNOWN_PLAYERS:
        if re.search(r'\b' + re.escape(p) + r'\b', headline, re.IGNORECASE):
            protagonist = p
            break

    if not protagonist:
        role_m = re.search(r'\b(?:defender|striker|winger|midfielder|star|forward|prodigy|coach|manager)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', headline)
        if role_m and role_m.group(1) not in TOP_CLUBS:
            protagonist = role_m.group(1)

    if not protagonist:
        protagonist = headline.split()[0].strip('":,.') if headline.split() else "The Star"

    current_club = detected_clubs[0] if len(detected_clubs) > 0 else "His Current Club"
    pursuing_club = detected_clubs[1] if len(detected_clubs) > 1 else ("Manchester United" if "Man Utd" in headline or "Man United" in headline else "Top European Suitors")

    clean_id = re.sub(r'[^a-zA-Z0-9]+', '_', protagonist.lower()) + "_" + re.sub(r'[^a-zA-Z0-9]+', '_', current_club.lower()[:8])
    clean_id = clean_id.strip('_')[:32]

    dossier = StoryDossier(
        story_id=clean_id,
        protagonist_name=protagonist,
        current_club=current_club,
        current_manager="The Manager",
        pursuing_club=pursuing_club,
        reported_base_fee="an undisclosed fee",
        reported_bonuses="performance incentives",
        reported_buyback="not agreed",
        complication="contractual complications and rival pressure",
        reporting_sources=[source],
        headline_kicker="● BREAKING TRANSFER REPORT",
        main_headline=headline.upper(),
        ticker_text=f"{source.upper()}: {headline.upper()} ✦ 1990s TV BROADCAST DESK ✦"
    )
    return FactChecker.audit_and_enrich_dossier(dossier)
