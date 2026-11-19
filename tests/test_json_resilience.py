"""
Automated Unit Tests: LLM Output & JSON Parser Resilience.
Tests:
1. Markdown code fence wrapping (```json ... ```) with conversational preamble and postamble.
2. Embedded JSON surrounded by arbitrary text and reasoning tags.
3. Proper exception signaling and retry triggering for irreparable / truncated JSON.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.script_generator import extract_json_from_llm

def test_json_resilience():
    print("[TestJSONResilience] 1. Testing markdown wrapped JSON with conversational chatter...")
    raw_case_1 = """Sure! Here is the script you requested for the video:
```json
{
  "headline": "Arsenal sign Riccardo Calafiori",
  "scenes": [
    {"scene_id": 1, "text": "Arsenal make a defensive statement.", "type": "hook"},
    {"scene_id": 2, "text": "According to Sky Sports, terms are agreed.", "type": "body"}
  ]
}
```
Let me know if you want any modifications!"""

    res_1 = extract_json_from_llm(raw_case_1)
    assert res_1["headline"] == "Arsenal sign Riccardo Calafiori", "Failed case 1 extraction"
    print("  ✅ Case 1 passed: Successfully parsed markdown wrapped JSON.")

    print("[TestJSONResilience] 2. Testing embedded JSON with raw text before and after...")
    raw_case_2 = """Here is the response: {"headline": "Real Madrid announce Mbappe", "source_name": "BBC Sport", "reliability_tier": "confirmed", "scenes": []} Thank you!"""
    res_2 = extract_json_from_llm(raw_case_2)
    assert res_2["headline"] == "Real Madrid announce Mbappe", "Failed case 2 extraction"
    print("  ✅ Case 2 passed: Successfully parsed embedded JSON with raw surrounding text.")

    print("[TestJSONResilience] 3. Testing truncated / unparseable JSON error triggering...")
    malformed_json = """{"headline": "Manchester City agree deal", "scenes": ["""
    try:
        extract_json_from_llm(malformed_json)
        assert False, "Should have thrown ValueError for irreparable truncated JSON"
    except ValueError as ve:
        print(f"  ✅ Case 3 passed: Correctly triggered ValueError for retry ({str(ve)[:40]}...)")

    print("\n[TestJSONResilience] ALL JSON RESILIENCE TESTS PASSED SUCCESSFULLY! ✅")

if __name__ == "__main__":
    test_json_resilience()
