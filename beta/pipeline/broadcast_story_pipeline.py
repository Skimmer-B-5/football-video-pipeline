"""
beta/pipeline/broadcast_story_pipeline.py
Generalized 1990s Football Broadcast Pipeline Engine.
Accepts any StoryDossier, processes it through the audited Beta V7.1 architecture,
and produces a 1080x1920 30fps retro-styled television short.
"""

import os
import sys
import json
import time
import shutil
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.pipeline.neural_instructions import (
    StoryDossier,
    SCREENPLAY_SYSTEM_PROMPT,
    VISUAL_ARCHITECT_PROMPT,
    VOICE_ARCHITECTURE_SPEC,
    CRT_RENDERING_SPEC,
    CONFIGURED_LLM_MODEL,
    CONFIGURED_LLM_FALLBACK,
    CONFIGURED_VLM_MODEL
)
from beta.stages.story_workspace_manager import StoryWorkspace
from beta.stages.telegram_bot import TelegramBotClient, get_env_credentials
from beta.stages.production_voice_engine import ProductionVoiceEngine
from beta.stages.asset_ledger import StoryAssetLedger

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_audio_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def build_subtitles_from_scenes(
    scenes_props: List[Dict[str, Any]],
    audio_scenes: List[Dict[str, Any]],
    chunk_size: int = 4
) -> List[Dict[str, Any]]:
    """Builds speech-aligned subtitle cues from compiled scene props and audio manifests."""
    audio_map = {a["scene_id"]: a for a in audio_scenes}
    subtitles: List[Dict[str, Any]] = []
    current_f = 0
    cue_id = 1

    for sc_prop in scenes_props:
        sid = sc_prop.get("scene_id", "")
        sc_audio = audio_map.get(sid, {})
        dur_f = int(sc_prop.get("durationInFrames", sc_audio.get("duration_frames", 0)))

        if sid != "outro" and sc_prop.get("role") != "outro":
            onset_f = int(sc_audio.get("speech_onset_frame", 3))
            offset_f = int(sc_audio.get("speech_offset_frame", max(onset_f + 15, dur_f - 4)))
            offset_f = min(dur_f, max(onset_f + 1, offset_f))
            speech_window_f = max(15, offset_f - onset_f)

            text = (sc_prop.get("narration") or sc_prop.get("spoken_narration") or "").strip()
            words = text.split()
            chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)] if words else []
            total_chars = sum(len(c) for c in chunks) or 1
            chunk_cursor_f = current_f + onset_f

            for c_idx, chunk in enumerate(chunks):
                chunk_dur_f = max(8, int(round((len(chunk) / float(total_chars)) * speech_window_f)))
                if c_idx == len(chunks) - 1:
                    end_f = current_f + offset_f
                else:
                    end_f = min(current_f + offset_f, chunk_cursor_f + chunk_dur_f)
                if end_f <= chunk_cursor_f:
                    end_f = min(current_f + dur_f, chunk_cursor_f + 8)

                subtitles.append({
                    "id": cue_id,
                    "start_frame": chunk_cursor_f,
                    "end_frame": end_f,
                    "text": chunk.upper()
                })
                cue_id += 1
                chunk_cursor_f = end_f

        current_f += dur_f

    return subtitles


_SPOKEN_NUM_WORDS = {
    "5": "five", "10": "ten", "12": "twelve", "15": "fifteen", "20": "twenty",
    "25": "twenty five", "30": "thirty", "35": "thirty five", "40": "forty",
    "45": "forty five", "50": "fifty", "55": "fifty five", "60": "sixty",
    "65": "sixty five", "70": "seventy", "75": "seventy five", "80": "eighty",
    "90": "ninety", "100": "one hundred", "120": "one hundred twenty", "150": "one hundred fifty"
}


def normalize_spoken_broadcast_text(text: str) -> str:
    """Normalizes currencies, shorthand (£30M -> thirty million pounds), and dashes for natural TTS cadence."""
    import re
    out = (text or "").replace("—", " ").replace("–", " ").replace("--", " ")
    def _curr_repl(m):
        sym, num_str, scale = m.group(1), m.group(2), (m.group(3) or "").lower()
        unit = "pounds" if sym == "£" else ("euros" if sym == "€" else "dollars")
        word_num = _SPOKEN_NUM_WORDS.get(num_str, num_str)
        if scale.startswith("m"):
            return f"{word_num} million {unit}"
        if scale.startswith("k"):
            return f"{word_num} thousand {unit}"
        return f"{word_num} {unit}"
    out = re.sub(r"([£€$])\s*(\d+)\s*([mMkK]|million|thousand)?\b", _curr_repl, out)
    return re.sub(r"\s+", " ", out).strip()


def _get_category_beats_guidance(category: str) -> str:
    cat = (category or "transfer_rumour").lower()
    mapping = {
        "managerial_change": "Focus beats on S01 boardroom storm (conceal name), S02 coach reveal, S03 dressing-room/results cause, S04 board verdict & terms, S05 club statement/candidates, S06 rival reaction, S07 stay vs new appointment dilemma.",
        "injury_crisis": "Focus beats on S01 locker-room shock (conceal name), S02 player injury reveal, S03 scan/recovery timeline, S04 missed key fixtures, S05 manager tactical headache, S06 replacement options, S07 can they survive without him dilemma.",
        "confirmed_deal": "Focus beats on S01 secret framework done (conceal name), S02 official unveil reveal, S03 confirmed club agreement, S04 reported fee & contract length, S05 selling/buying manager tactical plan, S06 fan reaction, S07 instant starter or risky gamble dilemma.",
        "contract_negotiation": "Focus beats on S01 club dressing-room pressure (conceal name), S02 star identity & expiry tension, S03 rival suitors circling, S04 contract/salary gap, S05 manager stance, S06 player's demands, S07 sign extension or leave on transfer dilemma.",
    }
    return mapping.get(
        cat,
        "Focus beats on S01 high-stakes club tension (conceal name), S02 dramatic player reveal, S03 suitor move, S04 financial valuation, S05 managerial resistance, S06 squad/player reality, S07 stay vs switch closing dilemma."
    )


class GeneralizedBroadcastPipeline:
    def __init__(self, dossier: StoryDossier, run_id: str = "run_v7_1"):
        self.dossier = dossier
        self.run_id = run_id
        self.ws = StoryWorkspace(dossier.story_id, run_id)
        self.fps = 30.0

    def generate_screenplay(self, user_directive: Optional[str] = None, prior_script: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates or rewrites the 5-Beat Dual-Script following the locked neural screenplay rules.
        When user_directive is provided, Groq LLM directly rebuilds the broadcast narrative
        around the user's critique/instructions rather than cutting and pasting.
        """
        from stages.fact_checker import FactChecker
        self.dossier = FactChecker.audit_and_enrich_dossier(self.dossier)
        d = self.dossier

        print(f"\n[Stage 1] Generating Screenplay for: {self.dossier.story_id} (directive: {user_directive[:40] if user_directive else 'None'})")
        
        # 1. Try LLM generation if directive provided or for dynamic initial generation
        try:
            import re
            from stages.groq_client import call_groq_chat
            from stages.editorial_policy import OpeningSecrecyValidator, BANNED_CLICHES
            from stages.fact_checker import FactChecker

            category = getattr(d, "story_category", "transfer_rumour") or "transfer_rumour"
            cat_guide = _get_category_beats_guidance(category)
            blocked_names = (
                FactChecker.get_obsolete_managers(d.current_club) +
                FactChecker.get_obsolete_managers(d.pursuing_club)
            )
            article_ctx = (getattr(d, "raw_article_text", "") or "").strip()[:2200]

            sys_prompt = f"""You are an elite British sports news television editor producing a high-impact 8-scene screenplay (7 story scenes + 1 ending card outro) for a 30-second broadcast short.

EDITORIAL, GROUNDING & VOCAL MANDATES:
1. STORY CATEGORY ({category.upper()}): {cat_guide}
2. RUNTIME WORD BUDGET: 55–66 spoken words TOTAL across S01–S07 (8–10 words per beat). Fast explosive live newsroom punch.
3. NATURAL BROADCAST CONJUNCTION FLOW (MANDATORY):
   - S01–S07 MUST flow as ONE urgent connected breaking-news bulletin, NOT choppy standalone robot headlines!
   - Link S02–S07 naturally using spoken conjunctions ("Because", "And now", "While", "Even though", "Yet", "Meanwhile", "So").
   - NEVER tack weak filler ("...now.", "...today.") onto the end of sentences. Vary phrasing naturally!
4. MANDATORY S01 SECRECY (MINIMUM 4.0s ANONYMITY):
   - S01 MUST NOT name the protagonist in spoken_narration, on_screen.headline, on_screen.subheadline, or on_screen.kicker!
5. SPOKEN NUMBER CLARITY & ENERGY FOR VOICE ENGINE:
   - Inside "spoken_narration", write currencies & shorthand in clean spoken words ("thirty million pounds", NOT "£30M" or "30m"). Keep crisp symbols ("£30M") inside "on_screen" ONLY.
   - NO em-dashes (—), NO hyphens as pauses, ZERO clickbait clichés ("the catch?", "bombshell", "changes everything", "you won't believe").
6. STRICT FACTUAL ACCURACY: Use ONLY facts explicitly stated in the dossier & source article below. NEVER invent "free agent" claims, contract years, fees, or quotes unless written in the article, and NEVER mention obsolete managers ({', '.join(blocked_names) if blocked_names else 'none'}).
7. TELEMETRY CALLOUTS: On S03 or S04, when concrete fees, durations, or clauses exist in the article/dossier, set concise "data_callout" (e.g. "£30M + £5M ADD-ONS") and optionally structured "infographic" summary.
8. outro: EXACTLY "This is football in thirty seconds. Follow for daily transfer updates."

Output ONLY valid JSON matching this schema:
{{
  "scenes": [
    {{
      "scene_id": "S01",
      "spoken_narration": "...",
      "transition_hint": "clean_hard_cut",
      "on_screen": {{"kicker": "TRANSFER WATCH", "headline": "UPPERCASE TITLE (NO PLAYER NAME)", "subheadline": "...", "status_badge": "DEVELOPING", "data_callout": null}}
    }},
    {{
      "scene_id": "S02",
      "spoken_narration": "And ...",
      "transition_hint": "camera_flash",
      "on_screen": {{"kicker": "REVEAL", "headline": "...", "subheadline": "...", "status_badge": "REVEALED", "data_callout": null}}
    }},
    {{
      "scene_id": "S03",
      "spoken_narration": "...",
      "transition_hint": "whip_pan",
      "on_screen": {{"kicker": "THE MOVE", "headline": "...", "subheadline": "...", "status_badge": "REPORTED", "data_callout": null}}
    }},
    {{
      "scene_id": "S04",
      "spoken_narration": "...",
      "transition_hint": "document_snap",
      "on_screen": {{"kicker": "THE FIGURES", "headline": "...", "subheadline": "...", "status_badge": "UNAGREED", "data_callout": "SHORT STAT OR FEE"}}
    }},
    {{
      "scene_id": "S05",
      "spoken_narration": "...",
      "transition_hint": "shutter_wipe",
      "on_screen": {{"kicker": "CLUB STANCE", "headline": "...", "subheadline": "...", "status_badge": "DEVELOPING", "data_callout": null}}
    }},
    {{
      "scene_id": "S06",
      "spoken_narration": "...",
      "transition_hint": "cross_dissolve",
      "on_screen": {{"kicker": "THE REALITY", "headline": "...", "subheadline": "...", "status_badge": "OFFICIAL", "data_callout": null}}
    }},
    {{
      "scene_id": "S07",
      "spoken_narration": "... or ...?",
      "transition_hint": "whip_pan",
      "on_screen": {{"kicker": "THE VERDICT", "headline": "...", "subheadline": "...", "status_badge": "EDITORIAL", "data_callout": null}}
    }},
    {{
      "scene_id": "outro",
      "spoken_narration": "This is football in thirty seconds. Follow for daily transfer updates.",
      "on_screen": {{"headline": "THIS IS FOOTBALL IN 30 SECONDS", "kicker": "FOLLOW FOR MORE"}}
    }}
  ]
}}"""
            pursuing_mgr = getattr(d, "pursuing_manager", "") or "Unknown"
            curr_std = getattr(d, "current_stadium", "") or ""
            suitor_std = getattr(d, "pursuing_stadium", "") or ""
            fan_reactions = getattr(d, "fan_reactions", []) or []

            user_prompt = f"""STORY HEADLINE: {d.main_headline}
CATEGORY: {category}
PROTAGONIST: {d.protagonist_name}
CURRENT CLUB: {d.current_club}{f" (Stadium: {curr_std})" if curr_std else ""}
PURSUING CLUB / RIVAL: {d.pursuing_club} (Current Manager: {pursuing_mgr}{f", Stadium: {suitor_std}" if suitor_std else ""})
CURRENT MANAGER: {d.current_manager}
REPORTED FEE: {d.reported_base_fee} (Bonuses: {d.reported_bonuses})
COMPLICATION: {d.complication}
SOURCES: {', '.join(d.reporting_sources or ['Football Desk'])}
"""
            if article_ctx:
                user_prompt += f"\nFULL VERIFIED SOURCE ARTICLE CONTEXT:\n{article_ctx}\n"
            if fan_reactions:
                user_prompt += "\nVERIFIED FAN REACTIONS (Reddit/Fans - capture genuine sentiment, do NOT fabricate quotes):\n"
                for fr in fan_reactions[:4]:
                    user_prompt += f"- {fr}\n"
            if prior_script:
                user_prompt += f"\nPREVIOUS SCRIPT DRAFT:\n{prior_script}\n"
            if user_directive:
                user_prompt += f"\nUSER DIRECTIVE & EDITORIAL CRITIQUE:\n\"{user_directive}\"\n"
                user_prompt += "Rebuild the entire 8-scene script to directly address the user's critique above seamlessly."

            def _parse_json_payload(txt: Optional[str]) -> Optional[Dict[str, Any]]:
                if not txt:
                    return None
                clean_t = re.sub(r'^```json\s*', '', txt.strip(), flags=re.MULTILINE)
                clean_t = re.sub(r'```$', '', clean_t.strip(), flags=re.MULTILINE)
                match_j = re.search(r'\{.*\}', clean_t, re.DOTALL)
                if not match_j:
                    return None
                cand_j = re.sub(r',\s*([\]\}])', r'\1', match_j.group(0))
                return json.loads(cand_j)

            raw = call_groq_chat(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                preferred_model=CONFIGURED_LLM_MODEL,
                fallback_model=CONFIGURED_LLM_FALLBACK,
                temperature=0.25,
                timeout=15
            )
            parsed = _parse_json_payload(raw)

            if parsed and parsed.get("scenes") and len(parsed["scenes"]) >= 5:
                # Deterministic pre-audit (Secrecy, Banned Clichés, Obsolete Managers, Word Budget)
                def _audit_scenes(sc_list: List[Dict[str, Any]]) -> List[str]:
                    issues: List[str] = []
                    name_tokens = [d.protagonist_name] + [p for p in d.protagonist_name.split() if len(p) > 2]
                    s01_obj = next((s for s in sc_list if s.get("scene_id") == "S01"), None)
                    if s01_obj:
                        ok_sec, sec_v = OpeningSecrecyValidator.validate_opening_secrecy(
                            {"narration": s01_obj.get("spoken_narration", ""), "on_screen": s01_obj.get("on_screen", {})},
                            name_tokens
                        )
                        if not ok_sec:
                            issues.extend(sec_v)
                    story_words = 0
                    for s in sc_list:
                        sid_u = str(s.get("scene_id", "")).upper()
                        narr = s.get("spoken_narration", "")
                        if sid_u != "OUTRO":
                            story_words += len(narr.split())
                        low_n = narr.lower()
                        for cl in BANNED_CLICHES:
                            if cl in low_n:
                                issues.append(f"Banned cliché '{cl}' in {s.get('scene_id')}")
                        for obs in blocked_names:
                            if obs and obs.lower() in low_n:
                                issues.append(f"Obsolete manager '{obs}' in {s.get('scene_id')}")
                    if story_words < 45 or story_words > 74:
                        issues.append(f"Story spoken word budget {story_words} out of target 55-66 range")
                    conj_rx = re.compile(r"\b(because|and|but|while|even though|although|yet|meanwhile|so)\b", re.IGNORECASE)
                    conj_hits = sum(
                        1 for s in sc_list if str(s.get("scene_id", "")).upper() != "OUTRO" and conj_rx.search(s.get("spoken_narration", ""))
                    )
                    if conj_hits < 3:
                        issues.append(f"Weak conjunction flow ({conj_hits} linked beats < 3): link S02-S07 with natural conjunctions (because, while, yet, even though, so)")
                    return issues

                audit_issues = _audit_scenes(parsed["scenes"])

                # Pass 2: API Critic & Broadcast Punch-Up Pass (always polish if issues exist OR if full article context present)
                if audit_issues or len(article_ctx) > 300:
                    critic_prompt = (
                        f"Audit & tighten this draft broadcast JSON for '30 Football Plus'.\n"
                        f"FIX THESE SPECIFIC AUDIT ISSUES: {audit_issues or ['None - tighten punchiness, factual specificity from the source article, and S07 choice clarity']}\n"
                        f"CONSTRAINTS: Keep S01 100% free of protagonist name '{d.protagonist_name}', keep total S01-S07 spoken words between 54-62 words, spell out currency/abbreviations in spoken_narration (never '£30M', say 'thirty million pounds'), zero em-dashes, zero clichés.\n"
                        f"SOURCE FACTS:\nHeadline: {d.main_headline}\nArticle Excerpt: {article_ctx[:1400]}\n"
                        f"DRAFT JSON:\n{json.dumps(parsed, ensure_ascii=False)}\n\nReturn ONLY improved valid JSON matching the exact same schema."
                    )
                    crit_raw = call_groq_chat(
                        system_prompt="You are a ruthless senior BBC/Sky broadcast sub-editor. Output ONLY valid JSON.",
                        user_prompt=critic_prompt,
                        preferred_model=CONFIGURED_LLM_FALLBACK,
                        fallback_model=CONFIGURED_LLM_MODEL,
                        temperature=0.15,
                        timeout=14,
                    )
                    crit_parsed = _parse_json_payload(crit_raw)
                    if crit_parsed and crit_parsed.get("scenes") and len(crit_parsed["scenes"]) == len(parsed["scenes"]):
                        crit_issues = _audit_scenes(crit_parsed["scenes"])
                        if len(crit_issues) <= len(audit_issues):
                            parsed = crit_parsed
                            print(f"  [API Critic Pass 2] Refined script cleanly (issues {len(audit_issues)} -> {len(crit_issues)})")

                for sc in parsed["scenes"]:
                    if str(sc.get("scene_id", "")).upper() == "OUTRO":
                        sc["scene_id"] = "outro"
                    else:
                        sc["spoken_narration"] = normalize_spoken_broadcast_text(sc.get("spoken_narration", ""))
                    on_s = sc.get("on_screen") or {}
                    if isinstance(on_s, dict) and on_s.get("kicker"):
                        on_s["kicker"] = re.sub(r"^[●•○\s]+", "", str(on_s["kicker"])).strip()
                    if not isinstance(on_s, dict) or not on_s.get("source_credit"):
                        if isinstance(on_s, dict) and d.reporting_sources:
                            on_s["source_credit"] = d.reporting_sources[0]

                # Programmatically enforce S01 secrecy & infographic attachment on S04 if verified fee present
                s01_sc = next((s for s in parsed["scenes"] if s.get("scene_id") == "S01"), None)
                if s01_sc:
                    for tok in ([d.protagonist_name] + [p for p in d.protagonist_name.split() if len(p) > 2]):
                        s01_sc["spoken_narration"] = re.sub(rf"\b{re.escape(tok)}\b", "their key star", s01_sc.get("spoken_narration", ""), flags=re.I)
                s04_sc = next((s for s in parsed["scenes"] if s.get("scene_id") == "S04"), None)
                if s04_sc and d.reported_base_fee and "undisclosed" not in d.reported_base_fee.lower():
                    s04_sc["visual"] = {
                        "kind": "transfer_fee_graphic",
                        "infographic_data": {
                            "transfer_fee": {
                                "guaranteed": d.reported_base_fee,
                                "add_ons": d.reported_bonuses or "Performance Incentives",
                                "total_package": f"{d.reported_base_fee} PACKAGE",
                                "selling_club": d.current_club,
                                "buying_club": d.pursuing_club,
                                "structure": d.complication or "Reported Package"
                            }
                        }
                    }

                screenplay_data = {
                    "story_id": d.story_id,
                    "story_category": category,
                    "master_headline": d.main_headline or f"{d.pursuing_club.upper()} PLOT {d.protagonist_name.upper()} MOVE",
                    "kicker": d.headline_kicker,
                    "ticker_text": d.ticker_text or f"{d.reporting_sources[0] if d.reporting_sources else 'TRANSFER DESK'}: {d.pursuing_club} PREPARE {d.reported_base_fee} PROPOSAL ✦ {d.current_club}: {d.current_manager} RESISTS EXIT ✦",
                    "llm_model_used": CONFIGURED_LLM_MODEL,
                    "scenes": parsed["scenes"]
                }
                out_file = self.ws.base_dir / "editorial" / "screenplay_dual_script.json"
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_text(json.dumps(screenplay_data, indent=2), encoding="utf-8")
                print(f"  [LLM Screenplay V2] Generated & audited successfully ({category}): {out_file}")
                return screenplay_data
        except Exception as err:
            print(f"[Screenplay] LLM generation note ({err}), using canonical template...")

        # Fallback Canonical Template
        src_name = d.reporting_sources[0] if d.reporting_sources else "European"
        fee_spoken = d.reported_base_fee if d.reported_base_fee != "an undisclosed fee" else "a substantial fee"
        bonus_spoken = f", plus {d.reported_bonuses} in bonuses" if d.reported_bonuses and "performance" not in d.reported_bonuses else ""

        scenes = [
            {
                "scene_id": "S01",
                "spoken_narration": f"{d.current_club} face a huge battle to keep their star player!",
                "on_screen": {
                    "kicker": "TRANSFER REPORT",
                    "headline": f"{d.current_club.upper()} STAR TARGETED",
                    "subheadline": "MANAGER FIGHTS TO KEEP KEY FIGURE",
                    "status_badge": "REPORTED"
                }
            },
            {
                "scene_id": "S02",
                "spoken_narration": f"Because {d.pursuing_club} are actively circling {d.protagonist_name}!",
                "on_screen": {
                    "kicker": "PROPOSED PACKAGE",
                    "headline": f"{d.protagonist_name.upper()} TARGETED",
                    "subheadline": f"{d.pursuing_club.upper()} CIRCLING",
                    "status_badge": "PROPOSAL"
                }
            },
            {
                "scene_id": "S03",
                "spoken_narration": f"And {src_name} reports confirm serious interest from the suitor.",
                "on_screen": {
                    "kicker": "SUITOR INTEREST",
                    "headline": f"{d.pursuing_club.upper()} MAKE APPROACH",
                    "subheadline": "INTEREST FORMALIZED",
                    "status_badge": "REPORTED"
                }
            },
            {
                "scene_id": "S04",
                "spoken_narration": f"Even though talks continue, any deal could reach {fee_spoken}{bonus_spoken}.",
                "on_screen": {
                    "kicker": "DEAL CLAUSE",
                    "headline": "FINANCIAL PACKAGE",
                    "subheadline": f"{fee_spoken.upper()} PROPOSAL",
                    "status_badge": "UNAGREED"
                }
            },
            {
                "scene_id": "S05",
                "spoken_narration": f"Meanwhile, {d.current_manager} wants his board to block the move!",
                "on_screen": {
                    "kicker": "MANAGERIAL STAND",
                    "headline": f"{d.current_manager.upper()} RESISTS",
                    "subheadline": "BOARD URGED TO BLOCK DEAL",
                    "status_badge": "DEVELOPING"
                }
            },
            {
                "scene_id": "S06",
                "spoken_narration": f"While behind the scenes, {d.complication or 'crucial negotiations remain ongoing'}.",
                "on_screen": {
                    "kicker": "CONTRACT UPDATE",
                    "headline": "STATUS & TALKS",
                    "subheadline": "CLUB MONITORS NEXT STEP",
                    "status_badge": "OFFICIAL"
                }
            },
            {
                "scene_id": "S07",
                "spoken_narration": f"So will {d.current_manager} keep him, or will {d.pursuing_club} win the race?",
                "on_screen": {
                    "kicker": "THE VERDICT",
                    "headline": f"{d.current_club.upper()} OR {d.pursuing_club.upper()}?",
                    "subheadline": "STAY OR SWITCH?",
                    "status_badge": "EDITORIAL"
                }
            },
            {
                "scene_id": "outro",
                "spoken_narration": "This is football in thirty seconds. Follow for daily transfer updates.",
                "on_screen": {
                    "headline": "THIS IS FOOTBALL IN 30 SECONDS",
                    "kicker": "FOLLOW FOR MORE"
                }
            }
        ]

        screenplay_data = {
            "story_id": d.story_id,
            "master_headline": d.main_headline or f"{d.pursuing_club.upper()} PLOT {d.protagonist_name.upper()} MOVE",
            "kicker": d.headline_kicker,
            "ticker_text": d.ticker_text or f"{d.reporting_sources[0] if d.reporting_sources else 'TRANSFER DESK'}: {d.pursuing_club} PREPARE {d.reported_base_fee} PROPOSAL ✦ {d.current_club}: {d.current_manager} RESISTS EXIT ✦",
            "llm_model_used": CONFIGURED_LLM_MODEL,
            "scenes": scenes
        }

        out_file = self.ws.base_dir / "editorial" / "screenplay_dual_script.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(screenplay_data, indent=2), encoding="utf-8")
        print(f"  Screenplay compiled: {out_file}")
        return screenplay_data

    def synthesize_voice(self, screenplay_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes voice using ProductionVoiceEngine (V7.1.6.7 Standard):
        - Default: Qwen3-TTS 0.6B CustomVoice (Ryan) — Original British sports-presenter voice design.
        - Conditional: Qwen3-TTS 0.6B Base — Reference cloning ONLY when authorized audio is explicitly configured.
        - Enforces minimum 4.0s anonymity duration on S01.
        - Records story duration (~30s) and branded outro (5-6s) separately.
        """
        print(f"\n[Stage 2] Neural Voice Synthesis & Clean Acoustic Assembly (V7.1.6.7 Standard)")
        voice_dir = self.ws.base_dir / "voice" / "vocal_transitions"
        voice_engine = ProductionVoiceEngine(voice_dir=voice_dir, fps=self.fps)
        audio_data = voice_engine.assemble_full_narration(screenplay_data)
        return audio_data

    def compile_visual_props(
        self,
        screenplay_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        shot_images: Dict[str, List[str]]
    ) -> Path:
        """Compiles Remotion props JSON with speech-aligned subtitles and exact frame reconciliation."""
        print(f"\n[Stage 3] Compiling Remotion Props (8-Scene Editorial Timeline)")
        scenes_props = []

        for sc_script, sc_audio in zip(screenplay_data["scenes"], audio_data["scenes"]):
            sid = sc_script["scene_id"]
            dur_f = sc_audio["duration_frames"]

            if sid != "outro":
                raw_shots = shot_images.get(sid, [])
                num_shots = len(raw_shots) if raw_shots else 1
                base_shot_dur = dur_f // num_shots
                remainder = dur_f % num_shots

                rem_shots = []
                for idx, shot_item in enumerate(raw_shots):
                    s_dur = base_shot_dur + (remainder if idx == num_shots - 1 else 0)
                    if isinstance(shot_item, dict):
                        shot_dict = {
                            "image_path": shot_item["image_path"],
                            "durationInFrames": s_dur,
                            "focal_x": shot_item.get("focal_x", 50.0),
                            "focal_y": shot_item.get("focal_y", 25.0),
                            "framing_mode": shot_item.get("framing_mode", "full_bleed"),
                            "pan_direction": shot_item.get("pan_direction", "center"),
                            "overlay_crest_path": shot_item.get("overlay_crest_path"),
                            "club_label": shot_item.get("club_label"),
                        }
                    else:
                        shot_dict = {
                            "image_path": shot_item,
                            "durationInFrames": s_dur,
                            "focal_x": 50.0,
                            "focal_y": 25.0,
                            "framing_mode": "full_bleed",
                            "pan_direction": "center",
                        }
                    rem_shots.append(shot_dict)

                # Validate shot duration reconciliation
                sum_shot_f = sum(s["durationInFrames"] for s in rem_shots)
                assert sum_shot_f == dur_f, f"Scene {sid} shot frames ({sum_shot_f}) != scene duration frames ({dur_f})"

                first_mode = rem_shots[0].get("framing_mode", "full_bleed") if rem_shots else "full_bleed"
                has_two = len(rem_shots) >= 2
                wants_dual_split = has_two and any(
                    s.get("framing_mode") == "dual_landscape_split" for s in rem_shots
                )
                if sid == "S07" and has_two:
                    motion_cfg = {"type": "split_duel"}
                elif wants_dual_split:
                    motion_cfg = {"type": "dual_landscape_split"}
                elif first_mode == "pan_horizontal":
                    motion_cfg = {"type": "slow_pan", "direction": rem_shots[0].get("pan_direction", "right")}
                elif sid == "S02":
                    motion_cfg = {"type": "pop_in"}
                elif sid in ("S03", "S05"):
                    motion_cfg = {"type": "slow_pan"}
                else:
                    motion_cfg = {"type": "subtle_push_in"}

                scenes_props.append({
                    "scene_id": sid,
                    "role": "news_beat",
                    "narration": sc_script["spoken_narration"],
                    "durationInFrames": dur_f,
                    "duration_sec": sc_audio["duration_sec"],
                    "audio_path": sc_audio["wav_path"],
                    "image_path": rem_shots[0]["image_path"] if rem_shots else None,
                    "shots": rem_shots,
                    "on_screen": sc_script["on_screen"],
                    "visual": sc_script.get("visual"),
                    "transition_hint": sc_script.get("transition_hint"),
                    "motion": motion_cfg,
                })
            else:
                scenes_props.append({
                    "scene_id": "outro",
                    "role": "outro",
                    "narration": sc_script["spoken_narration"],
                    "durationInFrames": dur_f,
                    "duration_sec": sc_audio["duration_sec"],
                    "audio_path": sc_audio["wav_path"],
                    "image_path": None,
                    "shots": [],
                    "on_screen": sc_script["on_screen"],
                    "motion": {"type": "static"}
                })

        # Decorate scenes with purposeful editorial transitions (camera_flash, whip_pan, document_snap, shutter_wipe, cross_dissolve)
        try:
            from stages.transition_engine import TransitionDirector
        except ModuleNotFoundError:
            from beta.stages.transition_engine import TransitionDirector
        scenes_props = TransitionDirector.plan_transitions_for_scenes(scenes_props)

        # Speech-aligned subtitles via shared helper (reused across EN / ES-419 / PT-BR)
        subtitles = build_subtitles_from_scenes(scenes_props, audio_data["scenes"], chunk_size=4)

        # Validate master timeline duration reconciliation
        total_scene_f = sum(sc["durationInFrames"] for sc in scenes_props)
        assert total_scene_f == audio_data["total_frames"], (
            f"Master frame mismatch: scenes sum ({total_scene_f}) != master total ({audio_data['total_frames']})"
        )

        # Branding Assets (base64)
        logo_file = PROJECT_ROOT / "data" / "branding" / "user_bezel_tv_bug.png"
        master_logo_file = PROJECT_ROOT / "data" / "branding" / "user_bezel_logo_master.png"
        ticker_base_file = PROJECT_ROOT / "data" / "branding" / "ticker_base_3d.png"
        headlines_tab_file = PROJECT_ROOT / "data" / "branding" / "headlines_tab_3d.png"

        import base64
        def load_b64(p: Path):
            if p.exists():
                with open(p, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('ascii')}"
            return None

        remotion_props = {
            "story_id": self.dossier.story_id,
            "headline": screenplay_data["master_headline"],
            "storyDurationInFrames": audio_data.get("story_frames", audio_data["total_frames"]),
            "storyDurationSec": audio_data.get("story_sec", audio_data["total_sec"]),
            "outroDurationInFrames": audio_data.get("outro_frames", 0),
            "outroDurationSec": audio_data.get("outro_sec", 0.0),
            "totalDurationInFrames": audio_data["total_frames"],
            "totalDurationSec": audio_data["total_sec"],
            "kicker": screenplay_data["kicker"],
            "tickerText": screenplay_data["ticker_text"],
            "scenes": scenes_props,
            "subtitles": subtitles,
            "logoSrc": load_b64(logo_file),
            "masterLogoSrc": load_b64(master_logo_file),
            "tickerBaseSrc": load_b64(ticker_base_file),
            "headlinesTabSrc": load_b64(headlines_tab_file),
            "enableRetroEffects": True
        }

        props_file = self.ws.base_dir / "output" / f"remotion_props_{self.dossier.story_id}.json"
        props_file.parent.mkdir(parents=True, exist_ok=True)
        props_file.write_text(json.dumps(remotion_props, indent=2), encoding="utf-8")
        print(f"  Remotion props saved: {props_file}")
        return props_file

    def render_and_master(
        self,
        props_file: Path,
        audio_mix_path: Path,
        total_frames: int,
        out_dir: Optional[Path] = None,
        filename_prefix: Optional[str] = None,
    ) -> Path:
        """Executes Remotion CLI render and muxes with 1990s CRT analog broadcast filter."""
        print(f"\n[Stage 4] Rendering Video & Applying CRT Analog Broadcast Treatment")
        remotion_dir = PROJECT_ROOT / "beta" / "remotion"
        target_dir = Path(out_dir) if out_dir else (self.ws.base_dir / "output")
        target_dir.mkdir(parents=True, exist_ok=True)
        stem = filename_prefix or self.dossier.story_id
        raw_video = target_dir / f"raw_video_{stem}.mp4"
        final_master = target_dir / f"{stem}_broadcast_master.mp4"

        cmd = [
            "npx.cmd" if sys.platform == "win32" else "npx",
            "remotion", "render",
            "src/index.ts",
            "FootballShort",
            str(raw_video),
            f"--props={str(props_file)}",
            f"--frames=0-{total_frames - 1}",
            "--concurrency=2",
            "--timeout=120000",
            "--gl=angle",
            "--muted"
        ]
        print(f"  Rendering {total_frames} frames via Remotion...")
        t0 = time.time()
        subprocess.run(cmd, cwd=str(remotion_dir), check=True)
        print(f"  Raw video rendered in {time.time()-t0:.2f}s")

        # 1990s Broadcast Color Warmth & Subtle Tape Grain ONLY (No chromashift/unsharp so foreground UI typography stays razor-sharp)
        retro_filter = "colorbalance=rs=0.03:gs=0.01:bs=-0.02,noise=alls=1.2:allf=t+u"
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-i", str(audio_mix_path),
            "-vf", retro_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(final_master)
        ]
        subprocess.run(mux_cmd, check=True, capture_output=True)
        print(f"  Master video produced: {final_master} ({get_audio_duration(final_master):.2f}s)")
        return final_master

    def run(self, shot_images: Dict[str, List[str]], dispatch_telegram: bool = True) -> Path:
        """Executes full automated broadcast pipeline for the story."""
        t_start = time.time()
        print("==================================================================")
        print(f"  EXECUTING BROADCAST PIPELINE: {self.dossier.story_id.upper()}")
        print("==================================================================")

        script_data = self.generate_screenplay()
        audio_data = self.synthesize_voice(script_data)
        props_path = self.compile_visual_props(script_data, audio_data, shot_images)
        final_video = self.render_and_master(props_path, Path(audio_data["master_audio_path"]), audio_data["total_frames"])

        # Copy to artifacts
        artifact_dir = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")
        dest_video = artifact_dir / f"{self.dossier.story_id}_broadcast_master.mp4"
        shutil.copy2(str(final_video), str(dest_video))

        actual_voice_name = audio_data.get("voice_name", "Original British Sports Presenter (Ryan)")
        actual_voice_mode = audio_data.get("voice_mode", "CUSTOM_VOICE")

        qa_report = {
            "version": "v7.1.6.7_generalized",
            "story_id": self.dossier.story_id,
            "run_id": self.run_id,
            "voice_personality": actual_voice_name,
            "voice_mode": actual_voice_mode,
            "total_duration_sec": round(get_audio_duration(final_video), 2),
            "total_frames": audio_data["total_frames"],
            "resolution": "1080x1920",
            "fps": 30,
            "file_size_bytes": final_video.stat().st_size,
            "sha256": sha256_of_file(final_video)
        }
        qa_file = self.ws.base_dir / "output" / f"qa_report_{self.dossier.story_id}.json"
        qa_file.write_text(json.dumps(qa_report, indent=2), encoding="utf-8")
        shutil.copy2(str(qa_file), str(artifact_dir / f"qa_report_{self.dossier.story_id}.json"))

        if dispatch_telegram:
            token, env_chat_id = get_env_credentials()
            chat_id = "5909103212" or env_chat_id
            if token and chat_id:
                client = TelegramBotClient(token=token, default_chat_id=chat_id)
                caption = (
                    f"🎬 <b>GENERALIZED 1990s BROADCAST MASTER: {self.dossier.story_id.upper()}</b>\n\n"
                    f"• <b>Protagonist</b>: {self.dossier.protagonist_name} ({self.dossier.current_club} ➔ {self.dossier.pursuing_club})\n"
                    f"• <b>Voice & Cadence</b>: {actual_voice_name} [{actual_voice_mode}] (clean vocal stops, zero whooshes)\n"
                    f"• <b>Master Treatment</b>: 1990s Trinitron CRT footage layer + crisp foreground UI (-14 LUFS stereo)\n"
                    f"• <b>Runtime</b>: {qa_report['total_duration_sec']}s ({qa_report['total_frames']} frames @ 30fps)"
                )
                client.send_video(str(final_video), caption=caption, chat_id=chat_id)

        print(f"\nPipeline finished in {time.time()-t_start:.1f}s: {final_video}")
        return final_video
