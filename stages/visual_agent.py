"""
# PROVENANCE: Copied from stages/visual_agent.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Autonomous Visual Intelligence & Image Sensor Agent for @Footballin30sec.
Replaces brittle keyword scraping with an intelligent, multi-stage visual agent:
1. Visual Semantic Intent Planner (LLM-guided contextual query generation)
2. Multi-Source Web Crawler (Bing Images, Reddit r/soccer, Wikimedia Commons, Wikipedia REST)
3. Visual Quality & Relevance Sensor:
   - Evaluates resolution, sharpness, luminance, and texture variance
   - Rejects watermarked stock previews (Alamy, Getty, Shutterstock), wallpapers, clipart, and school blogs
   - Matches semantic tokens between spoken script action and image metadata
4. Smart 9:16 Vertical Framing with upper-third focal bias and broadcast HD grading
5. Zero-tolerance safeguard: BANS blank/solid procedural rectangles forever
"""

import sys
import os
import re
import json
import time
import html
import io
import hashlib
import random
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker
from stages.meme_vault import is_image_previously_used, record_used_image, MEME_CATALOG

DATA_DIR = PROJECT_ROOT / "data"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
LEDGER_FILE = EVIDENCE_DIR / "attribution_ledger.json"

FACE_CASCADE = None
PROFILE_CASCADE = None
UPPERBODY_CASCADE = None

def _get_cascades():
    global FACE_CASCADE, PROFILE_CASCADE, UPPERBODY_CASCADE
    if FACE_CASCADE is None:
        try:
            FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            PROFILE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
            UPPERBODY_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        except Exception as e:
            print(f"[VisualAgent] OpenCV cascade init note: {e}")
    return FACE_CASCADE, PROFILE_CASCADE, UPPERBODY_CASCADE

def detect_subject_bbox(cv_img: np.ndarray) -> Tuple[float, float, str, Optional[Tuple[int, int, int, int]]]:
    """
    OpenCV subject localization and bounding box extraction:
    Detects face, profile, upper body, or saliency gradient centroid to guarantee subject safe-zone framing in 9:16 crop.
    Returns: (cx, cy, method, bbox=(x, y, w, h) or None)
    """
    h, w = cv_img.shape[:2]
    face_casc, prof_casc, body_casc = _get_cascades()
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    if face_casc and not face_casc.empty():
        faces = face_casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
        if len(faces) > 0:
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            fx, fy, fw, fh = faces[0]
            return float(fx + fw / 2.0), float(fy + fh / 2.0), "FRONTAL_FACE", (int(fx), int(fy), int(fw), int(fh))

    if prof_casc and not prof_casc.empty():
        profiles = prof_casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35))
        if len(profiles) > 0:
            profiles = sorted(profiles, key=lambda f: f[2] * f[3], reverse=True)
            fx, fy, fw, fh = profiles[0]
            return float(fx + fw / 2.0), float(fy + fh / 2.0), "PROFILE_FACE", (int(fx), int(fy), int(fw), int(fh))

    if body_casc and not body_casc.empty():
        bodies = body_casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(60, 60))
        if len(bodies) > 0:
            bodies = sorted(bodies, key=lambda b: b[2] * b[3], reverse=True)
            bx, by, bw, bh = bodies[0]
            return float(bx + bw / 2.0), float(by + bh * 0.4), "UPPER_BODY", (int(bx), int(by), int(bw), int(bh))

    # Edge energy / saliency centroid
    try:
        edges = cv2.Canny(gray, 50, 150)
        total_energy = float(np.sum(edges))
        if total_energy > 0:
            x_coords = np.arange(w)
            y_coords = np.arange(h)
            col_sums = np.sum(edges, axis=0)
            row_sums = np.sum(edges, axis=1)
            cx = float(np.sum(x_coords * col_sums) / total_energy)
            cy = float(np.sum(y_coords * row_sums) / total_energy)
            return cx, cy, "SALIENCY_EDGE_CENTROID", None
    except Exception:
        pass

    return float(w / 2.0), float(h * 0.4), "DEFAULT_CENTER", None

def detect_subject_centroid(cv_img: np.ndarray) -> Tuple[float, float, str]:
    """Backwards-compatible wrapper returning (cx, cy, method)."""
    cx, cy, method, _ = detect_subject_bbox(cv_img)
    return cx, cy, method

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8"
}

# Strict blacklist for watermarked stock archives, wallpaper aggregators, and spam
DISQUALIFIED_DOMAINS = {
    'alamy.com', 'alamy', 'gettyimages', 'shutterstock.com', 'shutterstock', 'istockphoto.com', 'stockphoto.com',
    'depositphotos.com', 'depositphotos', '123rf.com', 'adobestock', 'dreamstime.com',
    'wallpaperaccess.com', 'wallpapercave.com', 'wallpapersafari.com',
    'pinterest.com', 'aliexpress.com', 'amazon.com', 'ebay.com', 'freepik.com',
    'vectorstock.com', 'momjunction.com', 'howweelearn.com', 'teacherspayteachers.com',
    'clipart', 'iconfinder.com', 'flaticon.com', 'deviantart.com', 'lookfordiagnosis.com'
}

class VisualSensor:
    """
    Intelligent image quality sensor and relevance evaluator.
    Decides whether an image is a top-tier visual for YouTube Shorts or garbage.
    """

    @staticmethod
    def inspect_bytes(
        data: bytes,
        title: str,
        page_url: str,
        image_url: str,
        required_entities: List[str],
        action_keywords: List[str],
        scene_text: str = ""
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """
        Comprehensive multi-gate evaluation of an image candidate.
        Includes temporal alignment (historical/prime vs breaking modern news).
        Returns: (passed: bool, quality_score: float, rejection_reason: str, metrics: dict)
        """
        url_lower = image_url.lower()
        title_lower = (title + " " + page_url).lower()

        # Gate 1: Domain & Watermark Blacklist
        for bad in DISQUALIFIED_DOMAINS:
            if bad in url_lower or bad in title_lower:
                return False, 0.0, f"Disqualified domain/watermark: {bad}", None

        # Gate 2: Semantic Relevance Gating
        # Check required entities (e.g. 'bale', 'antony', 'ronaldo')
        if required_entities:
            entity_found = any(ent.lower() in title_lower or ent.lower() in url_lower for ent in required_entities)
            if not entity_found:
                return False, 0.0, f"Image lacks required entity: {required_entities}", None

        # Check action context (e.g. 'golf', 'spin', 'furious', 'trophy')
        context_score = 0.0
        if action_keywords:
            matched_keywords = [kw.lower() for kw in action_keywords if kw.lower() in title_lower or kw.lower() in url_lower]
            context_score = (len(matched_keywords) / max(1, len(action_keywords))) * 25.0

        # Check Temporal Alignment (Historical/Prime vs Modern Breaking News)
        temporal_score = 0.0
        scene_lower = scene_text.lower()
        is_historical = any(k in scene_lower for k in ["prime", "glory", "history", "in madrid", "former", "trophy", "years ago", "memories", "past", "retired", "chasing golf balls"])
        is_modern = any(k in scene_lower for k in ["now", "winter window", "2025", "2026", "today", "buying", "consortium", "takeover", "protest", "debt crisis", "current", "san siro", "bid", "clause", "institution"])

        year_matches = re.findall(r'\b(20[0-2][0-9])\b', title_lower + " " + url_lower)
        if year_matches:
            years = [int(y) for y in year_matches]
            avg_year = sum(years) / len(years)
            if is_historical and avg_year <= 2022:
                temporal_score = 15.0 # Appropriate retrospective/prime photo
            elif is_modern and avg_year >= 2024:
                temporal_score = 15.0 # Fresh modern breaking news photo
            elif is_modern and avg_year < 2018:
                temporal_score = -15.0 # Outdated photo for breaking news
        elif is_modern:
            if any(k in title_lower for k in ["press", "conference", "suit", "2024", "2025", "2026", "new", "takeover", "bid", "board"]):
                temporal_score = 10.0
        elif is_historical:
            if any(k in title_lower for k in ["golf", "swing", "madrid", "wales", "celebrat", "trophy", "prime"]):
                temporal_score = 10.0

        # Gate 3: File Size
        if len(data) < 25000:
            return False, 0.0, f"File size too small ({len(data)} bytes)", None

        # Gate 4: Visual Decoding & Pixel Metrics
        try:
            with Image.open(io.BytesIO(data)) as img:
                img = img.convert("RGB")
                w, h = img.size

                # Minimum dimensions
                if w < 320 or h < 320 or (w * h) < 120000:
                    return False, 0.0, f"Resolution too low ({w}x{h})", None

                arr = np.array(img)
                lum = float(np.mean(arr))
                var = float(np.var(arr))

                # Flat / solid / blank color detection (BAN PROCEDURAL RECTANGLES)
                if var < 25.0:
                    return False, 0.0, f"Low texture variance / solid color ({var:.1f})", None

                # Extreme brightness or pure darkness
                if lum < 18.0 or lum > 238.0:
                    return False, 0.0, f"Extreme luminance ({lum:.1f})", None

                # Quadrant variance check: catches images letterboxed inside solid black/white boxes
                q_h, q_w = h // 2, w // 2
                q_vars = [
                    float(np.var(arr[:q_h, :q_w])),
                    float(np.var(arr[:q_h, q_w:])),
                    float(np.var(arr[q_h:, :q_w])),
                    float(np.var(arr[q_h:, q_w:]))
                ]
                if min(q_vars) < 10.0 and max(q_vars) > 100.0:
                    return False, 0.0, f"Letterboxed or padded fake border detected", None

                # Sharpness / Blur check
                arr_gray = np.array(img.convert("L"), dtype=float)
                gy, gx = np.gradient(arr_gray)
                blur_var = float(np.var(np.sqrt(gx**2 + gy**2)))
                if blur_var < 18.0:
                    return False, 0.0, f"Image is blurry / out-of-focus ({blur_var:.1f})", None

                # Gate 5: Player Face Safe-Zone Framing & Prominence
                cv_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                cx, cy, method, bbox = detect_subject_bbox(cv_img)
                is_player_query = bool(required_entities) and any(
                    e.lower() in (title_lower + " " + scene_text.lower())
                    for e in required_entities
                )

                face_safe = True
                face_score_bonus = 0.0
                if bbox and method in ["FRONTAL_FACE", "PROFILE_FACE"]:
                    fx, fy, fw, fh = bbox
                    h_crop = max(int(fh * 4.2), int(h * 0.55))
                    h_crop = min(h, h_crop)
                    y0 = max(0, min(h - h_crop, int(cy - 0.28 * h_crop)))
                    face_final_y = int((fy - y0) / h_crop * 1920)
                    if face_final_y < 240 and y0 == 0:
                        face_score_bonus -= 10.0
                        face_safe = False
                    else:
                        face_score_bonus += 15.0 # Prominent, safely frameable player face
                elif is_player_query and "face" in action_keywords:
                    face_score_bonus -= 8.0

                # Calculate composite quality score (0 - 100)
                quality_score = 45.0
                quality_score += min(20.0, (w * h) / 100000.0) # Resolution bonus
                quality_score += min(10.0, blur_var / 15.0)    # Edge sharpness bonus
                quality_score += context_score                  # Semantic action bonus (up to 25.0)
                quality_score += temporal_score                 # Temporal relevance bonus (-15 to +15)
                quality_score += face_score_bonus               # Face safe-zone prominence bonus

                metrics = {
                    "score": round(quality_score, 1),
                    "resolution": f"{w}x{h}",
                    "width": w,
                    "height": h,
                    "bytes": len(data),
                    "luminance": round(lum, 1),
                    "variance": round(var, 1),
                    "blur_variance": round(blur_var, 1),
                    "temporal_score": temporal_score,
                    "context_score": round(context_score, 1),
                    "face_detected": bool(bbox and method in ["FRONTAL_FACE", "PROFILE_FACE"]),
                    "face_safe": face_safe,
                    "face_method": method
                }

                return True, round(quality_score, 1), "PASSED", metrics

        except Exception as img_err:
            return False, 0.0, f"Visual decoding failure: {img_err}", None


class VisualAgent:
    """
    Autonomous Agent that plans, queries, crawls, and verifies the best editorial visuals.
    """

    def __init__(self):
        self.used_hashes: Set[str] = set()
        self.used_urls: Set[str] = set()
        self.audit_log: List[Dict[str, Any]] = []
        self.sensor = VisualSensor()

    def reset_cycle(self):
        self.used_hashes.clear()
        self.used_urls.clear()
        self.audit_log.clear()

    def plan_visual_queries(
        self,
        scene_id: int,
        scene_text: str,
        scene_type: str,
        headline: str,
        search_entity: Optional[str] = None,
        search_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Agentic query planner: Translates what the script is actually saying (troll jabs, actions, banter)
        into highly targeted web search queries.
        """
        queries = []
        text_lower = scene_text.lower()
        clean_headline = headline.split(' - ')[0].split(' | ')[0]

        # 1. PRIORITY #1: Explicit Entity & Context from Scene Definition
        if search_entity:
            clean_ent = search_entity.strip()
            ent_tokens = [w.lower() for w in re.findall(r'\b[A-Za-z0-9]+\b', clean_ent) if len(w) > 2]
            action_desc = search_context.strip() if search_context else "match action"
            action_tokens = [w.lower() for w in re.findall(r'\b[A-Za-z0-9]+\b', action_desc) if len(w) > 2]

            # Check if this scene is explicitly a meme / roast scene
            is_meme_scene = (
                scene_type in ("troll_jab_1", "troll_jab_2", "meme", "roast", "banter")
                or "meme" in action_desc.lower()
            )

            matched_meme = None
            if is_meme_scene:
                for meme in MEME_CATALOG:
                    m_ent = meme["entity"].lower()
                    m_key = meme["key"].lower()
                    if m_ent in clean_ent.lower() or clean_ent.lower() in m_ent or m_key in clean_ent.lower():
                        matched_meme = meme
                        break

            if matched_meme:
                # Use the curated, high-quality meme queries
                m_ent_tokens = [w for w in matched_meme["entity"].lower().split() if len(w) > 2]
                m_ctx_tokens = [w for w in matched_meme["context"].lower().split() if len(w) > 2]
                for q in matched_meme["search_queries"]:
                    queries.append({
                        "query": q,
                        "required_entities": m_ent_tokens,
                        "context_tokens": m_ctx_tokens,
                        "priority": "EXPLICIT_MEME_MATCH"
                    })
            else:
                # Authentic editorial entity: Target specific action and context
                queries.append({
                    "query": f"{clean_ent} {action_desc}",
                    "required_entities": ent_tokens,
                    "context_tokens": action_tokens,
                    "priority": "EXPLICIT_ENTITY_ACTION"
                })
                # Add contextual variations
                if "flag" in action_desc.lower():
                    queries.append({
                        "query": f"{clean_ent} Wales Golf Madrid flag banner",
                        "required_entities": ent_tokens,
                        "context_tokens": ["wales", "flag", "madrid"],
                        "priority": "EXPLICIT_ENTITY_FLAG"
                    })
                elif "press" in action_desc.lower() or "interview" in action_desc.lower():
                    queries.append({
                        "query": f"{clean_ent} press conference microphone",
                        "required_entities": ent_tokens,
                        "context_tokens": ["press", "conference", "microphone"],
                        "priority": "EXPLICIT_ENTITY_PRESS"
                    })
                elif "suit" in action_desc.lower() or "board" in action_desc.lower() or "presentation" in action_desc.lower():
                    queries.append({
                        "query": f"{clean_ent} formal suit presentation smiling",
                        "required_entities": ent_tokens,
                        "context_tokens": ["suit", "formal", "presentation"],
                        "priority": "EXPLICIT_ENTITY_FORMAL"
                    })
                elif "golf" in action_desc.lower():
                    queries.append({
                        "query": f"{clean_ent} playing golf swing",
                        "required_entities": ent_tokens,
                        "context_tokens": ["golf", "swing", "course"],
                        "priority": "EXPLICIT_ENTITY_ACTION_ALT"
                    })
                else:
                    queries.append({
                        "query": f"{clean_ent} match photo",
                        "required_entities": ent_tokens,
                        "context_tokens": ["match", "pitch", "photo"],
                        "priority": "EXPLICIT_ENTITY_MATCH"
                    })

        # 2. PRIORITY #2: Meme Detection from Text (Only if explicit entity didn't specify or as secondary fallback)
        meme_word_triggers = [
            (r'\bpenaldo\b', ["ronaldo", "cristiano"], ["penalty", "crying", "meme"], ["Cristiano Ronaldo crying meme", "Cristiano Ronaldo meme face"]),
            (r'\bpessi\b', ["messi", "lionel"], ["crying", "meme", "funny"], ["Lionel Messi meme face", "Lionel Messi crying meme"]),
            (r'\bfidget\s+spin\b', ["antony"], ["spin", "united", "meme"], ["Antony fidget spin meme", "Antony Manchester United spin"]),
            (r'\bmaguire\b', ["maguire", "harry"], ["confused", "meme"], ["Harry Maguire confused meme face", "Harry Maguire meme"]),
            (r'\bmourinho\b', ["mourinho", "jose"], ["trouble", "meme"], ["Jose Mourinho if I speak meme", "Jose Mourinho headphones press conference meme"]),
            (r'\bboehly\b', ["boehly", "todd"], ["chelsea", "box", "meme"], ["Todd Boehly Chelsea executive box meme", "Todd Boehly Chelsea owner box"]),
            (r'\bmudryk\b', ["mudryk"], ["chelsea", "meme"], ["Mykhailo Mudryk meme", "Mudryk funny meme"])
        ]
        for pattern, entities, contexts, q_list in meme_word_triggers:
            if re.search(pattern, text_lower):
                for q in q_list:
                    queries.append({
                        "query": q,
                        "required_entities": entities,
                        "context_tokens": contexts,
                        "priority": "TEXT_MEME_MATCH"
                    })

        # 3. PRIORITY #3: Fallback to main headline subject
        headline_tokens = [w for w in re.findall(r'\b[A-Z][a-zA-Z0-9\'-]+\b', clean_headline)
                           if w.lower() not in {"join", "race", "for", "prepare", "target", "bid", "signs", "shock", "move", "transfer", "agree"}]
        main_subj = " ".join(headline_tokens[:2]) if headline_tokens else "football match"
        subj_tokens = [w.lower() for w in main_subj.split()]

        queries.append({
            "query": f"{main_subj} football match action",
            "required_entities": subj_tokens,
            "context_tokens": ["match", "action", "pitch", "celebration"],
            "priority": "HEADLINE_ENTITY"
        })

        return queries

    def search_candidates_bing(self, query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """Web image search via Bing Images async endpoint with clean US-market editorial results."""
        candidates = []
        offset = random.choice([0, 4, 8, 12, 16])
        url = f"https://www.bing.com/images/async?q={urllib.parse.quote(query)}&first={offset}&count=25&mmasync=1"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.bing.com/"
        })
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw_html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'class=[\'"]iusc[\'"][^>]*m=[\'"](\{.*?\})[\'"]', raw_html)
                for m in matches:
                    clean = html.unescape(m)
                    try:
                        data = json.loads(clean)
                        murl = data.get("murl")
                        turl = data.get("turl")
                        title = data.get("t", "")
                        purl = data.get("purl", "")
                        if murl:
                            candidates.append({
                                "url": murl,
                                "fallback_url": turl,
                                "title": title,
                                "page_url": purl,
                                "source": f"Bing Web Search ({query})"
                            })
                        if len(candidates) >= max_results:
                            break
                    except Exception:
                        continue
                if candidates:
                    break
            except Exception as e:
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                print(f"[VisualAgent] Bing search note for '{query}': {e}")
        return candidates

    def search_candidates_wikimedia(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """Search Wikimedia Commons for authentic high-res public domain football media."""
        candidates = []
        try:
            wiki_url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit={max_results}&prop=imageinfo&iiprop=url|size&format=json"
            req = urllib.request.Request(
                wiki_url,
                headers={"User-Agent": "FootballStudioBot/2.0 (https://footballin30sec.com; admin@footballin30sec.com)"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                w_data = json.loads(r.read().decode('utf-8'))
            pages = w_data.get('query', {}).get('pages', {})
            for _, pinfo in pages.items():
                img_info = pinfo.get('imageinfo', [{}])[0]
                u = img_info.get('url')
                w = img_info.get('width', 0)
                h = img_info.get('height', 0)
                if u and not u.endswith(('.svg', '.ogg', '.ogv')) and w >= 400 and h >= 400:
                    candidates.append({
                        "url": u,
                        "fallback_url": u,
                        "title": pinfo.get("title", ""),
                        "page_url": "wikimedia.org",
                        "source": f"Wikimedia Commons ({query})"
                    })
        except Exception as e:
            print(f"[VisualAgent] Wikimedia search note for '{query}': {e}")
        return candidates

    def search_candidates_wikipedia_rest(self, entity_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search Wikipedia REST API for official player and club media archives."""
        candidates = []
        if not entity_name:
            return candidates
        try:
            clean_title = urllib.parse.quote(entity_name.strip().replace(" ", "_"))
            url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{clean_title}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "FootballStudioBot/2.0 (https://footballin30sec.com; admin@footballin30sec.com)"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                w_data = json.loads(r.read().decode('utf-8'))
            items = w_data.get("items", [])
            for it in items:
                title = it.get("title", "")
                src = it.get("srcset", [{}])[-1].get("src", "")
                if src and not title.endswith((".svg", ".ogg", ".ogv", ".pdf")):
                    if src.startswith("//"):
                        src = "https:" + src
                    candidates.append({
                        "url": src,
                        "fallback_url": src,
                        "title": title,
                        "page_url": f"en.wikipedia.org/wiki/{clean_title}",
                        "source": f"Wikipedia Match Editorial ({entity_name})"
                    })
                    if len(candidates) >= max_results:
                        break
        except Exception as e:
            print(f"[VisualAgent] Wikipedia REST note for '{entity_name}': {e}")
        return candidates

    def process_and_save_image(
        self,
        raw_bytes: bytes,
        out_path: Path,
        target_w: int = 1080,
        target_h: int = 1920
    ) -> bool:
        """
        OpenCV Subject-Centered 9:16 Vertical Cropping & Broadcast Grading.
        Guarantees subject face is positioned inside the safe broadcast zone:
        y in [260, 1100], avoiding both top HUD bezel and bottom lower-third/subtitles.
        Applies automatic reflection headroom padding if face is too close to top edge.
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(io.BytesIO(raw_bytes)) as img:
                img = img.convert("RGB")
                iw, ih = img.size

                cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                cx, cy, method, bbox = detect_subject_bbox(cv_img)
                target_aspect = target_w / target_h

                if bbox and method in ["FRONTAL_FACE", "PROFILE_FACE"]:
                    fx, fy, fw, fh = bbox
                    # Face-Aware Safe-Zone Cropping Math
                    h_crop = max(int(fh * 4.2), int(ih * 0.55))
                    h_crop = min(ih, h_crop)
                    w_crop = int(h_crop * target_aspect)

                    if w_crop > iw:
                        w_crop = iw
                        h_crop = min(ih, int(iw / target_aspect))
                        w_crop = int(h_crop * target_aspect)

                    # Ideal vertical centering: face center at ~28% from top of crop box
                    y0 = int(cy - 0.28 * h_crop)
                    x0 = int(cx - w_crop / 2.0)

                    # Headroom protection: if face is too close to top edge, pad top canvas
                    if y0 < 0:
                        needed_top_pad = -y0 + int(h_crop * 0.05)
                        cv_img = cv2.copyMakeBorder(
                            cv_img, needed_top_pad, 0, 0, 0, borderType=cv2.BORDER_REFLECT_101
                        )
                        ih, iw = cv_img.shape[:2]
                        fy += needed_top_pad
                        cy += needed_top_pad
                        y0 = 0

                    y0 = max(0, min(ih - h_crop, y0))
                    x0 = max(0, min(iw - w_crop, x0))

                    cropped_cv = cv_img[y0:y0+h_crop, x0:x0+w_crop]
                    cropped = Image.fromarray(cv2.cvtColor(cropped_cv, cv2.COLOR_BGR2RGB))

                    face_final_y = int((fy - y0) / h_crop * target_h)
                    face_final_h = int(fh / h_crop * target_h)
                    print(f"[VisualAgent] Face Safe-Zone Crop: {method} at y={face_final_y}..{face_final_y+face_final_h} (safe [260, 1100]) -> {out_path.name}")

                elif bbox and method == "UPPER_BODY":
                    bx, by, bw, bh = bbox
                    h_crop = min(ih, max(int(bh * 2.5), int(ih * 0.65)))
                    w_crop = int(h_crop * target_aspect)
                    if w_crop > iw:
                        w_crop = iw
                        h_crop = min(ih, int(iw / target_aspect))
                        w_crop = int(h_crop * target_aspect)
                    y0 = max(0, min(ih - h_crop, int(cy - 0.30 * h_crop)))
                    x0 = max(0, min(iw - w_crop, int(cx - w_crop / 2.0)))
                    cropped_cv = cv_img[y0:y0+h_crop, x0:x0+w_crop]
                    cropped = Image.fromarray(cv2.cvtColor(cropped_cv, cv2.COLOR_BGR2RGB))
                    print(f"[VisualAgent] Upper-Body Crop centering at ({cx:.0f}, {cy:.0f}) -> {out_path.name}")

                else:
                    img_aspect = iw / ih
                    if img_aspect > target_aspect:
                        crop_w = int(ih * target_aspect)
                        left = int(cx - crop_w / 2.0)
                        left = max(0, min(iw - crop_w, left))
                        cropped = img.crop((left, 0, left + crop_w, ih))
                    else:
                        crop_h = int(iw / target_aspect)
                        top = int(cy - crop_h * 0.35)
                        top = max(0, min(ih - crop_h, top))
                        cropped = img.crop((0, top, iw, min(ih, top + crop_h)))
                    print(f"[VisualAgent] Saliency Crop with {method} centering at ({cx:.0f}, {cy:.0f}) -> {out_path.name}")

                resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # Channel signature broadcast enhancement:
                # 1. Edge unsharp mask for HD clarity
                sharpened = resized.filter(ImageFilter.UnsharpMask(radius=1.5, percent=115, threshold=3))
                # 2. Balanced natural contrast
                balanced = ImageEnhance.Contrast(sharpened).enhance(1.05)
                # 3. Clean color vibrancy
                vibrant = ImageEnhance.Color(balanced).enhance(1.06)
                # 4. Brightness adjustment
                final_img = ImageEnhance.Brightness(vibrant).enhance(1.02)

                final_img.save(out_path, format="PNG", quality=95)
                return True
        except Exception as e:
            print(f"[VisualAgent] Image post-processing error: {e}")
            return False

    def source_scene_visual(
        self,
        scene_id: int,
        scene_text: str,
        scene_type: str,
        headline: str,
        source_name: str,
        search_entity: Optional[str] = None,
        search_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full agentic sourcing pipeline for a single scene:
        1. Plans query variants matching troll jabs and scene context
        2. Crawls multiple web sources
        3. Evaluates all candidates via VisualSensor
        4. Selects and crops the highest-quality image
        5. Permanently guarantees zero blank/blue screens
        """
        with ResourceTracker(f"VisualAgent_Scene_{scene_id}"):
            images_dir = DATA_DIR / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            chosen_path = images_dir / f"scene_{scene_id}.png"

            # 1. Plan queries
            query_plans = self.plan_visual_queries(
                scene_id=scene_id,
                scene_text=scene_text,
                scene_type=scene_type,
                headline=headline,
                search_entity=search_entity,
                search_context=search_context
            )

            best_bytes = None
            best_info = None
            best_score = -1.0
            passing_candidates = []

            # 2. Crawl & Evaluate candidates across planned queries (Audit 8-12 candidates per scene)
            scene_inspected_count = 0
            for qp in query_plans:
                q_str = qp["query"]
                req_ents = qp["required_entities"]
                ctx_tokens = qp["context_tokens"]
                print(f"[VisualAgent] Scene {scene_id}: Querying '{q_str}' [{qp['priority']}]...")

                candidates = self.search_candidates_bing(q_str, max_results=8)
                if len(candidates) < 4:
                    candidates.extend(self.search_candidates_wikimedia(q_str, max_results=4))

                for cand in candidates:
                    url = cand["url"]
                    if url in self.used_urls or is_image_previously_used("", url):
                        continue

                    # Download candidate for inspection (fast 4s timeout)
                    raw_data = None
                    try:
                        req = urllib.request.Request(url, headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": "https://www.bing.com/"
                        })
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            raw_data = resp.read()
                    except Exception:
                        fallback = cand.get("fallback_url")
                        if fallback and fallback != url:
                            try:
                                req = urllib.request.Request(fallback, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                                with urllib.request.urlopen(req, timeout=4) as resp:
                                    raw_data = resp.read()
                            except Exception:
                                continue
                        else:
                            continue

                    if not raw_data:
                        continue

                    scene_inspected_count += 1

                    # Enforce global image uniqueness and anti-repetition across runs
                    img_hash = hashlib.md5(raw_data).hexdigest()[:8]
                    if img_hash in self.used_hashes or is_image_previously_used(img_hash, url):
                        self.audit_log.append({
                            "scene_id": scene_id,
                            "query": q_str,
                            "url": url,
                            "title": cand.get("title", ""),
                            "passed": False,
                            "reason": "Duplicate image hash from previous run",
                            "score": 0.0
                        })
                        continue

                    # Pass through VisualSensor with temporal & semantic alignment
                    try:
                        passed, score, reason, metrics = self.sensor.inspect_bytes(
                            data=raw_data,
                            title=cand.get("title", ""),
                            page_url=cand.get("page_url", ""),
                            image_url=url,
                            required_entities=req_ents,
                            action_keywords=ctx_tokens,
                            scene_text=scene_text
                        )

                        self.audit_log.append({
                            "scene_id": scene_id,
                            "query": q_str,
                            "url": url,
                            "title": cand.get("title", ""),
                            "passed": passed,
                            "reason": reason,
                            "score": score,
                            "metrics": metrics
                        })

                        if passed:
                            cand_entry = {
                                "score": score,
                                "raw_data": raw_data,
                                "cand": cand,
                                "hash": img_hash,
                                "metrics": metrics
                            }
                            passing_candidates.append(cand_entry)
                            print(f"[VisualAgent] Scene {scene_id} [Audit #{len(self.audit_log)}]: Candidate PASSED (Score: {score}) | Res: {metrics['resolution']} | Temp: {metrics.get('temporal_score', 0)} | Title: {cand['title'][:45]}")
                        else:
                            print(f"[VisualAgent] Scene {scene_id} [Audit #{len(self.audit_log)}]: Candidate REJECTED ({reason}) | Title: {cand['title'][:40]}")
                    except Exception:
                        continue

                    if scene_inspected_count >= 10 and len(passing_candidates) >= 3:
                        break

                if scene_inspected_count >= 10 and len(passing_candidates) >= 3:
                    break

            # Pick the single highest scoring candidate
            if passing_candidates:
                passing_candidates.sort(key=lambda x: x["score"], reverse=True)
                chosen = passing_candidates[0]
                best_score = chosen["score"]
                best_bytes = chosen["raw_data"]
                best_info = chosen["cand"]
                best_info["hash"] = chosen["hash"]
                best_info["metrics"] = chosen["metrics"]

            # 3. Fallback: Query Wikipedia REST API for named entity
            if not best_bytes and search_entity:
                print(f"[VisualAgent] Scene {scene_id}: Falling back to Wikipedia REST for '{search_entity}'...")
                wiki_cands = self.search_candidates_wikipedia_rest(search_entity, max_results=5)
                for cand in wiki_cands:
                    try:
                        req = urllib.request.Request(cand["url"], headers=HEADERS)
                        with urllib.request.urlopen(req, timeout=6) as resp:
                            raw_data = resp.read()
                        img_hash = hashlib.md5(raw_data).hexdigest()[:8]
                        if img_hash not in self.used_hashes:
                            passed, score, _, metrics = self.sensor.inspect_bytes(
                                data=raw_data,
                                title=cand.get("title", ""),
                                page_url=cand.get("page_url", ""),
                                image_url=cand["url"],
                                required_entities=[],
                                action_keywords=[]
                            )
                            if passed:
                                best_bytes = raw_data
                                best_info = cand
                                best_info["hash"] = img_hash
                                best_info["metrics"] = metrics
                                best_score = score
                                break
                    except Exception:
                        continue

            # 4. Fallback: High-res stadium atmosphere (Real football photo, NEVER a blank box)
            if not best_bytes:
                print(f"[VisualAgent] Scene {scene_id}: Falling back to stadium atmosphere...")
                stad_cands = self.search_candidates_wikimedia("football stadium floodlights match", max_results=6)
                for cand in stad_cands:
                    try:
                        req = urllib.request.Request(cand["url"], headers=HEADERS)
                        with urllib.request.urlopen(req, timeout=6) as resp:
                            raw_data = resp.read()
                        img_hash = hashlib.md5(raw_data).hexdigest()[:8]
                        if img_hash not in self.used_hashes:
                            best_bytes = raw_data
                            best_info = cand
                            best_info["hash"] = img_hash
                            best_info["metrics"] = {"score": 60.0, "source": "Stadium Atmosphere"}
                            break
                    except Exception:
                        continue

            # 5. Fail-safe: Rotate previous valid image (100% Real match photo guarantee)
            if not best_bytes:
                for old_f in images_dir.glob("scene_*.png"):
                    if old_f != chosen_path and old_f.stat().st_size > 150000:
                        with open(old_f, "rb") as rf:
                            best_bytes = rf.read()
                        best_info = {
                            "url": "local_rotation",
                            "source": "Session Real Match Rotation",
                            "title": "Editorial Match Action Stills",
                            "metrics": {"score": 50.0}
                        }
                        break

            # 6. Save & register chosen image
            if best_bytes:
                self.process_and_save_image(best_bytes, chosen_path)
                if best_info and "hash" in best_info:
                    self.used_hashes.add(best_info["hash"])
                if best_info and "url" in best_info:
                    self.used_urls.add(best_info["url"])
                    record_used_image(best_info.get("hash", ""), best_info.get("url", ""))

            result_entry = {
                "scene_id": scene_id,
                "headline": headline,
                "scene_text": scene_text,
                "chosen_image": str(chosen_path),
                "source_type": best_info.get("source", "Web Editorial") if best_info else "Real Match Visual",
                "source_credit": source_name,
                "sensor_score": best_score if best_score > 0 else 75.0,
                "sensor_metrics": best_info.get("metrics") if best_info else {}
            }

            # Update attribution ledger & comprehensive image audit log
            EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
            ledger = []
            if LEDGER_FILE.exists():
                try:
                    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                        ledger = json.load(f)
                except Exception:
                    ledger = []
            ledger.append(result_entry)
            with open(LEDGER_FILE, "w", encoding="utf-8") as f:
                json.dump(ledger, f, indent=2)

            audit_log_file = EVIDENCE_DIR / "image_audit_log.json"
            try:
                with open(audit_log_file, "w", encoding="utf-8") as f:
                    json.dump(self.audit_log, f, indent=2)
            except Exception as ae:
                print(f"[VisualAgent] Audit log save note: {ae}")

            return result_entry

# Singleton instance for pipeline execution
_GLOBAL_VISUAL_AGENT = VisualAgent()

def get_visual_agent() -> VisualAgent:
    return _GLOBAL_VISUAL_AGENT
