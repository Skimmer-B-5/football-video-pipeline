"""
beta/consult_ai_architects.py
Queries OpenAI GPT-OSS-120B and Qwen3.8-27B for comprehensive architectural audits
and upgrade proposals across all 7 pipeline stages.
"""

import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.stages.groq_client import call_groq_chat

AUDIT_PROMPT = """You are a Principal AI Video Systems Architect and Senior Television Broadcast Engineer. 
Conduct a rigorous, highly technical architectural review and upgrade analysis of the '30 Football Plus' V2 autonomous short-form video broadcast system.
The system produces 30-second (8-scene, ~26s story + 5s branded outro) vertical (9:16, 1080x1920 @ 30fps) 1990s TV broadcast shorts for YouTube Shorts and TikTok from breaking football news.

Examine and provide concrete architectural critique, trade-off analysis, failure modes, and upgrade proposals for each of the following 7 core subsystems:
1. Stage 1: News Aggregation & Scraping (Google News, BBC, Sky Sports, Guardian, Transfermarkt, Reddit)
2. Stage 2: Ground-Truth Fact-Checking & Knowledge Validation (Manager, stadium, ownership verification e.g. Pochettino at Man Utd, Marco Silva at Fulham)
3. Stage 3: 8-Scene Screenplay & Cynical British Tactician Dialogue Generation
4. Stage 4: Action-Aware Visual Direction & Semantic Real-Image Procurement (Banning static poses, enforcing sliding tackles/duels/sprints/tactical shouts, handling OR/AND dilemmas with split visuals, zero image reuse)
5. Stage 5: Voice Synthesis & Vocal Dynamics (Qwen3-TTS / Edge-TTS, speech rate, pause pacing, stutter/whisper suppression, EBU R128 loudness mastering at -14 LUFS)
6. Stage 6: Video Rendering & Trinitron CRT Post-Processing (Remotion React engine, 4px scanlines, aperture grille, chromatic aberration, safe-area typography)
7. Stage 7: Multilingual Localization (Latin American Spanish ES-419 & Brazilian Portuguese PT-BR, syllable expansion budgeting, audio-subtitle synchronization)

For each subsystem, structure your analysis with:
- Current Architecture & Bottlenecks (latent fragility points, failure modes)
- Specific Engineering Recommendations (algorithmic, architectural, or model upgrades)
- Next-Gen V3 Horizon (future autonomous paradigms)

Be precise, highly technical, and direct. Avoid generic praise."""

def main():
    print("==================================================================")
    print("  CONSULTING AI ARCHITECTS: GPT-OSS-120B & QWEN-27B             ")
    print("==================================================================")

    # 1. Query GPT-OSS-120B
    print("\n[*] Querying OpenAI GPT-OSS-120B on Groq...")
    gpt_response = call_groq_chat(
        preferred_model="openai/gpt-oss-120b",
        fallback_model="openai/gpt-oss-20b",
        system_prompt="You are a Principal AI Video Systems Architect.",
        user_prompt=AUDIT_PROMPT,
        temperature=0.3,
        max_tokens=4000
    )
    if gpt_response:
        print("[✓] GPT-OSS-120B audit completed successfully.")
        out_gpt = PROJECT_ROOT / "beta" / "gpt_oss_audit_response.txt"
        with open(out_gpt, "w", encoding="utf-8") as f:
            f.write(gpt_response)
        print(f"    Saved to {out_gpt}")
    else:
        print("[!] Warning: GPT-OSS-120B query returned None")

    # 2. Query Qwen 27B
    print("\n[*] Querying Qwen3.8-27B on Groq...")
    qwen_response = call_groq_chat(
        preferred_model="qwen/qwen3.8-27b",
        fallback_model="openai/gpt-oss-20b",
        system_prompt="You are a Principal AI Video Systems Architect.",
        user_prompt=AUDIT_PROMPT,
        temperature=0.3,
        max_tokens=4000
    )
    if qwen_response:
        print("[✓] Qwen3.8-27B audit completed successfully.")
        out_qwen = PROJECT_ROOT / "beta" / "qwen_27b_audit_response.txt"
        with open(out_qwen, "w", encoding="utf-8") as f:
            f.write(qwen_response)
        print(f"    Saved to {out_qwen}")
    else:
        print("[!] Warning: Qwen3.8-27B query returned None")

    print("\n[Audit Query Complete]")

if __name__ == "__main__":
    main()
