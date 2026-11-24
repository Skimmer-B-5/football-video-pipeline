"""
beta/execute_multilang_production.py
Autonomous Multi-Language (Spanish & Portuguese) Video Production & Audit.

Translates the latest approved Calvin Bassey / Fulham broadcast story into:
1. Brazilian Portuguese (PT-BR) - Voice: pt-BR-AntonioNeural (Pedro Bial style)
2. Latin American Spanish (ES-419) - Voice: es-MX-JorgeNeural (Enrique Acevedo style)

Renders full broadcast videos via Remotion with Trinitron CRT effects and delivers to artifacts directory.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from beta.pipeline.neural_instructions import StoryDossier
from beta.pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline
from beta.stages.multilang_engine import MultilingualEngine, VOICE_PROFILES
from beta.stages.fact_checker import FactChecker

def run_multilang_pipeline():
    story_id = "calvin_bassey_fulham"
    run_id = "v7_8scenes_master"
    ws_dir = PROJECT_ROOT / "beta" / "workspaces" / story_id / run_id
    script_path = ws_dir / "editorial" / "screenplay_dual_script.json"
    en_props_path = ws_dir / "output" / f"remotion_props_{story_id}.json"

    if not script_path.exists() or not en_props_path.exists():
        print("ERROR: English screenplay or props file missing!")
        return

    en_script = json.loads(script_path.read_text(encoding="utf-8"))
    en_props = json.loads(en_props_path.read_text(encoding="utf-8"))

    dossier = StoryDossier(
        story_id=story_id,
        main_headline=en_props.get("headline", "MAN UTD TRANSFER NEWS: CALVIN BASSEY TALKS"),
        protagonist_name="Calvin Bassey",
        current_club="Fulham",
        current_manager="Marco Silva",
        pursuing_club="Manchester United",
        reported_base_fee="£30M",
        reported_bonuses="£5M"
    )
    dossier = FactChecker.audit_and_enrich_dossier(dossier)

    pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id=run_id)

    languages = [
        ("es-419", "Spanish (Latin America)", "es-MX-JorgeNeural"),
        ("pt-BR", "Portuguese (Brazil)", "pt-BR-AntonioNeural")
    ]

    results = {}

    for lang_code, lang_title, voice_id in languages:
        print(f"\n=======================================================")
        print(f"PRODUCING MULTILINGUAL BROADCAST: {lang_title} ({lang_code})")
        print(f"Voice Profile: {voice_id}")
        print(f"=======================================================")

        lang_dir = ws_dir / "multilang" / lang_code
        lang_dir.mkdir(parents=True, exist_ok=True)

        # 1. Translate 8 Scenes
        print(f"[{lang_code}] Translating 8 scenes with strict sports jargon and word budget...")
        translated_script = MultilingualEngine.translate_screenplay_llm(en_script, target_lang=lang_code)
        
        # Save translated script
        (lang_dir / "screenplay.json").write_text(json.dumps(translated_script, indent=2, ensure_ascii=False), encoding="utf-8")
        for sc in translated_script["scenes"]:
            print(f"  [{sc['scene_id']}]: {sc['spoken_narration']}")

        # 2. Synthesize Voice Audio
        print(f"[{lang_code}] Synthesizing localized speech audio via {voice_id} (+8% speed)...")
        audio_data = MultilingualEngine.synthesize_localized_voice(
            translated_screenplay=translated_script,
            target_lang=lang_code,
            output_dir=lang_dir / "voice"
        )
        print(f"[{lang_code}] Story duration: {audio_data['story_sec']:.2f}s, Outro: {audio_data['outro_sec']:.2f}s, Total: {audio_data['total_sec']:.2f}s ({audio_data['total_frames']} frames)")

        # 3. Construct Remotion Props with Shared Images and Localized Text
        lang_props = dict(en_props)
        lang_props["totalDurationInFrames"] = audio_data["total_frames"]
        lang_props["totalDurationSec"] = audio_data["total_sec"]
        lang_props["storyDurationInFrames"] = int(round(audio_data["story_sec"] * 30.0))
        lang_props["storyDurationSec"] = audio_data["story_sec"]
        lang_props["outroDurationInFrames"] = int(round(audio_data["outro_sec"] * 30.0))
        lang_props["outroDurationSec"] = audio_data["outro_sec"]
        lang_props["enableRetroEffects"] = True

        v_prof = VOICE_PROFILES[lang_code]
        lang_props["kicker"] = v_prof["live_kicker"]
        if lang_code == "pt-BR":
            lang_props["tickerText"] = "MERCADO DA BOLA: FULHAM ABRE CONVERSAS POR BASSEY ✦ MANCHESTER UNITED MONITORA COM POCHETTINO ✦"
            lang_props["headline"] = "MERCADO DA BOLA: CALVIN BASSEY NA MIRA DO MANCHESTER UNITED"
        else:
            lang_props["tickerText"] = "RADAR DE FICHAJES: FULHAM NEGOCIA CON BASSEY ✦ MANCHESTER UNITED ATENTO CON POCHETTINO ✦"
            lang_props["headline"] = "MERCADO DE FICHAJES: CALVIN BASSEY EN LA MIRA DEL MANCHESTER UNITED"

        # Update scene durations and texts from audio manifest
        audio_scene_map = {m["scene_id"]: m for m in audio_data["scenes"]}
        trans_scene_map = {s["scene_id"]: s for s in translated_script["scenes"]}

        for sc_prop in lang_props["scenes"]:
            sid = sc_prop["scene_id"]
            if sid in audio_scene_map:
                aud = audio_scene_map[sid]
                sc_prop["durationInFrames"] = aud["duration_frames"]
                sc_prop["duration_sec"] = aud["duration_sec"]
                sc_prop["audio_path"] = aud["wav_path"]
            if sid in trans_scene_map:
                tr = trans_scene_map[sid]
                sc_prop["narration"] = tr["spoken_narration"]
                if "on_screen" in tr:
                    sc_prop["on_screen"] = tr["on_screen"]

            # Reconcile internal shots duration
            if "shots" in sc_prop and sc_prop["shots"]:
                total_f = sc_prop["durationInFrames"]
                n_shots = len(sc_prop["shots"])
                per_shot = total_f // n_shots
                rem = total_f % n_shots
                for s_idx, sh in enumerate(sc_prop["shots"]):
                    sh["durationInFrames"] = per_shot + (rem if s_idx == n_shots - 1 else 0)

        props_file = lang_dir / f"remotion_props_{lang_code}.json"
        props_file.write_text(json.dumps(lang_props, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[{lang_code}] Props file compiled: {props_file}")

        # 4. Render Master Video via Remotion & Trinitron CRT
        print(f"[{lang_code}] Rendering broadcast master video via Remotion and Trinitron CRT filter...")
        final_video = pipeline.render_and_master(
            props_file=props_file,
            audio_mix_path=Path(audio_data["master_audio_path"]),
            total_frames=audio_data["total_frames"]
        )
        target_lang_video = lang_dir / f"calvin_bassey_{lang_code.replace('-', '_')}_master.mp4"
        shutil.copy(final_video, target_lang_video)
        print(f"[{lang_code}] Render complete: {target_lang_video}")

        results[lang_code] = {
            "title": lang_title,
            "video_path": str(target_lang_video),
            "duration_sec": audio_data["total_sec"],
            "total_frames": audio_data["total_frames"],
            "voice": voice_id
        }

    # Summary
    print("\n=======================================================")
    print("MULTILINGUAL PRODUCTION COMPLETED!")
    print("=======================================================")
    for lc, info in results.items():
        print(f"  [{lc}] {info['title']}: {info['duration_sec']}s ({info['total_frames']} frames) -> {info['video_path']}")

if __name__ == "__main__":
    run_multilang_pipeline()
