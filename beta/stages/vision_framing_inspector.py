"""
beta/stages/vision_framing_inspector.py
Node 3: Vision & Editorial Framing Inspector for the V7.1.6.7 / V2 Broadcast Standard.
Combines:
1. Metadata & Disqualified Term Screening (eliminates wrong clubs, obsolete coaches, watermarks).
2. True Pixel Identity Verification via OpenCV YuNet + SFace against Wikipedia official portraits
   (blocks impersonators/mismatches like celebrating teammates or wrong managers).
3. Perceptual dHash + SHA256 Zero-Reuse Enforcement across scenes and runs.
4. Optional Cloud VLM Advisory Check (when API billing/token is valid, cleanly skipped otherwise).
5. OpenCV ActionAwareCropper (resolution floor, Laplacian blur >= 45, X+Y safe-zones).
6. Verified Club Crest Card Fallback (never substitutes unrelated stock football clutter).
"""

import os
import re
import cv2
import json
import hashlib
import base64
import urllib.request
import urllib.error
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from stages.action_aware_cropper import ActionAwareCropper
    from stages.llm_visual_director import EditorialShotSpec
    from stages.editorial_image_sourcer import EditorialImageSourcer
    from stages.groq_client import call_groq_chat
except ModuleNotFoundError:
    from beta.stages.action_aware_cropper import ActionAwareCropper
    from beta.stages.llm_visual_director import EditorialShotSpec
    from beta.stages.editorial_image_sourcer import EditorialImageSourcer
    from beta.stages.groq_client import call_groq_chat


def compute_dhash(cv_bgr: np.ndarray) -> int:
    """Computes a 64-bit perceptual difference hash for near-duplicate rejection."""
    gray = cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    val = 0
    for bit in diff.flatten():
        val = (val << 1) | int(bool(bit))
    return val


class VisionFramingInspector:
    def __init__(self):
        self.cropper = ActionAwareCropper()
        self.sourcer = EditorialImageSourcer()
        self._vlm_unavailable_logged = False

    def verify_candidate_metadata_llm(
        self,
        candidate_title: str,
        candidate_url: str,
        spec: EditorialShotSpec
    ) -> Tuple[bool, str]:
        """
        Verifies metadata & URLs before downloading bytes.
        Explicitly rejects obsolete entities/avoid_terms and checks entity relevance.
        """
        title_lower = (candidate_title or "").lower()
        url_lower = (candidate_url or "").lower()

        # Rule 1: Check avoid terms locally (includes obsolete managers like Ruben Amorim)
        for avoid in spec.avoid_terms:
            av = avoid.lower().strip()
            if av and (av in title_lower or av in url_lower):
                return False, f"Candidate metadata contains disqualified term: '{avoid}'"

        # Rule 2: Entity/Club relevance check (for Bing results where title or URL confirms topic)
        entity_parts = [w.lower() for w in spec.primary_entity.split() if len(w) > 2]
        full_name_low = spec.primary_entity.lower()
        if full_name_low in title_lower or full_name_low.replace(" ", "-") in url_lower or full_name_low.replace(" ", "_") in url_lower:
            return True, f"Full entity '{spec.primary_entity}' matched in metadata"

        club_low = spec.club_affiliation.lower()
        stadium_aliases = {
            "manchester united": ["old trafford"],
            "fulham": ["craven cottage"],
            "real madrid": ["bernabeu", "santiago bernabeu"],
            "barcelona": ["camp nou", "montjuic"],
            "ac milan": ["san siro"],
            "inter milan": ["san siro"],
            "arsenal": ["emirates"],
            "chelsea": ["stamford bridge"],
            "liverpool": ["anfield"],
            "manchester city": ["etihad"],
            "bayern munich": ["allianz arena"],
            "tottenham": ["tottenham hotspur stadium"]
        }
        for c_key, s_aliases in stadium_aliases.items():
            if c_key in club_low and any(sa in title_lower or sa in url_lower for sa in s_aliases):
                return True, f"Stadium alias '{s_aliases[0]}' confirmed"

        if entity_parts and (
            all(tok in title_lower or tok in url_lower for tok in entity_parts)
            or (entity_parts[-1] in title_lower and (club_low in title_lower or "premier league" in title_lower or "football" in title_lower or "fc" in title_lower))
        ):
            return True, f"Deterministic entity/club token match for '{spec.primary_entity}'"

        # Rule 3: Optional Groq LLM Semantic Verification ONLY on ambiguous metadata (budget <= 2 per shot)
        meta_calls = getattr(self, "_meta_llm_calls", 0)
        if meta_calls < 2:
            self._meta_llm_calls = meta_calls + 1
            try:
                prompt = f"""You are a football news photo verification editor.
INTENDED SUBJECT: {spec.primary_entity} ({spec.club_affiliation})
SHOT ROLE: {spec.role} ({spec.required_context})
AVOID TERMS: {', '.join(spec.avoid_terms)}
CANDIDATE IMAGE TITLE: "{candidate_title}"
CANDIDATE URL: "{candidate_url}"

Does this photo specifically depict {spec.primary_entity} or {spec.club_affiliation}'s ground/action, and NOT another club or obsolete coach?
Reply ONLY valid JSON: {{"approved": true/false, "reason": "..."}}"""
                raw = call_groq_chat(
                    system_prompt="You are a strict editorial photo compliance inspector. Output ONLY JSON.",
                    user_prompt=prompt,
                    preferred_model="qwen/qwen3.8-27b",
                    fallback_model="openai/gpt-oss-20b",
                    temperature=0.1,
                    timeout=6
                )
                if raw:
                    m = re.search(r'\{.*\}', raw, re.DOTALL)
                    if m:
                        res = json.loads(m.group(0))
                        if not res.get("approved", False):
                            return False, f"LLM rejected metadata ({res.get('reason')})"
                        return True, "LLM approved metadata"
            except Exception:
                pass

        if entity_parts and any(tok in title_lower for tok in entity_parts):
            return True, "Partial entity token matched in title"
        if club_low in title_lower and spec.crop_strategy in ("tactical", "stadium"):
            return True, "Club matched for stadium/tactical shot"

        return False, f"Metadata does not substantiate '{spec.primary_entity}'"

    def _optional_vlm_pixel_check(self, cv_bgr: np.ndarray, spec: EditorialShotSpec) -> Tuple[Optional[bool], str]:
        """Advisory VLM pixel check via Gemini Vision if key has active quota; never fakes pass if 401/403."""
        gem_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not gem_key or self._vlm_unavailable_logged:
            return None, "VLM unavailable"
        try:
            resized = cv2.resize(cv_bgr, (384, 384), interpolation=cv2.INTER_AREA)
            ok, enc = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                return None, "Encode skip"
            b64 = base64.b64encode(enc.tobytes()).decode("ascii")
            prompt = (
                f"Inspect this football photograph. Expected: {spec.primary_entity} ({spec.club_affiliation}) "
                f"- context: {spec.required_context}. Must NOT be: {', '.join(spec.avoid_terms[:5])}. "
                'Reply ONLY JSON: {"approved": true/false, "depicted": "..."}'
            )
            payload = {"contents": [{"parts": [{"inline_data": {"mime_type": "image/jpeg", "data": b64}}, {"text": prompt}]}], "generationConfig": {"temperature": 0.1}}
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gem_key}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                txt = json.loads(r.read().decode("utf-8"))["candidates"][0]["content"]["parts"][0]["text"]
            m = re.search(r'\{.*\}', txt, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                return bool(parsed.get("approved", True)), f"VLM: {parsed.get('depicted', '')}"
        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                self._vlm_unavailable_logged = True
                print(f"  [VLM Advisory] Gemini HTTP {he.code} unavailable -> using local YuNet+SFace pixel verification.")
        except Exception:
            pass
        return None, "VLM skipped"

    def verify_candidate_pixels(
        self,
        cv_bgr: np.ndarray,
        spec: EditorialShotSpec,
        protagonist_name: str = ""
    ) -> Tuple[bool, str]:
        """
        True Pixel Verification Gate:
        1. For named entities (players/managers), compares candidate faces against official
           Wikipedia 128-D SFace embedding to catch wrong players or obsolete managers!
        2. For S01 concealment, rejects if SFace identifies protagonist inside the frame.
        3. For stadium/venue tactical shots, rejects close-up headshots filling > 8% of frame.
        4. Optionally applies VLM check when cloud quota is active.
        """
        det_engine = self.cropper.detector
        ent = (spec.primary_entity or "").strip()
        ent_low = ent.lower()
        is_venue_shot = any(k in ent_low for k in ("stadium", "cottage", "trafford", "anfield", "emirates", "bernabeu", "arena", "matchday", "park", "bridge"))

        # 0. GPU Person / Sports-Ball Object Detection & Pixel Content Awareness
        scene_objects = det_engine.detect_scene_objects(cv_bgr)
        self._last_scene_objects = scene_objects
        aware_ok, aware_reason, aware_metrics = det_engine.evaluate_content_awareness(
            cv_bgr, strategy=spec.crop_strategy, is_venue=is_venue_shot, objects=scene_objects
        )
        self._last_content_metrics = aware_metrics
        if not aware_ok:
            return False, f"Content Awareness Reject: {aware_reason}"

        # 1. S01 Protagonist Concealment Enforcement (Pixels)
        if spec.scene_id == "S01" and protagonist_name:
            prot_match, prot_sim, _ = det_engine.verify_face_identity(cv_bgr, protagonist_name, threshold=0.28)
            if prot_match:
                return False, f"S01 Anonymity Violation: SFace matched protagonist '{protagonist_name}' (sim={prot_sim})"

        # 2. Venue / Stadium Tactical Shot check (reject big human portraits posing as stadiums)
        if is_venue_shot:
            faces = det_engine.detect_yunet_faces(cv_bgr)
            ih, iw = cv_bgr.shape[:2]
            for f in faces:
                if (f["area"] / float(iw * ih)) > 0.06:
                    return False, f"Stadium shot contains giant close-up face ({f['area']/(iw*ih)*100:.1f}% of frame)"
            return True, "Stadium/venue pixel check passed"

        # 3. Named Player / Manager Identity Check via SFace
        self._last_matched_bbox = None
        if " " in ent and spec.crop_strategy in ("portrait", "managerial", "match_action", "celebration"):
            matched, sim, reason, matched_bbox = det_engine.verify_face_identity_with_box(cv_bgr, ent, threshold=0.27)
            if matched is False:
                return False, f"Pixel Identity Mismatch: {reason}"
            if matched is True:
                self._last_matched_bbox = matched_bbox
                return True, f"Pixel Identity Verified: {reason}"
            # If Wikipedia lacked a reference face OR candidate was extreme side-profile where SFace returned None,
            # allow optional VLM check or pass to cropper if strategy is dynamic match_action.
            if spec.crop_strategy == "managerial":
                # Managers on touchline / press conf almost always have visible faces; reject faceless shots when Ref exists
                if det_engine.get_reference_face_embedding(ent) is not None and not det_engine.detect_yunet_faces(cv_bgr):
                    return False, f"Managerial shot for '{ent}' has no detectable face for identity verification"

        # 4. Optional VLM sanity check
        vlm_ok, vlm_reason = self._optional_vlm_pixel_check(cv_bgr, spec)
        if vlm_ok is False:
            return False, vlm_reason

        return True, "Pixel gates passed"

    def audit_and_produce_shot(
        self,
        spec: EditorialShotSpec,
        out_path: Path,
        ledger: Optional[Any] = None,
        protagonist_name: str = "",
        story_id: str = "",
        extra_candidate_urls: Optional[List[str]] = None,
        out_audit: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Finds, verifies, crops, and locks in a verified photo for this exact shot spec.
        Guarantees zero image reuse (URL + SHA256 + dHash), pixel identity matching,
        CUDA person/ball content awareness, blur floor, and X/Y safe-zone framing.
        """
        print(f"\n[Inspector] Auditing Shot {spec.shot_id} [{spec.role}]: Target '{spec.primary_entity}'")
        self._meta_llm_calls = 0
        self.sourcer.hydrate_from_ledgers(current_ledger=ledger, current_story_id=story_id)

        candidates = []

        # Tier 0: Exact Scraped Article Hero / Candidate Images (skip protagonist beats if S01 anonymity active)
        if extra_candidate_urls and spec.scene_id != "S01":
            for eu in extra_candidate_urls:
                if eu and not self.sourcer.is_url_or_hash_used(url=eu):
                    candidates.append({
                        "url": eu,
                        "title": f"{spec.primary_entity} {spec.club_affiliation} article hero photo",
                        "source": "Scraped Article Hero (Direct)",
                        "priority": 0,
                    })

        # Tier 1: ESPN Multi-League Public Media Bank
        espn_photos = self.sourcer.fetch_espn_photo_bank(spec.primary_entity, spec.club_affiliation, max_results=6)
        if espn_photos:
            print(f"  [ESPN Media] Found {len(espn_photos)} match/news photos for '{spec.primary_entity}'")
            candidates.extend(espn_photos)

        # Tier 2: Wikipedia Official Archive (best for managers/players)
        if spec.crop_strategy in ["portrait", "celebration", "managerial"] and " " in spec.primary_entity:
            wiki_photos = self.sourcer.fetch_wikipedia_player_photos(spec.primary_entity)
            if wiki_photos:
                print(f"  [Wikipedia Archive] Found {len(wiki_photos)} verified photos for '{spec.primary_entity}'")
                candidates.extend(wiki_photos)

        # Tier 3: Sports News Article Hero Extraction (Sky Sports, BBC, Guardian, FourFourTwo)
        if spec.search_queries:
            news_hero_photos = self.sourcer.search_news_article_images(
                spec.search_queries[0], avoid_terms=spec.avoid_terms, max_results=6
            )
            if news_hero_photos:
                print(f"  [News Articles] Extracted {len(news_hero_photos)} editorial article hero photos")
                candidates.extend(news_hero_photos)

        # Tier 4: Wikimedia Commons
        for q in spec.search_queries[:2]:
            commons_photos = self.sourcer.search_wikimedia_commons(q)
            if commons_photos:
                candidates.extend(commons_photos)

        # Tier 5: Bing Full-Res + Social/Editorial Coverage (ESPN FC, Sky, BBC, PL, Fabrizio/Reddit press)
        for q in spec.search_queries:
            bing_photos = self.sourcer.search_bing_full_res(q, avoid_terms=spec.avoid_terms, max_results=10)
            candidates.extend(bing_photos)
        social_photos = self.sourcer.search_social_editorial_candidates(
            spec.primary_entity, spec.club_affiliation, avoid_terms=spec.avoid_terms, max_results=8
        )
        candidates.extend(social_photos)

        candidates.sort(key=lambda c: int(c.get("priority", 3)))

        print(f"  [Discovery] Total candidate images to inspect: {len(candidates)}")

        for idx, cand in enumerate(candidates, 1):
            title = cand.get("title", "")
            url = cand.get("url", "")

            if self.sourcer.is_url_or_hash_used(url=url):
                continue

            # Gate A: Metadata & Subject Verification
            is_valid_meta, meta_reason = self.verify_candidate_metadata_llm(title, url, spec)
            if not is_valid_meta:
                continue

            # Gate B: Download Full-Res Image Bytes & SHA256 Uniqueness Check
            raw_bytes = self.sourcer.download_image_bytes(url)
            if not raw_bytes:
                continue
            raw_sha = hashlib.sha256(raw_bytes).hexdigest()
            if self.sourcer.is_url_or_hash_used(sha256_hex=raw_sha):
                continue

            # Gate C: Decode & Perceptual dHash Deduplication
            try:
                np_arr = np.frombuffer(raw_bytes, np.uint8)
                cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if cv_img is None:
                    continue
                img_dhash = compute_dhash(cv_img)
                if self.sourcer.is_url_or_hash_used(dhash_val=img_dhash):
                    print(f"    Candidate {idx} rejected (perceptual near-duplicate already used)")
                    continue
            except Exception:
                continue

            # Gate D: Pixel-Level Identity & Context Verification (YuNet + SFace + VLM advisory)
            px_ok, px_reason = self.verify_candidate_pixels(cv_img, spec, protagonist_name=protagonist_name)
            if not px_ok:
                print(f"    Candidate {idx} rejected by Pixel Gate: {px_reason}")
                continue

            # Gate E: ActionAwareCropper (Body+Face+Ball Joint Framing + Wide Broadcast Card fallback)
            preferred_box = getattr(self, "_last_matched_bbox", None)
            scene_objs = getattr(self, "_last_scene_objects", {}) or {}
            det_engine = self.cropper.detector
            matched_body = det_engine.match_face_to_person_box(preferred_box, scene_objs.get("persons", []))
            top_ball = scene_objs["balls"][0][:4] if scene_objs.get("balls") else None
            passed, final_bgr, crop_audit = self.cropper.crop_candidate(
                cv_bgr=cv_img,
                strategy=spec.crop_strategy,
                preferred_bbox=preferred_box,
                body_box=matched_body,
                ball_box=top_ball,
                person_boxes=scene_objs.get("persons", []),
            )
            if not passed:
                continue

            # Gate F: Post-Crop Pixel Identity & Anonymity Verification (skip strict post-crop SFace on broadcast_card
            # ONLY if downscaled inset face < 35px, though 1000x562 inset keeps faces > 60px!)
            ent_name = (spec.primary_entity or "").strip()
            if spec.scene_id == "S01" and protagonist_name:
                leak_match, leak_sim, _ = det_engine.verify_face_identity(final_bgr, protagonist_name, threshold=0.25)
                if leak_match:
                    print(f"    Candidate {idx} rejected Post-Crop: S01 anonymity leak ({leak_sim})")
                    continue
            elif " " in ent_name and spec.crop_strategy in ("portrait", "managerial", "match_action", "celebration"):
                post_match, post_sim, post_reason = det_engine.verify_face_identity(final_bgr, ent_name, threshold=0.22)
                if post_match is False:
                    print(f"    Candidate {idx} rejected Post-Crop: {post_reason}")
                    continue

            crop_audit["content_metrics"] = getattr(self, "_last_content_metrics", {})
            if out_audit is not None:
                out_audit.clear()
                out_audit.update(crop_audit)

            # Approved! Save and lock into both asset ledger & zero-reuse registry
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_path), final_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 4])
            self.sourcer.record_used_image(url=url, sha256_hex=raw_sha, dhash_val=img_dhash, story_id=story_id)
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
            print(f"  ✅ [APPROVED] Shot {spec.shot_id} ({px_reason}) [Blur: {crop_audit.get('blur_variance')}, Scale: {crop_audit.get('scale_factor')}x] -> {out_path.name}")
            return True

        print(f"  ⚠️ [Fallback Triggered] No candidate met strict verification for '{spec.primary_entity}'")
        return self.sourcer.generate_broadcast_crest_fallback(spec.club_affiliation, out_path)
