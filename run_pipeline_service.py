"""
run_pipeline_service.py
30 Football Plus - Primary V2 Autonomous Broadcast Engine Entrypoint.
Delegates directly to beta/run_telegram_broadcast_service.py.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BETA_SERVICE = PROJECT_ROOT / "beta" / "run_telegram_broadcast_service.py"

def main():
    if not BETA_SERVICE.exists():
        print(f"[Service Error] Beta broadcast service not found at {BETA_SERVICE}")
        sys.exit(1)
    cmd = [sys.executable, "-u", str(BETA_SERVICE)] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
