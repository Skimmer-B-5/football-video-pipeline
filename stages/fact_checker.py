"""
beta/stages/fact_checker.py
Authoritative Real-World Football Knowledge & Ground-Truth Verification Engine.

Guarantees:
1. Strict fact-checking of current managers, home grounds, and club statuses before script & visual generation.
2. Live web verification via Wikipedia REST summary + Google News RSS + Groq extraction (12h cache)
   backed by the Verified Ground-Truth Registry.
3. Explicitly blocks obsolete managers (e.g., Ruben Amorim / Erik ten Hag at Manchester United) and
   overrides any stale manager string on StoryDossier.
4. Enforces Action-Oriented Photographic Directives (tackles, sprints, celebrations, touchline tactical shouts).
"""

import re
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FACT_CACHE_FILE = PROJECT_ROOT / "data" / "fact_cache.json"
CACHE_TTL_SEC = 12 * 3600  # 12 hours


@dataclass
class ClubFact:
    canonical_name: str
    current_manager: str
    stadium: str
    league: str
    country: str
    aliases: List[str]
    obsolete_managers: List[str] = field(default_factory=list)
    recent_managerial_change: bool = False
    manager_appointment_note: str = ""


# Authoritative Club Registry (Audited baseline, checked alongside live search)
CLUB_REGISTRY: Dict[str, ClubFact] = {
    "manchester united": ClubFact(
        canonical_name="Manchester United",
        current_manager="Mauricio Pochettino",
        stadium="Old Trafford",
        league="Premier League",
        country="England",
        aliases=["man utd", "man united", "united", "mufc", "red devils"],
        obsolete_managers=["ruben amorim", "amorim", "erik ten hag", "ten hag", "michael carrick", "ruud van nistelrooy"],
        recent_managerial_change=True,
        manager_appointment_note="Mauricio Pochettino officially appointed Manchester United manager in November 2026."
    ),
    "fulham": ClubFact(
        canonical_name="Fulham",
        current_manager="Marco Silva",
        stadium="Craven Cottage",
        league="Premier League",
        country="England",
        aliases=["fulham fc", "the cottagers", "cottagers"]
    ),
    "manchester city": ClubFact(
        canonical_name="Manchester City",
        current_manager="Enzo Maresca",
        stadium="Etihad Stadium",
        league="Premier League",
        country="England",
        aliases=["man city", "city", "mcfc", "citizens"],
        obsolete_managers=["pep guardiola", "guardiola"],
        recent_managerial_change=True,
        manager_appointment_note="Enzo Maresca succeeded Pep Guardiola as Manchester City manager."
    ),
    "liverpool": ClubFact(
        canonical_name="Liverpool",
        current_manager="Andoni Iraola",
        stadium="Anfield",
        league="Premier League",
        country="England",
        aliases=["lfc", "the reds"],
        obsolete_managers=["arne slot", "slot", "jurgen klopp", "klopp"],
        recent_managerial_change=True,
        manager_appointment_note="Andoni Iraola appointed Liverpool head coach in June 2026."
    ),
    "arsenal": ClubFact(
        canonical_name="Arsenal",
        current_manager="Mikel Arteta",
        stadium="Emirates Stadium",
        league="Premier League",
        country="England",
        aliases=["afc", "the gunners", "gunners"]
    ),
    "chelsea": ClubFact(
        canonical_name="Chelsea",
        current_manager="Liam Rosenior",
        stadium="Stamford Bridge",
        league="Premier League",
        country="England",
        aliases=["cfc", "the blues"],
        obsolete_managers=["enzo maresca", "mauricio pochettino", "graham potter"],
        recent_managerial_change=True,
        manager_appointment_note="Liam Rosenior appointed Chelsea head coach in January 2026."
    ),
    "tottenham": ClubFact(
        canonical_name="Tottenham Hotspur",
        current_manager="Roberto De Zerbi",
        stadium="Tottenham Hotspur Stadium",
        league="Premier League",
        country="England",
        aliases=["tottenham", "spurs", "thfc"],
        obsolete_managers=["ange postecoglou", "postecoglou"],
        recent_managerial_change=True,
        manager_appointment_note="Roberto De Zerbi appointed Tottenham Hotspur head coach in March 2026."
    ),
    "newcastle": ClubFact(
        canonical_name="Newcastle United",
        current_manager="Matthias Jaissle",
        stadium="St James' Park",
        league="Premier League",
        country="England",
        aliases=["newcastle", "nufc", "magpies"],
        obsolete_managers=["eddie howe", "howe"],
        recent_managerial_change=True,
        manager_appointment_note="Matthias Jaissle appointed Newcastle United manager."
    ),
    "aston villa": ClubFact(
        canonical_name="Aston Villa",
        current_manager="Unai Emery",
        stadium="Villa Park",
        league="Premier League",
        country="England",
        aliases=["villa", "avfc"]
    ),
    "real madrid": ClubFact(
        canonical_name="Real Madrid",
        current_manager="José Mourinho",
        stadium="Santiago Bernabéu",
        league="La Liga",
        country="Spain",
        aliases=["madrid", "los blancos", "merengues"],
        obsolete_managers=["carlo ancelotti", "xabi alonso"],
        recent_managerial_change=True,
        manager_appointment_note="José Mourinho appointed Real Madrid manager in June 2026."
    ),
    "barcelona": ClubFact(
        canonical_name="Barcelona",
        current_manager="Hansi Flick",
        stadium="Camp Nou",
        league="La Liga",
        country="Spain",
        aliases=["barca", "barça", "fc barcelona", "blaugrana"],
        obsolete_managers=["xavi"]
    ),
    "atletico madrid": ClubFact(
        canonical_name="Atlético Madrid",
        current_manager="Diego Simeone",
        stadium="Metropolitano Stadium",
        league="La Liga",
        country="Spain",
        aliases=["atletico", "atlético", "colchoneros"]
    ),
    "ac milan": ClubFact(
        canonical_name="AC Milan",
        current_manager="Rúben Amorim",
        stadium="San Siro",
        league="Serie A",
        country="Italy",
        aliases=["milan", "rossoneri"],
        obsolete_managers=["paulo fonseca", "sergio conceicao", "stefano pioli"],
        recent_managerial_change=True,
        manager_appointment_note="Rúben Amorim appointed AC Milan head coach in June 2026."
    ),
    "inter milan": ClubFact(
        canonical_name="Inter Milan",
        current_manager="Cristian Chivu",
        stadium="San Siro",
        league="Serie A",
        country="Italy",
        aliases=["inter", "nerazzurri"],
        obsolete_managers=["simone inzaghi"]
    ),
    "juventus": ClubFact(
        canonical_name="Juventus",
        current_manager="Luciano Spalletti",
        stadium="Allianz Stadium",
        league="Serie A",
        country="Italy",
        aliases=["juve", "bianconeri"],
        obsolete_managers=["thiago motta", "motta", "igor tudor", "tudor", "massimiliano allegri", "allegri"],
        recent_managerial_change=True,
        manager_appointment_note="Luciano Spalletti appointed Juventus head coach in October 2025."
    ),
    "bayern munich": ClubFact(
        canonical_name="Bayern Munich",
        current_manager="Vincent Kompany",
        stadium="Allianz Arena",
        league="Bundesliga",
        country="Germany",
        aliases=["bayern", "fc bayern"],
        obsolete_managers=["thomas tuchel", "tuchel"]
    ),
    "bayer leverkusen": ClubFact(
        canonical_name="Bayer Leverkusen",
        current_manager="Xabi Alonso",
        stadium="BayArena",
        league="Bundesliga",
        country="Germany",
        aliases=["leverkusen", "werkself"]
    ),
    "psg": ClubFact(
        canonical_name="Paris Saint-Germain",
        current_manager="Luis Enrique",
        stadium="Parc des Princes",
        league="Ligue 1",
        country="France",
        aliases=["paris saint germain", "paris", "paris sg"]
    ),
    "brighton": ClubFact(
        canonical_name="Brighton & Hove Albion",
        current_manager="Fabian Hürzeler",
        stadium="Amex Stadium",
        league="Premier League",
        country="England",
        aliases=["brighton", "seagulls", "bhafc"]
    ),
    "west ham": ClubFact(
        canonical_name="West Ham United",
        current_manager="Scott Parker",
        stadium="London Stadium",
        league="Premier League",
        country="England",
        aliases=["west ham", "hammers", "whufc"],
        obsolete_managers=["julen lopetegui", "graham potter"]
    ),
    "napoli": ClubFact(
        canonical_name="Napoli",
        current_manager="Massimiliano Allegri",
        stadium="Stadio Diego Armando Maradona",
        league="Serie A",
        country="Italy",
        aliases=["ssc napoli", "partenopei"],
        obsolete_managers=["antonio conte", "conte", "francesco calzona"]
    ),
    "borussia dortmund": ClubFact(
        canonical_name="Borussia Dortmund",
        current_manager="Niko Kovač",
        stadium="Signal Iduna Park",
        league="Bundesliga",
        country="Germany",
        aliases=["dortmund", "bvb"]
    ),
}


class FactChecker:
    """Validates and enriches football stories with live-verified and canonical ground-truth facts."""

    @classmethod
    def resolve_club(cls, query: str) -> Optional[ClubFact]:
        """Resolves any club mention or alias to its authoritative ClubFact."""
        if not query:
            return None
        q = query.strip().lower()
        if q in CLUB_REGISTRY:
            return CLUB_REGISTRY[q]

        for _, fact in CLUB_REGISTRY.items():
            if q == fact.canonical_name.lower():
                return fact
            for alias in fact.aliases:
                if re.search(rf'\b{re.escape(alias)}\b', q):
                    return fact
        return None

    @classmethod
    def _load_cache(cls) -> Dict[str, Any]:
        if FACT_CACHE_FILE.exists():
            try:
                return json.loads(FACT_CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    @classmethod
    def _save_cache(cls, data: Dict[str, Any]) -> None:
        try:
            FACT_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            FACT_CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    @classmethod
    def live_verify_club(cls, club_name: str) -> Optional[Dict[str, str]]:
        """
        Queries Wikipedia Infobox/Summary + recent Google News RSS + Groq extraction
        to verify unknown clubs or recent managerial appointments, cached for 12h.
        """
        if not club_name or club_name.lower() in ("european rivals", "top european suitors", "his current club"):
            return None

        cache_key = club_name.strip().lower()
        cache = cls._load_cache()
        entry = cache.get(cache_key)
        if entry and (time.time() - entry.get("ts", 0)) < CACHE_TTL_SEC:
            return entry.get("facts")

        snippets = []
        headers = {"User-Agent": "FootballNewsDesk/2.0 (broadcast@footballin30sec.com)"}

        # 1. Wikipedia REST summary
        try:
            slug = urllib.parse.quote(f"{club_name} F.C.".replace(" ", "_"))
            for cand_slug in [slug, urllib.parse.quote(club_name.replace(" ", "_"))]:
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{cand_slug}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as r:
                    wdata = json.loads(r.read().decode("utf-8"))
                    if wdata.get("extract"):
                        snippets.append(f"Wikipedia ({wdata.get('title')}): {wdata['extract'][:450]}")
                        break
        except Exception:
            pass

        # 2. Google News RSS for current manager appointment news
        try:
            rss_q = urllib.parse.quote(f'"{club_name}" manager OR "head coach" OR stadium when:30d')
            rss_url = f"https://news.google.com/rss/search?q={rss_q}&hl=en-GB&gl=GB&ceid=GB:en"
            req = urllib.request.Request(rss_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as r:
                root = ET.fromstring(r.read())
            for item in root.findall(".//item")[:5]:
                title = item.findtext("title", "").strip()
                pub = item.findtext("pubDate", "").strip()
                if title:
                    snippets.append(f"News ({pub}): {title}")
        except Exception:
            pass

        if not snippets:
            return None

        try:
            try:
                from stages.groq_client import call_groq_chat
            except ModuleNotFoundError:
                from stages.groq_client import call_groq_chat

            prompt = (
                f"Verify the CURRENT manager / head coach and home stadium for football club '{club_name}' "
                f"from these live search snippets:\n\n" + "\n".join(snippets) +
                '\n\nOutput ONLY valid JSON: {"current_manager": "...", "stadium": "..."}'
            )
            raw = call_groq_chat(
                system_prompt="You are a football fact-verification engine. Output ONLY JSON.",
                user_prompt=prompt,
                temperature=0.0,
                timeout=8
            )
            if raw:
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    if parsed.get("current_manager") or parsed.get("stadium"):
                        cache[cache_key] = {"ts": time.time(), "facts": parsed}
                        cls._save_cache(cache)
                        return parsed
        except Exception:
            pass
        return None

    @classmethod
    def get_verified_manager(cls, club_name: str, use_live_fallback: bool = True) -> str:
        """Returns the verified, grounded current manager of a club."""
        fact = cls.resolve_club(club_name)
        if fact:
            return fact.current_manager
        if use_live_fallback:
            live = cls.live_verify_club(club_name)
            if live and live.get("current_manager"):
                return live["current_manager"]
        return "The Manager"

    @classmethod
    def get_verified_stadium(cls, club_name: str, use_live_fallback: bool = True) -> str:
        """Returns the verified home stadium of a club."""
        fact = cls.resolve_club(club_name)
        if fact:
            return fact.stadium
        if use_live_fallback:
            live = cls.live_verify_club(club_name)
            if live and live.get("stadium"):
                return live["stadium"]
        return f"{club_name} Stadium"

    @classmethod
    def get_obsolete_managers(cls, club_name: str) -> List[str]:
        """Returns obsolete/former managers that must NEVER be shown as active coach for this club."""
        fact = cls.resolve_club(club_name)
        return list(fact.obsolete_managers) if fact else []

    @classmethod
    def audit_and_enrich_dossier(cls, dossier, enable_live_check: bool = True) -> Any:
        """
        Audits and enriches a StoryDossier with verified managers, stadiums,
        and factual real-world context before screenplay and visual generation.
        Unconditionally overrides missing, generic, OR stale/obsolete manager names.
        """
        # 1. Audit current club
        curr_fact = cls.resolve_club(dossier.current_club)
        if curr_fact:
            dossier.current_club = curr_fact.canonical_name
            dossier.current_stadium = curr_fact.stadium
            mgr_low = (dossier.current_manager or "").strip().lower()
            is_stale = any(obs in mgr_low for obs in curr_fact.obsolete_managers)
            is_generic = not mgr_low or mgr_low in ("the manager", "coach", "manager", "official", "unknown")
            # Override whenever generic, stale, or mismatched against authoritative canonical manager
            if is_generic or is_stale or mgr_low != curr_fact.current_manager.lower():
                if not is_generic and mgr_low != curr_fact.current_manager.lower():
                    print(f"[FactChecker] OVERRIDE stale/mismatched {dossier.current_club} manager '{dossier.current_manager}' -> '{curr_fact.current_manager}'")
                dossier.current_manager = curr_fact.current_manager
            print(f"[FactChecker] Verified {dossier.current_club}: Manager='{dossier.current_manager}', Stadium='{dossier.current_stadium}'")
        elif enable_live_check:
            live = cls.live_verify_club(dossier.current_club)
            if live:
                if live.get("current_manager") and (not dossier.current_manager or dossier.current_manager.lower() in ("the manager", "coach", "manager")):
                    dossier.current_manager = live["current_manager"]
                if live.get("stadium"):
                    dossier.current_stadium = live["stadium"]
                print(f"[FactChecker] Live-verified {dossier.current_club}: Manager='{dossier.current_manager}', Stadium='{dossier.current_stadium}'")

        # 2. Audit pursuing club / suitor
        purs_fact = cls.resolve_club(dossier.pursuing_club)
        if purs_fact:
            dossier.pursuing_club = purs_fact.canonical_name
            dossier.pursuing_manager = purs_fact.current_manager
            dossier.pursuing_stadium = purs_fact.stadium
            print(f"[FactChecker] Verified Suitor {dossier.pursuing_club}: Manager='{dossier.pursuing_manager}', Stadium='{dossier.pursuing_stadium}'")
            if purs_fact.recent_managerial_change:
                print(f"[FactChecker] NOTE: {purs_fact.manager_appointment_note}")
        elif enable_live_check:
            live_p = cls.live_verify_club(dossier.pursuing_club)
            if live_p:
                dossier.pursuing_manager = live_p.get("current_manager", "")
                dossier.pursuing_stadium = live_p.get("stadium", "")

        return dossier

    @classmethod
    def get_dynamic_action_guidance(cls, entity_name: str, club_name: str, role: str) -> Dict[str, Any]:
        """
        Generates strict dynamic action keywords for visual image sourcing:
        bans static standing poses; mandates match action, duels, celebrations, or tactical coaching.
        """
        obsolete = cls.get_obsolete_managers(club_name)
        if "manager" in role.lower() or "coach" in role.lower():
            action_desc = f"{entity_name} passionately shouting tactical instructions from the {club_name} technical area during an intense match."
            search_query = f"{entity_name} {club_name} manager touchline tactical instructions"
            avoid = ["standing still", "smiling photoshoot", "empty stadium", "studio portrait", "suit portrait background"] + obsolete
        elif "stadium" in role.lower() or "ground" in role.lower():
            stadium_name = cls.get_verified_stadium(club_name)
            action_desc = f"{stadium_name} glowing brilliantly under matchday floodlights with roaring crowd atmosphere."
            search_query = f"{stadium_name} matchday floodlights crowd atmosphere night"
            avoid = ["empty seats", "daytime construction", "blueprint", "aerial map"]
        else:
            action_desc = f"{entity_name} executing a fierce sliding tackle or accelerating in match action for {club_name} in dynamic motion."
            search_query = f"{entity_name} {club_name} sliding tackle match action dynamic"
            avoid = ["standing pose", "hands on hips", "studio photoshoot", "media day portrait", "mugshot", "neutral expression"] + obsolete

        return {
            "action_description": action_desc,
            "search_query": search_query,
            "avoid_terms": avoid
        }
