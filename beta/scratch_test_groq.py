import sys
import json
import re
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/sb000/.gemini/antigravity/scratch/football-video-pipeline")
sys.path.insert(0, str(PROJECT_ROOT / "beta"))
sys.path.insert(1, str(PROJECT_ROOT))

from stages.groq_client import call_groq_chat
from pipeline.neural_instructions import SCREENPLAY_SYSTEM_PROMPT, CONFIGURED_LLM_MODEL, CONFIGURED_LLM_FALLBACK

d_prompt = """STORY HEADLINE: MAN UTD TRANSFER NEWS: FULHAM DEFENDER CALVIN BASSEY IS IN TALKS OVER NEW CONTRACT AMID MAN UTD LINKS
PROTAGONIST: Calvin Bassey
CURRENT CLUB: Fulham
PURSUING CLUB / SUITOR: Manchester United
MANAGER: Marco Silva
REPORTED FEE: £30M
COMPLICATION: Silva determined to block any Old Trafford approach
"""

raw = call_groq_chat(
    system_prompt=SCREENPLAY_SYSTEM_PROMPT,
    user_prompt=d_prompt,
    preferred_model=CONFIGURED_LLM_MODEL,
    fallback_model=CONFIGURED_LLM_FALLBACK,
    temperature=0.3
)
print("RAW:")
print(raw)
