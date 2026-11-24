import sys
import json
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from stages.groq_client import call_groq_chat

def extract_entities_llm(headline: str, raw_text: str = "") -> dict:
    prompt = f"""Extract the football entities from this breaking news story.
HEADLINE: {headline}
TEXT: {raw_text[:500]}

Return ONLY JSON with these exact keys:
{{
  "protagonist_name": "Full name of the player or manager at the center of the story",
  "current_club": "The club the player currently belongs to (e.g. Fulham)",
  "current_manager": "Manager of current club (or prominent manager mentioned)",
  "pursuing_club": "The club trying to sign/bid for him (e.g. Manchester United)",
  "reported_base_fee": "Reported fee or clause if mentioned, else 'undisclosed'",
  "reported_bonuses": "Add-ons or bonuses if mentioned, else 'performance incentives'",
  "complication": "Key complication, injury, contract standoff, or rival interest"
}}
"""
    raw = call_groq_chat(
        system_prompt="You are a football transfer desk data extractor. Output ONLY valid JSON.",
        user_prompt=prompt,
        temperature=0.1
    )
    import re
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    return json.loads(raw)

samples = [
    ("Man Utd transfer news: Fulham defender Calvin Bassey is in talks over new contract amid Man Utd links - Paper Talk", "Fulham defender Calvin Bassey..."),
    ("Transfer Centre LIVE! 'Real Madrid close to agreeing new contract with Bellingham'", "Real Madrid are close to agreeing..."),
    ("Bayern Munich feels ‘gentlemen’s agreement’ on contract has been violated by Jamal Musiala’s camp", "Bayern Munich hierarchy..."),
    ("Milan prepare €60m bid for Endrick", "Real Madrid striker Endrick...")
]

for h, t in samples:
    print(f"\n--- EXTRACTING: {h[:60]}... ---")
    data = extract_entities_llm(h, t)
    print(f"Protagonist: {data.get('protagonist_name')}")
    print(f"Current Club: {data.get('current_club')}")
    print(f"Pursuing Club: {data.get('pursuing_club')}")
    print(f"Manager: {data.get('current_manager')}")
    print(f"Fee: {data.get('reported_base_fee')}")
