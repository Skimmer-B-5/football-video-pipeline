"""
# PROVENANCE: Copied from stages/image_semantic_agent.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Stage: Semantic Relevance & Verification Agent for @Footballin30sec.
Location: stages/image_semantic_agent.py

Provides:
1. Intelligent Query Planner with Negative Filters:
   - Uses Groq Qwen-27B and Groq GPT-OSS-120B (via stages.groq_client) with automatic model failover
     and dual-key redundancy to generate search queries with negative keywords and context guards.
   - Formats queries with exact entity quotes and minus exclusions (e.g. -"Real Madrid" -"2014" -"shirt" -"Champions League").
   - Explicitly distinguishes between authentic editorial scenes vs roast/meme scenes.
   - Resilient rule-based heuristic fallback if Groq API is temporarily unavailable or rate-limited.

2. Candidate Semantic Verifier:
   - Audits image candidate titles, page URLs, image URLs, and snippet text before downloading.
   - Enforces negative filter rejection (e.g. rejecting "Santiago Bernabeu final" when searching for golf).
   - Enforces emotional intent & action alignment (e.g. rejecting celebration photos when searching for crying meme).
   - Enforces domain blacklists (watermarked stock previews, clipart, wallpaper spam).
   - Supports both ultra-fast (<0.1ms) regex/token gating and deep LLM semantic audit via Groq.

3. Anti-Repetition & History Tracking:
   - Full integration with evidence/used_images_history.json.
   - Dual perceptual image hashing: Difference Hash (dHash) and DCT Perceptual Hash (pHash).
   - Canonical URL normalization and tracking.
   - Prevents duplicate or near-duplicate reuse across consecutive scenes or videos.
   - 100% backwards-compatible with existing schema (hashes and urls).
"""

import os
import sys
import re
import json
import time
import html
import io
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict

from PIL import Image
import numpy as np
import scipy.fftpack

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from stages.groq_client import call_groq_chat

EVIDENCE_DIR = PROJECT_ROOT / "evidence"
HISTORY_FILE = EVIDENCE_DIR / "used_images_history.json"

# Stock photo archives and low-quality aggregators to disqualify immediately
DISQUALIFIED_DOMAINS = {
    'alamy.com', 'alamy', 'gettyimages', 'getty', 'shutterstock.com', 'shutterstock',
    'istockphoto.com', 'istock', 'stockphoto.com', 'dreamstime.com', 'depositphotos.com',
    'wallpaperaccess.com', 'wallpapercave.com', 'wallpapersafari.com', 'wallpaper',
    'pinterest.com', 'aliexpress.com', 'amazon.com', 'ebay.com', 'freepik.com',
    'vectorstock.com', 'momjunction.com', 'howweelearn.com', 'teacherspayteachers.com',
    'clipart', 'iconfinder.com', 'flaticon.com', 'deviantart.com', 'lookfordiagnosis.com',
    'coloring', 'sketch'
}

# Common emotion keyword dictionaries for fast semantic audit
EMOTION_KEYWORDS = {
    "crying_despair": {
        "positives": ["crying", "tears", "cry", "weep", "sob", "despair", "heartbreak", "devastated", "dejected", "in tears", "gutted", "missed penalty", "penalty miss", "anguish"],
        "negatives": ["celebration", "celebrates", "celebrating", "smiling", "smiles", "smile", "siu", "trophy", "happy", "jubilant", "triumphant", "cheering", "laughter", "laughing", "ballon d'or", "champion"]
    },
    "stressed_frown": {
        "positives": ["frown", "frowning", "stressed", "head in hands", "dejected", "grim", "frustrated", "scowl", "worried", "unhappy", "concerned", "agony", "directors box", "executive box"],
        "negatives": ["smiling", "smiles", "smile", "happy", "celebration", "celebrating", "beaming", "thumbs up", "baseball", "dodgers", "world series", "parade", "trophy"]
    },
    "relaxed_leisure": {
        "positives": ["golf", "swing", "fairway", "course", "tee", "club", "putt", "green", "pebble beach", "pro-am", "drive", "hole-in-one", "caddie"],
        "negatives": ["real madrid", "madrid", "bernabeu", "champions league", "la liga", "shirt", "jersey", "football pitch", "stadium", "match", "trophy", "soccer", "2014"]
    },
    "historic_signing": {
        "positives": ["1996", "signing", "signs", "contract", "keegan", "kevin keegan", "st james", "unveiled", "unveiling", "press conference", "transfer"],
        "negatives": ["2010", "2015", "2020", "2024", "match of the day", "motd", "pundit", "studio", "guest", "commentator", "talking", "analysis"]
    }
}


@dataclass
class SemanticQueryPlan:
    """Structured search query plan with negative keywords and context guards."""
    entity: str
    scene_category: str          # "editorial" | "roast_meme" | "historic_archive"
    emotional_intent: str        # e.g. "relaxed leisure", "crying despair", "executive frown"
    target_action: str           # e.g. "golf swing", "crying after penalty miss", "sitting in directors box"
    primary_query: str           # e.g. '"Gareth Bale" golf swing -"Real Madrid" -"2014" -"shirt" -"Champions League"'
    alternative_queries: List[str] = field(default_factory=list)
    positive_guards: List[str] = field(default_factory=list)
    negative_filters: List[str] = field(default_factory=list)
    raw_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateAuditResult:
    """Detailed audit verdict for a single image candidate."""
    passed: bool
    confidence: float            # 0.0 to 1.0
    reason: str
    scene_intent: str
    matched_positives: List[str] = field(default_factory=list)
    matched_negatives: List[str] = field(default_factory=list)
    candidate_title: str = ""
    candidate_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerceptualHasher:
    """
    Computes difference hash (dHash) and DCT-based perceptual hash (pHash)
    for invariant image duplicate detection.
    """

    @staticmethod
    def compute_dhash(img_input: Any, hash_size: int = 8) -> str:
        """
        Computes Difference Hash (dHash) - 64-bit hex.
        Tracks gradients between adjacent pixels. Invariant to scaling and mild color changes.
        """
        try:
            if isinstance(img_input, (bytes, bytearray)):
                img = Image.open(io.BytesIO(img_input))
            elif isinstance(img_input, (str, Path)):
                img = Image.open(str(img_input))
            elif isinstance(img_input, Image.Image):
                img = img_input
            else:
                return ""

            # Resize to (hash_size + 1, hash_size) grayscale
            gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            arr = np.asarray(gray, dtype=np.int16)

            # Compare adjacent horizontal pixels
            diff = arr[:, :-1] > arr[:, 1:]
            val = 0
            for idx, bit in enumerate(diff.flatten()):
                if bit:
                    val |= (1 << idx)
            return f"{val:016x}"
        except Exception as e:
            return ""

    @staticmethod
    def compute_phash(img_input: Any, hash_size: int = 8, highfreq_factor: int = 4) -> str:
        """
        Computes DCT-based Perceptual Hash (pHash) - 64-bit hex.
        Extracts low-frequency DCT energy. Invariant to brightness, contrast, and compression.
        """
        try:
            if isinstance(img_input, (bytes, bytearray)):
                img = Image.open(io.BytesIO(img_input))
            elif isinstance(img_input, (str, Path)):
                img = Image.open(str(img_input))
            elif isinstance(img_input, Image.Image):
                img = img_input
            else:
                return ""

            img_size = hash_size * highfreq_factor  # 32
            gray = img.convert("L").resize((img_size, img_size), Image.Resampling.LANCZOS)
            arr = np.asarray(gray, dtype=float)

            # 2D Discrete Cosine Transform
            dct = scipy.fftpack.dct(scipy.fftpack.dct(arr.T, norm='ortho').T, norm='ortho')
            low_freq = dct[:hash_size, :hash_size]

            # Compare low frequencies with median (excluding DC term at [0, 0])
            med = np.median(low_freq.flatten()[1:])
            diff = low_freq > med

            val = 0
            for idx, bit in enumerate(diff.flatten()):
                if bit:
                    val |= (1 << idx)
            return f"{val:016x}"
        except Exception as e:
            return ""

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """Compute bitwise Hamming distance between two 16-character hex hashes."""
        if not hash1 or not hash2:
            return 999
        try:
            val1 = int(hash1, 16)
            val2 = int(hash2, 16)
            return bin(val1 ^ val2).count("1")
        except Exception:
            return 999

    @staticmethod
    def is_similar(hash1: str, hash2: str, max_distance: int = 6) -> bool:
        """True if Hamming distance <= max_distance."""
        return PerceptualHasher.hamming_distance(hash1, hash2) <= max_distance


class ImageHistoryTracker:
    """
    Manages persistent anti-repetition registry in evidence/used_images_history.json.
    Tracks canonical URLs, exact hashes, dHashes, and pHashes.
    Maintains 100% backward compatibility with meme_vault.py.
    """

    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = history_path or HISTORY_FILE
        self._data: Dict[str, Any] = {
            "hashes": [],
            "urls": [],
            "canonical_urls": [],
            "dhashes": [],
            "phashes": [],
            "records": []
        }
        self.load()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Strips query parameters, tracking tags, and fragments for canonical matching."""
        if not url:
            return ""
        try:
            parsed = urllib.parse.urlparse(url)
            # Retain scheme, netloc, and path, ignore query params (often CDN auth/resizing)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            return clean.lower()
        except Exception:
            return url.strip().lower()

    def load(self) -> Dict[str, Any]:
        """Load history file from disk."""
        if self.history_path.exists():
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self._data["hashes"] = loaded.get("hashes", [])
                        self._data["urls"] = loaded.get("urls", [])
                        self._data["canonical_urls"] = loaded.get("canonical_urls", [])
                        self._data["dhashes"] = loaded.get("dhashes", [])
                        self._data["phashes"] = loaded.get("phashes", [])
                        self._data["records"] = loaded.get("records", [])
            except Exception as e:
                print(f"[ImageHistoryTracker] Load note: {e}")
        return self._data

    def save(self):
        """Save history to disk preserving directory structure and capping history."""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            # Cap history to prevent unbounded growth while keeping solid multi-video memory
            save_payload = {
                "hashes": self._data["hashes"][-250:],
                "urls": self._data["urls"][-250:],
                "canonical_urls": self._data["canonical_urls"][-250:],
                "dhashes": self._data["dhashes"][-250:],
                "phashes": self._data["phashes"][-250:],
                "records": self._data["records"][-250:]
            }
            # Atomic write
            temp_file = self.history_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(save_payload, f, indent=2)
            temp_file.replace(self.history_path)
        except Exception as e:
            print(f"[ImageHistoryTracker] Save error: {e}")

    def is_image_used(
        self,
        url: str,
        image_bytes: Optional[bytes] = None,
        dhash: Optional[str] = None,
        phash: Optional[str] = None,
        dhash_threshold: int = 6,
        phash_threshold: int = 8
    ) -> Tuple[bool, str]:
        """
        Check if an image was used previously via:
        1. Exact URL match
        2. Canonical URL match
        3. Perceptual dHash near-duplicate match
        4. Perceptual pHash near-duplicate match
        """
        if not url:
            return False, ""

        # 1. Exact URL
        if url in self._data["urls"]:
            return True, f"Exact URL previously used: {url}"

        # 2. Canonical URL
        canon_url = self.normalize_url(url)
        if canon_url and canon_url in self._data["canonical_urls"]:
            return True, f"Canonical URL previously used: {canon_url}"

        # Calculate hashes if image bytes provided
        if image_bytes:
            if not dhash:
                dhash = PerceptualHasher.compute_dhash(image_bytes)
            if not phash:
                phash = PerceptualHasher.compute_phash(image_bytes)

        # 3. Perceptual dHash check
        if dhash:
            for stored_dh in self._data["dhashes"]:
                dist = PerceptualHasher.hamming_distance(dhash, stored_dh)
                if dist <= dhash_threshold:
                    return True, f"Perceptual dHash near-duplicate match (Hamming distance {dist} <= {dhash_threshold})"

        # 4. Perceptual pHash check
        if phash:
            for stored_ph in self._data["phashes"]:
                dist = PerceptualHasher.hamming_distance(phash, stored_ph)
                if dist <= phash_threshold:
                    return True, f"Perceptual pHash near-duplicate match (Hamming distance {dist} <= {phash_threshold})"

        return False, ""

    def record_used_image(
        self,
        url: str,
        image_bytes: Optional[bytes] = None,
        dhash: Optional[str] = None,
        phash: Optional[str] = None,
        entity: str = "",
        scene_id: Optional[int] = None
    ):
        """Record used image in history and persist to disk."""
        canon_url = self.normalize_url(url)

        if image_bytes:
            if not dhash:
                dhash = PerceptualHasher.compute_dhash(image_bytes)
            if not phash:
                phash = PerceptualHasher.compute_phash(image_bytes)

        # Legacy 8-char hash compatible with meme_vault.py
        legacy_hash = dhash[:8] if dhash else ""

        if legacy_hash and legacy_hash not in self._data["hashes"]:
            self._data["hashes"].append(legacy_hash)
        if url and url not in self._data["urls"]:
            self._data["urls"].append(url)
        if canon_url and canon_url not in self._data["canonical_urls"]:
            self._data["canonical_urls"].append(canon_url)
        if dhash and dhash not in self._data["dhashes"]:
            self._data["dhashes"].append(dhash)
        if phash and phash not in self._data["phashes"]:
            self._data["phashes"].append(phash)

        record_entry = {
            "url": url,
            "canonical_url": canon_url,
            "dhash": dhash,
            "phash": phash,
            "legacy_hash": legacy_hash,
            "entity": entity,
            "scene_id": scene_id,
            "timestamp": int(time.time())
        }
        self._data["records"].append(record_entry)
        self.save()


class ImageSemanticAgent:
    """
    Semantic Relevance & Verification Agent.
    Plans negative-filtered queries and audits candidate metadata against scene intent.
    """

    def __init__(self, history_tracker: Optional[ImageHistoryTracker] = None):
        self.history = history_tracker or ImageHistoryTracker()

    def plan_queries(
        self,
        scene_desc: str,
        scene_type: str = "editorial",
        context: str = "",
        entity: Optional[str] = None
    ) -> SemanticQueryPlan:
        """
        Generate search queries with negative keywords and context guards using Groq
        (Qwen-27B with fallback to GPT-OSS-120B).
        Includes deterministic heuristic fallback if the LLM is temporarily unavailable.
        """
        # Determine likely entity if omitted
        inferred_entity = entity or ""
        if not inferred_entity:
            # Common football figures
            for known in ["Gareth Bale", "Alan Shearer", "Cristiano Ronaldo", "Todd Boehly",
                          "Lionel Messi", "Erling Haaland", "Kylian Mbappe", "Jose Mourinho",
                          "Pep Guardiola", "Erik ten Hag", "Antony", "Marcus Rashford"]:
                if known.lower() in scene_desc.lower() or known.lower() in context.lower():
                    inferred_entity = known
                    break
        if not inferred_entity:
            # First 2-3 capitalized words or words in quotes
            quoted = re.findall(r'"([^"]+)"', scene_desc)
            if quoted:
                inferred_entity = quoted[0]
            else:
                words = [w for w in scene_desc.split() if w and w[0].isupper()]
                inferred_entity = " ".join(words[:2]) if words else "football"

        # System prompt for Groq Qwen-27B / GPT-OSS-120B
        system_prompt = (
            "You are the Lead Visual Search & Semantic Query Planner for @Footballin30sec. "
            "Your mission is to construct web search queries with positive context guards and negative keyword filters "
            "(-'keyword') so image search engines return exactly the right visual scene and zero noise.\n\n"
            "Rules:\n"
            "1. Enclose the main person or club name in quotes (e.g. \"Gareth Bale\", \"Alan Shearer\").\n"
            "2. Include essential positive context guards (e.g. golf swing, fairway, 1996 signing Keegan, crying penalty tears).\n"
            "3. Append negative keywords with minus signs to aggressively ban irrelevant eras, teams, celebration vs sadness, or pundit shows:\n"
            "   - Bale golfing: -\"Real Madrid\" -\"2014\" -\"shirt\" -\"Champions League\" -\"football pitch\"\n"
            "   - Shearer 1996 signing: -\"2010\" -\"match of the day\" -\"motd\" -\"pundit\" -\"studio\"\n"
            "   - Ronaldo penalty cry: -\"celebration\" -\"smiling\" -\"siu\" -\"trophy\" -\"happy\"\n"
            "   - Todd Boehly box: -\"Dodgers\" -\"baseball\" -\"smiling\" -\"happy\"\n"
            "4. Distinguish clearly:\n"
            "   - 'editorial': genuine real-life match photo, press conference, historic signing.\n"
            "   - 'roast_meme': viral reaction faces, troll graphics, crying memes, clown edits, despair expressions.\n\n"
            "Respond STRICTLY in JSON matching this schema:\n"
            "{\n"
            "  \"entity\": \"name\",\n"
            "  \"scene_category\": \"editorial\" or \"roast_meme\",\n"
            "  \"emotional_intent\": \"emotion description\",\n"
            "  \"target_action\": \"action description\",\n"
            "  \"primary_query\": \"formatted search query with quotes and -exclusions\",\n"
            "  \"alternative_queries\": [\"alt query 1\", \"alt query 2\"],\n"
            "  \"positive_guards\": [\"token1\", \"token2\"],\n"
            "  \"negative_filters\": [\"forbidden1\", \"forbidden2\"]\n"
            "}"
        )

        user_prompt = (
            f"Plan visual search query for:\n"
            f"Topic: {scene_desc}\n"
            f"Scene Type: {scene_type}\n"
            f"Context: {context or scene_desc}\n"
            f"Entity: {inferred_entity}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        llm_response = call_groq_chat(
            messages=messages,
            preferred_model="qwen/qwen3.8-27b",
            fallback_model="openai/gpt-oss-120b",
            max_tokens=600,
            temperature=0.2,
            timeout=12
        )

        plan = None
        if llm_response:
            try:
                # Find JSON block
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    raw_json = json.loads(json_match.group(0))
                    plan = SemanticQueryPlan(
                        entity=raw_json.get("entity", inferred_entity).strip('\"'),
                        scene_category=raw_json.get("scene_category", scene_type),
                        emotional_intent=raw_json.get("emotional_intent", "authentic"),
                        target_action=raw_json.get("target_action", context or scene_desc),
                        primary_query=raw_json.get("primary_query", ""),
                        alternative_queries=raw_json.get("alternative_queries", []),
                        positive_guards=raw_json.get("positive_guards", []),
                        negative_filters=raw_json.get("negative_filters", []),
                        raw_response=llm_response
                    )
            except Exception as parse_err:
                print(f"[ImageSemanticAgent] LLM JSON parse notice ({parse_err}), employing heuristic fallback.")

        # If LLM failed or response incomplete, apply deterministic heuristic planner
        if not plan or not plan.primary_query:
            plan = self._generate_heuristic_plan(scene_desc, scene_type, context, inferred_entity)

        return plan

    def _generate_heuristic_plan(
        self,
        scene_desc: str,
        scene_type: str,
        context: str,
        entity: str
    ) -> SemanticQueryPlan:
        """
        Deterministic, robust heuristic query planner with negative filters.
        Guarantees that the pipeline never fails even if internet/LLM is offline.
        """
        text_lower = (scene_desc + " " + context).lower()
        clean_ent = entity.strip() if entity else "football"
        category = "roast_meme" if any(w in text_lower for w in ["meme", "roast", "troll", "cry", "clown", "fraud", "despair"]) else "editorial"

        # Bale golfing scenario
        if "golf" in text_lower:
            emotional_intent = "relaxed leisurely golf"
            target_action = "swinging golf club on green course"
            positive_guards = ["golf", "swing", "fairway", "course", "tee", "pebble beach", "club"]
            negative_filters = ["Real Madrid", "2014", "shirt", "Champions League", "Bernabeu", "football pitch", "soccer", "trophy"]
            primary_query = f'"{clean_ent}" golf swing fairway -"Real Madrid" -"2014" -"shirt" -"Champions League"'
            alts = [
                f'"{clean_ent}" playing golf course -"Real Madrid" -"football" -"match"',
                f'"{clean_ent}" Pebble Beach golf -"soccer" -"Bernabeu"'
            ]

        # Shearer 1996 signing scenario
        elif "shearer" in text_lower and ("1996" in text_lower or "signing" in text_lower):
            emotional_intent = "historic signing announcement"
            target_action = "signing Newcastle contract alongside Kevin Keegan in 1996"
            positive_guards = ["1996", "signing", "Newcastle", "Keegan", "contract", "St James"]
            negative_filters = ["2010", "match of the day", "motd", "pundit", "studio", "2015", "2020", "2024"]
            primary_query = f'"{clean_ent}" Newcastle 1996 Keegan signing -"2010" -"match of the day" -"motd" -"pundit"'
            alts = [
                f'"{clean_ent}" Kevin Keegan 1996 contract -"pundit" -"studio"',
                f'"{clean_ent}" Newcastle United 1996 unveiling -"motd"'
            ]

        # Ronaldo penalty cry scenario
        elif "ronaldo" in text_lower and any(w in text_lower for w in ["cry", "tears", "penalty", "frustrat", "sad"]):
            emotional_intent = "crying despair frustration"
            target_action = "crying devastated face after missed penalty"
            category = "roast_meme"
            positive_guards = ["crying", "tears", "penalty miss", "devastated", "meme", "despair", "frustrated"]
            negative_filters = ["celebration", "smiling", "siu", "trophy", "happy", "champion", "jubilant"]
            primary_query = f'"{clean_ent}" penalty miss crying meme -"celebration" -"smiling" -"siu" -"trophy" -"happy"'
            alts = [
                f'"{clean_ent}" crying tears frustrated reaction meme -"celebration" -"smiling"',
                f'"{clean_ent}" devastated penalty shootout face meme -"siu" -"trophy"'
            ]

        # Todd Boehly Chelsea box scenario
        elif "boehly" in text_lower and any(w in text_lower for w in ["box", "chelsea", "frown", "stress", "deject"]):
            emotional_intent = "executive stress and frowning"
            target_action = "sitting in Chelsea directors box frowning dejectedly"
            category = "roast_meme"
            positive_guards = ["directors box", "Chelsea", "frown", "stressed", "head in hands", "dejected"]
            negative_filters = ["Dodgers", "baseball", "smiling", "happy", "celebration", "world series"]
            primary_query = f'"{clean_ent}" Chelsea directors box stressed frowning -"Dodgers" -"baseball" -"smiling" -"happy"'
            alts = [
                f'"{clean_ent}" Stamford Bridge box dejected meme -"Dodgers" -"baseball"',
                f'"{clean_ent}" Chelsea executive box head in hands -"smiling"'
            ]

        # Generic roast/meme
        elif category == "roast_meme":
            emotional_intent = "satirical troll reaction"
            target_action = "viral reaction face or meme still"
            positive_guards = ["meme", "funny", "reaction", "face", "troll"]
            negative_filters = ["wallpaper", "clipart", "stock", "poster"]
            primary_query = f'"{clean_ent}" funny reaction face meme -"wallpaper" -"clipart"'
            alts = [f'"{clean_ent}" meme still']

        # Generic editorial
        else:
            emotional_intent = "authentic match or press conference"
            target_action = context or scene_desc
            positive_guards = [w.lower() for w in re.findall(r'\b[A-Za-z0-9]+\b', context or scene_desc) if len(w) > 3][:5]
            negative_filters = ["wallpaper", "clipart", "sketch", "drawing"]
            primary_query = f'"{clean_ent}" {context or scene_desc} -"wallpaper" -"clipart"'
            alts = [f'"{clean_ent}" match action']

        return SemanticQueryPlan(
            entity=clean_ent,
            scene_category=category,
            emotional_intent=emotional_intent,
            target_action=target_action,
            primary_query=primary_query,
            alternative_queries=alts,
            positive_guards=positive_guards,
            negative_filters=negative_filters
        )

    def audit_candidate(
        self,
        candidate: Dict[str, Any],
        plan: SemanticQueryPlan,
        use_llm: bool = False
    ) -> CandidateAuditResult:
        """
        Audit a candidate's metadata (title, snippet, page URL, image URL) before downloading.
        Rejects:
        - Blacklisted stock photo / clipart domains
        - Matches against negative filters
        - Emotional / action intent mismatches
        """
        title = candidate.get("title") or ""
        desc = candidate.get("desc") or candidate.get("snippet") or ""
        page_url = candidate.get("page_url") or ""
        img_url = candidate.get("url") or ""

        combined_text = f"{title} {desc} {page_url} {img_url}".lower()

        # Gate 1: Domain Blacklist
        for bad_domain in DISQUALIFIED_DOMAINS:
            if bad_domain in img_url.lower() or bad_domain in page_url.lower():
                return CandidateAuditResult(
                    passed=False,
                    confidence=1.0,
                    reason=f"Disqualified domain/stock watermark: '{bad_domain}'",
                    scene_intent=plan.emotional_intent,
                    candidate_title=title,
                    candidate_url=img_url
                )

        # Gate 2: Explicit Negative Filter Matching
        matched_negatives = []
        for neg_term in plan.negative_filters:
            clean_neg = neg_term.strip('\"').lower()
            if not clean_neg:
                continue
            # Word boundary or exact phrase match
            pattern = r'\b' + re.escape(clean_neg) + r'\b'
            if re.search(pattern, combined_text):
                matched_negatives.append(neg_term)

        if matched_negatives:
            return CandidateAuditResult(
                passed=False,
                confidence=0.95,
                reason=f"Candidate triggered negative filters: {matched_negatives}",
                scene_intent=plan.emotional_intent,
                matched_negatives=matched_negatives,
                candidate_title=title,
                candidate_url=img_url
            )

        # Gate 3: Context & Emotion Specific Guard Checks
        # E.g. If Bale golfing: reject any mention of Madrid, Bernabeu, Champions League final
        if "golf" in plan.target_action.lower() or "golf" in plan.emotional_intent.lower():
            golf_negatives = ["bernabeu", "real madrid", "champions league", "la liga", "overhead kick", "bicycle kick", "shirt", "jersey"]
            clashes = [g for g in golf_negatives if re.search(r'\b' + re.escape(g) + r'\b', combined_text)]
            if clashes:
                return CandidateAuditResult(
                    passed=False,
                    confidence=0.98,
                    reason=f"Scene requires golf, but candidate mentions football match/stadium context: {clashes}",
                    scene_intent=plan.emotional_intent,
                    matched_negatives=clashes,
                    candidate_title=title,
                    candidate_url=img_url
                )

        # E.g. If Ronaldo penalty cry: reject celebration, siu, smiling, trophy
        if any(w in plan.target_action.lower() for w in ["cry", "tears", "penalty miss", "devastat"]):
            cry_negatives = ["celebration", "celebrates", "smiling", "smiles", "siu", "trophy", "jubilant", "happy", "ballon d'or", "triumphant"]
            clashes = [c for c in cry_negatives if re.search(r'\b' + re.escape(c) + r'\b', combined_text)]
            if clashes:
                return CandidateAuditResult(
                    passed=False,
                    confidence=0.95,
                    reason=f"Scene requires crying/frustration, but candidate depicts celebration/joy: {clashes}",
                    scene_intent=plan.emotional_intent,
                    matched_negatives=clashes,
                    candidate_title=title,
                    candidate_url=img_url
                )

        # E.g. If Todd Boehly Chelsea box: reject Dodgers baseball and smiling
        if "boehly" in plan.entity.lower() and ("box" in plan.target_action.lower() or "frown" in plan.target_action.lower()):
            boehly_negatives = ["dodgers", "baseball", "world series", "smiling", "smiles", "happy", "parade"]
            clashes = [b for b in boehly_negatives if re.search(r'\b' + re.escape(b) + r'\b', combined_text)]
            if clashes:
                return CandidateAuditResult(
                    passed=False,
                    confidence=0.95,
                    reason=f"Scene requires Chelsea directors box dejection, but candidate mentions baseball/smiling: {clashes}",
                    scene_intent=plan.emotional_intent,
                    matched_negatives=clashes,
                    candidate_title=title,
                    candidate_url=img_url
                )

        # Gate 4: Required Entity Matching
        # Entity tokens (e.g. ['gareth', 'bale'])
        ent_tokens = [w.lower() for w in re.findall(r'\b[A-Za-z0-9]+\b', plan.entity) if len(w) > 2]
        if ent_tokens:
            has_entity = any(tok in combined_text for tok in ent_tokens)
            if not has_entity:
                return CandidateAuditResult(
                    passed=False,
                    confidence=0.85,
                    reason=f"Missing required entity tokens '{plan.entity}'",
                    scene_intent=plan.emotional_intent,
                    candidate_title=title,
                    candidate_url=img_url
                )

        # Gate 5: Positive Guard / Action Keyword Alignment
        matched_positives = []
        for pos in plan.positive_guards:
            clean_pos = pos.lower()
            if re.search(r'\b' + re.escape(clean_pos) + r'\b', combined_text):
                matched_positives.append(pos)

        # Score confidence based on positive matches
        confidence = 0.70
        if matched_positives:
            confidence = min(0.98, 0.70 + (len(matched_positives) / max(1, len(plan.positive_guards))) * 0.28)
        else:
            # Check target action tokens
            action_tokens = [w.lower() for w in re.findall(r'\b[A-Za-z0-9]+\b', plan.target_action) if len(w) > 3]
            matched_act = [w for w in action_tokens if w in combined_text]
            if matched_act:
                matched_positives.extend(matched_act)
                confidence = 0.80
            else:
                return CandidateAuditResult(
                    passed=False,
                    confidence=0.40,
                    reason=f"Lacks positive action context keywords matching '{plan.target_action}'",
                    scene_intent=plan.emotional_intent,
                    candidate_title=title,
                    candidate_url=img_url
                )

        # Optional Gate 6: LLM-Assisted Semantic Verification for high stakes
        if use_llm:
            llm_result = self._audit_candidate_with_llm(candidate, plan)
            if llm_result is not None:
                return llm_result

        return CandidateAuditResult(
            passed=True,
            confidence=round(confidence, 2),
            reason=f"Verified: matches entity '{plan.entity}', action '{plan.target_action}', and emotion '{plan.emotional_intent}'.",
            scene_intent=plan.emotional_intent,
            matched_positives=matched_positives,
            matched_negatives=[],
            candidate_title=title,
            candidate_url=img_url
        )

    def _audit_candidate_with_llm(
        self,
        candidate: Dict[str, Any],
        plan: SemanticQueryPlan
    ) -> Optional[CandidateAuditResult]:
        """Deep semantic audit using Groq Qwen-27B / GPT-OSS-120B."""
        sys_prompt = (
            "You are the Chief Semantic Image Auditor for @Footballin30sec. "
            "Audit candidate metadata against scene emotional intent. Respond strictly in valid JSON."
        )
        user_prompt = (
            f"Desired Scene:\n"
            f"- Entity: {plan.entity}\n"
            f"- Category: {plan.scene_category}\n"
            f"- Target Action: {plan.target_action}\n"
            f"- Emotional Intent: {plan.emotional_intent}\n"
            f"- Negative Filters: {plan.negative_filters}\n\n"
            f"Candidate Metadata:\n"
            f"- Title: {candidate.get('title')}\n"
            f"- Snippet: {candidate.get('desc') or candidate.get('snippet')}\n"
            f"- Page URL: {candidate.get('page_url')}\n"
            f"- Image URL: {candidate.get('url')}\n\n"
            f"Respond ONLY in JSON:\n"
            f'{{"verified": true/false, "confidence": 0.0-1.0, "reason": "brief reason"}}'
        )

        resp = call_groq_chat(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
            preferred_model="qwen/qwen3.8-27b",
            fallback_model="openai/gpt-oss-120b",
            max_tokens=250,
            temperature=0.1,
            timeout=8
        )

        if resp:
            try:
                match = re.search(r'\{.*\}', resp, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    return CandidateAuditResult(
                        passed=bool(data.get("verified", False)),
                        confidence=float(data.get("confidence", 0.8)),
                        reason=data.get("reason", "LLM audit verdict"),
                        scene_intent=plan.emotional_intent,
                        candidate_title=candidate.get("title", ""),
                        candidate_url=candidate.get("url", "")
                    )
            except Exception:
                pass
        return None

    def audit_candidates_batch(
        self,
        candidates: List[Dict[str, Any]],
        plan: SemanticQueryPlan,
        max_verified: int = 5,
        use_llm: bool = False
    ) -> List[Tuple[Dict[str, Any], CandidateAuditResult]]:
        """
        Audit a list of image candidates, returning verified ones sorted by confidence.
        """
        verified = []
        for cand in candidates:
            audit = self.audit_candidate(cand, plan, use_llm=use_llm)
            if audit.passed:
                verified.append((cand, audit))
                if len(verified) >= max_verified:
                    break
        # Sort verified candidates by confidence descending
        verified.sort(key=lambda item: item[1].confidence, reverse=True)
        return verified

    def search_and_verify(
        self,
        query: Optional[str] = None,
        plan: Optional[SemanticQueryPlan] = None,
        count: int = 15,
        use_llm: bool = False
    ) -> List[Tuple[Dict[str, Any], CandidateAuditResult]]:
        """
        Execute Bing web search using query plan, then audit candidate metadata before downloading.
        Tries primary query first, cascading to alternatives if needed to build a candidate pool.
        """
        if not plan and not query:
            return []

        if not plan:
            plan = self.plan_queries(query or "")

        queries_to_try = [plan.primary_query]
        if plan.alternative_queries:
            queries_to_try.extend(plan.alternative_queries)
        clean_positive = f'"{plan.entity}" {plan.target_action}'
        if clean_positive not in queries_to_try:
            queries_to_try.append(clean_positive)

        candidates = []
        seen_urls = set()

        for q in queries_to_try:
            if not q:
                continue
            fetched = self._fetch_bing_candidates(q, count=max(count, 15))
            for f in fetched:
                u = f.get("url")
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    candidates.append(f)
            if len(candidates) >= count:
                break

        return self.audit_candidates_batch(candidates, plan, max_verified=count, use_llm=use_llm)

    def _fetch_bing_candidates(self, query: str, count: int = 15) -> List[Dict[str, Any]]:
        """Fetch raw image candidates from Bing Images async endpoint."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.bing.com/"
        }
        url = f"https://www.bing.com/images/async?q={urllib.parse.quote(query)}&first=0&count={max(count, 20)}&mmasync=1"
        req = urllib.request.Request(url, headers=headers)
        candidates = []
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            matches = re.findall(r'class=[\'"]iusc[\'"][^>]*m=[\'"](\{.*?\})[\'"]', raw)
            for m in matches:
                clean = html.unescape(m)
                try:
                    data = json.loads(clean)
                    murl = data.get("murl")
                    turl = data.get("turl")
                    title = data.get("t", "")
                    desc = data.get("desc", "")
                    purl = data.get("purl", "")
                    if murl:
                        candidates.append({
                            "url": murl,
                            "fallback_url": turl,
                            "title": title,
                            "desc": desc,
                            "page_url": purl,
                            "query": query
                        })
                    if len(candidates) >= count:
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"[ImageSemanticAgent] Bing search error for '{query}': {e}")
        return candidates

    def verify_and_record_download(
        self,
        image_bytes: bytes,
        url: str,
        entity: str = "",
        scene_id: Optional[int] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Post-download verification:
        1. Checks perceptual hashing against history to prevent repetition.
        2. Validates image dimensions, luminance, texture variance.
        3. If passed, records into persistent history.
        """
        # Anti-repetition check
        is_used, reason = self.history.is_image_used(url, image_bytes=image_bytes)
        if is_used:
            return False, f"Anti-repetition rejection: {reason}", {}

        # Visual decode & quality checks
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img = img.convert("RGB")
                w, h = img.size
                if w < 300 or h < 300:
                    return False, f"Resolution too low ({w}x{h})", {}

                arr = np.asarray(img)
                lum = float(np.mean(arr))
                var = float(np.var(arr))

                # Procedural blank rectangle rejection
                if var < 25.0:
                    return False, f"Solid/blank texture variance too low ({var:.1f})", {}
                if lum < 15.0 or lum > 240.0:
                    return False, f"Extreme luminance ({lum:.1f})", {}

                # Compute hashes
                dhash = PerceptualHasher.compute_dhash(img)
                phash = PerceptualHasher.compute_phash(img)

                # Record in history
                self.history.record_used_image(
                    url=url,
                    image_bytes=image_bytes,
                    dhash=dhash,
                    phash=phash,
                    entity=entity,
                    scene_id=scene_id
                )

                metrics = {
                    "width": w,
                    "height": h,
                    "variance": round(var, 1),
                    "luminance": round(lum, 1),
                    "dhash": dhash,
                    "phash": phash
                }
                return True, "PASSED", metrics
        except Exception as e:
            return False, f"Image decoding error: {e}", {}


# Global instance
_GLOBAL_SEMANTIC_AGENT: Optional[ImageSemanticAgent] = None

def get_semantic_agent() -> ImageSemanticAgent:
    """Retrieve global ImageSemanticAgent singleton."""
    global _GLOBAL_SEMANTIC_AGENT
    if _GLOBAL_SEMANTIC_AGENT is None:
        _GLOBAL_SEMANTIC_AGENT = ImageSemanticAgent()
    return _GLOBAL_SEMANTIC_AGENT
