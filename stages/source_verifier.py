"""
beta/stages/source_verifier.py - Real Source Retrieval, HTTP Verification, and Corroboration Engine.

Implements:
1. Real HTTP fetching, redirect resolution, canonical URL tracking.
2. Rejection of placeholder URLs, invented slugs, generic homepages, and 404/inaccessible links.
3. Metadata extraction (canonical URL, article title, publisher, publication date, article body).
4. Text support verification: confirms that cited claims actually exist within the fetched article.
5. Independence & Corroboration analysis: detects duplicate URLs, syndication copies, and aggregators.
"""

import re
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict

# Known generic homepage patterns that are NOT valid article evidence
GENERIC_HOMEPAGE_PATTERNS = [
    r"^https?://(?:www\.)?bbc\.co(?:m|\.uk)/sport/?$",
    r"^https?://(?:www\.)?bbc\.co(?:m|\.uk)/sport/football/?$",
    r"^https?://(?:www\.)?corrieredellosport\.it/?$",
    r"^https?://(?:www\.)?marca\.com/?$",
    r"^https?://(?:www\.)?marca\.com/futbol/?$",
    r"^https?://(?:www\.)?theguardian\.com/?$",
    r"^https?://(?:www\.)?theguardian\.com/football/?$",
    r"^https?://(?:www\.)?theathletic\.com/?$",
    r"^https?://(?:www\.)?skysports\.com/?$",
    r"^https?://(?:www\.)?skysports\.com/football/?$",
    r"^https?://(?:www\.)?laliga\.com/?$",
    r"^https?://(?:www\.)?premierleague\.com/?$"
]

PLACEHOLDER_DOMAINS = [
    "example.com", "dummy.com", "test.com", "placeholder.com", "localhost"
]

@dataclass
class SourceVerificationResult:
    url: str
    canonical_url: str
    http_status: int
    is_accessible: bool
    is_generic_homepage: bool
    is_placeholder: bool
    title: str
    publisher: str
    published_date: Optional[str]
    article_text: str
    is_verified: bool
    rejection_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SourceVerifier:
    """Verifies real HTTP accessibility, extracts metadata, and validates source content."""

    @classmethod
    def is_generic_homepage(cls, url: str) -> bool:
        clean = url.strip().lower().rstrip("/")
        for pat in GENERIC_HOMEPAGE_PATTERNS:
            if re.match(pat, clean):
                return True
        # Check path depth: homepages usually have 0 or 1 path segment without an article slug
        parsed = urllib.parse.urlparse(clean)
        path_segments = [s for s in parsed.path.split("/") if s]
        if len(path_segments) == 0:
            return True
        if len(path_segments) == 1 and path_segments[0] in ["football", "sport", "calcio", "futbol"]:
            return True
        return False

    @classmethod
    def is_placeholder(cls, url: str) -> bool:
        clean = url.strip().lower()
        if not clean or clean.startswith("http://example") or clean.startswith("https://example"):
            return True
        for ph in PLACEHOLDER_DOMAINS:
            if ph in clean:
                return True
        return False

    @classmethod
    def normalize_canonical_url(cls, url: str) -> str:
        """Strips tracking query parameters (utm_*, ref, etc.) and normalizes casing/trailing slash."""
        parsed = urllib.parse.urlparse(url.strip())
        # Filter tracking params
        query_pairs = urllib.parse.parse_qsl(parsed.query)
        clean_pairs = [(k, v) for k, v in query_pairs if not k.startswith("utm_") and k not in ["ref", "fbclid"]]
        clean_query = urllib.parse.urlencode(clean_pairs)
        norm_path = parsed.path.rstrip("/")
        return urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            norm_path,
            parsed.params,
            clean_query,
            ""  # drop fragment
        ))

    @classmethod
    def verify_url(
        cls,
        url: str,
        timeout: float = 6.0,
        mock_registry: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> SourceVerificationResult:
        """
        Performs genuine verification of a source URL.
        Accepts mock_registry for hermetic testing and offline regression tests.
        """
        url_clean = url.strip()

        # 1. Check placeholder
        if cls.is_placeholder(url_clean):
            return SourceVerificationResult(
                url=url_clean,
                canonical_url=url_clean,
                http_status=0,
                is_accessible=False,
                is_generic_homepage=False,
                is_placeholder=True,
                title="",
                publisher="Unknown",
                published_date=None,
                article_text="",
                is_verified=False,
                rejection_reason="Placeholder or dummy URL rejected."
            )

        # 2. Check generic homepage
        if cls.is_generic_homepage(url_clean):
            return SourceVerificationResult(
                url=url_clean,
                canonical_url=cls.normalize_canonical_url(url_clean),
                http_status=200,
                is_accessible=True,
                is_generic_homepage=True,
                is_placeholder=False,
                title="Generic Homepage",
                publisher=urllib.parse.urlparse(url_clean).netloc,
                published_date=None,
                article_text="",
                is_verified=False,
                rejection_reason="Generic homepage URL rejected: Must link to a specific article or document."
            )

        # 3. Check mock registry if provided (for determinism in regression tests)
        if mock_registry and url_clean in mock_registry:
            m = mock_registry[url_clean]
            status = m.get("http_status", 200)
            is_acc = (status == 200)
            canonical = cls.normalize_canonical_url(m.get("canonical_url", url_clean))
            return SourceVerificationResult(
                url=url_clean,
                canonical_url=canonical,
                http_status=status,
                is_accessible=is_acc,
                is_generic_homepage=False,
                is_placeholder=False,
                title=m.get("title", ""),
                publisher=m.get("publisher", urllib.parse.urlparse(url_clean).netloc),
                published_date=m.get("published_date"),
                article_text=m.get("article_text", ""),
                is_verified=is_acc,
                rejection_reason=None if is_acc else f"HTTP {status} - Inaccessible"
            )

        # 4. Perform live request via requests/urllib
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url_clean, headers=headers, timeout=timeout, allow_redirects=True)
            canonical = cls.normalize_canonical_url(resp.url)
            status = resp.status_code

            if status != 200:
                return SourceVerificationResult(
                    url=url_clean,
                    canonical_url=canonical,
                    http_status=status,
                    is_accessible=False,
                    is_generic_homepage=False,
                    is_placeholder=False,
                    title="",
                    publisher=urllib.parse.urlparse(canonical).netloc,
                    published_date=None,
                    article_text="",
                    is_verified=False,
                    rejection_reason=f"HTTP {status}: Article not accessible."
                )

            html = resp.text
            # Extract title
            t_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
            title = t_match.group(1).strip() if t_match else ""
            title = re.sub(r'\s+', ' ', title)

            # Extract date
            d_match = re.search(r'property="article:published_time"\s+content="([^"]+)"', html, re.I)
            pub_date = d_match.group(1)[:10] if d_match else None

            # Extract publisher
            domain = urllib.parse.urlparse(canonical).netloc.replace("www.", "")
            publisher = domain.split(".")[0].title()

            # Clean text (strip tags)
            clean_text = re.sub(r'<script.*?</script>', '', html, flags=re.I | re.S)
            clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.I | re.S)
            clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()

            return SourceVerificationResult(
                url=url_clean,
                canonical_url=canonical,
                http_status=status,
                is_accessible=True,
                is_generic_homepage=False,
                is_placeholder=False,
                title=title,
                publisher=publisher,
                published_date=pub_date,
                article_text=clean_text[:5000],
                is_verified=True,
                rejection_reason=None
            )

        except Exception as e:
            return SourceVerificationResult(
                url=url_clean,
                canonical_url=url_clean,
                http_status=0,
                is_accessible=False,
                is_generic_homepage=False,
                is_placeholder=False,
                title="",
                publisher="Unknown",
                published_date=None,
                article_text="",
                is_verified=False,
                rejection_reason=f"Network fetch failed: {str(e)}"
            )

    @classmethod
    def verify_claim_support(
        cls,
        claim_extract: str,
        source_result: SourceVerificationResult
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifies whether the fetched article text genuinely supports the claim extract.
        """
        if not source_result.is_verified:
            return False, f"Cannot verify claim on invalid source: {source_result.rejection_reason}"

        article_lower = source_result.article_text.lower()
        extract_lower = claim_extract.lower()

        # Extract substantive keywords (> 4 letters) from claim
        keywords = [w for w in re.findall(r'[a-zA-Z0-9€$£-]+', extract_lower) if len(w) >= 4]
        if not keywords:
            return True, None

        # Check presence of key entities and numbers
        matched_keywords = [k for k in keywords if k in article_lower]
        ratio = len(matched_keywords) / len(keywords)

        if ratio < 0.40:
            missing = [k for k in keywords if k not in article_lower][:5]
            return False, f"Article text fails to corroborate claim: missing key terms {missing} (match ratio: {round(ratio*100, 1)}%)."

        return True, None


class SourceCorroborationEngine:
    """Analyzes a list of sources for independence, detecting duplicates and syndication."""

    @classmethod
    def analyze_sources(cls, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identifies:
        - canonical URL duplication
        - syndicated copies / aggregations
        - truly independent primary sources
        """
        seen_canonical = {}
        duplicates = []
        syndicated = []
        independent_sources = []

        for s in sources:
            url = s.get("url", "").strip()
            c_url = SourceVerifier.normalize_canonical_url(url)
            pub = s.get("publisher", "Unknown")

            if c_url in seen_canonical:
                duplicates.append({
                    "original_url": seen_canonical[c_url],
                    "duplicate_url": url,
                    "canonical_url": c_url
                })
                continue

            seen_canonical[c_url] = url

            # Check if source explicitly cites another outlet as the origin
            raw_text = s.get("raw_text", "").lower()
            cited_origin = None
            for outlet in ["corriere dello sport", "marca", "gazzetta", "the athletic", "bbc sport", "reuters", "sky sports"]:
                if outlet != pub.lower() and (f"according to {outlet}" in raw_text or f"reported by {outlet}" in raw_text or f"cites {outlet}" in raw_text):
                    cited_origin = outlet
                    break

            if cited_origin:
                syndicated.append({
                    "publisher": pub,
                    "url": url,
                    "underlying_origin": cited_origin
                })
            else:
                independent_sources.append({
                    "publisher": pub,
                    "url": url,
                    "canonical_url": c_url
                })

        is_independent_corroboration = len(independent_sources) >= 2

        return {
            "total_submitted": len(sources),
            "unique_canonical_count": len(seen_canonical),
            "duplicates": duplicates,
            "syndicated_aggregations": syndicated,
            "independent_primary_sources": independent_sources,
            "is_independent_corroboration": is_independent_corroboration
        }
