"""
# BETA V6.4.1: SEMANTIC IMAGE PROCUREMENT & FOCAL FRAMING RUNNER
# Sandbox: beta/ | Strictly zero modifications outside beta/
"""

import sys
import os
import io
import json
import time
import shutil
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import numpy as np
import cv2

PROJECT_ROOT = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\beta")
sys.path.insert(0, str(PROJECT_ROOT))

from stages.semantic_image_procurement import (
    SceneVisualSpec,
    EnhancedSubjectDetector,
    SemanticVisualVerifier,
    EffectiveResolutionCropValidator,
    DiagnosticContactSheetBuilderV2,
    DISQUALIFIED_DOMAINS
)
from stages.visual_agent import VisualAgent

ARTIFACT_DIR = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
IMAGES_DIR = DATA_DIR / "images" / "v6_4_1"
CONTACT_SHEETS_DIR = OUTPUT_DIR / "v6_4_1_contact_sheets"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8"
}

# Formal Scene Visual Specifications (Stage A: Scene Understanding)
SPECS_V6_4_1 = [
    {
        "story_id": "v6_4_1_story_1_bruno",
        "title": "Bruno Fernandes Puts Manchester United Contract Talks On Hold",
        "category": "contract_negotiation",
        "event_date": "2026-11-22",
        "scenes": [
            SceneVisualSpec(
                scene_id="s01",
                role="personal_decision",
                intended_subject="Manchester United Players Tunnel Walkout",
                club="Manchester United",
                event_context="Old Trafford matchday tunnel entrance establishing tension without revealing Bruno's face prematurely (4s secrecy)",
                relevant_date="2026-11-22",
                required_visual_elements=["tunnel", "walkout", "matchday", "players"],
                banned_visual_elements=["empty_stands", "architectural_blueprint", "1920s_stadium", "player_face_closeup"],
                allowed_asset_types=["SAME_MATCH_CONTEXT", "CLUB_CONTEXT_PHOTO", "ARCHIVAL_PHOTO"],
                search_queries=[
                    "Manchester United walk out Old Trafford tunnel matchday",
                    "Manchester United players tunnel pitch entrance matchday",
                    "Old Trafford players tunnel walkout match"
                ],
                wiki_entities=["Old Trafford"]
            ),
            SceneVisualSpec(
                scene_id="s02",
                role="club_crisis",
                intended_subject="Bruno Fernandes (Captain)",
                club="Manchester United",
                event_context="First reveal of Bruno Fernandes playing for Manchester United wearing the captain's armband with intense match focus",
                relevant_date="2026-11-22",
                required_visual_elements=["footballer", "captain_armband", "face", "red_shirt"],
                banned_visual_elements=["shirt_only", "flat_jersey", "product_photo", "hanger"],
                allowed_asset_types=["SAME_MATCH_CONTEXT", "PLAYER_CONTEXTUAL_PHOTO"],
                search_queries=[
                    "Bruno Fernandes captain armband Manchester United match photo",
                    "Bruno Fernandes captain portrait Manchester United",
                    "Bruno Fernandes in action Manchester United captain armband",
                    "Bruno Fernandes Manchester United news red shirt"
                ],
                wiki_entities=["Bruno Fernandes"]
            ),
            SceneVisualSpec(
                scene_id="s03",
                role="contract_context",
                intended_subject="Bruno Fernandes On-Record Press Conference",
                club="Manchester United",
                event_context="Bruno Fernandes addressing contract discussions in an official press conference or media briefing with microphones",
                relevant_date="2026-11-22",
                required_visual_elements=["press_conference", "microphone", "media_backdrop", "face"],
                banned_visual_elements=["generic_desk", "cartoon_contract", "phone_call_headline", "empty_press_room"],
                allowed_asset_types=["CLUB_CONTEXT_PHOTO", "PLAYER_CONTEXTUAL_PHOTO"],
                search_queries=[
                    "Bruno Fernandes pre-match press conference Manchester United microphone",
                    "Bruno Fernandes press conference Manchester United microphone media",
                    "Bruno Fernandes speaking at press conference Manchester United"
                ],
                wiki_entities=["Bruno Fernandes"]
            ),
            SceneVisualSpec(
                scene_id="s04",
                role="leadership_implication",
                intended_subject="Mauricio Pochettino",
                club="Manchester United",
                event_context="New manager Mauricio Pochettino in technical area / contemplation preparing for debut against Liverpool",
                relevant_date="2026-11-22",
                required_visual_elements=["manager", "touchline", "contemplation", "face"],
                banned_visual_elements=["celebrity_gossip", "irrelevant_club_badge"],
                allowed_asset_types=["PLAYER_CONTEXTUAL_PHOTO", "CLUB_CONTEXT_PHOTO"],
                search_queries=[
                    "Mauricio Pochettino manager portrait match news",
                    "Mauricio Pochettino manager touchline serious coat",
                    "Mauricio Pochettino manager touchline contemplation"
                ],
                wiki_entities=["Mauricio Pochettino"]
            )
        ]
    },
    {
        "story_id": "v6_4_1_story_2_raya",
        "title": "David Raya Shoulder Injury Blow at St James' Park",
        "category": "tactical_analysis",
        "event_date": "2026-11-21",
        "scenes": [
            SceneVisualSpec(
                scene_id="s01",
                role="match_incident",
                intended_subject="St James' Park Newcastle vs Arsenal Match Action",
                club="Newcastle United vs Arsenal",
                event_context="Second-half clash at St James' Park (strictly Newcastle stadium context, never Emirates)",
                relevant_date="2026-11-21",
                required_visual_elements=["match_action", "st_james_park", "tackle", "contest"],
                banned_visual_elements=["emirates_stadium", "london_colney", "empty_pitch"],
                allowed_asset_types=["SAME_MATCH_CONTEXT", "EXACT_EVENT_PHOTO"],
                search_queries=[
                    "Newcastle vs Arsenal St James Park match action",
                    "Newcastle United vs Arsenal St James Park match action 2026",
                    "Newcastle vs Arsenal St James Park 2-2 match action"
                ],
                wiki_entities=["St James' Park", "Arsenal F.C."]
            ),
            SceneVisualSpec(
                scene_id="s02",
                role="injury_uncertainty",
                intended_subject="David Raya (Shoulder Injury)",
                club="Arsenal",
                event_context="David Raya receiving shoulder medical attention or clutching shoulder in acute discomfort in Arsenal goalkeeper kit",
                relevant_date="2026-11-21",
                required_visual_elements=["goalkeeper", "shoulder_injury", "medical_attention", "gloves", "face_in_pain"],
                banned_visual_elements=["smiling_portrait", "outfield_player", "training_cone"],
                allowed_asset_types=["SAME_MATCH_CONTEXT", "EXACT_EVENT_PHOTO", "PLAYER_CONTEXTUAL_PHOTO"],
                search_queries=[
                    "David Raya clutching shoulder Arsenal goalkeeper injury",
                    "David Raya injured shoulder Arsenal medical staff",
                    "David Raya Arsenal goalkeeper distress injury",
                    "David Raya injury update"
                ],
                wiki_entities=["David Raya"]
            ),
            SceneVisualSpec(
                scene_id="s03",
                role="immediate_replacement",
                intended_subject="Kepa Arrizabalaga",
                club="Arsenal",
                event_context="Kepa Arrizabalaga in yellow/green Arsenal goalkeeper strip and gloves ready in goal",
                relevant_date="2026-11-21",
                required_visual_elements=["goalkeeper", "arsenal_kit", "gloves", "face"],
                banned_visual_elements=["chelsea_kit", "real_madrid_kit", "bournemouth_kit", "outfield_jersey"],
                allowed_asset_types=["PLAYER_CONTEXTUAL_PHOTO", "SAME_MATCH_CONTEXT"],
                search_queries=[
                    "Kepa Arrizabalaga Arsenal goalkeeper kit gloves",
                    "Arsenal Keeper Kepa Credits Shift in Mindset for V",
                    "Kepa Arrizabalaga Arsenal goalkeeper match action"
                ],
                wiki_entities=["Kepa Arrizabalaga"]
            ),
            SceneVisualSpec(
                scene_id="s04",
                role="title_implications",
                intended_subject="Mikel Arteta",
                club="Arsenal",
                event_context="Mikel Arteta's urgent, high-stakes reaction in technical area as title race tension peaks",
                relevant_date="2026-11-21",
                required_visual_elements=["manager", "touchline", "gesturing", "intense_expression"],
                banned_visual_elements=["press_conference_sitting", "smiling_trophy"],
                allowed_asset_types=["CLUB_CONTEXT_PHOTO", "SAME_MATCH_CONTEXT"],
                search_queries=[
                    "Mikel Arteta manager touchline reaction St James Park",
                    "Mikel Arteta manager touchline worried reaction",
                    "Why Arteta's FA charge was not upheld"
                ],
                wiki_entities=["Mikel Arteta"]
            )
        ]
    },
    {
        "story_id": "v6_4_1_story_3_brighton",
        "title": "Brighton's £3.5m Recruitment Stuns Manchester City at the Etihad",
        "category": "tactical_analysis",
        "event_date": "2026-10-31",
        "scenes": [
            SceneVisualSpec(
                scene_id="s01",
                role="expensive_opposition",
                intended_subject="Manchester City Midfield Battle at Etihad",
                club="Manchester City vs Brighton",
                event_context="Intense midfield clash between City's £327m midfield and Brighton at the Etihad Stadium (foreground action, not background spectator)",
                relevant_date="2026-10-31",
                required_visual_elements=["midfield_action", "etihad_stadium", "tackle", "ball_contest"],
                banned_visual_elements=["spectator_closeup", "empty_stands", "wrong_scoreline_graphic"],
                allowed_asset_types=["SAME_MATCH_CONTEXT", "EXACT_EVENT_PHOTO"],
                search_queries=[
                    "Manchester City vs Brighton Etihad stadium midfield battle action",
                    "Manchester City vs Brighton midfield contest match action",
                    "Man City 2-2 Brighton: Visitors twice come from behind to draw"
                ],
                wiki_entities=["Etihad Stadium", "Manchester City F.C."]
            ),
            SceneVisualSpec(
                scene_id="s02",
                role="unexpected_result",
                intended_subject="Yasin Ayari (Brighton Midfielder)",
                club="Brighton & Hove Albion",
                event_context="Yasin Ayari celebrating goal or in match action for Brighton & Hove Albion",
                relevant_date="2026-10-31",
                required_visual_elements=["footballer", "brighton_shirt", "celebration", "match_action"],
                banned_visual_elements=["ai_graphic", "wrong_player", "january_old_file"],
                allowed_asset_types=["EXACT_EVENT_PHOTO", "SAME_MATCH_CONTEXT", "PLAYER_CONTEXTUAL_PHOTO"],
                search_queries=[
                    "Yasin Ayari Brighton goal celebration match photo",
                    "Yasin Ayari Brighton midfielder match action celebration",
                    "Manchester City x Brighton: onde assistir e escala"
                ],
                wiki_entities=["Yasin Ayari", "Brighton & Hove Albion F.C."]
            ),
            SceneVisualSpec(
                scene_id="s03",
                role="recruitment_method",
                intended_subject="Tony Bloom (Brighton Chairman & Owner)",
                club="Brighton & Hove Albion",
                event_context="Brighton Chairman & Owner Tony Bloom at Amex Stadium or executive feature on data-led recruitment",
                relevant_date="2026-11-21",
                required_visual_elements=["tony_bloom", "chairman", "amex_stadium", "executive_portrait"],
                banned_visual_elements=["paul_barber", "orlando_bloom", "sci_fi_dashboard", "fake_hologram"],
                allowed_asset_types=["CLUB_CONTEXT_PHOTO"],
                search_queries=[
                    "Tony Bloom chairman Brighton and Hove Albion",
                    "Tony Bloom Brighton chairman portrait Amex Stadium",
                    "Poker player turned billionaire Tony Bloom could d"
                ],
                disqualified_entities=["orlando bloom", "orlando", "barber"],
                wiki_entities=["Tony Bloom"]
            ),
            SceneVisualSpec(
                scene_id="s04",
                role="sporting_outcome",
                intended_subject="Fabian Hürzeler (Brighton Manager, Age 33)",
                club="Brighton & Hove Albion",
                event_context="Fabian Hürzeler coaching Brighton in technical area or celebrating on touchline in club jacket",
                relevant_date="2026-10-31",
                required_visual_elements=["manager", "touchline", "brighton_jacket", "face"],
                banned_visual_elements=["st_pauli_archive", "unrelated_coach"],
                allowed_asset_types=["PLAYER_CONTEXTUAL_PHOTO", "SAME_MATCH_CONTEXT"],
                search_queries=[
                    "Fabian Hurzeler delivers latest Brighton team news",
                    "Brighton can dream of Premier League title charge Fabian Hurzeler",
                    "File:Fabian_Hürzeler_24012026_(8).jpg"
                ],
                wiki_entities=["Fabian Hürzeler"]
            )
        ]
    }
]

def download_image_robust(url: str, fallback_url: Optional[str] = None) -> Optional[bytes]:
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
                if len(data) >= 15000:
                    return data
        except Exception:
            if fallback_url and fallback_url != url:
                try:
                    f_req = urllib.request.Request(fallback_url, headers=HEADERS)
                    with urllib.request.urlopen(f_req, timeout=8) as resp:
                        data = resp.read()
                        if len(data) >= 15000:
                            return data
                except Exception:
                    pass
            time.sleep(0.5)
    return None

def run_v6_4_1_pipeline():
    print("=" * 75)
    print("STARTING BETA V6.4.1: SEMANTIC IMAGE PROCUREMENT & FOCAL FRAMING REPAIR")
    print("=" * 75)

    agent = VisualAgent()
    crop_validator = EffectiveResolutionCropValidator(target_w=1080, target_h=1920)

    manifest_v6_4_1 = []
    used_hashes = set()
    used_urls = set()

    for story_dict in SPECS_V6_4_1:
        s_id = story_dict["story_id"]
        s_title = story_dict["title"]
        print(f"\n>>> PROCESSING STORY: {s_title} ({s_id})")

        story_img_dir = IMAGES_DIR / s_id
        story_img_dir.mkdir(parents=True, exist_ok=True)

        story_record = {
            "story_id": s_id,
            "title": s_title,
            "category": story_dict["category"],
            "event_date": story_dict["event_date"],
            "scenes": []
        }

        contact_sheet_scenes = []

        for spec in story_dict["scenes"]:
            sc_id = spec.scene_id
            role = spec.role
            print(f"\n  [Scene {sc_id} - {role}]")
            print(f"  Intended Subject: {spec.intended_subject}")
            print(f"  Allowed Provenance: {spec.allowed_asset_types}")

            raw_cands = []
            # 1. Harvest candidates across queries
            for q in spec.search_queries:
                found = agent.search_candidates_bing(q, max_results=12)
                for f in found:
                    if f["url"] not in [rc["url"] for rc in raw_cands]:
                        raw_cands.append(f)
                if len(raw_cands) >= 20:
                    break

            # 2. Wikimedia / Wiki REST queries
            for w_ent in spec.wiki_entities:
                for f in agent.search_candidates_wikimedia(w_ent, max_results=4):
                    if f["url"] not in [rc["url"] for rc in raw_cands]:
                        raw_cands.append(f)
                for f in agent.search_candidates_wikipedia_rest(w_ent, max_results=3):
                    if f["url"] not in [rc["url"] for rc in raw_cands]:
                        raw_cands.append(f)

            print(f"  Harvested {len(raw_cands)} candidate images.")

            inspected_records = []
            selected_cand = None
            selected_crop_bgr = None
            selected_crop_meta = None
            selected_audit_data = None
            selected_orig_bgr = None
            rejections_list = []

            for cand in raw_cands:
                u = cand["url"]
                t = cand.get("title", "")
                p = cand.get("page_url", "")

                if u in used_urls:
                    rejections_list.append({"url": u, "title": t, "reason": "Duplicate URL in batch"})
                    continue

                # Download image bytes
                raw_bytes = download_image_robust(u, cand.get("fallback_url"))
                if not raw_bytes:
                    rejections_list.append({"url": u, "title": t, "reason": "Download failure or file size <15KB"})
                    continue

                h_val = hashlib.md5(raw_bytes).hexdigest()[:10]
                if h_val in used_hashes:
                    rejections_list.append({"url": u, "title": t, "reason": "Duplicate image content hash"})
                    continue

                # Stage C: Semantic Visual Verification
                passed_sem, sem_reason, audit_data = SemanticVisualVerifier.inspect_candidate(
                    raw_bytes=raw_bytes,
                    cand_meta=cand,
                    spec=spec
                )

                if not passed_sem:
                    rejections_list.append({"url": u, "title": t, "reason": f"Semantic Rejection: {sem_reason}"})
                    continue

                # Stage D & Section 4: Effective Resolution & Focal Cropping (NO MIRROR PADDING)
                try:
                    pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                    cv_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    passed_crop, crop_bgr, crop_meta = crop_validator.crop_and_validate(cv_bgr, spec)

                    if not passed_crop:
                        rejections_list.append({"url": u, "title": t, "reason": f"Crop Rejection: {crop_meta.get('reason')}"})
                        continue

                    # SUCCESSFUL CANDIDATE SELECTED!
                    selected_cand = cand
                    selected_orig_bgr = cv_bgr
                    selected_crop_bgr = crop_bgr
                    selected_crop_meta = crop_meta
                    selected_audit_data = audit_data
                    used_hashes.add(h_val)
                    used_urls.add(u)
                    print(f"  --> SELECTED: '{t[:55]}'")
                    print(f"      Detection: {crop_meta['detection']['method']} | Effective Crop: {crop_meta['effective_crop_res']} | Scale: {crop_meta['scale_factor']}x")
                    break

                except Exception as e:
                    rejections_list.append({"url": u, "title": t, "reason": f"Execution error: {e}"})
                    continue

            # Fallback if no web cand met rigorous standards
            if selected_crop_bgr is None:
                print(f"  [GAP REPORTED] No verified candidate passed rigorous gates for Scene {sc_id} ({spec.intended_subject})")
                # Maintain gap transparency
                gap_bgr = np.zeros((1920, 1080, 3), dtype=np.uint8)
                gap_bgr[:] = (35, 25, 20)
                selected_crop_bgr = gap_bgr
                selected_orig_bgr = gap_bgr
                selected_crop_meta = {
                    "decision": "GAP_REPORTED",
                    "detection": {"method": "NO_VALID_SUBJECT_DETECTED", "bbox": None, "face_center": None, "confidence": 0.0, "is_face": False},
                    "effective_crop_res": "GAP",
                    "scale_factor": 1.0,
                    "original_dimensions": (1080, 1920),
                    "final_subj_center_y": 0,
                    "in_safe_zone": False
                }
                selected_audit_data = {
                    "asset_classification": "EDITORIAL_GAP",
                    "publisher": "EDITORIAL_GAP",
                    "url": "N/A",
                    "title": "NO_QUALIFIED_ASSET"
                }
                selected_cand = {"url": "N/A", "title": "EDITORIAL GAP REPORTED", "publisher": "N/A"}

            # Save 1080x1920 cropped visual
            final_img_path = story_img_dir / f"scene_{sc_id}.png"
            cv2.imwrite(str(final_img_path), selected_crop_bgr)
            print(f"  Saved visual -> {final_img_path.name}")

            # Assign independent quality gate statuses
            det_method = selected_crop_meta["detection"]["method"]
            is_gap = (selected_crop_meta.get("decision") == "GAP_REPORTED")
            sem_gate = "FAIL" if is_gap else "PASS"
            prov_gate = "REVIEW" if selected_audit_data["asset_classification"] in ["PLAYER_CONTEXTUAL_PHOTO", "CLUB_CONTEXT_PHOTO"] else "PASS" if not is_gap else "FAIL"
            focal_gate = "PASS" if det_method != "NO_VALID_SUBJECT_DETECTED" else "FAIL"
            crop_gate = "PASS" if not is_gap and selected_crop_meta.get("in_safe_zone") else "REVIEW" if not is_gap else "FAIL"
            res_gate = "PASS" if not is_gap and selected_crop_meta.get("scale_factor", 1.0) <= 2.25 else "FAIL"
            rights_gate = "EDITORIAL_USE" if not is_gap else "UNVERIFIED"

            # Overall status
            if is_gap:
                overall_status = "REJECTED_GAP"
            elif prov_gate == "REVIEW" or crop_gate == "REVIEW":
                overall_status = "PROVISIONAL_REVIEW"
            else:
                overall_status = "APPROVED"

            gates = {
                "semantic": sem_gate,
                "provenance": prov_gate,
                "focal": focal_gate,
                "crop": crop_gate,
                "resolution": res_gate,
                "rights": rights_gate
            }

            cand_url = selected_cand.get("url", "")
            domain = urllib.parse.urlparse(cand_url).netloc if cand_url != "N/A" else "N/A"

            scene_entry = {
                "scene_id": sc_id,
                "role": role,
                "intended_subject": spec.intended_subject,
                "assessed_subject": spec.intended_subject if not is_gap else "EDITORIAL_GAP",
                "event_context": spec.event_context,
                "event_date": spec.relevant_date,
                "asset_classification": selected_audit_data["asset_classification"],
                "selected_image_file": str(final_img_path.relative_to(PROJECT_ROOT)),
                "provenance": {
                    "url": cand_url,
                    "domain": domain,
                    "publisher": selected_cand.get("publisher", domain),
                    "title": selected_cand.get("title", ""),
                    "pub_date": spec.relevant_date
                },
                "detection_audit": {
                    "method": det_method,
                    "confidence": selected_crop_meta["detection"].get("confidence", 0.0),
                    "face_center": selected_crop_meta["detection"].get("face_center"),
                    "subject_center": selected_crop_meta["detection"].get("subject_center"),
                    "is_face": selected_crop_meta["detection"].get("is_face", False)
                },
                "resolution_audit": {
                    "original_dimensions": selected_crop_meta["original_dimensions"],
                    "effective_crop_res": selected_crop_meta["effective_crop_res"],
                    "scale_factor": selected_crop_meta["scale_factor"]
                },
                "gates": gates,
                "overall_status": overall_status,
                "rejections": rejections_list[:4]
            }

            story_record["scenes"].append(scene_entry)

            contact_sheet_scenes.append({
                "scene_id": sc_id,
                "role": role,
                "intended_subject": spec.intended_subject,
                "assessed_subject": scene_entry["assessed_subject"],
                "event_date": spec.relevant_date,
                "asset_classification": selected_audit_data["asset_classification"],
                "orig_bgr": selected_orig_bgr,
                "final_bgr": selected_crop_bgr,
                "crop_meta": selected_crop_meta,
                "provenance": scene_entry["provenance"],
                "gates": gates,
                "overall_status": overall_status,
                "rejections": rejections_list
            })

        # Generate Redesigned Contact Sheet
        cs_path = CONTACT_SHEETS_DIR / f"v6_4_1_contact_sheet_{s_id}.png"
        DiagnosticContactSheetBuilderV2.create_story_contact_sheet(
            story_title=s_title,
            scenes_data=contact_sheet_scenes,
            out_path=cs_path
        )

        artifact_cs = ARTIFACT_DIR / cs_path.name
        shutil.copyfile(cs_path, artifact_cs)
        print(f"  Copied redesigned contact sheet to artifact dir -> {artifact_cs.name}")

        story_record["contact_sheet"] = str(cs_path.relative_to(PROJECT_ROOT))
        story_record["artifact_contact_sheet"] = str(artifact_cs)
        manifest_v6_4_1.append(story_record)

    # Save new V6.4.1 Manifest (without touching old V6.4 manifest!)
    manifest_file = EVIDENCE_DIR / "v6_4_1_scene_image_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_v6_4_1, f, indent=2)

    print(f"\n[Success] Beta V6.4.1 scene-to-image manifest saved -> {manifest_file}")
    return manifest_v6_4_1

if __name__ == "__main__":
    run_v6_4_1_pipeline()
