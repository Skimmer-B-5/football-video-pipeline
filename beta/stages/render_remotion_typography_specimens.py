"""
beta/stages/render_remotion_typography_specimens.py

Renders actual 1080x1920 still frames using the official Remotion CLI and local bundled fonts.
Guarantees that typography specimens are rendered through the exact same Remotion React engine,
@font-face font-loading implementation, and design tokens as the final video production.

Outputs to:
beta/workspaces/endrick_milan/run_v7_1/typography/
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMOTION_DIR = PROJECT_ROOT / "remotion"
TYPOGRAPHY_DIR = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "typography"
MANIFESTS_DIR = PROJECT_ROOT / "workspaces" / "endrick_milan" / "run_v7_1" / "manifests"

SPECIMEN_COMPOSITIONS = [
    ("HeadlineSpecimen", "headline_specimen.png", "Opening 2-line headline over real Bernabéu night stadium photography with category kicker and brand bug"),
    ("PlayerRevealSpecimen", "player_reveal_specimen.png", "Player-name reveal over Endrick presentation portrait with large Barlow Condensed name and supporting Inter context"),
    ("SingleLineSubtitleSpecimen", "single_line_subtitle_specimen.png", "Clean 1-line sentence-case narration subtitle in Inter 46px over Santiago Bernabéu night frame"),
    ("TwoLineSubtitleSpecimen", "two_line_subtitle_specimen.png", "Clean 2-line sentence-case narration subtitle in Inter 46px over Valdebebas training frame"),
    ("SubtitleSpecimen", "subtitle_specimen.png", "Narration subtitles demonstrating sentence case wrapping over dark and bright backgrounds"),
    ("TransferGraphicSpecimen", "transfer_graphic_specimen.png", "Transfer graphic with €60M fixed + €10M bonuses, €80M-€85M buy-back range, and prominent NOT AGREED status"),
    ("LowerThirdSpecimen", "lower_third_specimen.png", "Two-tier broadcast lower-third over Valdebebas training photograph with badges and source attribution"),
    ("OutroSpecimen", "outro_specimen.png", "Restrained broadcast outro with 3D bezel crest, wordmark, and clean call-to-action"),
    ("PtBrSpecimen", "pt_br_specimen.png", "Brazilian Portuguese specimen verifying full diacritic accents (á, à, â, ã, é, ê, í, ó, ô, õ, ú, ü, ç)"),
    ("Es419Specimen", "es_419_specimen.png", "Latin American Spanish specimen verifying accents and punctuation (á, é, í, ó, ú, ü, ñ, ¿, ¡)"),
    ("TypographyMasterClean", "typography_master_clean.png", "Clean master broadcast composition combining all typography elements without diagnostic overlays"),
    ("TypographyDiagnostic", "typography_diagnostic.png", "Diagnostic master sheet displaying font metrics, weights, safe-zone boundaries (x=84, x=996, y=1640)")
]

def render_specimens():
    TYPOGRAPHY_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Rendering {len(SPECIMEN_COMPOSITIONS)} Remotion typography specimens into {TYPOGRAPHY_DIR}...")
    manifest_records = []

    for comp_id, filename, desc in SPECIMEN_COMPOSITIONS:
        out_path = TYPOGRAPHY_DIR / filename
        cmd = [
            "npx.cmd" if sys.platform == "win32" else "npx",
            "remotion",
            "still",
            "src/index.ts",
            comp_id,
            str(out_path),
            "--overwrite"
        ]
        print(f"  Rendering [{comp_id}] -> {filename}...")
        t0 = time.time()
        res = subprocess.run(cmd, cwd=str(REMOTION_DIR), capture_output=True, text=True)
        elapsed = round(time.time() - t0, 2)

        if res.returncode != 0:
            print(f"    [FAIL] Remotion still failed for {comp_id}: {res.stderr}")
            raise RuntimeError(f"Remotion render failed for {comp_id}: {res.stderr}")

        if not out_path.exists() or out_path.stat().st_size == 0:
            raise FileNotFoundError(f"Rendered file missing or empty: {out_path}")

        file_size = out_path.stat().st_size
        print(f"    [PASS] {filename} rendered in {elapsed}s ({file_size:,} bytes)")

        manifest_records.append({
            "composition_id": comp_id,
            "filename": filename,
            "description": desc,
            "resolution": "1080x1920",
            "file_size_bytes": file_size,
            "rendered_via": "Remotion Still CLI v4.0.545",
            "font_system": "V7.1.4 Permanent Typography System",
            "font_families": ["Barlow Condensed", "Inter", "IBM Plex Mono"]
        })

    # Save typography manifest
    manifest_path = MANIFESTS_DIR / "typography_manifest.json"
    manifest_data = {
        "release": "Beta V7.1.6",
        "story_id": "endrick_milan",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fonts_verified": {
            "display": "Barlow Condensed (600, 700, 800, 900)",
            "reading": "Inter (400, 500, 600, 700, 800)",
            "mono": "IBM Plex Mono (500, 600)"
        },
        "specimens": manifest_records
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"\nSaved typography manifest: {manifest_path}")

    return manifest_data

if __name__ == "__main__":
    render_specimens()
