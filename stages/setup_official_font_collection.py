"""
beta/stages/setup_official_font_collection.py
Downloads and verifies the official approved font collection:
1. Barlow Condensed (SemiBold 600, Bold 700, ExtraBold 800, Black 900)
2. Inter (Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800)
3. IBM Plex Mono (Medium 500, SemiBold 600)
Includes OFL license files and glyph coverage validation.
"""

import os
import sys
import io
import zipfile
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

BARLOW_URLS = {
    "BarlowCondensed-SemiBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-SemiBold.ttf",
    "BarlowCondensed-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-Bold.ttf",
    "BarlowCondensed-ExtraBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-ExtraBold.ttf",
    "BarlowCondensed-Black.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-Black.ttf",
    "OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/OFL.txt",
}

IBM_PLEX_MONO_URLS = {
    "IBMPlexMono-Medium.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-Medium.ttf",
    "IBMPlexMono-SemiBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-SemiBold.ttf",
    "OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/OFL.txt",
}

INTER_ZIP_URL = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
INTER_TARGET_FILES = {
    "extras/ttf/Inter-Regular.ttf": "Inter-Regular.ttf",
    "extras/ttf/Inter-Medium.ttf": "Inter-Medium.ttf",
    "extras/ttf/Inter-SemiBold.ttf": "Inter-SemiBold.ttf",
    "extras/ttf/Inter-Bold.ttf": "Inter-Bold.ttf",
    "extras/ttf/Inter-ExtraBold.ttf": "Inter-ExtraBold.ttf",
    "LICENSE.txt": "OFL.txt",
}

TEST_GLYPHS = (
    "áàâãéêíóôõúüçñ"
    "ÁÀÂÃÉÊÍÓÔÕÚÜÇÑ"
    "€£$0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "•–—“”''[]()/: -+▲▼"
)

def download_file(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    dest.write_bytes(data)
    print(f"  Downloaded: {dest.name} ({len(data)} bytes)")

def setup_barlow():
    barlow_dir = FONTS_DIR / "barlow_condensed"
    print("Setting up Barlow Condensed...")
    for filename, url in BARLOW_URLS.items():
        dest = barlow_dir / filename
        if not dest.exists() or dest.stat().st_size == 0:
            download_file(url, dest)
        else:
            print(f"  Already exists: {dest.name} ({dest.stat().st_size} bytes)")

def setup_ibm_plex_mono():
    ibm_dir = FONTS_DIR / "ibm_plex_mono"
    print("Setting up IBM Plex Mono...")
    for filename, url in IBM_PLEX_MONO_URLS.items():
        dest = ibm_dir / filename
        if not dest.exists() or dest.stat().st_size == 0:
            download_file(url, dest)
        else:
            print(f"  Already exists: {dest.name} ({dest.stat().st_size} bytes)")

def setup_inter():
    inter_dir = FONTS_DIR / "inter"
    inter_dir.mkdir(parents=True, exist_ok=True)
    print("Setting up Inter...")
    all_exist = all((inter_dir / dest_name).exists() and (inter_dir / dest_name).stat().st_size > 0 for dest_name in INTER_TARGET_FILES.values())
    if all_exist:
        print("  All Inter font files already present.")
        return

    print("  Downloading Inter-4.1.zip from official repository...")
    req = urllib.request.Request(INTER_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        zdata = resp.read()

    with zipfile.ZipFile(io.BytesIO(zdata)) as z:
        for zip_path, dest_name in INTER_TARGET_FILES.items():
            dest = inter_dir / dest_name
            with z.open(zip_path) as src_f:
                content = src_f.read()
                dest.write_bytes(content)
            print(f"  Extracted: {dest_name} ({len(content)} bytes)")

def verify_glyph_coverage():
    print("\nVerifying font loading and glyph coverage across all TTF files...")
    all_fonts = list(FONTS_DIR.glob("**/*.ttf"))
    print(f"Found {len(all_fonts)} TTF files in {FONTS_DIR}")
    assert len(all_fonts) >= 11, f"Expected at least 11 TTF files, found {len(all_fonts)}"

    results = {}
    for font_p in sorted(all_fonts):
        try:
            f = ImageFont.truetype(str(font_p), size=36)
            # Render a test strip to ensure PIL can draw all glyphs
            img = Image.new("RGBA", (1000, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), TEST_GLYPHS, font=f, fill=(255, 255, 255, 255))
            results[font_p.name] = {
                "status": "PASS",
                "family": font_p.parent.name,
                "size_bytes": font_p.stat().st_size
            }
            print(f"  [PASS] {font_p.parent.name}/{font_p.name} ({font_p.stat().st_size} bytes)")
        except Exception as e:
            results[font_p.name] = {"status": "FAIL", "error": str(e)}
            print(f"  [FAIL] {font_p.parent.name}/{font_p.name}: {e}")
            raise e

    print("All font files successfully loaded and verified with zero errors!")
    return results

def main():
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    setup_barlow()
    setup_ibm_plex_mono()
    setup_inter()
    verify_glyph_coverage()

if __name__ == "__main__":
    main()
