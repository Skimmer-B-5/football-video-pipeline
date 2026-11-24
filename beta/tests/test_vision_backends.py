import os
import urllib.request
import urllib.error
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_file = PROJECT_ROOT / ".env"
env = {}
for line in env_file.read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

# 1. Test Gemini
gem_key = env.get("GEMINI_API_KEY")
if gem_key:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gem_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"contents": [{"parts": [{"text": "Hello"}]}]}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            print("Gemini 1.5 Flash: SUCCESS")
    except urllib.error.HTTPError as e:
        print("Gemini Error:", e.code, e.read().decode()[:200])
    except Exception as e:
        print("Gemini Exception:", e)

# 2. Test Cloudflare Workers AI
cf_id = env.get("CLOUDFLARE_ACCOUNT_ID") or env.get("CF_ACCOUNT_ID")
cf_token = env.get("CLOUDFLARE_API_TOKEN") or env.get("CF_API_TOKEN")
if cf_id and cf_token:
    cf_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_id}/ai/run/@cf/meta/llama-3.2-11b-vision-instruct"
    cf_req = urllib.request.Request(
        cf_url,
        data=json.dumps({"prompt": "Hello"}).encode("utf-8"),
        headers={"Authorization": f"Bearer {cf_token}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(cf_req, timeout=8) as r:
            print("Cloudflare Vision: SUCCESS")
    except urllib.error.HTTPError as e:
        print("Cloudflare Error:", e.code, e.read().decode()[:200])
    except Exception as e:
        print("Cloudflare Exception:", e)
