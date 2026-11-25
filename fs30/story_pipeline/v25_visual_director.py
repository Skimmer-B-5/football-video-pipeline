"""
V2.5 Visual Sourcing, CUDA Content Awareness & Tactile 2.5D Paper Asset Builder for FS30.
Connects beta/'s V2.5 EditorialImageSourcer + CUDA FasterRCNN + SFace Identity Verification +
ActionAwareCropper with fs30/'s rembg matte refiner, proportional archival photo mounter,
dynamic newspaper highlighter cards, rubber stamps, and 43-asset reusable paper library.
"""

import gc
import io
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "beta") not in sys.path:
    sys.path.insert(1, str(PROJECT_ROOT / "beta"))

from beta.stages.editorial_image_sourcer import EditorialImageSourcer, DISQUALIFIED_DOMAINS, DISQUALIFIED_TITLE_TERMS
from beta.stages.semantic_image_procurement import EnhancedSubjectDetector
from beta.stages.vision_framing_inspector import compute_dhash
from beta.stages.action_aware_cropper import ActionAwareCropper
from fs30.cutout_refiner import refine_cutout_matte
from fs30.paper_compositor import apply_handcut_paper_edge, multiply_paper_texture
from fs30.story_pipeline.photo_mounter import mount_archival_photo, scale_cutout_proportional
from fs30.story_pipeline.paper_widgets import (
    get_font,
    wrap_text_to_width,
    create_torn_headline_banner,
    REUSABLE_STOCK_DIR,
    ARCHIVAL_RED,
    CHARCOAL,
)
from fs30.story_pipeline.story_director import StoryPackage, StoryBeatPlan

REMOTION_DOC_PUBLIC = PROJECT_ROOT / "beta" / "remotion" / "public" / "doc_stories"
BADGES_DIR = Path(__file__).resolve().parent / "assets" / "badges"


def _dhash_distance(h1: int, h2: int) -> int:
    return bin(int(h1) ^ int(h2)).count("1")


def create_dynamic_rubber_stamp(stamp_text: str, sub_text: str = "DISCIPLINARY RECORD") -> Image.Image:
    """Renders a crisp archival red rubber stamp over an aged off-white slip for high legibility on any backdrop."""
    w, h = 440, 170
    stamp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(stamp)

    paper_fill = (246, 241, 226, 228)
    red = (198, 18, 36, 248)
    f_main = get_font("headline", 54)
    # Auto-fit stamp text
    cur_sz = 54
    while cur_sz > 28:
        ft = get_font("headline", cur_sz)
        bb = ft.getbbox(stamp_text.upper())
        if (bb[2] - bb[0]) <= w - 60:
            f_main = ft
            break
        cur_sz -= 3
    f_sub = get_font("meta", 20)

    # Warm archival paper slip behind double ink border so stamp reads crisply over dark crowds
    draw.rectangle([(6, 6), (w - 6, h - 6)], fill=paper_fill)
    draw.rectangle([(12, 12), (w - 12, h - 12)], outline=red, width=6)
    draw.rectangle([(22, 22), (w - 22, h - 22)], outline=red, width=2)
    draw.text((w // 2, 74), stamp_text.upper(), font=f_main, fill=red, anchor="mm")
    draw.text((w // 2, 124), sub_text.upper(), font=f_sub, fill=(172, 20, 36, 235), anchor="mm")

    # Subtle distressed ink texture grit (mild alpha wear while preserving slip backing)
    arr = np.array(stamp)
    rng = np.random.default_rng(abs(hash(stamp_text)) % 10000)
    grit = np.where(rng.random((h, w)) > 0.08, 1.0, 0.72)
    arr[:, :, 3] = (arr[:, :, 3] * grit).astype(np.uint8)
    stamp_distressed = Image.fromarray(arr).rotate(-7.5, resample=Image.Resampling.BICUBIC, expand=True)
    return stamp_distressed


def create_newspaper_highlighter_card(
    publication: str,
    date_text: str,
    headline: str,
    quote_excerpt: str,
    highlight_phrase: str,
    width: int = 920,
) -> Tuple[Image.Image, List[Dict[str, float]]]:
    """
    Renders a realistic cream aged-newsprint card via Source Serif 4 & Barlow Condensed,
    returning both the transparent PNG and normalized % bounding boxes for Remotion's
    animated translucent yellow highlighter wipe.
    """
    newsprint_path = REUSABLE_STOCK_DIR / "textures" / "texture_variant_b_newspaper_newsprint.jpg"
    if newsprint_path.exists():
        with Image.open(newsprint_path) as tx:
            base = ImageOps.fit(tx.convert("RGB"), (width, 520), Image.Resampling.LANCZOS)
            # Soften newsprint into light readable cream sheet
            arr = np.clip(np.array(base, dtype=np.float32) * 0.25 + 195.0, 0, 248).astype(np.uint8)
            sheet = Image.fromarray(arr).convert("RGBA")
    else:
        sheet = Image.new("RGBA", (width, 520), (242, 236, 222, 255))

    draw = ImageDraw.Draw(sheet)
    pad_x = 54
    max_w = width - pad_x * 2

    # Masthead rule + publication name
    f_pub = get_font("serif", 28)
    f_date = get_font("meta", 22)
    draw.text((pad_x, 34), publication.upper(), font=f_pub, fill=CHARCOAL)
    d_bb = f_date.getbbox(date_text.upper())
    draw.text((width - pad_x - (d_bb[2] - d_bb[0]), 38), date_text.upper(), font=f_date, fill=(95, 92, 86, 255))
    draw.line([(pad_x, 76), (width - pad_x, 76)], fill=(32, 34, 38, 255), width=4)
    draw.line([(pad_x, 84), (width - pad_x, 84)], fill=(140, 134, 124, 255), width=1)

    # Newspaper headline
    f_hl = get_font("headline", 54)
    hl_lines = wrap_text_to_width(headline.upper(), f_hl, max_w)[:2]
    y_cur = 104
    for line in hl_lines:
        draw.text((pad_x, y_cur), line, font=f_hl, fill=CHARCOAL)
        y_cur += 58

    y_cur += 14
    draw.line([(pad_x, y_cur), (width - pad_x, y_cur)], fill=(165, 158, 148, 255), width=2)
    y_cur += 22

    # Body excerpt in Source Serif 4 with per-line highlight box computation
    f_body = get_font("serif", 32)
    body_lines = wrap_text_to_width(quote_excerpt, f_body, max_w)[:4]
    phrase_low = (highlight_phrase or "").strip().lower()
    phrase_tokens = [w.strip(".,;:!?\"'") for w in phrase_low.split() if len(w.strip(".,;:!?\"'")) > 2]

    raw_rects: List[Tuple[int, int, int, int]] = []
    line_h = 46
    for line in body_lines:
        draw.text((pad_x, y_cur), line, font=f_body, fill=(28, 30, 36, 255))
        line_low = line.lower()
        # Check direct phrase match or significant token overlap on this line
        matched_span = None
        if phrase_low and phrase_low in line_low:
            idx = line_low.find(phrase_low)
            matched_span = (idx, idx + len(phrase_low))
        elif phrase_tokens:
            hits = [tok for tok in phrase_tokens if tok in line_low]
            if len(hits) >= max(1, min(2, len(phrase_tokens))):
                s_idx = min(line_low.find(h) for h in hits)
                e_idx = max(line_low.find(h) + len(h) for h in hits)
                matched_span = (s_idx, e_idx)

        if matched_span:
            prefix = line[:matched_span[0]]
            sub = line[matched_span[0]:matched_span[1]]
            pre_bb = f_body.getbbox(prefix) if prefix else (0, 0, 0, 0)
            sub_bb = f_body.getbbox(sub)
            hx1 = pad_x + (pre_bb[2] - pre_bb[0]) - 6
            hw = (sub_bb[2] - sub_bb[0]) + 14
            raw_rects.append((hx1, y_cur - 2, hw, 42))

        y_cur += line_h

    # Fallback highlight box on first line if substring drifted slightly
    if not raw_rects and body_lines:
        l0_bb = f_body.getbbox(body_lines[0])
        raw_rects.append((pad_x - 4, y_cur - len(body_lines) * line_h - 2, min(max_w, (l0_bb[2] - l0_bb[0]) + 8), 42))

    final_h = max(320, min(520, y_cur + 38))
    sheet = sheet.crop((0, 0, width, final_h))

    # Subtle deckle paper edge mask + soft white border
    mask = Image.new("L", (width, final_h), 0)
    mdraw = ImageDraw.Draw(mask)
    pts = [(6, 6)]
    for x in range(20, width - 10, 28):
        pts.append((x, 6 + int(2.5 * np.sin(x * 0.08))))
    pts.append((width - 6, 6))
    for y in range(20, final_h - 10, 24):
        pts.append((width - 6 + int(2.0 * np.cos(y * 0.09)), y))
    pts.append((width - 6, final_h - 6))
    for x in range(width - 20, 10, -28):
        pts.append((x, final_h - 6 + int(2.5 * np.sin(x * 0.07))))
    pts.append((6, final_h - 6))
    mdraw.polygon(pts, fill=255)
    sheet.putalpha(mask)

    norm_rects = [
        {
            "x_pct": round((rx / float(width)) * 100.0, 2),
            "y_pct": round((ry / float(final_h)) * 100.0, 2),
            "w_pct": round((rw / float(width)) * 100.0, 2),
            "h_pct": round((rh / float(final_h)) * 100.0, 2),
        }
        for (rx, ry, rw, rh) in raw_rects
    ]
    return sheet, norm_rects


class V25DocumentaryVisualDirector:
    """Produces verified, aspect-intact, zero-reuse 2.5D paper-cut assets for fs30."""

    def __init__(self, run_id: str, run_dir: Path):
        self.run_id = run_id
        self.run_dir = Path(run_dir)
        self.staged_dir = self.run_dir / "staged_assets"
        self.staged_dir.mkdir(parents=True, exist_ok=True)
        self.public_dir = REMOTION_DOC_PUBLIC / run_id
        if self.public_dir.exists():
            shutil.rmtree(self.public_dir, ignore_errors=True)
        self.public_dir.mkdir(parents=True, exist_ok=True)

        self.sourcer = EditorialImageSourcer()
        self.sourcer.reset()
        self.detector = EnhancedSubjectDetector()
        self.cropper = ActionAwareCropper(target_w=1080, target_h=1920)
        self._rembg_session = None

        self.used_urls: set = set()
        self.used_hashes: set = set()
        self.used_dhashes: List[int] = []
        self.provenance_records: List[Dict[str, Any]] = []

    def _get_rembg(self):
        if self._rembg_session is None:
            import rembg
            print("[DocVisual] Loading rembg u2netp segmenter...")
            self._rembg_session = rembg.new_session("u2netp")
        return self._rembg_session

    def release_models(self):
        """Strictly frees CUDA/ONNX models before voice synthesis loads."""
        EnhancedSubjectDetector.release_gpu_memory()
        if self._rembg_session is not None:
            self._rembg_session = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        print("[DocVisual] Released FasterRCNN & rembg sessions cleanly.")

    def _stage_to_public(self, local_path: Path) -> str:
        dest = self.public_dir / local_path.name
        shutil.copy2(str(local_path), str(dest))
        return f"/doc_stories/{self.run_id}/{local_path.name}"

    def _stage_shared_library_assets(self) -> Dict[str, str]:
        shared: Dict[str, str] = {}
        copy_map = {
            "badge": BADGES_DIR / "fs30_official_badge.png",
            "tv_bug": PROJECT_ROOT / "data" / "branding" / "user_bezel_tv_bug.png",
            "paper_texture": REUSABLE_STOCK_DIR / "textures" / "texture_variant_b_newspaper_newsprint.jpg",
            "film_grain": REUSABLE_STOCK_DIR / "textures" / "texture_variant_e_film_grain.jpg",
            "reticle_circle": REUSABLE_STOCK_DIR / "markers" / "marker_circle_reticle.png",
            "marker_arrow": REUSABLE_STOCK_DIR / "markers" / "marker_arrow_right.png",
            "tape_marker": REUSABLE_STOCK_DIR / "date_labels" / "date_label_variant_a_torn_tag.png",
        }
        for key, src in copy_map.items():
            if src.exists():
                shared[key] = self._stage_to_public(src)
        return shared

    def _gather_candidates(
        self,
        entity_name: str,
        query: str,
        fallback_query: str,
        is_venue: bool = False,
        extra_avoid: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        base_entity = entity_name.split(" (")[0].strip() if entity_name else ""
        # Tier 1: ESPN Public Media Archive
        candidates.extend(self.sourcer.fetch_espn_photo_bank(base_entity, max_results=5))
        # Tier 2: News Articles og:image
        candidates.extend(self.sourcer.search_news_article_images(query, max_results=5))
        # Tier 3: Wikipedia Archive (uses full disambiguated title when available)
        if entity_name and " " in base_entity and not is_venue:
            candidates.extend(self.sourcer.fetch_wikipedia_player_photos(entity_name, max_results=5))
        # Tier 4: Wikimedia Commons
        candidates.extend(self.sourcer.search_wikimedia_commons(query, max_results=4))
        # Tier 5: Bing Full-Res + Social Editorial Press
        for q in [query, fallback_query]:
            if q:
                candidates.extend(self.sourcer.search_bing_full_res(q, max_results=10))
        if base_entity and not is_venue:
            candidates.extend(self.sourcer.search_social_editorial_candidates(base_entity, max_results=6))

        q_low = f"{query} {fallback_query}".lower()
        avoid_terms = [a.lower() for a in (extra_avoid or []) if a.lower() not in q_low]

        # Extract specific historical event/club/opponent tokens so era-specific query hits outrank generic headshots
        generic_toks = set((base_entity or "").lower().split()) | {
            "football", "soccer", "player", "match", "action", "portrait", "celebration",
            "stadium", "pitch", "crowd", "vs", "and", "the", "bite", "biting", "press", "conference",
        }
        event_tokens = [
            t for t in re.findall(r"[a-z0-9]{3,}", query.lower())
            if t not in generic_toks
        ]

        # Deduplicate and rank by event-query relevance FIRST, then tier priority
        deduped: List[Dict[str, Any]] = []
        seen_u = set()
        for c in candidates:
            u = (c.get("url") or "").strip()
            if not u or u in seen_u or u in self.used_urls:
                continue
            low = u.lower()
            if any(b in low for b in DISQUALIFIED_DOMAINS) or "://shop." in low or "/shop/" in low:
                continue
            title_low = (c.get("title") or "").lower()
            if any(t in title_low for t in DISQUALIFIED_TITLE_TERMS):
                continue
            if avoid_terms and any(av in title_low or av in low for av in avoid_terms):
                continue
            seen_u.add(u)
            blob = f"{title_low} {low} {(c.get('page_url') or '').lower()}"
            ev_hits = sum(1 for tok in event_tokens if tok in blob)
            c["_ev_score"] = ev_hits
            deduped.append(c)
        deduped.sort(key=lambda c: (-int(c.get("_ev_score", 0)), int(c.get("priority", 3))))
        return deduped

    def _download_unique_valid(self, url: str) -> Optional[Tuple[np.ndarray, str, int, float]]:
        img_bytes = self.sourcer.download_image_bytes(url)
        if not img_bytes:
            return None
        sha = hashlib.sha256(img_bytes).hexdigest()
        if sha in self.used_hashes:
            return None
        arr = np.frombuffer(img_bytes, np.uint8)
        cv_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if cv_bgr is None:
            return None
        ih, iw = cv_bgr.shape[:2]
        if min(iw, ih) < 420:
            return None
        blur = float(cv2.Laplacian(cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
        if blur < 40.0:
            return None
        dh = compute_dhash(cv_bgr)
        if any(_dhash_distance(dh, ex) <= 6 for ex in self.used_dhashes):
            return None
        return cv_bgr, sha, dh, blur

    def _register_used(self, url: str, sha: str, dh: int, meta: Dict[str, Any]):
        self.used_urls.add(url)
        self.used_hashes.add(sha)
        self.used_dhashes.append(dh)
        self.provenance_records.append(meta)

    def _resolve_canonical_wiki_name(self, entity_name: str) -> str:
        """
        Resolves unaccented names AND Wikipedia disambiguation pages
        (e.g. 'Luis Suarez' -> 'Luis Suárez (footballer, born 1987)') so SFace ref always loads.
        """
        if not entity_name:
            return entity_name
        if not hasattr(self, "_wiki_name_cache"):
            self._wiki_name_cache = {}
        key = entity_name.strip().lower()
        if key in self._wiki_name_cache:
            return self._wiki_name_cache[key]

        import urllib.request, urllib.parse, json

        def _valid_summary(title: str) -> Optional[str]:
            try:
                slug = urllib.parse.quote(title.strip().replace(" ", "_"))
                su = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                sreq = urllib.request.Request(su, headers={"User-Agent": "FS30Documentary/2.5"})
                with urllib.request.urlopen(sreq, timeout=6) as sr:
                    sdata = json.loads(sr.read().decode("utf-8", errors="ignore"))
                if sdata.get("type") == "disambiguation":
                    return None
                if sdata.get("originalimage") or sdata.get("thumbnail"):
                    return str(sdata.get("title") or title).strip()
            except Exception:
                return None
            return None

        resolved = entity_name.strip()
        found = _valid_summary(resolved)
        if not found:
            for q_str in (f"{resolved} footballer", resolved):
                try:
                    u = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(q_str)}&limit=5&format=json"
                    req = urllib.request.Request(u, headers={"User-Agent": "FS30Documentary/2.5"})
                    with urllib.request.urlopen(req, timeout=6) as r:
                        res = json.loads(r.read().decode("utf-8", errors="ignore"))
                    titles = [str(t).strip() for t in (res[1] if len(res) > 1 else []) if t]
                    # Prefer explicit footballer/manager pages first
                    ordered = sorted(titles, key=lambda t: (0 if ("football" in t.lower() or "soccer" in t.lower() or "manager" in t.lower()) else 1))
                    for t in ordered:
                        chk = _valid_summary(t)
                        if chk:
                            found = chk
                            break
                    if found:
                        break
                except Exception:
                    continue

        if found:
            resolved = found
        self._wiki_name_cache[key] = resolved
        return resolved

    def _build_verified_cutout(
        self,
        beat_idx: int,
        slot_tag: str,
        entity_name: str,
        query: str,
        fallback_query: str,
        out_prefix: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches a real photo of `entity_name`, verifies identity with SFace + CUDA FasterRCNN,
        runs rembg matte extraction & defringing, strips disconnected teammates, adds a restrained
        5px warm-ivory paper edge, and preserves exact intrinsic aspect ratio.
        """
        canon_entity = self._resolve_canonical_wiki_name(entity_name)
        ref_feat = self.detector.get_reference_face_embedding(canon_entity) if canon_entity else None
        candidates = self._gather_candidates(
            canon_entity, query, fallback_query, is_venue=False,
            extra_avoid=["osmajic", "owen beck", "preston", "blackburn", "hannibal"],
        )
        print(f"  [Cutout {out_prefix}] Entity='{canon_entity}' | Candidates={len(candidates)} | HasRef={ref_feat is not None}")

        best_fallback = None
        for idx, cand in enumerate(candidates[:28], 1):
            dl = self._download_unique_valid(cand["url"])
            if dl is None:
                continue
            cv_bgr, sha, dh, blur = dl
            ih, iw = cv_bgr.shape[:2]

            objs = self.detector.detect_scene_objects(cv_bgr)
            c_ok, c_reason, _ = self.detector.evaluate_content_awareness(
                cv_bgr, strategy="portrait", is_venue=False, objects=objs
            )
            if not c_ok:
                print(f"    Cand {idx} reject: {c_reason}")
                continue

            faces = self.detector.detect_yunet_faces(cv_bgr)
            person_boxes = objs.get("persons") or []

            sim_score = None
            target_box = None
            is_face_only = False
            id_matched = None
            if canon_entity:
                id_matched, sim_val, id_reason, matched_fbox = self.detector.verify_face_identity_with_box(
                    cv_bgr, expected_entity=canon_entity, threshold=0.25
                )
                if id_matched is False:
                    print(f"    Cand {idx} reject: {id_reason}")
                    continue
                if id_matched is True:
                    sim_score = sim_val
                    p_match = self.detector.match_face_to_person_box(matched_fbox, person_boxes)
                    if p_match is not None:
                        target_box = p_match
                    else:
                        target_box = matched_fbox
                        is_face_only = True

            if target_box is None:
                if person_boxes:
                    pb = max(person_boxes, key=lambda b: b[2] * b[3])
                    target_box = (pb[0], pb[1], pb[2], pb[3])
                elif faces:
                    target_box = faces[0]["bbox"]
                    is_face_only = True

            # Tight proportional crop around verified person; expand downward/sideways when box is face-only
            x1, y1, x2, y2 = 0, 0, iw, ih
            matched_fh = matched_fbox[3] if (matched_fbox is not None) else (faces[0]["bbox"][3] if faces else 0)
            if target_box is not None:
                bx, by, bw, bh = target_box
                if not is_face_only and bw / float(max(1, bh)) > 0.72 and bh < ih * 0.45:
                    is_face_only = True
                if is_face_only:
                    pad_top = int(bh * 0.48)
                    pad_bot = int(bh * 1.65)
                    pad_x = int(bw * 0.90)
                else:
                    pad_top = int(bh * 0.16)
                    pad_bot = int(bh * 0.22)
                    pad_x = int(bw * 0.14)
                x1 = max(0, bx - pad_x)
                y1 = max(0, by - pad_top)
                x2 = min(iw, bx + bw + pad_x)
                y2 = min(ih, by + bh + pad_bot)
                crop_bgr = cv_bgr[y1:y2, x1:x2]
                if min(crop_bgr.shape[:2]) < 320:
                    x1, y1, x2, y2 = 0, 0, iw, ih
                    crop_bgr = cv_bgr
            else:
                crop_bgr = cv_bgr

            # Reject crowded/embracing crops where a 2nd full person/face shares the same cutout box
            if canon_entity and len(faces) >= 2:
                crop_faces = [
                    f for f in faces
                    if x1 <= (f["bbox"][0] + f["bbox"][2] * 0.5) <= x2
                    and y1 <= (f["bbox"][1] + f["bbox"][3] * 0.5) <= y2
                    and f["bbox"][3] >= max(36, matched_fh * 0.52)
                ]
                if len(crop_faces) >= 2:
                    print(f"    Cand {idx} reject: multi-person embrace ({len(crop_faces)} faces inside crop)")
                    continue
            if slot_tag not in ("puppet_left", "puppet_right") and len(person_boxes) >= 2 and target_box is not None:
                tb_cx = target_box[0] + target_box[2] * 0.5
                crop_w = max(1, x2 - x1)
                stray_pb = any(
                    (pb[2] * pb[3]) >= 0.08 * crop_w * max(1, y2 - y1)
                    and x1 <= (pb[0] + pb[2] * 0.5) <= x2
                    and y1 <= (pb[1] + pb[3] * 0.5) <= y2
                    and abs((pb[0] + pb[2] * 0.5) - tb_cx) > 0.24 * crop_w
                    for pb in person_boxes
                )
                if stray_pb:
                    print(f"    Cand {idx} reject: secondary full teammate overlapping solo cutout")
                    continue

            pil_rgb = Image.fromarray(cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB))
            pre_h = float(max(1, pil_rgb.height))
            if max(pil_rgb.size) > 1280:
                pil_rgb = scale_cutout_proportional(pil_rgb, target_h=1200) if pil_rgb.height >= pil_rgb.width else scale_cutout_proportional(pil_rgb, target_w=1200)
            scale_f = pil_rgb.height / pre_h

            try:
                import rembg
                rgba = rembg.remove(pil_rgb, session=self._get_rembg())
                refined = refine_cutout_matte(rgba, erode_px=2, defringe=True, feather_px=0.8, min_island_area=400)
            except Exception as e:
                print(f"    Cand {idx} rembg note: {e}")
                continue

            # Keep ONLY primary connected foreground component closest to crop center (shears fingertip-touching side players too)
            r_np = np.array(refined)
            core_bin = (r_np[:, :, 3] > 140).astype(np.uint8)
            core_eroded = cv2.erode(core_bin, np.ones((3, 3), np.uint8), iterations=2)
            n_lbl, lbl_map, stats, centroids = cv2.connectedComponentsWithStats(core_eroded)
            if n_lbl > 2:
                cx_mid, cy_mid = r_np.shape[1] * 0.5, r_np.shape[0] * 0.45
                best_lbl = max(
                    range(1, n_lbl),
                    key=lambda i: stats[i, cv2.CC_STAT_AREA] - 14.0 * np.hypot(centroids[i][0] - cx_mid, centroids[i][1] - cy_mid),
                )
                keep_core = (lbl_map == best_lbl).astype(np.uint8)
                keep_mask = cv2.dilate(keep_core, np.ones((7, 7), np.uint8), iterations=1) > 0
                r_np[:, :, 3] = np.where(keep_mask, r_np[:, :, 3], 0)
                refined = Image.fromarray(r_np)

            alpha_np = np.array(refined.split()[-1])
            cov = float(np.count_nonzero(alpha_np > 40)) / float(alpha_np.size)
            if cov < 0.14 or cov > 0.88:
                print(f"    Cand {idx} reject: Cutout alpha coverage {cov:.2f} out of [0.14, 0.88]")
                continue

            # Trim transparent bounds cleanly so bounding box mirrors subject footprint
            bbox = refined.getbbox()
            if bbox:
                refined = refined.crop(bbox)

            # Reject flat photo-border vertical slices AND severed floating heads (no shoulders/torso)
            trim_a = np.array(refined.split()[-1]) > 60
            left_wall = float(trim_a[:, :3].mean()) if trim_a.shape[1] >= 4 else 0.0
            right_wall = float(trim_a[:, -3:].mean()) if trim_a.shape[1] >= 4 else 0.0
            if left_wall > 0.55 or right_wall > 0.55:
                print(f"    Cand {idx} reject: flat crop-edge slice (L={left_wall:.2f}, R={right_wall:.2f})")
                continue
            if matched_fh > 0:
                face_ratio = (matched_fh * scale_f) / float(max(1, refined.height))
                if face_ratio > 0.48:
                    print(f"    Cand {idx} reject: floating head without shoulders/torso (face_ratio={face_ratio:.2f})")
                    continue

            # Apply restrained 5px warm-ivory tactile paper edge + gentle paper fiber multiply
            textured = multiply_paper_texture(refined, intensity=0.14)
            paper_cutout = apply_handcut_paper_edge(textured, stroke_w=5, edge_color=(247, 244, 236))

            # If SFace reference exists and face was verified False earlier we already skipped; if None (side/action), store best fallback
            out_file = self.staged_dir / f"{out_prefix}.png"
            if ref_feat is not None and sim_score is None:
                if best_fallback is None:
                    best_fallback = (paper_cutout, cand, sha, dh, blur, cov)
                continue

            paper_cutout.save(out_file, "PNG")
            pub_path = self._stage_to_public(out_file)
            self._register_used(cand["url"], sha, dh, {
                "beat": beat_idx, "slot": slot_tag, "entity": entity_name,
                "url": cand["url"], "source": cand.get("source"), "sha256": sha,
                "sface_sim": round(sim_score, 3) if sim_score is not None else None,
                "blur": round(blur, 1), "alpha_coverage": round(cov, 3),
            })
            print(f"  [APPROVED Cutout] {out_prefix}.png ({paper_cutout.width}x{paper_cutout.height}, sim={sim_score}, blur={blur:.1f})")
            return {
                "path": pub_path,
                "width": paper_cutout.width,
                "height": paper_cutout.height,
            }

        if best_fallback is not None:
            paper_cutout, cand, sha, dh, blur, cov = best_fallback
            out_file = self.staged_dir / f"{out_prefix}.png"
            paper_cutout.save(out_file, "PNG")
            pub_path = self._stage_to_public(out_file)
            self._register_used(cand["url"], sha, dh, {
                "beat": beat_idx, "slot": slot_tag, "entity": entity_name,
                "url": cand["url"], "source": cand.get("source"), "sha256": sha,
                "sface_sim": None, "blur": round(blur, 1), "note": "person_box_fallback",
            })
            print(f"  [APPROVED Fallback Cutout] {out_prefix}.png ({paper_cutout.width}x{paper_cutout.height})")
            return {"path": pub_path, "width": paper_cutout.width, "height": paper_cutout.height}

        return None

    def _build_photo_asset(
        self,
        beat_idx: int,
        slot_tag: str,
        entity_name: str,
        query: str,
        fallback_query: str,
        out_prefix: str,
        mode: str = "background",  # "background" | "mounted_photo" | "clean_editorial"
        secondary_entity: str = "",
    ) -> Optional[Dict[str, Any]]:
        is_venue = (mode == "background")
        canon_entity = self._resolve_canonical_wiki_name(entity_name) if (entity_name and not is_venue) else ""
        canon_sec = self._resolve_canonical_wiki_name(secondary_entity) if (secondary_entity and not is_venue) else ""
        has_ref = False
        if canon_entity and not is_venue:
            has_ref = self.detector.get_reference_face_embedding(canon_entity) is not None
        candidates = self._gather_candidates(
            canon_entity, query, fallback_query, is_venue=is_venue,
            extra_avoid=[
                "osmajic", "owen beck", "preston", "blackburn", "hannibal",
                "rugby", "nrl", "bulldogs", "canterbury", "afl", "boxing", "ufc", "nfl", "cricket", "hockey", "basketball",
            ] if not is_venue else None,
        )
        print(f"  [Photo {out_prefix} ({mode})] Entity='{canon_entity or 'venue'}' | Candidates={len(candidates)} | HasRef={has_ref}")

        best_fallback = None
        for idx, cand in enumerate(candidates[:28], 1):
            dl = self._download_unique_valid(cand["url"])
            if dl is None:
                continue
            cv_bgr, sha, dh, blur = dl
            ih, iw = cv_bgr.shape[:2]

            objs = self.detector.detect_scene_objects(cv_bgr)
            c_ok, c_reason, _ = self.detector.evaluate_content_awareness(
                cv_bgr, strategy="tactical" if is_venue else "portrait", is_venue=is_venue, objects=objs
            )
            if not c_ok:
                print(f"    Cand {idx} reject: {c_reason}")
                continue

            id_matched = None
            sim_val = None
            if canon_entity and not is_venue:
                id_matched, sim_val, id_reason, matched_fbox = self.detector.verify_face_identity_with_box(
                    cv_bgr, expected_entity=canon_entity, threshold=0.23
                )
                if id_matched is False and canon_sec:
                    sec_matched, sec_sim, _, sec_fbox = self.detector.verify_face_identity_with_box(
                        cv_bgr, expected_entity=canon_sec, threshold=0.23
                    )
                    if sec_matched is True:
                        id_matched = True
                        sim_val = sec_sim
                        matched_fbox = sec_fbox
                if id_matched is False:
                    print(f"    Cand {idx} reject: {id_reason}")
                    continue
                if has_ref and id_matched is None:
                    if best_fallback is None:
                        best_fallback = (cand, cv_bgr, sha, dh, blur, ih, iw, objs, matched_fbox)
                    continue
            else:
                matched_fbox = None

            res = self._finalize_photo_asset(beat_idx, slot_tag, out_prefix, mode, cand, cv_bgr, sha, dh, blur, ih, iw, objs, matched_fbox, sim_val)
            if res is not None:
                return res

        if best_fallback is not None:
            cand, cv_bgr, sha, dh, blur, ih, iw, objs, matched_fbox = best_fallback
            res = self._finalize_photo_asset(beat_idx, slot_tag, out_prefix, mode, cand, cv_bgr, sha, dh, blur, ih, iw, objs, matched_fbox, None)
            if res is not None:
                return res

        return None

    def _finalize_photo_asset(
        self,
        beat_idx: int,
        slot_tag: str,
        out_prefix: str,
        mode: str,
        cand: Dict[str, Any],
        cv_bgr: np.ndarray,
        sha: str,
        dh: int,
        blur: float,
        ih: int,
        iw: int,
        objs: Dict[str, Any],
        matched_fbox: Any,
        sim_val: Optional[float],
    ) -> Optional[Dict[str, Any]]:
            # Trim side-by-side split collages cleanly to the sharper panel
            if mode == "mounted_photo" and iw >= 800:
                mid_lo, mid_hi = int(iw * 0.47), int(iw * 0.53)
                col_stds = [float(np.std(cv_bgr[:, cx, :], axis=0).mean()) for cx in range(mid_lo, mid_hi)]
                best_off = int(np.argmin(col_stds)) if col_stds else -1
                if col_stds and col_stds[best_off] < 22.0:
                    split_x = mid_lo + best_off
                    left_panel = cv_bgr[:, : max(1, split_x - 4)]
                    right_panel = cv_bgr[:, min(iw - 1, split_x + 4) :]
                    if min(left_panel.shape[1], right_panel.shape[1]) >= 360:
                        l_lap = float(cv2.Laplacian(cv2.cvtColor(left_panel, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
                        r_lap = float(cv2.Laplacian(cv2.cvtColor(right_panel, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
                        cv_bgr = left_panel if l_lap >= r_lap else right_panel
                        ih, iw = cv_bgr.shape[:2]
                        objs = self.detector.detect_scene_objects(cv_bgr)
                        print(f"    Split collage separated -> kept sharper panel ({iw}x{ih})")

            pil_img = Image.fromarray(cv2.cvtColor(cv_bgr, cv2.COLOR_BGR2RGB))

            if mode == "mounted_photo":
                faces = self.detector.detect_yunet_faces(cv_bgr)
                person_boxes = objs.get("persons") or []
                fx, fy = 0.5, 0.4
                if faces:
                    f = faces[0]["bbox"]
                    fx = min(0.85, max(0.15, (f[0] + f[2] * 0.5) / float(iw)))
                    fy = min(0.85, max(0.15, (f[1] + f[3] * 0.5) / float(ih)))
                elif person_boxes:
                    pb = person_boxes[0]
                    fx = min(0.85, max(0.15, (pb[0] + pb[2] * 0.5) / float(iw)))
                    fy = min(0.85, max(0.15, (pb[1] + pb[3] * 0.35) / float(ih)))

                ar = iw / float(ih)
                tw = 900
                th = int(min(780, max(520, round(tw / max(1.15, min(1.75, ar)))))) if ar >= 1.0 else 740
                mounted = mount_archival_photo(
                    pil_img, target_w=tw, target_h=th,
                    border_width=14, shadow_radius=12, shadow_alpha=155, focus_point=(fx, fy),
                )
                out_file = self.staged_dir / f"{out_prefix}.png"
                mounted.save(out_file, "PNG")
                pub_path = self._stage_to_public(out_file)
                self._register_used(cand["url"], sha, dh, {
                    "beat": beat_idx, "slot": slot_tag, "url": cand["url"],
                    "source": cand.get("source"), "sha256": sha, "blur": round(blur, 1),
                })
                print(f"  [APPROVED Mounted] {out_prefix}.png ({mounted.width}x{mounted.height})")
                return {"path": pub_path, "width": mounted.width, "height": mounted.height, "focal_x": round(fx * 100, 1), "focal_y": round(fy * 100, 1)}

            elif mode == "clean_editorial":
                raw_persons = objs.get("persons") or []
                raw_balls = objs.get("balls") or []
                p_box = self.detector.match_face_to_person_box(matched_fbox, raw_persons) if matched_fbox else None
                if p_box is None and raw_persons:
                    p_box = raw_persons[0][:4]
                b_box = raw_balls[0][:4] if raw_balls else None
                ok_crop, out_bgr, crop_audit = self.cropper.crop_candidate(
                    cv_bgr,
                    strategy="portrait",
                    preferred_bbox=matched_fbox,
                    body_box=p_box,
                    ball_box=b_box,
                    person_boxes=raw_persons,
                )
                if not ok_crop or out_bgr is None:
                    return None
                out_file = self.staged_dir / f"{out_prefix}.jpg"
                cv2.imwrite(str(out_file), out_bgr, [cv2.IMWRITE_JPEG_QUALITY, 94])
                pub_path = self._stage_to_public(out_file)
                self._register_used(cand["url"], sha, dh, {
                    "beat": beat_idx, "slot": slot_tag, "url": cand["url"],
                    "source": cand.get("source"), "sha256": sha, "blur": round(blur, 1),
                    "framing_mode": crop_audit.get("framing_mode"),
                })
                print(f"  [APPROVED Editorial] {out_prefix}.jpg ({crop_audit.get('framing_mode')})")
                return {
                    "path": pub_path,
                    "width": out_bgr.shape[1],
                    "height": out_bgr.shape[0],
                    "focal_x": crop_audit.get("focal_x", 50.0),
                    "focal_y": crop_audit.get("focal_y", 35.0),
                    "framing_mode": crop_audit.get("framing_mode", "full_bleed"),
                }

            else:  # ambient desaturated cover background
                bg_fit = ImageOps.fit(pil_img, (1080, 1920), Image.Resampling.LANCZOS, centering=(0.5, 0.45))
                out_file = self.staged_dir / f"{out_prefix}.jpg"
                bg_fit.save(out_file, "JPEG", quality=90)
                pub_path = self._stage_to_public(out_file)
                self._register_used(cand["url"], sha, dh, {
                    "beat": beat_idx, "slot": slot_tag, "url": cand["url"],
                    "source": cand.get("source"), "sha256": sha, "blur": round(blur, 1),
                })
                print(f"  [APPROVED Backdrop] {out_prefix}.jpg")
                return {"path": pub_path, "width": 1080, "height": 1920}

    def prepare_story_visual_assets(self, pkg: StoryPackage) -> Dict[str, Any]:
        """Builds all staged Remotion assets for every beat in StoryPackage."""
        shared = self._stage_shared_library_assets()
        beat_assets: Dict[int, Dict[str, Any]] = {}

        try:
            for b in pkg.beats:
                idx = b.beat_number
                print(f"\n[DocVisual] Preparing Beat {idx} ({b.layout_style}) — Primary: '{b.primary_entity}'")
                b_info: Dict[str, Any] = {}

                # 1. Torn Headline Banner via authentic paper_widgets variants A-E (used selectively, skipped on epilogue)
                if b.layout_style != "clean_editorial_epilogue" and b.visual_headline:
                    banner_img = create_torn_headline_banner(
                        headline=b.visual_headline,
                        kicker=b.visual_kicker,
                        width=920,
                        height=195,
                        headline_size=56,
                        kicker_size=28,
                        variant=b.banner_variant,
                    )
                    b_file = self.staged_dir / f"beat{idx}_banner.png"
                    banner_img.save(b_file, "PNG")
                    b_info["banner_path"] = self._stage_to_public(b_file)
                    b_info["banner_width"] = banner_img.width
                    b_info["banner_height"] = banner_img.height

                # 2. Backdrop Stage (atmospheric pitch/stadium photo or textured newsprint fallback)
                bg_res = self._build_photo_asset(
                    idx, "background", "", b.background_query, f"{pkg.primary_protagonist} stadium pitch", f"beat{idx}_bg", mode="background"
                )
                if bg_res:
                    b_info["bg_path"] = bg_res["path"]
                else:
                    b_info["bg_path"] = shared.get("paper_texture")

                # 3. Layout-specific primary visual planes
                if b.layout_style == "newspaper_highlighter" and b.newspaper_clip:
                    nc = b.newspaper_clip
                    card_img, rects = create_newspaper_highlighter_card(
                        publication=nc.publication,
                        date_text=nc.date_text,
                        headline=nc.headline,
                        quote_excerpt=nc.quote_excerpt,
                        highlight_phrase=nc.highlight_phrase,
                        width=920,
                    )
                    nc_file = self.staged_dir / f"beat{idx}_newspaper.png"
                    card_img.save(nc_file, "PNG")
                    b_info["newspaper_path"] = self._stage_to_public(nc_file)
                    b_info["newspaper_width"] = card_img.width
                    b_info["newspaper_height"] = card_img.height
                    b_info["highlight_rects"] = rects
                    # Optional cutout inset beside/under newsprint
                    cut = self._build_verified_cutout(
                        idx, "news_inset_cutout", b.primary_entity, b.search_query, b.fallback_query, f"beat{idx}_cutout"
                    )
                    if cut:
                        b_info["cutout"] = cut

                elif b.layout_style == "archival_pinboard":
                    mounted = self._build_photo_asset(
                        idx, "mounted_photo", b.primary_entity, b.search_query, b.fallback_query, f"beat{idx}_mounted", mode="mounted_photo", secondary_entity=b.secondary_entity or ""
                    )
                    if mounted:
                        b_info["mounted"] = mounted
                        if b.tactical_reticle and b.tactical_reticle.enabled:
                            fx = float(mounted.get("focal_x") or 50.0)
                            fy = float(mounted.get("focal_y") or 38.0)
                            # Keep reticle off player face/nose — shift cleanly toward forearm/shoulder zone
                            if abs(b.tactical_reticle.target_x_pct - fx) < 12.0 and abs(b.tactical_reticle.target_y_pct - fy) < 16.0:
                                b.tactical_reticle.target_y_pct = round(min(74.0, fy + 22.0), 1)
                                b.tactical_reticle.target_x_pct = round(max(26.0, min(74.0, fx + (8.0 if fx < 55.0 else -8.0))), 1)

                elif b.layout_style == "puppet_confrontation_25d":
                    c1 = self._build_verified_cutout(
                        idx, "puppet_left", b.primary_entity, b.search_query, f"{b.primary_entity} match action", f"beat{idx}_puppet1"
                    )
                    sec_ent = b.secondary_entity or b.primary_entity
                    if b.fallback_query and sec_ent.split()[-1].lower() in b.fallback_query.lower():
                        sec_q = b.fallback_query
                    else:
                        prim_toks = set(b.primary_entity.lower().split())
                        ctx_toks = [t for t in b.search_query.split() if t.lower() not in prim_toks]
                        sec_q = f"{sec_ent} {' '.join(ctx_toks[:3])} match".strip()
                    c2 = self._build_verified_cutout(
                        idx, "puppet_right", sec_ent, sec_q, f"{sec_ent} national team match", f"beat{idx}_puppet2"
                    )
                    if c1:
                        b_info["cutout"] = c1
                    if c2:
                        b_info["secondary_cutout"] = c2

                elif b.layout_style == "clean_editorial_epilogue":
                    ed = self._build_photo_asset(
                        idx, "clean_editorial", b.primary_entity, b.search_query, b.fallback_query, f"beat{idx}_editorial", mode="clean_editorial"
                    )
                    if ed:
                        b_info["editorial"] = ed

                else:  # "vox_25d_cutout" | "tactile_timeline_card"
                    if b.use_cutout:
                        cut = self._build_verified_cutout(
                            idx, "hero_cutout", b.primary_entity, b.search_query, b.fallback_query, f"beat{idx}_cutout"
                        )
                        if cut:
                            b_info["cutout"] = cut
                    if not b_info.get("cutout"):
                        mounted = self._build_photo_asset(
                            idx, "fallback_mount", b.primary_entity, b.search_query, b.fallback_query, f"beat{idx}_mounted", mode="mounted_photo"
                        )
                        if mounted:
                            b_info["mounted"] = mounted

                # 4. Dynamic Rubber Stamp Overlay if present
                if b.stamp_text:
                    st_img = create_dynamic_rubber_stamp(b.stamp_text)
                    st_file = self.staged_dir / f"beat{idx}_stamp.png"
                    st_img.save(st_file, "PNG")
                    b_info["stamp_path"] = self._stage_to_public(st_file)
                    b_info["stamp_width"] = st_img.width
                    b_info["stamp_height"] = st_img.height

                beat_assets[idx] = b_info
        finally:
            self.release_models()

        manifest = {
            "run_id": self.run_id,
            "story_id": pkg.story_id,
            "shared": shared,
            "beats": beat_assets,
            "provenance": self.provenance_records,
        }
        (self.run_dir / "visual_manifest.json").write_text(
            __import__("json").dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return manifest
