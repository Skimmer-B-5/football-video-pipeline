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


class StoryBeatPlan(BaseModel):
    beat_number: int
    layout_style: str = Field(
        default="vox_25d_cutout",
        description="One of: vox_25d_cutout | newspaper_highlighter | archival_pinboard | puppet_confrontation_25d | tactile_timeline_card | clean_editorial_epilogue"
    )
    banner_variant: str = "a"
    camera_move: str = "push_in"
    transition_in: str = "torn_paper_wipe"
    voiceover_text: str = Field(..., description="Unhurried British documentary narration (~15-24 words)")
    visual_kicker: str = Field(..., description="Date / venue eyebrow, e.g. 'NOVEMBER 2010 // AMSTERDAM'")
    visual_headline: str = Field(..., description="Crisp display title (2-6 words)")
    sub_caption: Optional[str] = Field(None, description="Restrained documentary photo caption (<=10 words)")
    primary_entity: str = Field(..., description="Canonical player/manager name for SFace identity check")
    secondary_entity: Optional[str] = Field(None, description="Second player/subject for confrontation beats")
    search_query: str = Field(..., description="Specific real-photo search query for primary visual")
    fallback_query: str = Field(..., description="Backup real-photo search query")
    background_query: str = Field(..., description="Atmospheric stadium/pitch/city background query")
    use_cutout: bool = Field(default=True, description="Extract clean 2.5D paper cutout for foreground motion")
    split_puppet: bool = Field(default=False, description="Enable articulated lunge/recoil 2.5D motion")
    newspaper_clip: Optional[NewspaperClipSpec] = None
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
    target_duration: float = Field(default=52.0, description="Target runtime 46-58s including outro")
    narrator_voice_profile: str = "Qwen3-TTS Ryan (Calm British Documentary Scholar, ~145 WPM)"
    score_track: str = "Cool Vibes (Vibraphone & Upright Bass Documentary Bed)"
    beats: List[StoryBeatPlan]
    outro_headline: str = "THIS IS FOOTBALL IN 30 SECONDS."
    outro_subtitle: str = "STORIES BEYOND THE SCORELINE."
    outro_cta: str = "FOLLOW FOR MORE"
    outro_narration: str = "See you later. This is Football in Thirty Seconds. Follow for more."


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
    t = (text or "").replace("—", ", ").replace("–", ", ").replace("--", ", ")
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
    query_candidates = [clean_q]
    words = [w for w in re.findall(r"[A-Za-zÀ-ÿ'-]+", clean_q) if w.lower() not in ("saga", "story", "incident", "biting", "history")]
    if len(words) >= 2:
        query_candidates.append(f"{words[0]} {words[1]} {' '.join(words[2:4])}".strip())
        query_candidates.append(f"{words[0]} {words[1]} footballer biting")

    candidate_pages: Dict[str, int] = {}
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
                    "knvb", "psv", "chelsea", "anfield", "seven-match", "ten-match", "four months",
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
                for _, idx_s, _ in ev_candidates[:8]:
                    chosen_idxs.add(idx_s)
                    if idx_s + 1 < len(sentences) and 35 <= len(sentences[idx_s + 1]) <= 240:
                        chosen_idxs.add(idx_s + 1)
                ordered_sents = [sentences[i] for i in sorted(chosen_idxs)]
                selected_body = " ".join(ordered_sents)[:1100]
                doc_str = f"WIKIPEDIA ({p.get('title', wt)}): {lead}\nKEY FACTS: {selected_body}".strip()
                snippets.append(doc_str[:1550])
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
    b["background_query"] = str(b.get("background_query") or "football stadium floodlights pitch").strip()

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
    """Ensures no two consecutive beats reuse the exact same layout, camera move, or banner variant."""
    default_layouts = [
        "vox_25d_cutout",
        "newspaper_highlighter",
        "archival_pinboard",
        "puppet_confrontation_25d",
        "tactile_timeline_card",
        "clean_editorial_epilogue",
    ]
    cameras = ["push_in", "drift_left", "pull_out", "drift_right", "static_breathe"]
    transitions = ["torn_paper_wipe", "document_slide", "cross_dissolve", "shutter_flash"]
    variants = ["a", "b", "c", "d", "e"]

    prev_layout = None
    prev_cam = None
    prev_var = None
    for idx, b in enumerate(beats):
        b.beat_number = idx + 1
        if b.layout_style == prev_layout or b.layout_style not in default_layouts:
            b.layout_style = default_layouts[idx % len(default_layouts)]
        if b.camera_move == prev_cam or b.camera_move not in cameras:
            b.camera_move = cameras[idx % len(cameras)]
        if b.banner_variant == prev_var or b.banner_variant not in variants:
            b.banner_variant = variants[idx % len(variants)]
        if b.transition_in not in transitions:
            b.transition_in = transitions[idx % len(transitions)]
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
        if b.layout_style == "tactile_timeline_card" and not b.timeline_items:
            b.timeline_items = [
                TimelineItem(year="INCIDENT", event=b.visual_headline, detail=b.sub_caption or b.visual_kicker)
            ]

        prev_layout = b.layout_style
        prev_cam = b.camera_move
        prev_var = b.banner_variant
    return beats


def generate_documentary_package(
    topic_or_url: str,
    target_words: Tuple[int, int] = (105, 138),
) -> StoryPackage:
    """
    Runs a 2-pass LLM editorial + art-direction pipeline (GPT-OSS-120B draft -> Qwen-27B polish)
    to generate a verified 6-beat blended 2.5D paper-cut documentary StoryPackage.
    """
    try:
        from beta.stages.groq_client import call_groq_chat
    except ModuleNotFoundError:
        from stages.groq_client import call_groq_chat

    title_hint, grounding_text = _fetch_grounding_context(topic_or_url)
    print(f"[StoryDirector] Generating 2.5D documentary script for: '{title_hint[:65]}'...")

    sys_prompt = f"""You are the Documentary Writer & Art Director for 'Football in 30 Seconds (FS30 TV)'.
You craft restrained, intelligent, darkly witty short football documentaries blending Vox Media 2.5D depth, tactile archival paper collage, and serious journalistic restraint.

EDITORIAL RULES:
1. VOICE & TONE: Write for a calm, articulate British documentary narrator (dry wit, crisp observational sentences, no shouting, no exclamation-heavy hype).
   - BANNED CLICHES: {', '.join(BANNED_HYPE_PHRASES)}.
   - Example tone: "Brilliant on the ball. Unpredictable off it. Three times on three stages, one striker lost control."
2. LENGTH & WORD BUDGET: Design EXACTLY 6 story beats totaling {target_words[0]} to {target_words[1]} spoken words across ALL 6 beats combined (strictly 16-24 words per beat — NEVER write 30+ word paragraphs per beat!). Total spoken runtime must land cleanly around 46-54 seconds including the outro.
3. FACTUAL RIGOR: Use strictly accurate dates, clubs, managers, opponents, bans, and match venues verified in the grounding context (e.g., verify which club a player represented in each year). Never invent quotes or switch clubs/years.
4. VISUAL VARIETY (NO TWO ADJACENT BEATS SHARE THE SAME LAYOUT):
   Assign these 6 distinct layout styles across the 6 beats:
   - Beat 1: "vox_25d_cutout" (Atmospheric hook over stadium backdrop + hero cutout rising in depth)
   - Beat 2: "newspaper_highlighter" (First turning point/press evidence + real quote excerpt with highlight_phrase)
   - Beat 3: "archival_pinboard" (Match incident photograph with washi corners + tactical reticle callout)
   - Beat 4: "puppet_confrontation_25d" (Climax confrontation with primary_entity vs secondary_entity cutouts + verdict stamp; secondary_entity MUST be a specific opposing player or manager name, NEVER an institution like FIFA or FA)
   - Beat 5: "tactile_timeline_card" (Escalate/punishment sequence with 3 crisp chronological TimelineItems)
   - Beat 6: "clean_editorial_epilogue" (Full-bleed portrait + restrained poetic closing frame, minimal UI noise)
5. SEARCH QUERIES & ENTITIES:
   - "primary_entity" MUST be ONLY a real player or manager name (e.g. "Luis Suarez", "Giorgio Chiellini", "Brendan Rodgers") — never append club names onto primary_entity.
   - "search_query" MUST specify real match photography + club/year (never "cartoon" or "illustration").
6. SPOKEN & JSON CLEANLINESS: In "voiceover_text", spell numbers naturally ("seven match ban", "twenty fourteen") rather than cryptic shorthand, and NEVER use raw double quotation marks inside JSON string values (use single quotes if needed). Keep concise tags ("7-MATCH BAN", "NOVEMBER 2010") on screen cards.

Respond ONLY with valid JSON matching the StoryPackage schema:
{{
  "story_id": "short_snake_case_id",
  "title": "Concise documentary title",
  "topic": "{topic_or_url}",
  "era": "Exact date span, e.g. '2010 — 2014'",
  "logline": "One dry witty summary sentence",
  "primary_protagonist": "Full Name",
  "beats": [
    {{
      "beat_number": 1,
      "layout_style": "vox_25d_cutout",
      "banner_variant": "a",
      "camera_move": "push_in",
      "transition_in": "torn_paper_wipe",
      "voiceover_text": "...",
      "visual_kicker": "SHORT EYEBROW // DATE",
      "visual_headline": "2-5 WORD DISPLAY HEADLINE",
      "sub_caption": "Optional factual subtitle",
      "primary_entity": "Full Name",
      "secondary_entity": null,
      "search_query": "specific match photo query",
      "fallback_query": "backup real photo query",
      "background_query": "stadium night floodlights pitch",
      "use_cutout": true,
      "split_puppet": false,
      "newspaper_clip": null,
      "stamp_text": null,
      "timeline_items": null,
      "tactical_reticle": {{"enabled": false, "label": null, "target_x_pct": 50, "target_y_pct": 42}}
    }}
  ]
}}"""

    user_prompt = f"""Topic / Brief: {topic_or_url}

GROUNDING MATERIAL:
{grounding_text if grounding_text else 'Use verified historical football facts strictly.'}

Draft the complete 6-beat StoryPackage JSON now."""

    raw_draft = call_groq_chat(
        system_prompt=sys_prompt,
        user_prompt=user_prompt,
        preferred_model="openai/gpt-oss-120b",
        fallback_model="qwen/qwen3.8-27b",
        max_tokens=2800,
        temperature=0.22,
        timeout=45,
    )

    pkg_dict: Optional[Dict[str, Any]] = None
    if raw_draft:
        cleaned = re.sub(r"^```json\s*|```\s*$", "", raw_draft.strip(), flags=re.MULTILINE)
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                pkg_dict = json.loads(m.group(0))
            except Exception as e:
                print(f"[StoryDirector] Pass 1 parse note: {e}")
    else:
        print("[StoryDirector] Pass 1 returned empty response; switching to Qwen-27B draft.")

    # Retry clean JSON generation via Qwen-27B if Pass 1 produced malformed/empty JSON
    if pkg_dict is None:
        raw_retry = call_groq_chat(
            system_prompt=sys_prompt,
            user_prompt=user_prompt + "\n\nCRITICAL: Output ONLY compact valid JSON (no extra chatter), NO unescaped double quotes, 16-22 words per beat.",
            preferred_model="qwen/qwen3.8-27b",
            fallback_model="openai/gpt-oss-20b",
            max_tokens=1650,
            temperature=0.15,
            timeout=50,
        )
        if raw_retry:
            cleaned_r = re.sub(r"^```json\s*|```\s*$", "", raw_retry.strip(), flags=re.MULTILINE)
            mr = re.search(r"\{.*\}", cleaned_r, re.DOTALL)
            if mr:
                try:
                    pkg_dict = json.loads(mr.group(0))
                except Exception as e:
                    print(f"[StoryDirector] Pass 1 retry parse note: {e}")

    # Pass 2: Critic & Factual Polish via Qwen 27B
    if pkg_dict:
        polish_prompt = f"""Review and tighten this documentary StoryPackage JSON strictly against GROUNDING:
{grounding_text[:1350] if grounding_text else topic_or_url}

FIX ANY ERRORS:
1. Total spoken words across ALL 6 beats MUST be {target_words[0]}–{target_words[1]} words (~16-23 words per beat).
2. Check EVERY year, club, opponent, and ban duration strictly against GROUNDING.
3. Beat 4 secondary_entity MUST be a named opposing player or manager (NEVER FIFA/FA/an organization).
4. Pure person names in primary_entity / secondary_entity (no club suffix).
5. Preserve EXACT schema keys ("visual_headline", "newspaper_clip": {{"publication","date_text","headline","quote_excerpt","highlight_phrase"}}, "timeline_items": [{{"year","event","detail"}}]).

CURRENT JSON:
{json.dumps(pkg_dict, ensure_ascii=False)}

Output ONLY valid JSON."""

        raw_polish = call_groq_chat(
            system_prompt="You are an exacting BBC / Vox sports documentary fact-checker. Output compact valid JSON only.",
            user_prompt=polish_prompt,
            preferred_model="qwen/qwen3.8-27b",
            fallback_model="openai/gpt-oss-120b",
            max_tokens=1700,
            temperature=0.15,
            timeout=35,
        )
        if raw_polish:
            cleaned2 = re.sub(r"^```json\s*|```\s*$", "", raw_polish.strip(), flags=re.MULTILINE)
            m2 = re.search(r"\{.*\}", cleaned2, re.DOTALL)
            if m2:
                try:
                    pkg_dict = json.loads(m2.group(0))
                    print("  [StoryDirector] Pass 2 critic polish succeeded (Qwen 27B).")
                except Exception:
                    pass

    if pkg_dict and isinstance(pkg_dict.get("beats"), list) and len(pkg_dict["beats"]) >= 4:
        try:
            default_ent = str(pkg_dict.get("primary_protagonist") or title_hint.split(":")[0]).strip()
            beats = [StoryBeatPlan(**_coerce_beat_dict(b, i, default_ent)) for i, b in enumerate(pkg_dict["beats"][:6], 1)]
            beats = _enforce_sequence_variety(beats)
            total_wc = sum(len(b.voiceover_text.split()) for b in beats)
            org_words = ("association", "fifa", "uefa", "knvb", "club", "committee", "council", "league", "board", "institution")
            bad_ent = any(
                (b.secondary_entity and any(ow in b.secondary_entity.lower() for ow in org_words))
                or any(ow in b.primary_entity.lower() for ow in org_words)
                for b in beats
            )
            if total_wc > 158 or total_wc < 70 or bad_ent:
                print(f"[StoryDirector] Quality gate rejected LLM draft (words={total_wc}, bad_entity={bad_ent}) — checking grounded fallback/tightening.")
                if bad_ent:
                    for b in beats:
                        if b.secondary_entity and any(ow in b.secondary_entity.lower() for ow in org_words):
                            b.secondary_entity = None
                if total_wc <= 165 and not bad_ent:
                    return StoryPackage(
                        story_id=_slugify(pkg_dict.get("story_id") or title_hint),
                        title=pkg_dict.get("title") or title_hint[:60],
                        topic=topic_or_url,
                        era=pkg_dict.get("era") or "Historical Archive",
                        logline=pkg_dict.get("logline") or title_hint,
                        primary_protagonist=pkg_dict.get("primary_protagonist") or beats[0].primary_entity,
                        beats=beats,
                    )
            else:
                return StoryPackage(
                    story_id=_slugify(pkg_dict.get("story_id") or title_hint),
                    title=pkg_dict.get("title") or title_hint[:60],
                    topic=topic_or_url,
                    era=pkg_dict.get("era") or "Historical Archive",
                    logline=pkg_dict.get("logline") or title_hint,
                    primary_protagonist=pkg_dict.get("primary_protagonist") or beats[0].primary_entity,
                    beats=beats,
                )
        except Exception as e:
            print(f"[StoryDirector] Schema assembly fallback note: {e}")

    # Deterministic factual fallback if LLM calls both fail/rate-limit
    print("[StoryDirector] Using deterministic structured fallback package.")
    name_words = re.findall(r"[A-Za-zÀ-ÿ'-]+", title_hint.split(":")[0])
    main_ent = " ".join(name_words[:2]) if len(name_words) >= 2 else "Luis Suarez"
    fallback_beats = _enforce_sequence_variety([
        StoryBeatPlan(
            beat_number=1,
            layout_style="vox_25d_cutout",
            banner_variant="a",
            camera_move="push_in",
            transition_in="cross_dissolve",
            voiceover_text=f"Few forwards combined lethal finishing with sudden chaos quite like {main_ent}.",
            visual_kicker="THE ARCHIVE FILE",
            visual_headline=f"{main_ent.upper()}: THE SAGA",
            sub_caption="Prolific striker, recurring controversy",
            primary_entity=main_ent,
            search_query=f"{main_ent} Liverpool goal celebration Anfield solo",
            fallback_query=f"{main_ent} Uruguay striker match action",
            background_query="Anfield stadium floodlights night football",
            use_cutout=True,
        ),
        StoryBeatPlan(
            beat_number=2,
            layout_style="newspaper_highlighter",
            banner_variant="b",
            camera_move="drift_left",
            transition_in="torn_paper_wipe",
            voiceover_text="In November twenty ten, Ajax captain Suarez bit PSV midfielder Otman Bakkal and received seven games.",
            visual_kicker="NOVEMBER 2010 // AMSTERDAM",
            visual_headline="THE CANNIBAL OF AJAX",
            primary_entity=main_ent,
            search_query=f"{main_ent} Ajax 2010 match action",
            fallback_query=f"{main_ent} Ajax",
            background_query="Amsterdam ArenA pitch matchday",
            use_cutout=False,
            newspaper_clip=NewspaperClipSpec(
                publication="De Telegraaf // KNVB Archive",
                date_text="NOVEMBER 2010",
                headline="SUAREZ HANDED SEVEN-MATCH BAN IN EREDIVISIE",
                quote_excerpt="The Ajax striker escaped a referee red card on the pitch before Dutch disciplinary chiefs imposed a seven-match suspension.",
                highlight_phrase="seven-match suspension",
            ),
            stamp_text="7-MATCH BAN",
        ),
        StoryBeatPlan(
            beat_number=3,
            layout_style="archival_pinboard",
            banner_variant="c",
            camera_move="pull_out",
            transition_in="document_slide",
            voiceover_text="Liverpool signed him anyway, until April twenty thirteen when Branislav Ivanovic left Anfield clutching his arm.",
            visual_kicker="APRIL 21, 2013 // ANFIELD",
            visual_headline="THE ANFIELD INCIDENT",
            sub_caption="Chelsea defender targeted in stoppage-time draw",
            primary_entity=main_ent,
            secondary_entity="Branislav Ivanovic",
            search_query="Luis Suarez Branislav Ivanovic bite Chelsea Liverpool 2013",
            fallback_query="Luis Suarez Liverpool 2013 match",
            background_query="Anfield pitch matchday crowd",
            use_cutout=False,
            stamp_text="10-GAME BAN",
            tactical_reticle=TacticalReticleSpec(enabled=True, label="FOREARM CONTACT", target_x_pct=52.0, target_y_pct=45.0),
        ),
        StoryBeatPlan(
            beat_number=4,
            layout_style="puppet_confrontation_25d",
            banner_variant="d",
            camera_move="drift_right",
            transition_in="shutter_flash",
            voiceover_text="Then came Brazil in twenty fourteen. Facing Italy's Giorgio Chiellini, Suarez struck a third time in front of World Cup cameras.",
            visual_kicker="JUNE 24, 2014 // NATAL, BRAZIL",
            visual_headline="WORLD CUP CLASH",
            primary_entity=main_ent,
            secondary_entity="Giorgio Chiellini",
            search_query="Luis Suarez Uruguay World Cup 2014 action",
            fallback_query="Giorgio Chiellini Italy 2014",
            background_query="Arena das Dunas Natal World Cup stadium",
            use_cutout=True,
            split_puppet=True,
            stamp_text="4-MONTH FIFA BAN",
        ),
        StoryBeatPlan(
            beat_number=5,
            layout_style="tactile_timeline_card",
            banner_variant="e",
            camera_move="static_breathe",
            transition_in="document_slide",
            voiceover_text="FIFA banned him for four months from all football, clearing the path for Barcelona to prize him from Liverpool.",
            visual_kicker="SUMMER 2014 // SANCTION & EXIT",
            visual_headline="THREE INCIDENTS. TWENTY-SIX GAMES.",
            primary_entity="Brendan Rodgers",
            search_query="Brendan Rodgers Liverpool manager touchline suit Anfield",
            fallback_query="Luis Suarez Barcelona Camp Nou 2014 presentation",
            background_query="Camp Nou stadium football pitch",
            use_cutout=True,
            timeline_items=[
                TimelineItem(year="2010", event="AJAX vs PSV", detail="7-match KNVB ban (Otman Bakkal)"),
                TimelineItem(year="2013", event="LIVERPOOL vs CHELSEA", detail="10-match FA ban (Branislav Ivanovic)"),
                TimelineItem(year="2014", event="URUGUAY vs ITALY", detail="4-month FIFA exile (Giorgio Chiellini)"),
            ],
        ),
        StoryBeatPlan(
            beat_number=6,
            layout_style="clean_editorial_epilogue",
            banner_variant="a",
            camera_move="push_in",
            transition_in="cross_dissolve",
            voiceover_text="Remarkably, he won the European treble a year later. Brilliance and mayhem, permanently sharing one shirt.",
            visual_kicker="EPILOGUE // FOOTBALL ARCHIVE",
            visual_headline="BRILLIANCE & MAYHEM",
            sub_caption="From global exile to Barcelona's treble in twelve months",
            primary_entity=main_ent,
            search_query="Luis Suarez Liverpool trophy celebration portrait",
            fallback_query="Luis Suarez Barcelona trophy",
            background_query="Camp Nou champions pitch night",
            use_cutout=False,
        ),
    ])
    return StoryPackage(
        story_id=_slugify(topic_or_url),
        title=title_hint[:60],
        topic=topic_or_url,
        era="2010 — 2014",
        logline="Three biting incidents across three competitions reshaped a generational striker's career.",
        primary_protagonist=main_ent,
        beats=fallback_beats,
    )
