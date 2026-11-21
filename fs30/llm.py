"""
LLM Client for FS 30 Pipeline.
Handles calls to GPT-OSS 120B with network timeout, exponential backoff retries,
and robust JSON extraction.
"""

import time
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from fs30.config import PROJECT_ROOT, load_config
from stages.groq_client import call_groq_chat

def clean_json_text(text: str) -> str:
    """Extracts raw JSON object substring from model response."""
    text = text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Search for first { to last }
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return text

def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    preferred_model: str = "openai/gpt-oss-120b",
    timeout: int = 45,
    network_retries: int = 2,
    log_func=print
) -> Dict[str, Any]:
    """
    Calls LLM with network error retries and exponential backoff.
    Returns parsed JSON dictionary.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    last_error = None
    for attempt in range(network_retries + 1):
        try:
            log_func(f"[LLM] Calling {preferred_model} (attempt {attempt + 1}/{network_retries + 1})...")
            raw_response = call_groq_chat(
                messages=messages,
                preferred_model=preferred_model,
                fallback_model="qwen/qwen3.8-27b",
                timeout=timeout,
                temperature=0.2
            )
            if not raw_response:
                raise RuntimeError("LLM returned empty response.")
            
            cleaned = clean_json_text(raw_response)
            parsed = json.loads(cleaned)
            return parsed
        except Exception as e:
            last_error = e
            log_func(f"[LLM] Network/Parse Error on attempt {attempt + 1}: {e}")
            if attempt < network_retries:
                time.sleep(2.0 * (attempt + 1))

    raise RuntimeError(f"LLM call failed after {network_retries + 1} attempts: {last_error}")
