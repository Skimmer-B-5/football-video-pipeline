"""
FS 30 License Gate Subsystem.
Strictly evaluates asset licenses against an allow-list, rejects unknown or
non-commercial licenses, and automatically compiles attribution credits into
runs/<run_id>/credits.txt.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import json
import time

ALLOWLIST_LICENSES = {
    # Public Domain / CC0
    "cc0",
    "public domain",
    "pdm",
    "cc0 1.0",
    "cc0 1.0 universal",
    # User packs & authorized vendors
    "user local pack (personal/commercial)",
    "user local pack",
    "resource boy free license (personal/commercial)",
    "resource boy free license",
    "procedural vector kit (cc0)",
    "procedural vector kit",
    # Open Font License
    "ofl",
    "sil open font license",
    # Attribution permitted (commercial allowed)
    "cc by 4.0",
    "cc by 3.0",
    "cc by 2.0",
    "cc-by-4.0",
    "cc-by-3.0",
    "cc-by-sa-4.0",
    "cc by-sa 4.0",
    "cc by-sa 3.0",
    "cc-by-sa-3.0",
    "apache 2.0",
    "mit"
}

REVIEW_NEEDED_LICENSES = {
    "mixkit free license",
    "lottiefiles simple license"
}

REJECT_LICENSES = {
    "all rights reserved",
    "copyright",
    "cc by-nc",
    "cc by-nc 4.0",
    "cc by-nc-sa",
    "cc-by-nc",
    "cc-by-nc-sa",
    "non-commercial",
    "editorial only"
}

def validate_license(license_str: str) -> Tuple[bool, str, bool]:
    """
    Validates a license string.
    Returns: (is_allowed, canonical_license_name, attribution_required)
    """
    if not license_str:
        return False, "UNKNOWN (Rejected: No license provided)", False

    norm = license_str.strip().lower()

    # Reject non-commercial or forbidden licenses
    for rej in REJECT_LICENSES:
        if rej in norm:
            return False, f"REJECTED: Non-commercial/Restricted ({license_str})", False

    # Check allowlist
    for allowed in ALLOWLIST_LICENSES:
        if allowed in norm:
            is_attr = ("by" in norm or "attribution" in norm or "apache" in norm) and ("cc0" not in norm)
            return True, license_str, is_attr

    # Check review needed
    for rev in REVIEW_NEEDED_LICENSES:
        if rev in norm:
            return True, f"{license_str} (FLAGGED: Needs Review)", True

    return False, f"UNKNOWN (Rejected: License not in allowlist: '{license_str}')", False

def record_credit(run_dir: Path, asset_dict: Dict[str, Any]):
    """
    Appends an asset to runs/<run_id>/credits.txt if attribution is required.
    """
    if not asset_dict.get("attribution_required"):
        return

    credits_file = Path(run_dir) / "credits.txt"
    title = asset_dict.get("name") or asset_dict.get("id")
    author = asset_dict.get("author", "Unknown Author")
    lic = asset_dict.get("license", "Unknown License")
    src = asset_dict.get("source_url", "Local Asset")

    credit_line = f"• \"{title}\" by {author} ({lic}) - {src}\n"

    # Avoid duplicate lines
    existing = set()
    if credits_file.exists():
        with open(credits_file, "r", encoding="utf-8") as f:
            existing = set(f.readlines())

    if credit_line not in existing:
        with open(credits_file, "a", encoding="utf-8") as f:
            if not existing:
                f.write(f"FS 30 Short Credits & Attributions\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n" + "="*50 + "\n\n")
            f.write(credit_line)
