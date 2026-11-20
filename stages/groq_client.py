"""
Stage: Groq Ultra-Fast Inference & Semantic Claim Verification
Powers the Qwen Telegram persona, high-velocity script generation, and 120B reasoning claim verification.
Supports dual-key redundancy and automatic model failover between Qwen-27B and GPT-OSS-120B.
"""

import os
import json
import urllib.request
import urllib.error
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

HEADERS_BASE = {
    "Content-Type": "application/json",
    "User-Agent": "FootballIn30Sec/2.0 (Studio Automated Pipeline)"
}

def get_groq_keys() -> List[str]:
    """Retrieve primary and backup Groq keys strictly from environment or .env file."""
    keys = []
    k1 = os.environ.get("GROQ_API_KEY", "").strip()
    k2 = os.environ.get("GROQ_API_KEY_BACKUP", "").strip()

    if not k1 or not k2:
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not k1:
                            k1 = val
                    elif line.startswith("GROQ_API_KEY_BACKUP="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not k2:
                            k2 = val

    if k1:
        keys.append(k1)
    if k2 and k2 != k1:
        keys.append(k2)
    if not keys:
        raise RuntimeError(
            "GROQ_API_KEY is not configured in environment or .env file. "
            "Please add your Groq API key to .env before running."
        )
    return keys

def call_groq_chat(
    messages: Optional[List[Dict[str, str]]] = None,
    preferred_model: str = "openai/gpt-oss-120b",
    fallback_model: str = "qwen/qwen3.8-27b",
    max_tokens: int = 3500,
    temperature: float = 0.4,
    timeout: int = 25,
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Execute chat completion on Groq with multi-key redundancy and automatic model failover.
    Attempts preferred_model on primary key -> backup key, then fallback_model on primary -> backup.
    Supports both messages list format and system_prompt/user_prompt/model keyword arguments.
    """
    if model:
        preferred_model = model

    if messages is None:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

    keys = get_groq_keys()
    models_to_try = [preferred_model]
    if fallback_model and fallback_model not in models_to_try:
        models_to_try.append(fallback_model)
    for m in ("openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"):
        if m not in models_to_try:
            models_to_try.append(m)

    for current_model in models_to_try:
        for key in keys:
            try:
                headers = dict(HEADERS_BASE)
                headers["Authorization"] = f"Bearer {key}"

                payload = {
                    "model": current_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }

                req = urllib.request.Request(
                    GROQ_ENDPOINT,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers
                )

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    choice = data.get("choices", [{}])[0]
                    message = choice.get("message", {})
                    content = message.get("content", "").strip()

                    # Strip any lingering reasoning or think tags if present
                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

                    if content:
                        return content

            except urllib.error.HTTPError as he:
                error_body = he.read().decode("utf-8", errors="ignore")
                print(f"[GroqClient] Model '{current_model}' with key ...{key[-6:]} returned HTTP {he.code}: {error_body[:100]}")
            except Exception as e:
                print(f"[GroqClient] Model '{current_model}' with key ...{key[-6:]} failed: {e}")

    return None

def verify_script_with_120b(
    script_text: str,
    source_text: str,
    source_name: str,
    reliability_tier: str
) -> Dict[str, Any]:
    """
    Use Groq's openai/gpt-oss-120b reasoning architecture to perform a rigorous semantic audit
    of the generated script against the raw source article text.
    """
    system_instruction = (
        "You are the Chief Fact Checker and Claims Auditor for 'Football in 30 Seconds'. "
        "Your task is to ruthlessly verify whether every statement in the script is strictly grounded in the source text. "
        "Rules:\n"
        "1. No invented transfer fees, player salaries, or contract lengths.\n"
        "2. No invented quotes or fabricated manager statements.\n"
        "3. No off-pitch private life claims (wives, dating, nightclubs, court cases).\n"
        "4. Tone, satirical banter, and creative football jokes (e.g. Carlo Ancelotti benching wonderkids, coaching Milan in the past, Florentino Perez buy-backs, balance sheet chaos) are FULLY ALLOWED and must NEVER be flagged as unsupported claims as long as the core news transfer event is grounded in the article.\n"
        "5. Concluding audience engagement questions ('Tell us in the comments: yes or no') are standard format and fully valid.\n"
        "Respond ONLY with a JSON object matching this schema:\n"
        "{\n"
        "  \"is_valid\": true/false,\n"
        "  \"confidence_score\": 0.0 to 1.0,\n"
        "  \"unsupported_claims\": [\"list\", \"of\", \"issues\"],\n"
        "  \"audit_summary\": \"1-sentence summary of verification verdict\"\n"
        "}"
    )

    user_prompt = (
        f"SOURCE ARTICLE ({source_name} - {reliability_tier}):\n"
        f"{source_text[:3000]}\n\n"
        f"GENERATED SCRIPT TO AUDIT:\n"
        f"{script_text}\n\n"
        "Conduct the audit and respond strictly in valid JSON."
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]

    response = call_groq_chat(
        messages=messages,
        preferred_model="openai/gpt-oss-120b",
        fallback_model="qwen/qwen3.8-27b",
        max_tokens=500,
        temperature=0.2,
        timeout=15
    )

    if response:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                audit_result = json.loads(match.group(0))
                return audit_result
        except Exception as pe:
            print(f"[GroqClient] Audit JSON parse error: {pe} | Response: {response[:150]}")

    # Fail-safe: Never fabricate a pass when semantic verification is unreachable or unparseable
    return {
        "is_valid": False,
        "status": "UNVERIFIED",
        "confidence_score": 0.0,
        "unsupported_claims": [
            "Semantic claim verification service unavailable or returned unparseable output."
        ],
        "audit_summary": "UNVERIFIED: Semantic AI verification could not be confirmed. Manual review required."
    }
