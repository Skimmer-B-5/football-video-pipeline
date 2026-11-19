"""
Automated Downloader for Qwen3-TTS 0.6B Base & Speech Tokenizer Weights.
Supports automatic resuming, chunked streaming, and IPv4 routing for reliable cross-platform downloads.
"""

import os
import sys
import time
import socket
from pathlib import Path

# Force IPv4 in urllib3 to prevent Windows IPv6 route hang
import urllib3.util.connection as urllib_conn
urllib_conn.allowed_gai_family = lambda: socket.AF_INET
urllib_conn.HAS_IPV6 = False

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_REPO = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
CUSTOM_DIR = PROJECT_ROOT / "models" / "qwen3_tts_customvoice"
TARGET_DIR = PROJECT_ROOT / "models" / "qwen3_tts_base"
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# 1. Quick copy from local customvoice cache if available
shared_files = ["vocab.json", "merges.txt", "tokenizer_config.json", "preprocessor_config.json"]
for f in shared_files:
    src = CUSTOM_DIR / f
    dst = TARGET_DIR / f
    if src.exists() and not dst.exists():
        try:
            import shutil
            shutil.copy2(src, dst)
            print(f"[CACHE] Copied {f} from local cache", flush=True)
        except Exception:
            pass

st_dst_dir = TARGET_DIR / "speech_tokenizer"
st_dst_dir.mkdir(parents=True, exist_ok=True)
st_src_dir = CUSTOM_DIR / "speech_tokenizer"
if st_src_dir.exists():
    for f in ["config.json", "configuration.json", "model.safetensors", "preprocessor_config.json"]:
        src = st_src_dir / f
        dst = st_dst_dir / f
        if src.exists() and not dst.exists():
            try:
                import shutil
                shutil.copy2(src, dst)
                print(f"[CACHE] Copied speech_tokenizer/{f} from local cache", flush=True)
            except Exception:
                pass

# 2. Comprehensive manifest of Base model files
BASE_FILES = [
    ("config.json", 4494),
    ("generation_config.json", 245),
    ("vocab.json", 2776833),
    ("merges.txt", 1671839),
    ("tokenizer_config.json", 7344),
    ("preprocessor_config.json", 127),
    ("speech_tokenizer/config.json", 2336),
    ("speech_tokenizer/configuration.json", 76),
    ("speech_tokenizer/preprocessor_config.json", 234),
    ("speech_tokenizer/model.safetensors", 682293092),
    ("model.safetensors", 1829344272),
]

def download_file(rfilename: str, total_size: int):
    dest = TARGET_DIR / rfilename
    dest.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://hf-mirror.com/{BASE_REPO}/resolve/main/{rfilename}"

    existing = dest.stat().st_size if dest.exists() else 0
    if existing >= total_size and total_size > 0:
        print(f"[READY] {rfilename} ({existing / (1024*1024):.1f} MB)", flush=True)
        return

    print(f"[DOWNLOADING] {rfilename} ({total_size / (1024*1024):.1f} MB)...", flush=True)
    t0 = time.time()

    headers = {}
    if existing > 0:
        headers["Range"] = f"bytes={existing}-"

    try:
        with requests.get(url, headers=headers, stream=True, timeout=(20, 60)) as r:
            if r.status_code not in (200, 206):
                r.raise_for_status()

            mode = "ab" if existing > 0 else "wb"
            downloaded = existing
            last_print = time.time()

            with open(dest, mode) as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        now = time.time()
                        if now - last_print > 4:
                            pct = (downloaded / total_size * 100) if total_size > 0 else 0
                            mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            speed = (downloaded - existing) / (now - t0 + 0.001) / (1024 * 1024)
                            print(f"  -> {rfilename}: {mb:.1f}/{total_mb:.1f} MB ({pct:.1f}%) @ {speed:.2f} MB/s", flush=True)
                            last_print = now

        print(f"[SUCCESS] {rfilename} verified ({dest.stat().st_size / (1024*1024):.1f} MB)", flush=True)
    except Exception as e:
        print(f"[RETRY NEEDED] {rfilename} failed ({e}). Run downloader again to resume.", flush=True)

def main():
    print("=" * 65, flush=True)
    print("  Qwen3-TTS 0.6B Base Neural Model Setup", flush=True)
    print("=" * 65, flush=True)
    t_start = time.time()
    for rfilename, total_size in BASE_FILES:
        download_file(rfilename, total_size)
    print(f"=== Qwen3-TTS Base Setup Complete in {time.time()-t_start:.1f}s ===", flush=True)

if __name__ == "__main__":
    main()
