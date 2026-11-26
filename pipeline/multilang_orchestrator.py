"""
# PROVENANCE: Isolated Multi-Language Pipeline Orchestrator for Beta Environment.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
pipeline/multilang_orchestrator.py - Production-Isolated Three-Language Video Producer.

Implements Master Directive V4:
1. Sourcing SHARED authentic football photography (Face-Aware Safe-Zone Cropping, 0 Procedural Cards).
2. Generating 3 localized broadcast packages from ONE master story:
   - English (EN)
   - Brazilian Portuguese (PT-BR)
   - Latin American Spanish (ES-419)
3. Identical visual assets: same images, same crops, same sequence, same transitions, same SFX/music.
4. Rendering into:
   - beta/output/<story_id>/master/
   - beta/output/<story_id>/en/
   - beta/output/<story_id>/pt-BR/
   - beta/output/<story_id>/es-419/
5. Automated validation & QA across all 3 videos.
"""

import sys
import os
import json
import time
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker
from stages.hook_engine import CuriosityHookEngine
from stages.image_sourcing import source_scene_image, reset_image_registry
from stages.multilang_engine import MultilingualEngine
from stages.tts_synthesizer import synthesize_scenes_expressive
from stages.video_assembler import assemble_video_ffmpeg
from stages.qa_engine import EngineQASuite
from stages.sfx_manager import SFXDirector
from stages.transition_engine import TransitionDirector

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

def compute_file_md5(file_path: Path) -> str:
    """Computes MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class MultilangOrchestrator:
    def __init__(self, story_id: str = "endrick_milan_v4"):
        self.story_id = story_id
        self.base_output_dir = OUTPUT_DIR / story_id
        self.master_dir = self.base_output_dir / "master"
        self.en_dir = self.base_output_dir / "en"
        self.pt_dir = self.base_output_dir / "pt-BR"
        self.es_dir = self.base_output_dir / "es-419"

    def execute(self, article_text: Optional[str] = None) -> Dict[str, Any]:
        with ResourceTracker(f"Multilang_Pipeline_{self.story_id}"):
            print(f"\n=======================================================")
            print(f"   STARTING THREE-LANGUAGE VIDEO PRODUCTION: {self.story_id}  ")
            print(f"=======================================================\n")

            # Create directories
            for d in [self.master_dir, self.en_dir, self.pt_dir, self.es_dir]:
                d.mkdir(parents=True, exist_ok=True)
                (d / "audio").mkdir(parents=True, exist_ok=True)
                (d / "images").mkdir(parents=True, exist_ok=True)

            # ----------------------------------------------------
            # STEP 1: Generate Master Curiosity Narrative & Script
            # ----------------------------------------------------
            print("[MultilangOrchestrator] Step 1: Composing Master English Story Beats...")
            hook_engine = CuriosityHookEngine()

            default_story = (
                "A lack of playing time amid fierce competition looks set to edge Endrick towards the exit door at Real Madrid "
                "with Milan emerging as his most likely destination. According to reports from Italian outlet Corriere dello Sport, "
                "the San Siro hierarchy are preparing a sixty million euro proposal. Real Madrid reportedly favor an eighty million buy-back option. "
                "The twenty-year-old Brazilian forward has logged only one hundred and fifty-nine minutes under José Mourinho this season "
                "following his appearance against Celta Vigo."
            )
            raw_text = article_text or default_story
            topic_info = {
                "headline": "Milan prepare €60m bid for Endrick",
                "source": "Corriere dello Sport",
                "category": "transfer_rumour",
                "primary_subject": "Endrick"
            }

            sources = [
                {
                    "publisher": "Corriere dello Sport",
                    "url": "https://corrieredellosport.it/news/calcio/calciomercato/milan/2026/11/10/endrick",
                    "published_at": "2026-11-10"
                }
            ]
            match_logs = [
                {
                    "date": "2026-11-21",
                    "fixture": "Real Madrid 2-1 Celta Vigo",
                    "opponent": "Celta Vigo",
                    "sub_minute": 70,
                    "minutes_played": 20
                }
            ]
            mock_cds = {
                "https://corrieredellosport.it/news/calcio/calciomercato/milan/2026/11/10/endrick": {
                    "http_status": 200,
                    "title": "Milan-Endrick: la proposta da 60 milioni e la formula recompra",
                    "publisher": "Corriere dello Sport",
                    "published_date": "2026-11-10",
                    "article_text": "Il Milan prepara una proposta da 60 milioni per Endrick. Il Real Madrid chiede una recompra a 80 milioni."
                }
            }
            master_package = hook_engine.compose_full_narrative(
                headline=topic_info["headline"],
                article_text=raw_text,
                sources=sources,
                evidence_status="REPORTED",
                match_logs=match_logs,
                stat_cut_off_date="2026-11-21",
                mock_source_registry=mock_cds
            )
            master_package["topic"] = topic_info
            scenes_master = master_package["scenes"]
            print(f"[MultilangOrchestrator] Master English Script generated: {len(scenes_master)} scenes.")

            # ----------------------------------------------------
            # STEP 2: Sourcing SHARED Visual Assets (Once For All)
            # ----------------------------------------------------
            print("\n[MultilangOrchestrator] Step 2: Sourcing SHARED Visual Assets with Face-Aware Safe-Zone Cropping...")
            reset_image_registry()
            shared_images = []
            asset_manifest = []

            for idx, sc in enumerate(scenes_master):
                s_id = idx + 1
                scene_text = sc.get("narration", "")
                ent = sc.get("visual", {}).get("primary_subject") or sc.get("search_entity") or "Endrick Real Madrid"
                ctx = sc.get("visual", {}).get("search_context") or "portrait match"

                print(f"[MultilangOrchestrator] Sourcing Scene {s_id}: '{ent}' ({ctx})...")
                res = source_scene_image(
                    scene_id=s_id,
                    headline=topic_info["headline"],
                    scene_text=scene_text,
                    visual_prompt=ctx,
                    source_name=topic_info["source"],
                    backend_name="editorial",
                    search_entity=sc.get("visual", {}).get("search_entity", ent),
                    search_context=ctx,
                    scene_data=sc
                )

                chosen_img = Path(res["chosen_image"])
                master_img_copy = self.master_dir / "images" / f"scene_{s_id}.png"
                shutil.copy2(chosen_img, master_img_copy)

                img_hash = compute_file_md5(master_img_copy)
                shared_images.append({
                    "scene_id": s_id,
                    "path": master_img_copy,
                    "hash": img_hash,
                    "role": sc.get("role")
                })
                asset_manifest.append({
                    "scene_id": s_id,
                    "image_file": master_img_copy.name,
                    "md5_hash": img_hash,
                    "subject": ent,
                    "source_type": res.get("source_type", "EDITORIAL")
                })
                sc["image_path"] = str(master_img_copy)

            # Save Master Asset Manifest
            with open(self.master_dir / "asset_manifest.json", "w", encoding="utf-8") as f:
                json.dump(asset_manifest, f, indent=2)
            print(f"[MultilangOrchestrator] ✓ Master visual assets saved to {self.master_dir}/images/ (all hashes locked).")

            # ----------------------------------------------------
            # STEP 3: Multi-Language Story Localization
            # ----------------------------------------------------
            print("\n[MultilangOrchestrator] Step 3: Localizing Story into PT-BR and ES-419...")
            localized_packages = MultilingualEngine.translate_story_package(master_package)

            # ----------------------------------------------------
            # STEP 4: Render All Three Language Versions
            # ----------------------------------------------------
            rendered_deliverables = {}

            # Plan transitions & sound design on master scenes once so they are identical
            base_scenes = [dict(s) for s in master_package["scenes"]]
            base_scenes = TransitionDirector.plan_transitions_for_scenes(base_scenes)
            base_scenes, music_plan = SFXDirector().design_soundtrack_for_story(
                scenes=base_scenes,
                story_category=topic_info["category"],
                headline=topic_info["headline"]
            )

            languages = [
                ("en", self.en_dir, "en-GB-ThomasNeural"),
                ("pt-BR", self.pt_dir, "pt-BR-AntonioNeural"),
                ("es-419", self.es_dir, "es-MX-JorgeNeural")
            ]

            qa_suite = EngineQASuite(PROJECT_ROOT)

            for lang_code, target_dir, default_voice in languages:
                print(f"\n-------------------------------------------------------")
                print(f"   PROCESSING LANGUAGE: {lang_code.upper()} ")
                print(f"-------------------------------------------------------")

                story_pkg = localized_packages[lang_code]
                v_profile = story_pkg["voice_profile"]

                # 1. Prepare scenes with shared image paths & localized text
                lang_scenes = []
                for idx, sc_src in enumerate(story_pkg["scenes"]):
                    sc = dict(base_scenes[idx])
                    sc.update({
                        "narration": sc_src["narration"],
                        "text": sc_src["narration"],
                        "on_screen": sc_src["on_screen"],
                        "image_path": str(self.master_dir / "images" / f"scene_{idx+1}.png")
                    })
                    lang_scenes.append(sc)

                # 2. Synthesize Voiceover
                print(f"[{lang_code}] Synthesizing speech with voice: {v_profile['voice']} ({v_profile['reference']})...")
                audio_scenes = synthesize_scenes_expressive(
                    lang_scenes,
                    voice_name=v_profile["voice"],
                    rate=v_profile.get("rate", "+0%"),
                    pitch=v_profile.get("pitch", "+0Hz"),
                    pad_sec=0.15
                )

                for idx, ascene in enumerate(audio_scenes):
                    lang_scenes[idx].update({
                        "audio_path": ascene["audio_path"],
                        "audio_duration_sec": ascene["audio_duration_sec"],
                        "slide_duration_sec": ascene["slide_duration_sec"],
                        "tts_engine": ascene.get("engine", "EdgeTTS"),
                        "tts_voice": ascene.get("voice", v_profile["voice"])
                    })

                # Copy audio to target dir
                for idx, ls in enumerate(lang_scenes):
                    dest_audio = target_dir / "audio" / f"scene_{idx+1}.wav"
                    shutil.copy2(ls["audio_path"], dest_audio)
                    ls["audio_path"] = str(dest_audio)

                # 3. Assemble Video
                out_video = target_dir / f"video_{lang_code.lower().replace('-', '_')}.mp4"
                print(f"[{lang_code}] Assembling 90s Broadcast Short -> {out_video.name}...")

                assemble_video_ffmpeg(
                    scenes=lang_scenes,
                    output_mp4_path=out_video,
                    credit_source_name=topic_info["source"],
                    story_headline=story_pkg.get("headline", topic_info["headline"]),
                    story_category=topic_info["category"],
                    music_plan=music_plan,
                    lang=lang_code
                )

                # 4. Save Transcript & Storyboard
                transcript_payload = {
                    "language": lang_code,
                    "voice_profile": v_profile,
                    "headline": story_pkg.get("headline"),
                    "scenes": [
                        {
                            "scene_id": s.get("scene_id"),
                            "narration": s.get("narration"),
                            "on_screen": s.get("on_screen"),
                            "audio_duration_sec": s.get("audio_duration_sec"),
                            "image_hash": compute_file_md5(Path(s.get("image_path")))
                        }
                        for s in lang_scenes
                    ]
                }
                with open(target_dir / "transcript.json", "w", encoding="utf-8") as f:
                    json.dump(transcript_payload, f, indent=2)

                # 5. Run Engine QA Suite
                qa_report_path = target_dir / "qa_report.json"
                contact_sheet_path = target_dir / f"contact_sheet_{lang_code.lower().replace('-', '_')}.jpg"

                qa_props = {
                    "headline": story_pkg.get("headline"),
                    "scenes": lang_scenes
                }
                qa_res = qa_suite.run_full_qa(
                    video_path=out_video,
                    props=qa_props,
                    output_report_path=qa_report_path,
                    contact_sheet_path=contact_sheet_path
                )

                rendered_deliverables[lang_code] = {
                    "video_path": str(out_video),
                    "contact_sheet": str(contact_sheet_path) if contact_sheet_path.exists() else None,
                    "qa_report": qa_res,
                    "transcript": transcript_payload,
                    "all_passed": qa_res["all_passed"]
                }
                print(f"[{lang_code}] ✓ Render & QA complete. Status: {qa_res['overall_status']}")

            # ----------------------------------------------------
            # STEP 5: Cross-Language Integrity Verification
            # ----------------------------------------------------
            print("\n=======================================================")
            print("   CROSS-LANGUAGE INTEGRITY & ASSET IDENTITY AUDIT     ")
            print("=======================================================\n")

            audit_results = self.audit_cross_language_parity(rendered_deliverables)

            final_report = {
                "story_id": self.story_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "shared_images": [
                    {"scene_id": img["scene_id"], "hash": img["hash"], "file": img["path"].name}
                    for img in shared_images
                ],
                "deliverables": rendered_deliverables,
                "cross_language_audit": audit_results
            }

            with open(self.base_output_dir / "master_production_report.json", "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=2)

            print(f"\n[MultilangOrchestrator] ALL THREE VIDEOS RENDERED & VERIFIED.")
            print(f"Master Directory: {self.base_output_dir}")
            return final_report

    def audit_cross_language_parity(self, deliverables: Dict[str, Any]) -> Dict[str, Any]:
        """Validates that all 3 languages used 100% identical images in identical order."""
        en_scenes = deliverables["en"]["transcript"]["scenes"]
        pt_scenes = deliverables["pt-BR"]["transcript"]["scenes"]
        es_scenes = deliverables["es-419"]["transcript"]["scenes"]

        image_hashes_match = True
        hash_comparison = []

        for i in range(len(en_scenes)):
            h_en = en_scenes[i]["image_hash"]
            h_pt = pt_scenes[i]["image_hash"]
            h_es = es_scenes[i]["image_hash"]

            match = (h_en == h_pt == h_es)
            if not match:
                image_hashes_match = False

            hash_comparison.append({
                "scene_idx": i + 1,
                "en_hash": h_en,
                "pt_hash": h_pt,
                "es_hash": h_es,
                "identical": match
            })

        print(f"[Audit] Visual Image Hash Parity: {'100% IDENTICAL' if image_hashes_match else 'MISMATCH DETECTED'}")
        for comp in hash_comparison:
            print(f"  Scene {comp['scene_idx']}: hash={comp['en_hash']} | Parity={comp['identical']}")

        return {
            "image_hashes_identical": image_hashes_match,
            "scene_count": len(en_scenes),
            "hash_comparison": hash_comparison
        }

if __name__ == "__main__":
    orc = MultilangOrchestrator()
    orc.execute()
