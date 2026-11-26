"""
run_pipeline_service.py
30 Football Plus - Primary Broadcast Engine Entrypoint.
Delegates directly to run_telegram_broadcast_service.py.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SERVICE_SCRIPT = PROJECT_ROOT / "run_telegram_broadcast_service.py"

def main():
    if not SERVICE_SCRIPT.exists():
        print(f"[Service Error] Main broadcast service not found at {SERVICE_SCRIPT}")
        sys.exit(1)
    cmd = [sys.executable, "-u", str(SERVICE_SCRIPT)] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
