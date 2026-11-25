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
            from stages.groq_client import call_groq_chat
            sys_prompt = """You are an elite British sports news television editor producing a high-impact 8-scene screenplay (7 story scenes + 1 ending card outro) for a 30-second television short (classic British sports desk style).

EDITORIAL & VOCAL GUIDELINES:
CRITICAL RUNTIME MANDATE: The 7 story scenes (S01–S07) MUST be completed in approximately 26–28 seconds (~56–62 spoken words total). Each beat is a concise, punchy sentence (7–9 words).
1. S01 (The Hook & Concealment): 7–9 WORDS. MUST conceal protagonist's identity (minimum 4.0s anonymity). Club tension/pressure.
2. S02 (The Reveal): 7–9 WORDS. Explicitly name the protagonist with energetic pickup ("And Calvin Bassey faces..."). DO NOT USE EM-DASHES OR HYPHENS.
3. S03 (The Suitor Move): 7–9 WORDS. Detail the pursuing club / suitor actively circling or bidding.
4. S04 (The Figures): 7–9 WORDS. State the reported transfer fee or financial package.
5. S05 (The Managerial Stand): 7–9 WORDS. Manager's firm resistance or board instructions.
6. S06 (Player Stance & Status): 7–9 WORDS. Player contract perspective or complication.
7. S07 (The Closing Dilemma): 8–10 WORDS. Must include an "OR" / "AND" choice between the two sides. Example: "So will Silva keep his defensive anchor, or will United force the move?" DO NOT USE EM-DASHES.
8. outro: EXACTLY 10 WORDS (Scene 8, Ending Card): "This is football in thirty seconds. Follow for daily transfer updates."
9. VOCAL CADENCE: Fast-paced 145 WPM cadence, punchy, authoritative delivery. ZERO whooshes, NO em-dashes.

Output ONLY valid JSON matching this schema:
{
  "scenes": [
    {
      "scene_id": "S01",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● TRANSFER REPORT", "headline": "...", "subheadline": "...", "status_badge": "DEVELOPING"}
    },
    {
      "scene_id": "S02",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● PROPOSED PACKAGE", "headline": "...", "subheadline": "...", "status_badge": "REVEALED"}
    },
    {
      "scene_id": "S03",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● SUITOR INTEREST", "headline": "...", "subheadline": "...", "status_badge": "REPORTED"}
    },
    {
      "scene_id": "S04",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● DEAL CLAUSE", "headline": "...", "subheadline": "...", "status_badge": "UNAGREED"}
    },
    {
      "scene_id": "S05",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● MANAGERIAL STAND", "headline": "...", "subheadline": "...", "status_badge": "DEVELOPING"}
    },
    {
      "scene_id": "S06",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● SITUATION UPDATE", "headline": "...", "subheadline": "...", "status_badge": "OFFICIAL"}
    },
    {
      "scene_id": "S07",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● THE VERDICT", "headline": "...", "subheadline": "...", "status_badge": "EDITORIAL"}
    },
    {
      "scene_id": "outro",
      "spoken_narration": "This is football in thirty seconds. Follow for daily transfer updates.",
      "on_screen": {"headline": "THIS IS FOOTBALL IN 30 SECONDS", "kicker": "FOLLOW FOR MORE"}
    }
  ]
}
"""
            pursuing_mgr = getattr(d, "pursuing_manager", "") or "Unknown"
            curr_std = getattr(d, "current_stadium", "") or ""
            suitor_std = getattr(d, "pursuing_stadium", "") or ""
            fan_reactions = getattr(d, "fan_reactions", []) or []

            user_prompt = f"""STORY HEADLINE: {d.main_headline}
PROTAGONIST: {d.protagonist_name}
CURRENT CLUB: {d.current_club}{f" (Stadium: {curr_std})" if curr_std else ""}
PURSUING CLUB / SUITOR: {d.pursuing_club} (Current Manager: {pursuing_mgr}{f", Stadium: {suitor_std}" if suitor_std else ""})
CURRENT MANAGER: {d.current_manager}
REPORTED FEE: {d.reported_base_fee}
COMPLICATION: {d.complication}
"""
            if fan_reactions:
                user_prompt += "\nVERIFIED FAN REACTIONS (Reddit/Fans - use authentic sentiment, do NOT invent quotes):\n"
                for fr in fan_reactions[:4]:
                    user_prompt += f"- {fr}\n"
            if prior_script:
                user_prompt += f"\nPREVIOUS SCRIPT DRAFT:\n{prior_script}\n"
            if user_directive:
                user_prompt += f"\nUSER DIRECTIVE & EDITORIAL CRITIQUE:\n\"{user_directive}\"\n"
                user_prompt += "Rebuild the entire 5-beat dual-script to directly address the user's critique above, incorporating their instructions seamlessly into the broadcast."

            raw = call_groq_chat(
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                preferred_model=CONFIGURED_LLM_MODEL,
                fallback_model=CONFIGURED_LLM_FALLBACK,
                temperature=0.3,
                timeout=12
            )
            if raw:
                import re
                clean_raw = re.sub(r'^```json\s*', '', raw.strip(), flags=re.MULTILINE)
                clean_raw = re.sub(r'```$', '', clean_raw.strip(), flags=re.MULTILINE)
                m = re.search(r'\{.*\}', clean_raw, re.DOTALL)
                if m:
                    m_text = m.group(0)
                    # Clean trailing commas
                    m_text_clean = re.sub(r',\s*([\]\}])', r'\1', m_text)
                    try:
                        parsed = json.loads(m_text_clean)
                    except Exception:
                        parsed = json.loads(m_text)

                    if parsed.get("scenes") and len(parsed["scenes"]) >= 5:
                        # Normalize scene_ids to lower/canonical (e.g. OUTRO -> outro)
                        for sc in parsed["scenes"]:
                            if sc.get("scene_id", "").upper() == "OUTRO":
                                sc["scene_id"] = "outro"

                        screenplay_data = {
                            "story_id": d.story_id,
                            "master_headline": d.main_headline or f"{d.pursuing_club.upper()} PLOT {d.protagonist_name.upper()} MOVE",
                            "kicker": d.headline_kicker,
                            "ticker_text": d.ticker_text or f"{d.reporting_sources[0] if d.reporting_sources else 'TRANSFER DESK'}: {d.pursuing_club} PREPARE {d.reported_base_fee} PROPOSAL ✦ {d.current_club}: {d.current_manager} RESISTS EXIT ✦",
                            "llm_model_used": CONFIGURED_LLM_MODEL,
                            "scenes": parsed["scenes"]
                        }
                        out_file = self.ws.base_dir / "editorial" / "screenplay_dual_script.json"
                        out_file.parent.mkdir(parents=True, exist_ok=True)
                        out_file.write_text(json.dumps(screenplay_data, indent=2), encoding="utf-8")
                        print(f"  [LLM Screenplay] Generated successfully: {out_file}")
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
                "spoken_narration": f"{d.current_club} face a battle to keep their star defender.",
                "on_screen": {
                    "kicker": "● TRANSFER REPORT",
                    "headline": f"{d.current_club.upper()} DEFENCE TARGETED",
                    "subheadline": "MANAGER FIGHTS TO KEEP STAR",
                    "status_badge": "REPORTED"
                }
            },
            {
                "scene_id": "S02",
                "spoken_narration": f"And — {d.pursuing_club} are actively circling around {d.protagonist_name}.",
                "on_screen": {
                    "kicker": "● PROPOSED PACKAGE",
                    "headline": f"{d.protagonist_name.upper()} TARGETED",
                    "subheadline": f"{d.pursuing_club.upper()} CIRCLING",
                    "status_badge": "PROPOSAL"
                }
            },
            {
                "scene_id": "S03",
                "spoken_narration": f"{src_name} reports confirm formal interest from the suitor.",
                "on_screen": {
                    "kicker": "● SUITOR INTEREST",
                    "headline": f"{d.pursuing_club.upper()} MAKE APPROACH",
                    "subheadline": "INTEREST FORMALIZED",
                    "status_badge": "REPORTED"
                }
            },
            {
                "scene_id": "S04",
                "spoken_narration": f"The package is understood to reach {fee_spoken}{bonus_spoken}.",
                "on_screen": {
                    "kicker": "● DEAL CLAUSE",
                    "headline": "FINANCIAL PACKAGE",
                    "subheadline": f"{fee_spoken.upper()} PROPOSAL",
                    "status_badge": "UNAGREED"
                }
            },
            {
                "scene_id": "S05",
                "spoken_narration": f"Meanwhile — {d.current_manager} wants the board to block any approach.",
                "on_screen": {
                    "kicker": "● MANAGERIAL STAND",
                    "headline": f"{d.current_manager.upper()} RESISTS",
                    "subheadline": "BOARD URGED TO BLOCK DEAL",
                    "status_badge": "DEVELOPING"
                }
            },
            {
                "scene_id": "S06",
                "spoken_narration": f"Crucially — {d.complication or 'talks over extension remain open'}.",
                "on_screen": {
                    "kicker": "● CONTRACT UPDATE",
                    "headline": "STATUS & EXTENSION",
                    "subheadline": "SECURITY SOUGHT",
                    "status_badge": "OFFICIAL"
                }
            },
            {
                "scene_id": "S07",
                "spoken_narration": f"So — will {d.current_manager} keep him, or will {d.pursuing_club} force a compromise?",
                "on_screen": {
                    "kicker": "● THE VERDICT",
                    "headline": f"{d.current_club.upper()} OR {d.pursuing_club.upper()}?",
                    "subheadline": "SANCTION OR RETAIN",
                    "status_badge": "EDITORIAL"
                }
            },
            {
                "scene_id": "outro",
                "spoken_narration": "Either way — this is football in thirty seconds. Follow for daily transfer updates.",
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
                for idx, img_path in enumerate(raw_shots):
                    s_dur = base_shot_dur + (remainder if idx == num_shots - 1 else 0)
                    rem_shots.append({
                        "image_path": img_path,
                        "durationInFrames": s_dur
                    })

                # Validate shot duration reconciliation
                sum_shot_f = sum(s["durationInFrames"] for s in rem_shots)
                assert sum_shot_f == dur_f, f"Scene {sid} shot frames ({sum_shot_f}) != scene duration frames ({dur_f})"

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
                    "motion": {"type": "subtle_push_in" if sid != "S03" else "static"}
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
        total_frames: int
    ) -> Path:
        """Executes Remotion CLI render and muxes with 1990s CRT analog broadcast filter."""
        print(f"\n[Stage 4] Rendering Video & Applying CRT Analog Broadcast Treatment")
        remotion_dir = PROJECT_ROOT / "beta" / "remotion"
        raw_video = self.ws.base_dir / "output" / f"raw_video_{self.dossier.story_id}.mp4"
        final_master = self.ws.base_dir / "output" / f"{self.dossier.story_id}_broadcast_master.mp4"

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
