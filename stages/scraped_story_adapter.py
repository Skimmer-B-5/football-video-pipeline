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
    from pipeline.neural_instructions import StoryDossier

try:
    from stages.groq_client import call_groq_chat
except ModuleNotFoundError:
    from stages.groq_client import call_groq_chat

try:
    from stages.fact_checker import FactChecker
except ModuleNotFoundError:
    from stages.fact_checker import FactChecker

try:
    from stages.reddit_harvester import harvest_reddit_outrage
except ModuleNotFoundError:
    from stages.reddit_harvester import harvest_reddit_outrage

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
    """Uses LLM to accurately extract football entities, story category, club roles, and fees."""
    prompt = f"""Extract the football entities from this breaking news story.
HEADLINE: {headline}
ARTICLE TEXT:
{raw_text[:2500]}

Return ONLY valid JSON with these exact keys:
{{
  "protagonist_name": "Full name of the player or manager at the center of the story",
  "current_club": "The club the player/manager currently belongs to (e.g. Fulham)",
  "current_manager": "Manager of current club (e.g. Marco Silva)",
  "pursuing_club": "The club trying to sign/bid, or main rival club in context (e.g. Manchester United)",
  "story_category": "transfer_rumour | confirmed_deal | managerial_change | contract_negotiation | injury_crisis | tactical_drama",
  "reported_base_fee": "Exact reported fee, clause, or contract value if mentioned, else 'undisclosed'",
  "reported_bonuses": "Add-ons, contract length, or key terms if mentioned, else 'performance incentives'",
  "complication": "Concrete factual complication, board stance, injury, or rival interest"
}}
"""
    try:
        raw = call_groq_chat(
            system_prompt="You are an elite football desk analyst. Extract ONLY grounded entities and figures. Output ONLY valid JSON.",
            user_prompt=prompt,
            temperature=0.1,
            timeout=12
        )
        if raw:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
    except Exception as e:
        print(f"[StoryAdapter] LLM entity extraction note: {e}")
    return {}

def _finalize_dossier(dossier: StoryDossier, headline: str, protagonist: str) -> StoryDossier:
    """Enriches dossier with verified Reddit fan sentiment and canonical club/manager facts."""
    try:
        dossier.fan_reactions = harvest_reddit_outrage(
            headline=headline,
            club_or_player=protagonist,
            max_quotes=4
        )
    except Exception as e:
        print(f"[Adapter] Reddit harvest skipped: {e}")
        dossier.fan_reactions = []
    return FactChecker.audit_and_enrich_dossier(dossier)


def scraped_story_to_dossier(story: Dict[str, Any]) -> StoryDossier:
    """Extracts entities, full article body, hero images, and facts into a StoryDossier."""
    headline = story.get("headline", "Breaking Football Report")
    raw_text = story.get("raw_text") or story.get("article_text") or headline
    source = story.get("source") or "Football Desk"
    story_url = story.get("url") or ""
    hero_img = story.get("hero_image_url") or story.get("image_url")
    cand_imgs = list(story.get("candidate_images") or ([] if not hero_img else [hero_img]))
    art_urls = list(story.get("article_urls") or ([story_url] if story_url else []))

    # Hydrate sparse text/direct URLs automatically via upgraded url_scraper
    if story_url and ("news.google.com/rss/articles/" not in story_url) and (len(raw_text) < 450 or not hero_img or headline == "Direct Article Report"):
        try:
            try:
                from stages.url_scraper import scrape_article_from_url
            except ModuleNotFoundError:
                from stages.url_scraper import scrape_article_from_url
            scraped = scrape_article_from_url(story_url, timeout=8)
            if scraped.get("title") and headline in ("Direct Article Report", "Breaking Football Report"):
                headline = scraped["title"]
            if scraped.get("source") and source in ("Web Article", "Football Desk"):
                source = scraped["source"]
            if len(scraped.get("raw_text") or "") > len(raw_text):
                raw_text = scraped["raw_text"]
            if not hero_img and scraped.get("image_url"):
                hero_img = scraped["image_url"]
            for ci in (scraped.get("candidate_images") or []):
                if ci not in cand_imgs:
                    cand_imgs.append(ci)
        except Exception as e:
            print(f"[Adapter] Article hydration note for '{story_url}': {e}")

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
        category = llm_data.get("story_category") or story.get("category") or "transfer_rumour"

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
            headline_kicker="TRANSFER WATCH",
            main_headline=headline.upper(),
            ticker_text=f"{source.upper()}: {headline.upper()} ✦ 1990s TV BROADCAST DESK ✦",
            raw_article_text=raw_text[:4000],
            story_category=category,
            hero_image_url=hero_img,
            candidate_images=cand_imgs[:10],
            article_urls=art_urls[:5],
        )
        return _finalize_dossier(dossier, headline, protagonist)

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
        headline_kicker="TRANSFER WATCH",
        main_headline=headline.upper(),
        ticker_text=f"{source.upper()}: {headline.upper()} ✦ 1990s TV BROADCAST DESK ✦",
        raw_article_text=raw_text[:4000],
        story_category=story.get("category") or "transfer_rumour",
        hero_image_url=hero_img,
        candidate_images=cand_imgs[:10],
        article_urls=art_urls[:5],
    )
    return _finalize_dossier(dossier, headline, protagonist)
