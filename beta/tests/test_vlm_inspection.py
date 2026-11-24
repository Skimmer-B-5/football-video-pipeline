import re
import json
import base64
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_gemini_key():
    env_file = PROJECT_ROOT.parent / ".env" if (PROJECT_ROOT.parent / ".env").exists() else PROJECT_ROOT / ".env"
    text = env_file.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def test_gemini_vision():
    key = get_gemini_key()
    if not key:
        print("GEMINI_API_KEY not found.")
        return

    # Use test image from story_tg_1795519137
    img_path = PROJECT_ROOT / "remotion" / "public" / "images" / "story_tg_1795519137" / "S02_shot1_scene_4.png"
    if not img_path.exists():
        print(f"Test image not found: {img_path}")
        return

    img_b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": """You are an elite television broadcast editorial photo inspector for Sky Sports.
Analyze this candidate 9:16 vertical broadcast frame.

REQUIRED SUBJECT: Calvin Bassey (Fulham defender)
SCENE BEAT: S02 Reveal

Evaluate strictly:
1. Is the primary person in the photo Calvin Bassey?
2. Does the image depict the correct club kit/colors or is there a misleading visual mismatch (e.g. random Man United player)?
3. Is the framing/crop professional (head not cut off, face positioned safely in the upper/middle area, no weird partial bodies sliced on the edges)?
4. Is the image sharp, high-res, and broadcast worthy?

Return ONLY valid JSON matching this schema:
{
  "subject_identified": "Name of person/club identified in photo",
  "is_correct_subject": true/false,
  "has_misleading_mismatch": true/false,
  "crop_quality_score": 1-10,
  "safe_zone_compliant": true/false,
  "clarity_score": 1-10,
  "approved": true/false,
  "editorial_critique": "Brief explanation"
}
"""
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": img_b64
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            content = res_data["candidates"][0]["content"]["parts"][0]["text"]
            print("Gemini Vision Verdict:")
            print(content)
    except Exception as e:
        print(f"Gemini Vision call failed: {e}")

if __name__ == "__main__":
    test_gemini_vision()
