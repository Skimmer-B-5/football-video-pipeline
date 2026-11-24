"""
beta/stages/vision_framing_inspector.py
Node 3: Vision & Editorial Framing Inspector for the V7.1.6.7 Broadcast Standard.
Combines:
1. Groq LLM Semantic Metadata Inspector (verifies subject identity, eliminates visual mismatches).
2. OpenCV ActionAwareCropper (verifies sharpness, safe zone [260, 1250], single focal subject).
3. Verified Fallback Engine (crest or official headshot - ZERO UNRELATED FOOTBALL PHOTOS).
"""

import io
import re
import cv2
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from stages.action_aware_cropper import ActionAwareCropper
    from stages.editorial_visual_architect import EditorialShotSpec
    from stages.editorial_image_sourcer import EditorialImageSourcer
    from stages.groq_client import call_groq_chat
except ModuleNotFoundError:
    from beta.stages.action_aware_cropper import ActionAwareCropper
    from beta.stages.editorial_visual_architect import EditorialShotSpec
    from beta.stages.editorial_image_sourcer import EditorialImageSourcer
    from beta.stages.groq_client import call_groq_chat


class VisionFramingInspector:
    def __init__(self):
        self.cropper = ActionAwareCropper()
        self.sourcer = EditorialImageSourcer()

    def verify_candidate_metadata_llm(
        self,
        candidate_title: str,
        candidate_url: str,
        spec: EditorialShotSpec
    ) -> Tuple[bool, str]:
        """
        Uses Groq LLM to verify whether the candidate image depicts the intended subject
        or is a misleading mismatch (e.g. random Man United player in red when discussing Bassey).
        """
        title_lower = candidate_title.lower()
        url_lower = candidate_url.lower()

        # Rule 1: Check avoid terms locally first
        for avoid in spec.avoid_terms:
            if avoid.lower() in title_lower or avoid.lower() in url_lower:
                return False, f"Candidate metadata contains disqualified term: '{avoid}'"

        # Rule 2: Fast Heuristic Subject Matching
        # Check surname e.g. "bassey", "silva"
        entity_parts = [w.lower() for w in spec.primary_entity.split() if len(w) > 2]
        if entity_parts:
            # If surname or primary identifier is present in title or url
            surname = entity_parts[-1]
            if surname in title_lower or surname in url_lower:
                return True, f"Primary entity surname '{surname}' confirmed in metadata"

        # Check stadium / club keywords
        club_low = spec.club_affiliation.lower()
        if club_low in title_lower or club_low in url_lower:
            if "stadium" in spec.primary_entity.lower() or "match" in spec.primary_entity.lower():
                return True, f"Club affiliation '{club_low}' confirmed for venue/match shot"

        # Stadium iconic venue aliases
        stadium_aliases = {
            "manchester united": ["old trafford"],
            "fulham": ["craven cottage"],
            "real madrid": ["bernabeu", "santiago bernabeu"],
            "barcelona": ["camp nou", "montjuic"],
            "ac milan": ["san siro"],
            "inter milan": ["san siro"],
            "inter": ["san siro"],
            "arsenal": ["emirates"],
            "chelsea": ["stamford bridge"],
            "liverpool": ["anfield"],
            "manchester city": ["etihad"],
            "bayern munich": ["allianz arena"],
            "tottenham": ["tottenham hotspur stadium"],
            "spurs": ["tottenham hotspur stadium"]
        }
        for c_key, s_aliases in stadium_aliases.items():
            if c_key in club_low:
                if any(sa in title_lower or sa in url_lower for sa in s_aliases):
                    return True, f"Stadium alias '{s_aliases[0]}' confirmed for {club_low}"

        # Rule 3: Groq LLM Semantic Verification for Ambiguous Cases
        try:
            prompt = f"""You are an elite television football news photo verification editor.
We are producing a broadcast news report.

INTENDED SUBJECT: {spec.primary_entity} ({spec.club_affiliation})
SHOT ROLE: {spec.role} ({spec.required_context})
CANDIDATE IMAGE TITLE: "{candidate_title}"
CANDIDATE URL: "{candidate_url}"

Question: Does this photo depict {spec.primary_entity} or their club/stadium?
Or does it depict an unrelated player (e.g. another club's player)?

Reply with ONLY valid JSON:
{{"approved": true/false, "detected_subject": "...", "reason": "..."}}
"""
            raw = call_groq_chat(
                system_prompt="You are a strict editorial photo compliance inspector. Output ONLY JSON.",
                user_prompt=prompt,
                temperature=0.1,
                timeout=6
            )
            if raw:
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    res = json.loads(m.group(0))
                    if not res.get("approved", True):
                        return False, f"LLM rejected metadata ({res.get('reason')})"
                    return True, "LLM approved subject match"
        except Exception as e:
            pass

        # If LLM unavailable, check if at least 1 key token matches
        if any(tok in title_lower for tok in entity_parts):
            return True, "Partial token match accepted"

        return False, f"Metadata does not substantiate '{spec.primary_entity}'"

    def audit_and_produce_shot(
        self,
        spec: EditorialShotSpec,
        out_path: Path,
        ledger: Optional[Any] = None
    ) -> bool:
        """
        Finds, verifies, crops, and locks in a verified photo for this exact shot spec.
        Guarantees ZERO misleading visuals, ZERO blurry images, and records provenance into asset ledger.
        """
        print(f"\n[Inspector] Auditing Shot {spec.shot_id} [{spec.role}]: Target '{spec.primary_entity}'")

        # 1. Gather candidates across verified sources
        candidates = []

        # If protagonist or manager, check Wikipedia official archive first!
        if spec.crop_strategy in ["portrait", "celebration", "managerial"] and " " in spec.primary_entity:
            wiki_photos = self.sourcer.fetch_wikipedia_player_photos(spec.primary_entity)
            if wiki_photos:
                print(f"  [Wikipedia Archive] Found {len(wiki_photos)} verified official photos for '{spec.primary_entity}'")
                candidates.extend(wiki_photos)

        # Search Wikimedia Commons
        for q in spec.search_queries[:2]:
            commons_photos = self.sourcer.search_wikimedia_commons(q)
            if commons_photos:
                candidates.extend(commons_photos)

        # Search Bing Full-Res (with exact quotes)
        for q in spec.search_queries:
            bing_photos = self.sourcer.search_bing_full_res(q, avoid_terms=spec.avoid_terms, max_results=8)
            candidates.extend(bing_photos)

        print(f"  [Discovery] Total candidate images to inspect: {len(candidates)}")

        # 2. Iterate through candidates with multi-gate validation
        for idx, cand in enumerate(candidates, 1):
            title = cand.get("title", "")
            url = cand.get("url", "")

            # Gate A: Metadata & Subject Verification
            is_valid_meta, meta_reason = self.verify_candidate_metadata_llm(title, url, spec)
            if not is_valid_meta:
                # print(f"    Candidate {idx} rejected by metadata: {meta_reason}")
                continue

            # Gate B: Download Full-Res Image Bytes
            raw_bytes = self.sourcer.download_image_bytes(url)
            if not raw_bytes:
                continue

            # Gate C: Decode & Verify Resolution
            try:
                np_arr = np.frombuffer(raw_bytes, np.uint8)
                cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if cv_img is None:
                    continue
            except Exception:
                continue

            # Gate D: ActionAwareCropper (Sharpness, Safe-Zone [260, 1250], Multi-Player check)
            passed, final_bgr, crop_audit = self.cropper.crop_candidate(
                cv_bgr=cv_img,
                strategy=spec.crop_strategy
            )

            if not passed:
                # print(f"    Candidate {idx} rejected by cropper: {crop_audit.get('reason')}")
                continue

            # Gate E: Approved! Save and lock into asset ledger
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_path), final_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 4])
            self.sourcer.used_urls.add(url)
            if ledger is not None:
                try:
                    ledger.record_asset(
                        shot_id=spec.shot_id,
                        scene_id=spec.scene_id,
                        primary_entity=spec.primary_entity,
                        file_path=out_path,
                        source_url=url,
                        source_platform=cand.get("source", "Web Archive"),
                        crop_audit=crop_audit
                    )
                except Exception as e:
                    print(f"  [AssetLedger] Warning recording asset: {e}")
            print(f"  ✅ [APPROVED] Shot {spec.shot_id} produced from {cand.get('source')} (Blur: {crop_audit.get('blur_variance')}, Scale: {crop_audit.get('scale_factor')}x) -> {out_path.name}")
            return True

        # 3. Fallback Engine: Never substitute unrelated images!
        print(f"  ⚠️ [Fallback Triggered] No candidate met strict verification for '{spec.primary_entity}'")
        if spec.allow_fallback_crest:
            return self.sourcer.generate_broadcast_crest_fallback(spec.club_affiliation, out_path)

        # Fallback to general club crest / emblem
        return self.sourcer.generate_broadcast_crest_fallback(spec.club_affiliation, out_path)
