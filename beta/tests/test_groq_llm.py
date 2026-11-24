import sys
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from stages.groq_client import call_groq_chat

try:
    res = call_groq_chat(
        system_prompt="You are a 1990s Sky Sports football news desk editor.",
        user_prompt="Draft a punchy 20-word breaking news hook about Manchester United targeting Calvin Bassey from Fulham."
    )
    print("SUCCESS Groq LLM Response:")
    print(res)
except Exception as e:
    print(f"FAILED Groq LLM: {e}")
