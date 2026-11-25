"""
Story Director & Two-Pass Editorial Architect for the Blended FS30 2.5D Documentary Engine.
Unites:
- Restrained factual British documentary writing (dry wit, zero hype cliches)
- Alternating multi-style beat layouts (Vox 2.5D multiplane cutouts, newsprint highlighter
  clippings, mounted archival evidence, articulated 2.5D confrontation puppets, timelines)
- Real grounded context hydration (article URL + Wikipedia archival summary when available)
"""

import re
import json
import html
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class NewspaperClipSpec(BaseModel):
    publication: str = Field(..., description="Authentic outlet masthead, e.g. 'BBC Sport', 'The Guardian'")
    date_text: str = Field(..., description="Publication date label, e.g. 'APRIL 22, 2013'")
    headline: str = Field(..., description="Concise newspaper headline matching factual history")
    quote_excerpt: str = Field(..., description="Short factual press excerpt (18-30 words)")
    highlight_phrase: str = Field(..., description="Exact substring inside quote_excerpt or headline for yellow highlighter sweep")


class TacticalReticleSpec(BaseModel):
    enabled: bool = False
    label: Optional[str] = Field(None, description="Short uppercase callout (2-4 words), e.g. 'SHOULDER CONTACT'")
    target_x_pct: float = 52.0
    target_y_pct: float = 44.0


class TimelineItem(BaseModel):
    year: str
    event: str
    detail: str


class QuoteCardSpec(BaseModel):
    quote: str = Field(..., description="Punchy witty press quote or tribunal excerpt (8-16 words)")
    attribution: str = Field(..., description="Brief British attribution, e.g. 'THE GUARDIAN // 2013'")


class StoryBeatPlan(BaseModel):
    beat_number: int
    layout_style: str = Field(
        default="vox_25d_cutout",
        description="One of: vox_25d_cutout | newspaper_highlighter | full_bleed_callout | archival_pinboard | kinetic_quote_card | puppet_confrontation_25d | tactile_timeline_card | clean_editorial_epilogue"
    )
    banner_variant: str = "a"
    camera_move: str = "push_in"
    transition_in: str = "jagged_paper_tear"
    voiceover_text: str = Field(..., description="Crisp sarcastic Benedict Cumberbatch-style BBC narration (10-15 words)")
    visual_kicker: str = Field(..., description="Date / venue eyebrow, e.g. 'NOV 2010 // AMSTERDAM'")
    visual_headline: str = Field(..., description="Punchy display title (2-5 words)")
    kinetic_word: Optional[str] = Field(None, description="1-2 word giant background graphic word, e.g. 'DENTAL', '10 GAMES', 'TREBLE'")
    sub_caption: Optional[str] = Field(None, description="Dry ironic documentary photo caption (<=9 words)")
    primary_entity: str = Field(..., description="Canonical player/manager name for SFace identity check")
    secondary_entity: Optional[str] = Field(None, description="Second player/subject for confrontation beats")
    search_query: str = Field(..., description="Specific real-photo search query matching the exact club/era of THIS beat")
    fallback_query: str = Field(..., description="Backup real-photo search query for THIS beat")
    background_query: str = Field(..., description="Atmospheric stadium/pitch/city background query")
    use_cutout: bool = Field(default=True, description="Extract large 2.5D paper cutout for foreground motion")
    split_puppet: bool = Field(default=False, description="Enable articulated lunge/recoil 2.5D motion")
    newspaper_clip: Optional[NewspaperClipSpec] = None
    quote_card: Optional[QuoteCardSpec] = None
    stamp_text: Optional[str] = Field(None, description="Optional concise stamp badge, e.g. '10-MATCH BAN'")
    timeline_items: Optional[List[TimelineItem]] = None
    tactical_reticle: Optional[TacticalReticleSpec] = None


class StoryPackage(BaseModel):
    story_id: str
    title: str
    topic: str
    era: str
    logline: str
    primary_protagonist: str
    target_duration: float = Field(default=39.0, description="Brisk high-retention target runtime 35-44s including outro")
    narrator_voice_profile: str = "Qwen3-TTS Base (Benedict Cumberbatch Dry BBC Wit Clone, ~165 WPM)"
    score_track: str = "Cool Vibes (Vibraphone & Upright Bass Documentary Bed)"
    pronunciation_hints: Dict[str, str] = Field(default_factory=dict)
    beats: List[StoryBeatPlan]
    outro_headline: str = "THIS IS FOOTBALL IN 30 SECONDS."
    outro_subtitle: str = "BRILLIANCE & ABSURDITY, WEEKLY."
    outro_cta: str = "FOLLOW FOR MORE"
    outro_narration: str = "This is Football in Thirty Seconds. Follow for more."


BANNED_HYPE_PHRASES = (
    "you won't believe",
    "pure divinity",
    "sent shockwaves",
    "broke the internet",
    "changed football forever",
    "insane",
    "unbelievable scenes",
    "nobody saw coming",
)


def _slugify(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return (clean or "football_story")[:42]


def _normalize_spoken_tts(text: str) -> str:
    """Makes spoken text clean for TTS while preserving natural British cadence."""
    t = (text or "").replace("—", ", ").replace("–", ", ").replace("--", ", ").replace("...", ",")
    t = re.sub(r"\b(\d+)\s*[-]\s*match\b", r"\1 match", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(\d+)\s*[-]\s*month\b", r"\1 month", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _fetch_grounding_context(topic_or_url: str) -> Tuple[str, str]:
    """Fetches real factual context from URL scraper and/or Wikipedia REST summaries."""
    snippets: List[str] = []
    title_hint = topic_or_url.strip()

    if topic_or_url.strip().startswith("http"):
        try:
            try:
                from beta.stages.url_scraper import scrape_article_from_url
            except ModuleNotFoundError:
                from stages.url_scraper import scrape_article_from_url
            art = scrape_article_from_url(topic_or_url.strip(), timeout=10)
            if art.get("title"):
                title_hint = art["title"]
            if art.get("raw_text"):
                snippets.append(f"SOURCE ARTICLE ({art.get('source', 'Press')}): {art['raw_text'][:2200]}")
        except Exception as e:
            print(f"[StoryDirector] URL scrape note: {e}")

    # Query Wikipedia full-text search across topic & person tokens, scoring by topic keyword overlap
    clean_q = re.sub(r"https?://\S+", "", topic_or_url).strip() or title_hint
    headers = {"User-Agent": "FS30Documentary/2.5 (desk@football30.local)"}
    topic_tokens = [
        t.lower()
        for t in re.findall(r"[A-Za-zÀ-ÿ0-9]{3,}", clean_q)
        if t.lower() not in ("the", "and", "for", "with", "saga", "story", "history", "incident")
    ]
    query_candidates = []
    words = [w for w in re.findall(r"[A-Za-zÀ-ÿ'-]+", clean_q) if w.lower() not in ("saga", "story", "incident", "biting", "history", "kick", "kung", "fu")]
    if len(words) >= 2:
        query_candidates.append(f"{words[0]} {words[1]}")
        query_candidates.append(f"{words[0]} {words[1]} footballer")
    query_candidates.append(clean_q)

    candidate_pages: Dict[str, int] = {}
    person_prefix = f"{words[0]} {words[1]}".lower() if len(words) >= 2 else ""
    for q_str in query_candidates:
        try:
            sr_url = (
                "https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={urllib.parse.quote(q_str)}&srlimit=6&format=json"
            )
            req = urllib.request.Request(sr_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as r:
                sr_data = json.loads(r.read().decode("utf-8", errors="ignore"))
            for item in sr_data.get("query", {}).get("search", []) or []:
                wt = str(item.get("title") or "").strip()
                if not wt or "(disambiguation)" in wt.lower():
                    continue
                blob = f"{wt} {item.get('snippet', '')}".lower()
                score = sum(3 if tk in wt.lower() else 1 for tk in topic_tokens if tk in blob)
                if person_prefix and person_prefix in wt.lower():
                    score += 12
                candidate_pages[wt] = max(candidate_pages.get(wt, 0), score)
        except Exception:
            continue

    ranked_titles = [t for t, _ in sorted(candidate_pages.items(), key=lambda kv: -kv[1])]
    loaded_titles: List[str] = []
    for wt in ranked_titles[:3]:
        if snippets:
            break
        try:
            ext_url = (
                "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=true"
                f"&exsectionformat=plain&redirects=1&titles={urllib.parse.quote(wt)}&format=json"
            )
            req2 = urllib.request.Request(ext_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=10) as r2:
                ej = json.loads(r2.read().decode("utf-8", errors="ignore"))
            pages = ej.get("query", {}).get("pages", {})
            for p in pages.values():
                full_txt = str(p.get("extract") or "").strip()
                if not full_txt or "may refer to:" in full_txt[:120]:
                    continue
                paragraphs = [pg.strip() for pg in re.split(r"\n{2,}", full_txt) if pg.strip()]
                lead = paragraphs[0][:400] if paragraphs else ""
                sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\n+", " ", full_txt))
                specific_words = {
                    "bit", "bite", "bitten", "biting", "bakkal", "ivanovi", "chiellini",
                    "knvb", "psv", "chelsea", "anfield", "kick", "selhurst", "cantona",
                    "seagull", "palace", "headbutt", "materazzi", "red card", "banned", "ban",
                }
                ev_candidates = []
                for idx_s, sent in enumerate(sentences):
                    low_s = sent.lower()
                    if len(sent) < 30 or len(sent) > 320:
                        continue
                    spec_hits = sum(5 for aw in specific_words if aw in low_s)
                    ban_hits = 3 if any(bw in low_s for bw in ("ban", "banned", "suspend", "suspension", "fifa")) else 0
                    tok_hits = sum(1 for tk in topic_tokens if tk in low_s)
                    score = spec_hits + ban_hits + tok_hits
                    if spec_hits >= 5 or (ban_hits >= 3 and tok_hits >= 2):
                        ev_candidates.append((score, idx_s, sent))
                ev_candidates.sort(key=lambda x: (-x[0], x[1]))
                chosen_idxs = set()
                for _, idx_s, _ in ev_candidates[:12]:
                    chosen_idxs.add(idx_s)
                    if idx_s + 1 < len(sentences) and 35 <= len(sentences[idx_s + 1]) <= 260:
                        chosen_idxs.add(idx_s + 1)
                ordered_sents = [sentences[i] for i in sorted(chosen_idxs)]
                selected_body = " ".join(ordered_sents)[:2400]
                doc_str = f"WIKIPEDIA ({p.get('title', wt)}): {lead}\nCHRONOLOGICAL KEY FACTS: {selected_body}".strip()
                snippets.append(doc_str[:2900])
                loaded_titles.append(str(p.get("title", wt)))
                break
        except Exception:
            continue

    print(f"[StoryDirector] Wikipedia grounding docs loaded: {len(snippets)} ({', '.join(loaded_titles)})")
    return title_hint, "\n\n".join(snippets)


def _coerce_beat_dict(raw_b: Dict[str, Any], idx: int, default_ent: str = "Football Subject") -> Dict[str, Any]:
    """Normalizes LLM Pass 1/Pass 2 alias keys cleanly before Pydantic validation."""
    b = dict(raw_b or {})
    b["beat_number"] = int(b.get("beat_number") or idx)

    kicker = str(b.get("visual_kicker") or b.get("kicker") or b.get("date") or f"CHAPTER 0{idx}").strip()
    headline = str(b.get("visual_headline") or b.get("headline") or b.get("title") or f"STORY BEAT {idx}").strip()
    vo = str(b.get("voiceover_text") or b.get("narration") or b.get("spoken_text") or "").strip()
    primary = str(b.get("primary_entity") or b.get("entity") or default_ent).strip()

    b["visual_kicker"] = kicker
    b["visual_headline"] = headline
    b["voiceover_text"] = vo or headline
    b["primary_entity"] = primary
    if b.get("secondary_entity") in ("", "null", "None"):
        b["secondary_entity"] = None

    b["search_query"] = str(b.get("search_query") or b.get("query") or f"{primary} football action").strip()
    b["fallback_query"] = str(b.get("fallback_query") or f"{primary} portrait football").strip()
    bg_q = str(b.get("background_query") or "European football stadium floodlights pitch").strip()
    bg_q = re.sub(r"\bcricket\b", "football", bg_q, flags=re.IGNORECASE)
    if not any(kw in bg_q.lower() for kw in ("football", "soccer", "anfield", "camp nou", "wembley", "cruyff", "old trafford", "bernabeu", "maracana", "arena das dunas")):
        bg_q = f"{bg_q} football stadium pitch".strip()
    b["background_query"] = bg_q
    if b.get("kinetic_word"):
        b["kinetic_word"] = str(b["kinetic_word"]).strip().upper()[:18]

    qc = b.get("quote_card")
    if isinstance(qc, dict) and (qc.get("quote") or qc.get("text")):
        b["quote_card"] = {
            "quote": str(qc.get("quote") or qc.get("text") or "").strip(),
            "attribution": str(qc.get("attribution") or qc.get("source") or kicker).strip(),
        }
    elif qc is not None:
        b["quote_card"] = None

    # Coerce newspaper_clip aliases ('source'->'publication', 'date'->'date_text', 'quote'/'text'->'quote_excerpt', 'highlight'->'highlight_phrase')
    nc = b.get("newspaper_clip")
    if isinstance(nc, dict):
        pub = str(nc.get("publication") or nc.get("source") or nc.get("outlet") or "Football Archive").strip()
        dt = str(nc.get("date_text") or nc.get("date") or kicker.split("//")[0].strip()).strip()
        hl = str(nc.get("headline") or nc.get("title") or headline).strip()
        qex = str(nc.get("quote_excerpt") or nc.get("quote") or nc.get("excerpt") or nc.get("text") or vo).strip()
        hp = str(nc.get("highlight_phrase") or nc.get("highlight") or nc.get("highlighted_phrase") or "").strip()
        if not hp or hp.lower() not in (qex + " " + hl).lower():
            words = qex.split()
            hp = " ".join(words[: min(5, len(words))])
        b["newspaper_clip"] = {
            "publication": pub,
            "date_text": dt,
            "headline": hl,
            "quote_excerpt": qex,
            "highlight_phrase": hp,
        }
    elif nc is not None:
        b["newspaper_clip"] = None

    # Coerce timeline_items aliases
    t_items = b.get("timeline_items")
    if isinstance(t_items, list):
        clean_tl = []
        for item in t_items:
            if isinstance(item, dict):
                yr = str(item.get("year") or item.get("date") or "").strip()
                ev = str(item.get("event") or item.get("title") or item.get("match") or "").strip()
                det = str(item.get("detail") or item.get("summary") or item.get("description") or "").strip()
                if yr or ev or det:
                    clean_tl.append({"year": yr or "DATE", "event": ev or "EVENT", "detail": det or ev})
        b["timeline_items"] = clean_tl or None

    # Coerce tactical_reticle
    tr = b.get("tactical_reticle")
    if isinstance(tr, str):
        b["tactical_reticle"] = {"enabled": True, "label": tr[:32]} if tr.strip() else None
    elif isinstance(tr, dict):
        b["tactical_reticle"] = {
            "enabled": bool(tr.get("enabled", True)),
            "label": str(tr.get("label") or "").strip() or None,
            "target_x_pct": float(tr.get("target_x_pct") or 52.0),
            "target_y_pct": float(tr.get("target_y_pct") or 44.0),
        }

    # Drop stray keys not in StoryBeatPlan
    allowed = set(StoryBeatPlan.model_fields.keys())
    return {k: v for k, v in b.items() if k in allowed}


def _enforce_sequence_variety(beats: List[StoryBeatPlan]) -> List[StoryBeatPlan]:
    """Ensures no two consecutive beats reuse the exact same layout, camera move, transition, or banner variant."""
    default_layouts = [
        "vox_25d_cutout",
        "newspaper_highlighter",
        "full_bleed_callout",
        "archival_pinboard",
        "kinetic_quote_card",
        "puppet_confrontation_25d",
        "tactile_timeline_card",
        "clean_editorial_epilogue",
    ]
    cameras = ["push_in", "drift_left", "pull_out", "drift_right"]
    transitions = ["jagged_paper_tear", "card_flip_3d", "cutout_zoom_punch", "match_cut_slide"]
    variants = ["a", "b", "c", "d", "e"]

    prev_layout = None
    prev_cam = None
    prev_trans = None
    prev_var = None
    seen_layouts = set()
    for idx, b in enumerate(beats):
        b.beat_number = idx + 1
        if len(beats) == 8:
            b.layout_style = default_layouts[idx]
        elif b.layout_style == prev_layout or b.layout_style not in default_layouts or b.layout_style in seen_layouts:
            b.layout_style = default_layouts[idx % len(default_layouts)]
        seen_layouts.add(b.layout_style)
        if b.layout_style in ("vox_25d_cutout", "newspaper_highlighter", "kinetic_quote_card", "puppet_confrontation_25d", "tactile_timeline_card"):
            b.use_cutout = True
        if b.layout_style == "puppet_confrontation_25d":
            b.split_puppet = True
        if b.camera_move == prev_cam or b.camera_move not in cameras:
            b.camera_move = cameras[idx % len(cameras)]
        if b.transition_in == prev_trans or b.transition_in not in transitions:
            b.transition_in = transitions[idx % len(transitions)]
        if b.banner_variant == prev_var or b.banner_variant not in variants:
            b.banner_variant = variants[idx % len(variants)]
        b.voiceover_text = _normalize_spoken_tts(b.voiceover_text)

        # Ensure structural payloads exist if layout requires them
        if b.layout_style == "newspaper_highlighter" and not b.newspaper_clip:
            b.newspaper_clip = NewspaperClipSpec(
                publication="Football Archive Desk",
                date_text=b.visual_kicker.split("//")[0].strip(),
                headline=b.visual_headline,
                quote_excerpt=b.voiceover_text,
                highlight_phrase=" ".join(b.voiceover_text.split()[:5]),
            )
        if b.layout_style == "kinetic_quote_card" and not b.quote_card:
            b.quote_card = QuoteCardSpec(
                quote=b.sub_caption or b.voiceover_text,
                attribution=b.visual_kicker,
            )
        if b.layout_style == "tactile_timeline_card" and not b.timeline_items:
            b.timeline_items = [
                TimelineItem(year="INCIDENT", event=b.visual_headline, detail=b.sub_caption or b.visual_kicker)
            ]

        prev_layout = b.layout_style
        prev_cam = b.camera_move
        prev_trans = b.transition_in
        prev_var = b.banner_variant
    return beats


def _build_default_phonetics() -> Dict[str, str]:
    return {
        "Suárez": "Swarez",
        "Suarez": "Swarez",
        "Otman Bakkal": "Ohtman Bakkal",
        "Bakkal": "Bakkal",
        "Branislav Ivanović": "Brahnislav Eevanovich",
        "Ivanović": "Eevanovich",
        "Ivanovic": "Eevanovich",
        "Giorgio Chiellini": "Giorgio Kielini",
        "Chiellini": "Kielini",
    }


def _parse_json_object(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*|```\s*$", "", raw.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not m:
        return None
    cand = m.group(0)
    for attempt in range(2):
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except Exception as e:
            if attempt == 1:
                print(f"[StoryDirector] JSON parse note: {e}")
            # Repair common trailing commas before '}' or ']'
            cand = re.sub(r",(\s*[}\]])", r"\1", cand)
    return None


def generate_documentary_package(
    topic_or_url: str,
    target_words: Tuple[int, int] = (84, 114),
) -> StoryPackage:
    """
    Runs a 2-pass LLM editorial + art-direction pipeline (GPT-OSS-120B draft -> Qwen-27B/20B polish)
    to generate a brisk, sarcastic Benedict Cumberbatch–style 8-beat BBC 2.5D documentary StoryPackage.
    """
    try:
        from beta.stages.groq_client import call_groq_chat
    except ModuleNotFoundError:
        from stages.groq_client import call_groq_chat

    title_hint, grounding_text = _fetch_grounding_context(topic_or_url)
    print(f"[StoryDirector] Generating sarcastic 8-beat BBC 2.5D documentary script for: '{title_hint[:65]}'...")

    sys_prompt = f"""You are the Lead Writer & Art Director for 'Football in 30 Seconds (FS30 TV)'.
You write wickedly smart, deadpan, sarcastic British BBC mini-documentaries in the voice and comedic cadence of Benedict Cumberbatch inspecting absurd human behaviour.

PERSONA & WRITING CRAFT:
1. VOICE & WIT: Do NOT treat a cheeky football scandal like a somber tragedy or read dry Wikipedia chronology!
   - Use posh British understatement, wry observational irony, elevated formal diction applied to petty sporting chaos, and a crisp comedic turn on EVERY beat (setup -> deadpan punchline).
   - BANNED CLICHES: {', '.join(BANNED_HYPE_PHRASES)}.
   - Example tone: "A world-class striker, blessed with sublime technique, and an unexplained appetite for defenders." / "Naturally, Liverpool inspected his dental record and signed him immediately anyway."
2. BRISK HIGH-VELOCITY PACING (8 BEATS):
   - Write EXACTLY 8 punchy micro-beats totaling {target_words[0]} to {target_words[1]} spoken words combined (STRICTLY 10-15 words per beat!).
   - Every beat should snap fast (~3.8-4.8s), giving the viewer a new visual gag/reveal every ~4 seconds (~38-42s total video).
3. FACTUAL RIGOR & CLUB-MATCHED VISUALS:
   - Strictly preserve true historical chronology, clubs, opponents, ban durations, and outcomes from GROUNDING (never flip club timelines or invent events/quotes/trailing filler like 'today.' or 'anyway.').
   - NEVER use ellipsis ('...') or invented quotes from managers/players unless verbatim in GROUNDING.
   - CRITICAL: Each beat's "search_query" and "fallback_query" MUST specify the exact club/shirt matching that beat's narrative (e.g., if Beat 8 celebrates a treble with Barcelona, query MUST say Barcelona, NEVER the previous club!).
4. 8 DISTINCT ALTERNATING LAYOUTS:
   - Beat 1: "vox_25d_cutout" (Huge foreground cutout + kinetic_word + sarcastic hook)
   - Beat 2: "newspaper_highlighter" (Tilted archival clipping with highlight_phrase + large cutout)
   - Beat 3: "full_bleed_callout" (Full-screen action photo pushing in + ironic Turn caption)
   - Beat 4: "archival_pinboard" (Large framed evidence photo + tactical_reticle drawing around contact/moment)
   - Beat 5: "kinetic_quote_card" (Skewed torn parchment quote_card + big cutout + stamp_text)
   - Beat 6: "puppet_confrontation_25d" (Giant overlapping primary_entity vs secondary_entity cutouts + stamp_text; secondary_entity MUST be a named opposing player or manager, NEVER FIFA/UEFA)
   - Beat 7: "tactile_timeline_card" (Rapid 3-item chronological tally + cutout)
   - Beat 8: "clean_editorial_epilogue" (Full-bleed final-club trophy/portrait + dry British closing zinger)
5. PRONUNCIATION HINTS & JSON CLEANLINESS:
   - Include "pronunciation_hints" mapping foreign surnames to smooth unbroken phonetic words WITHOUT hyphens (e.g. "Giorgio Chiellini": "Giorgio Kielini", NEVER hyphenated syllables).
   - For stadium background_query, specify "arch pitch floodlights" or "stadium aerial", never "FA" or trophy words.
   - Spell numbers in spoken words ("twenty ten", "ten games"), escape or omit double quotes inside strings, and output strict RFC8259 valid JSON.

Respond ONLY with valid JSON matching the StoryPackage schema:
{{
  "story_id": "short_snake_case_id",
  "title": "Witty BBC-style title",
  "topic": "{topic_or_url}",
  "era": "Exact date span, e.g. '2010 — 2015'",
  "logline": "One sharp dry British logline",
  "primary_protagonist": "Full Name",
  "pronunciation_hints": {{"Name": "Phonetic"}},
  "beats": [
    {{
      "beat_number": 1,
      "layout_style": "vox_25d_cutout",
      "banner_variant": "a",
      "camera_move": "push_in",
      "transition_in": "jagged_paper_tear",
      "voiceover_text": "...",
      "visual_kicker": "SHORT EYEBROW // DATE",
      "visual_headline": "2-5 WORD DISPLAY HEADLINE",
      "kinetic_word": "APPETITE",
      "sub_caption": "Optional dry ironic subtitle",
      "primary_entity": "Full Name",
      "secondary_entity": null,
      "search_query": "specific club/era match photo query",
      "fallback_query": "backup real photo query",
      "background_query": "stadium night floodlights pitch",
      "use_cutout": true,
      "split_puppet": false,
      "newspaper_clip": null,
      "quote_card": null,
      "stamp_text": null,
      "timeline_items": null,
      "tactical_reticle": {{"enabled": false, "label": null, "target_x_pct": 50, "target_y_pct": 42}}
    }}
  ]
}}"""

    user_prompt = f"""Topic / Brief: {topic_or_url}

GROUNDING MATERIAL:
{grounding_text[:1550] if grounding_text else 'Use verified historical football facts strictly.'}

Write an 8-beat dry sarcastic BBC mini-documentary StoryPackage JSON now (10-15 words per beat!)."""

    strict_models = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
    raw_draft = call_groq_chat(
        system_prompt=sys_prompt,
        user_prompt=user_prompt,
        preferred_model="openai/gpt-oss-120b",
        fallback_model="qwen/qwen3.8-27b",
        max_tokens=1850,
        temperature=0.35,
        timeout=50,
        json_mode=True,
        allowed_models=strict_models,
    )

    pkg_dict: Optional[Dict[str, Any]] = _parse_json_object(raw_draft)
    if not raw_draft:
        print("[StoryDirector] Pass 1 returned empty response; switching to fallback LLM draft.")

    if pkg_dict is None:
        raw_retry = call_groq_chat(
            system_prompt=sys_prompt,
            user_prompt=user_prompt + "\n\nCRITICAL: Output ONLY compact valid JSON matching schema, 8 beats, 10-14 words per beat, sharp sarcastic British wit.",
            preferred_model="qwen/qwen3.8-27b",
            fallback_model="openai/gpt-oss-120b",
            max_tokens=1850,
            temperature=0.25,
            timeout=50,
            json_mode=True,
            allowed_models=strict_models,
        )
        pkg_dict = _parse_json_object(raw_retry)

    # Pass 2: Only polish when word count drifts out of crisp 38-42s range or needs cleanup (keeps TPM clean)
    def _draft_needs_polish(d: Dict[str, Any]) -> bool:
        bs = d.get("beats") or []
        if len(bs) < 8:
            return True
        wc = sum(len(str(x.get("voiceover_text") or x.get("narration") or "").split()) for x in bs)
        if wc < 76 or wc > 122:
            return True
        for x in bs:
            vo_l = str(x.get("voiceover_text") or "").strip().lower()
            if "..." in vo_l or re.search(r"\b(in|for|to|of|with|by|at|today|anyway|ultimately|again)\.?$", vo_l):
                return True
        return False

    if pkg_dict and _draft_needs_polish(pkg_dict):
        polish_prompt = f"""Audit and punch up this 8-beat documentary StoryPackage JSON strictly against GROUNDING:
{grounding_text[:1350] if grounding_text else topic_or_url}

FIX ANY FLAWS:
1. Ensure total spoken words across all 8 beats is {target_words[0]}-{target_words[1]} words (STRICTLY 10-14 complete words per beat — brisk, complete grammatical sentences, ZERO truncated fragments ending in prepositions like 'in.' or 'for.').
2. Sharpen dry Benedict Cumberbatch sarcasm & ironic deadpan punchlines using ONLY verified Grounding facts — NEVER invent quotes from managers or fans.
3. Verify EVERY search_query matches the exact club/kit mentioned in that beat's voiceover (e.g., Barcelona beat -> Barcelona query).
4. Beat 6 secondary_entity MUST be a real named opposing player/opponent (NEVER FIFA/FA/UEFA).
5. Ensure pronunciation_hints use smooth non-hyphenated respellings (never 'Kee-eh-lee-nee').
6. Preserve EXACT schema keys including quote_card, newspaper_clip, kinetic_word, timeline_items, pronunciation_hints.

CURRENT JSON:
{json.dumps(pkg_dict, ensure_ascii=False)}

Output ONLY valid JSON."""

        raw_polish = call_groq_chat(
            system_prompt="You are a ruthless BBC / Vox comedy-documentary script editor. Output valid JSON only.",
            user_prompt=polish_prompt,
            preferred_model="openai/gpt-oss-120b",
            fallback_model="qwen/qwen3.8-27b",
            max_tokens=1850,
            temperature=0.20,
            timeout=45,
            json_mode=True,
            allowed_models=strict_models,
        )
        polished = _parse_json_object(raw_polish)
        if polished and isinstance(polished.get("beats"), list) and len(polished["beats"]) >= 6:
            dangling = any(
                re.search(r"\b(in|for|to|of|with|by|at)\.?$", str(x.get("voiceover_text") or "").strip().lower())
                for x in polished["beats"]
            )
            if not dangling:
                pkg_dict = polished
                print("  [StoryDirector] Pass 2 sarcastic polish succeeded.")

    if pkg_dict and isinstance(pkg_dict.get("beats"), list) and len(pkg_dict["beats"]) >= 6:
        try:
            default_ent = str(pkg_dict.get("primary_protagonist") or title_hint.split(":")[0]).strip()
            beats = [StoryBeatPlan(**_coerce_beat_dict(b, i, default_ent)) for i, b in enumerate(pkg_dict["beats"][:8], 1)]
            beats = _enforce_sequence_variety(beats)
            total_wc = sum(len(b.voiceover_text.split()) for b in beats)
            org_words = ("association", "fifa", "uefa", "knvb", "club", "committee", "council", "league", "board", "institution")
            for b in beats:
                if b.secondary_entity and any(ow in b.secondary_entity.lower() for ow in org_words):
                    b.secondary_entity = None
            bad_prim = any(any(ow in b.primary_entity.lower() for ow in org_words) for b in beats)
            dangling = any(re.search(r"\b(in|for|to|of|with|by|at)\.?$", b.voiceover_text.strip().lower()) for b in beats)
            if 68 <= total_wc <= 155 and not bad_prim and not dangling:
                hints = _build_default_phonetics()
                if isinstance(pkg_dict.get("pronunciation_hints"), dict):
                    for k, v in pkg_dict["pronunciation_hints"].items():
                        ks, vs = str(k).strip(), str(v).strip()
                        if ks and vs and "-" not in vs and ks.lower() != vs.lower():
                            hints[ks] = vs
                return StoryPackage(
                    story_id=_slugify(pkg_dict.get("story_id") or title_hint),
                    title=pkg_dict.get("title") or title_hint[:60],
                    topic=topic_or_url,
                    era=pkg_dict.get("era") or "Historical Archive",
                    logline=pkg_dict.get("logline") or title_hint,
                    primary_protagonist=pkg_dict.get("primary_protagonist") or beats[0].primary_entity,
                    pronunciation_hints=hints,
                    beats=beats,
                )
            print(f"[StoryDirector] Quality gate rejected LLM draft (words={total_wc}, bad_prim={bad_prim}) — using structured fallback.")
        except Exception as e:
            print(f"[StoryDirector] Schema assembly fallback note: {e}")

    # Deterministic witty fallback if LLM calls fail/rate-limit
    print("[StoryDirector] Using sarcastic structured 8-beat fallback package.")
    name_words = re.findall(r"[A-Za-zÀ-ÿ'-]+", title_hint.split(":")[0])
    main_ent = " ".join(name_words[:2]) if len(name_words) >= 2 else "Luis Suarez"
    if "suarez" not in topic_or_url.lower() and "suárez" not in topic_or_url.lower():
        raw_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", grounding_text or "") if 30 <= len(s.strip()) <= 180 and "WIKIPEDIA" not in s][:8]
        layouts = [
            "vox_25d_cutout", "newspaper_highlighter", "full_bleed_callout", "archival_pinboard",
            "kinetic_quote_card", "puppet_confrontation_25d", "tactile_timeline_card", "clean_editorial_epilogue",
        ]
        generic_lines = [
            f"A gifted footballer, famed for brilliance, and an occasional allergy to sensible decisions.",
            raw_sents[0] if len(raw_sents) > 0 else f"Trouble arrived sharply, leaving officials reaching straight for the rulebook.",
            raw_sents[1] if len(raw_sents) > 1 else f"Naturally, supporters insisted nothing improper had occurred on pitch whatsoever.",
            raw_sents[2] if len(raw_sents) > 2 else f"Slow-motion replays proved remarkably unforgiving under stadium floodlights that evening.",
            raw_sents[3] if len(raw_sents) > 3 else f"The disciplinary tribunal duly assembled with raised eyebrows and red ink.",
            raw_sents[4] if len(raw_sents) > 4 else f"Every rival dugout suddenly acquired heightened respect for personal space.",
            raw_sents[5] if len(raw_sents) > 5 else f"Several missed fixtures later, normal footballing service resumed without formal apology.",
            f"Proof, if any were needed, that genius rarely reads the conduct handbook.",
        ]
        gen_beats = _enforce_sequence_variety([
            StoryBeatPlan(
                beat_number=i + 1,
                layout_style=layouts[i],
                voiceover_text=" ".join(generic_lines[i].split()[:15]),
                visual_kicker=f"ARCHIVE 0{i + 1} // REPORT",
                visual_headline=f"{main_ent.upper()}: EXHIBIT {i + 1}",
                kinetic_word="ARCHIVE" if i == 0 else None,
                primary_entity=main_ent,
                search_query=f"{main_ent} football match action",
                fallback_query=f"{main_ent} portrait pitch",
                background_query="football stadium night floodlights empty",
                use_cutout=(layouts[i] not in ("full_bleed_callout", "archival_pinboard", "clean_editorial_epilogue")),
            )
            for i in range(8)
        ])
        return StoryPackage(
            story_id=_slugify(topic_or_url),
            title=title_hint[:60],
            topic=topic_or_url,
            era="Football Archive",
            logline=f"A brief British inspection of {main_ent}'s most eyebrow-raising evening.",
            primary_protagonist=main_ent,
            pronunciation_hints=_build_default_phonetics(),
            beats=gen_beats,
        )
    fallback_beats = _enforce_sequence_variety([
        StoryBeatPlan(
            beat_number=1,
            layout_style="vox_25d_cutout",
            banner_variant="a",
            camera_move="push_in",
            transition_in="cutout_zoom_punch",
            voiceover_text=f"A world-class striker, blessed with sublime technique, and an unexplained appetite for defenders.",
            visual_kicker="EXHIBIT A // THE APPETITE",
            visual_headline=f"{main_ent.upper()}: A TASTE TEST",
            kinetic_word="APPETITE",
            sub_caption="Prolific finisher, deeply curious menu choices",
            primary_entity=main_ent,
            search_query=f"{main_ent} Liverpool goal celebration solo",
            fallback_query=f"{main_ent} Uruguay match portrait",
            background_query="Anfield stadium floodlights night football",
            use_cutout=True,
        ),
        StoryBeatPlan(
            beat_number=2,
            layout_style="newspaper_highlighter",
            banner_variant="b",
            camera_move="drift_left",
            transition_in="jagged_paper_tear",
            voiceover_text="In twenty ten, Ajax captain Suárez sampled Otman Bakkal, earning seven games off.",
            visual_kicker="NOV 2010 // AMSTERDAM",
            visual_headline="AMSTERDAM HORS D'OEUVRE",
            kinetic_word="COURSE 1",
            primary_entity=main_ent,
            search_query=f"{main_ent} Ajax shirt action 2010",
            fallback_query=f"{main_ent} Ajax football",
            background_query="Johan Cruyff Arena Amsterdam stadium",
            use_cutout=True,
            newspaper_clip=NewspaperClipSpec(
                publication="De Telegraaf // KNVB Archive",
                date_text="NOVEMBER 2010",
                headline="SUAREZ HANDED SEVEN-MATCH BAN FOR BITING BAKKAL",
                quote_excerpt="The Ajax captain missed no goalscoring form, yet Dutch disciplinary chiefs still awarded seven quiet Sundays at home.",
                highlight_phrase="seven quiet Sundays",
            ),
            stamp_text="7-MATCH BAN",
        ),
        StoryBeatPlan(
            beat_number=3,
            layout_style="full_bleed_callout",
            banner_variant="c",
            camera_move="push_in",
            transition_in="match_cut_slide",
            voiceover_text="Naturally, Liverpool inspected his dental record and signed him immediately anyway.",
            visual_kicker="JANUARY 2011 // MERSEYSIDE",
            visual_headline="DUE DILIGENCE COMPLETE",
            sub_caption="Twenty-two million pounds well spent, mostly.",
            primary_entity=main_ent,
            search_query=f"{main_ent} Liverpool signing shirt Anfield",
            fallback_query=f"{main_ent} Liverpool match pitch",
            background_query="Anfield pitch crowd floodlights",
            use_cutout=False,
        ),
        StoryBeatPlan(
            beat_number=4,
            layout_style="archival_pinboard",
            banner_variant="d",
            camera_move="pull_out",
            transition_in="card_flip_3d",
            voiceover_text="Until twenty thirteen, when Chelsea's Branislav Ivanović kindly hosted lunch at Anfield.",
            visual_kicker="APRIL 21, 2013 // ANFIELD",
            visual_headline="TABLE FOR TWO AT ANFIELD",
            kinetic_word="LUNCH",
            sub_caption="Chelsea's right-back unexpectedly joins the tasting menu",
            primary_entity=main_ent,
            secondary_entity="Branislav Ivanovic",
            search_query="Luis Suarez Branislav Ivanovic Chelsea Liverpool 2013",
            fallback_query="Luis Suarez Liverpool vs Chelsea 2013",
            background_query="Anfield stadium matchday",
            use_cutout=False,
            tactical_reticle=TacticalReticleSpec(enabled=True, label="FOREARM TASTING", target_x_pct=52.0, target_y_pct=45.0),
        ),
        StoryBeatPlan(
            beat_number=5,
            layout_style="kinetic_quote_card",
            banner_variant="e",
            camera_move="drift_right",
            transition_in="jagged_paper_tear",
            voiceover_text="Ten matches suspended. Surely, you might think, he packed sandwiches for Brazil.",
            visual_kicker="FA DISCIPLINARY VERDICT",
            visual_headline="A TEN-GAME DIGESTIF",
            kinetic_word="10 GAMES",
            primary_entity=main_ent,
            search_query="Luis Suarez Liverpool frustrated match 2013",
            fallback_query="Luis Suarez Premier League action",
            background_query="Wembley Stadium arch pitch night floodlights",
            use_cutout=True,
            quote_card=QuoteCardSpec(
                quote="Inexplicable conduct, apparently unperturbed by prior dentistry warnings in Amsterdam.",
                attribution="FA PANEL SUMMARY // APRIL 2013",
            ),
            stamp_text="10-GAME BAN",
        ),
        StoryBeatPlan(
            beat_number=6,
            layout_style="puppet_confrontation_25d",
            banner_variant="a",
            camera_move="drift_left",
            transition_in="cutout_zoom_punch",
            voiceover_text="Not quite. Giorgio Chiellini's Italian shoulder proved simply irresistible under World Cup cameras.",
            visual_kicker="JUNE 2014 // NATAL, BRAZIL",
            visual_headline="A BRIEF ITALIAN LUNCH",
            kinetic_word="BRAZIL",
            primary_entity=main_ent,
            secondary_entity="Giorgio Chiellini",
            search_query="Luis Suarez Uruguay World Cup 2014 portrait",
            fallback_query="Giorgio Chiellini Italy national team 2014",
            background_query="Arena das Dunas Natal World Cup stadium",
            use_cutout=True,
            split_puppet=True,
            stamp_text="4-MONTH BAN",
        ),
        StoryBeatPlan(
            beat_number=7,
            layout_style="tactile_timeline_card",
            banner_variant="b",
            camera_move="drift_right",
            transition_in="card_flip_3d",
            voiceover_text="FIFA issued four months in exile, allowing Barcelona to politely rescue him from Merseyside.",
            visual_kicker="HAT-TRICK OF INCIDENTS",
            visual_headline="THREE CLUBS. ZERO REGRETS.",
            kinetic_word="RESCUED",
            primary_entity="Brendan Rodgers",
            search_query="Brendan Rodgers Liverpool manager touchline",
            fallback_query="Luis Suarez Barcelona Camp Nou 2014",
            background_query="Camp Nou stadium lights pitch",
            use_cutout=True,
            timeline_items=[
                TimelineItem(year="2010", event="AJAX vs PSV", detail="7 games off for sampling Bakkal"),
                TimelineItem(year="2013", event="LIVERPOOL vs CHELSEA", detail="10 games off via Ivanović's forearm"),
                TimelineItem(year="2014", event="URUGUAY vs ITALY", detail="4 months banished after Chiellini"),
            ],
        ),
        StoryBeatPlan(
            beat_number=8,
            layout_style="clean_editorial_epilogue",
            banner_variant="c",
            camera_move="push_in",
            transition_in="match_cut_slide",
            voiceover_text="A year later he won Barcelona's treble. Apparently midfielders aren't nearly as filling.",
            visual_kicker="2015 // CAMP NOU EPILOGUE",
            visual_headline="CHAMPIONS OF EUROPE",
            sub_caption="Banned in June. Lifting the European treble by May.",
            primary_entity=main_ent,
            search_query="Luis Suarez Barcelona Champions League trophy 2015",
            fallback_query="Luis Suarez FC Barcelona celebration",
            background_query="Camp Nou Champions League night",
            use_cutout=False,
        ),
    ])
    return StoryPackage(
        story_id=_slugify(topic_or_url),
        title=title_hint[:60],
        topic=topic_or_url,
        era="2010 — 2015",
        logline="Three baffling bites, twenty-six missed games, and somehow a European treble.",
        primary_protagonist=main_ent,
        pronunciation_hints=_build_default_phonetics(),
        beats=fallback_beats,
    )
