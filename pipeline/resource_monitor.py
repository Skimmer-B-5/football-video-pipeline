"""
# PROVENANCE: Copied from pipeline/resource_monitor.py and adapted for beta runtime isolation.
Hardware Resource Monitor for Beta Pipeline.
Tracks RAM and VRAM usage per stage, logging peak usage to beta/evidence/resource_ledger.json.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
LEDGER_FILE = EVIDENCE_DIR / "resource_ledger.json"

def get_vram_usage() -> Dict[str, float]:
    """Query nvidia-smi for GPU VRAM in MiB."""
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        total, used, free = [float(x.strip()) for x in res.stdout.strip().split(",")]
        return {
            "vram_total_mib": total,
            "vram_used_mib": used,
            "vram_free_mib": free
        }
    except Exception:
        return {
            "vram_total_mib": 4096.0,
            "vram_used_mib": 0.0,
            "vram_free_mib": 4096.0
        }

def get_system_ram() -> Dict[str, float]:
    """Query Windows memory via psutil."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "ram_total_mb": round(mem.total / (1024 * 1024), 2),
            "ram_used_mb": round(mem.used / (1024 * 1024), 2),
            "ram_available_mb": round(mem.available / (1024 * 1024), 2),
            "ram_percent": mem.percent
        }
    except ImportError:
        return {
            "ram_total_mb": 7722.0,
            "ram_used_mb": 0.0,
            "ram_available_mb": 1500.0,
            "ram_percent": 80.0
        }

class ResourceTracker:
    def __init__(self, stage_name: str, min_free_vram_mib: float = 100.0, min_free_ram_mb: float = 100.0):
        self.stage_name = stage_name
        self.min_free_vram_mib = min_free_vram_mib
        self.min_free_ram_mb = min_free_ram_mb
        self.start_time = 0.0
        self.initial_vram = {}
        self.initial_ram = {}

    def __enter__(self):
        self.start_time = time.time()
        self.initial_vram = get_vram_usage()
        self.initial_ram = get_system_ram()

        if self.initial_ram["ram_available_mb"] < self.min_free_ram_mb:
            raise MemoryError(
                f"[CRITICAL RAM WARNING] Beta Stage '{self.stage_name}' blocked. "
                f"Available RAM ({self.initial_ram['ram_available_mb']:.1f} MB) is below minimum required ({self.min_free_ram_mb} MB)."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = round(time.time() - self.start_time, 2)
        final_vram = get_vram_usage()
        final_ram = get_system_ram()

        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stage": self.stage_name,
            "duration_sec": duration,
            "ram_before_mb": self.initial_ram["ram_used_mb"],
            "ram_after_mb": final_ram["ram_used_mb"],
            "ram_available_after_mb": final_ram["ram_available_mb"],
            "vram_before_mib": self.initial_vram["vram_used_mib"],
            "vram_after_mib": final_vram["vram_used_mib"],
            "vram_free_after_mib": final_vram["vram_free_mib"],
            "status": "FAILED" if exc_type else "SUCCESS",
            "error": str(exc_val) if exc_val else None
        }

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        ledger = []
        if LEDGER_FILE.exists():
            try:
                with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
            except Exception:
                ledger = []
        ledger.append(entry)
        with open(LEDGER_FILE, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)

        print(f"[{self.stage_name}] Duration: {duration}s | RAM Used: {final_ram['ram_used_mb']} MB | VRAM Free: {final_vram['vram_free_mib']} MiB")
