"""
Stage 1: fetch_story
Input: Story URL or pasted text.
Output: story.json {source_name, date, headline, article_text} saved in run directory.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import urllib.parse

try:
    import requests
except ImportError:
    requests = None

def clean_text(text: str) -> str:
    """Strips html tags and extra whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def fetch_story(source_input: str, run_dir: Path, log_func=print) -> Dict[str, Any]:
    """
    Fetches or parses a story, writing story.json to run_dir.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    out_file = run_dir / "story.json"

    log_func(f"[Stage 1: fetch_story] Processing input: {source_input[:80]}...")

    is_url = source_input.strip().startswith("http://") or source_input.strip().startswith("https://")

    if is_url:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(source_input.strip(), headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Extract title
        title_match = re.search(r"<meta\s+property=['\"]og:title['\"]\s+content=['\"]([^'\"]+)['\"]", html, re.I)
        if not title_match:
            title_match = re.search(r"<title>(.*?)</title>", html, re.I)
        headline = clean_text(title_match.group(1)) if title_match else "Breaking Football Story"

        # Extract domain/source name
        parsed_url = urllib.parse.urlparse(source_input)
        domain = parsed_url.netloc.replace("www.", "")
        source_name = domain.split(".")[0].upper()
        if "bbc" in domain:
            source_name = "BBC Sport"
        elif "theguardian" in domain:
            source_name = "The Guardian"
        elif "marca" in domain:
            source_name = "Marca"
        elif "as.com" in domain:
            source_name = "Diario AS"
        elif "skysports" in domain:
            source_name = "Sky Sports"
        elif "theathletic" in domain:
            source_name = "The Athletic"

        # Extract paragraphs
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.I | re.DOTALL)
        clean_paras = [clean_text(p) for p in paragraphs if len(clean_text(p).split()) > 6]
        article_text = "\n".join(clean_paras[:12]) if clean_paras else headline

        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        # Input is pasted text or structured text
        lines = [line.strip() for line in source_input.strip().split("\n") if line.strip()]
        
        # Check if structured "SOURCE NAME: ... HEADLINE: ..." was passed
        source_match = re.search(r"SOURCE\s*(?:NAME)?:\s*([^\n]+)", source_input, re.I)
        headline_match = re.search(r"HEADLINE:\s*([^\n]+)", source_input, re.I)
        date_match = re.search(r"(?:PUBLISHED|DATE):\s*([^\n]+)", source_input, re.I)
        article_match = re.search(r"ARTICLE\s*(?:TEXT)?:\s*(.+)", source_input, re.I | re.DOTALL)

        source_name = source_match.group(1).strip() if source_match else "The Guardian"
        date_str = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
        headline = headline_match.group(1).strip() if headline_match else (lines[0] if lines else "Breaking Football Story")
        
        if article_match:
            article_text = article_match.group(1).strip()
        else:
            article_text = "\n".join(lines[1:]) if len(lines) > 1 else lines[0]

    story_data = {
        "source_name": source_name,
        "date": date_str,
        "headline": headline,
        "article_text": article_text
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(story_data, f, indent=2)

    log_func(f"[Stage 1: fetch_story] ✓ Saved story.json: {headline[:60]} (Source: {source_name})")
    return story_data
