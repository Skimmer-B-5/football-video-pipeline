import sys
import json
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from stages.groq_client import call_groq_chat

SYSTEM_PROMPT = """You are a veteran 1990s television football-news desk executive editor (Sky Sports Saturday style).
Your task is to write a punchy, dramatic 5-beat television dual-script for a 30-second broadcast short.

MANDATORY RULES:
1. S01 (The Hook): MUST conceal the protagonist's identity for the first sentence. Sets up the high-stakes club drama.
2. S02 (The Reveal): Explicitly names the protagonist using em-dash attack ("And — ").
3. S03 (The Figures): Concrete fees, clauses, contract terms, or negotiation status with em-dash ("Now — ").
4. S04 (The Complication): Medical status, squad friction, or contractual sticking point ("Meanwhile — ").
5. S05 (The Verdict): Provocative editorial closing debate question ("So — ").
6. outro: "Either way — this is football in thirty seconds. Follow for daily transfer updates."
7. ZERO WHOOSHES, ZERO SFX, NATURAL SPOKEN CADENCE.

Output ONLY valid JSON with this exact schema:
{
  "scenes": [
    {
      "scene_id": "S01",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● TRANSFER REPORT", "headline": "...", "subheadline": "...", "status_badge": "DEVELOPING"}
    },
    {
      "scene_id": "S02",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● PROPOSED PACKAGE", "headline": "...", "subheadline": "...", "status_badge": "REVEALED"}
    },
    {
      "scene_id": "S03",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● DEAL CLAUSE", "headline": "...", "subheadline": "...", "status_badge": "UNAGREED"}
    },
    {
      "scene_id": "S04",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● SITUATION UPDATE", "headline": "...", "subheadline": "...", "status_badge": "OFFICIAL"}
    },
    {
      "scene_id": "S05",
      "spoken_narration": "...",
      "on_screen": {"kicker": "● THE VERDICT", "headline": "...", "subheadline": "...", "status_badge": "EDITORIAL"}
    },
    {
      "scene_id": "outro",
      "spoken_narration": "Either way — this is football in thirty seconds. Follow for daily transfer updates.",
      "on_screen": {"headline": "THIS IS FOOTBALL IN 30 SECONDS", "kicker": "FOLLOW FOR MORE"}
    }
  ]
}
"""

def generate_or_rewrite_screenplay(
    headline: str,
    article_text: str,
    protagonist: str,
    current_club: str,
    pursuing_club: str,
    prior_script: str = "",
    user_critique: str = ""
) -> dict:
    user_prompt = f"""STORY HEADLINE: {headline}
REPORTED FACTS: {article_text[:600]}
PROTAGONIST: {protagonist}
CURRENT CLUB: {current_club}
PURSUING CLUB / SUITOR: {pursuing_club}
"""
    if prior_script:
        user_prompt += f"\nCURRENT SCRIPT DRAFT:\n{prior_script}\n"
    if user_critique:
        user_prompt += f"\nCRITICAL USER EDITORIAL INSTRUCTION & FEEDBACK:\n\"{user_critique}\"\n"
        user_prompt += "Revise and rebuild the 5-beat dual-script completely to address the user's critique above, incorporating their exact feedback seamlessly into the television bulletin."

    raw = call_groq_chat(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3
    )
    
    # Extract JSON
    import re
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    return json.loads(raw)

# Test with the user's exact complaint!
test_headline = "Man Utd transfer news: Fulham defender Calvin Bassey is in talks over new contract amid Man Utd links - Paper Talk"
test_article = "Fulham defender Calvin Bassey is in talks over a new deal at Craven Cottage amid interest from Manchester United. The Nigerian international has impressed this season."
user_feedback = "Top suitors ? Just say Man united is going for a new sensation defender for their backline"

print("Calling Groq LLM to rewrite script taking user critique...")
result = generate_or_rewrite_screenplay(
    headline=test_headline,
    article_text=test_article,
    protagonist="Calvin Bassey",
    current_club="Fulham",
    pursuing_club="Manchester United",
    prior_script="Top Suitors have made their move, but The Manager wants him to stay...",
    user_critique=user_feedback
)

print("\n--- REWRITTEN DUAL-SCRIPT ---")
for s in result.get("scenes", []):
    print(f"[{s['scene_id']}] {s['spoken_narration']}")
    on_sc = s.get("on_screen", {})
    print(f"       On Screen: {on_sc.get('headline', '')} | {on_sc.get('subheadline', '')}")
