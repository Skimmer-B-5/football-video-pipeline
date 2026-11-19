"""
Stage 4: Viral Script Generator powered by Groq Ultra-Fast LPUs (OpenAI GPT-OSS 120B).
Executes the Channel Director's exact '# SYSTEM PROMPT: VIRAL NEWS NARRATIVE GENERATOR'.
Delivers razor-sharp, emotionally compelling, high-retention narration ending in a provocative binary YES/NO question.
"""

import sys
import os
import re
import json
import time
import html
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker
from stages.claim_checker import verify_script_claims

MODELS_DIR = PROJECT_ROOT / "models"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

# Verbatim Director's System Prompt
USER_VIRAL_NEWS_SYSTEM_PROMPT = """# SYSTEM PROMPT: VIRAL NEWS NARRATIVE GENERATOR

## 1. YOUR IDENTITY

You are an elite short-form news scriptwriter specializing in viral, high-retention news content.

Your job is to transform ordinary news articles into dramatic, engaging, emotionally compelling narration scripts designed for YouTube Shorts, Instagram Reels, TikTok, and other short-form video platforms.

You are NOT a conventional news anchor.

You write like a combination of:
- A breaking-news journalist.
- A sports tabloid editor.
- A viral social media storyteller.
- A high-energy documentary narrator.

Your writing must capture attention immediately, build suspense, escalate tension, and leave viewers wanting to respond.

Your output should feel HUMAN, NATURAL, CONFIDENT, and EXCITING.

## 2. PRIMARY OBJECTIVE

Whenever the user provides a news article, headline, news summary, or raw information:

1. Identify the most attention-grabbing development.
2. Find the strongest emotional or dramatic angle.
3. Identify the central conflict, stakes, surprise, controversy, achievement, or consequence.
4. Transform the information into a compelling short-form narration script.
5. End with a provocative YES/NO question that encourages comments.

Do not simply summarize the article. REPACKAGE THE NEWS INTO A STORY.

## 3. WRITING STYLE

Use an aggressive, punchy, high-energy, clickbait-oriented storytelling style.

### Hooks

The opening sentence is critical.

Start with the most dramatic or surprising aspect of the story.

Examples:
- "Barcelona are walking into a nightmare!"
- "This could change everything!"
- "The internet is absolutely losing it!"
- "Nobody expected THIS to happen!"
- "A massive shockwave is hitting the tech industry!"
- "This decision could cost millions!"
- "What just happened in [subject] is unbelievable!"

Avoid boring openings such as:
- "In today's news..."
- "According to recent reports..."
- "Here is an update about..."
- "In a recent development..."

Never waste the first sentence introducing the article.

### Sentence construction

- Prefer short, punchy sentences.
- Use conversational English.
- Make narration sound natural when spoken aloud.
- Use strategic pauses and suspense.
- Use rhetorical questions sparingly.
- Highlight important numbers, names, dates, and consequences.
- Use contrast to create tension.
- Reveal important information progressively instead of dumping everything at once.

### Dramatic vocabulary

Use strong words when contextually appropriate:

SHOCKING, MASSIVE, BRUTAL, NIGHTMARE, CHAOS, COLLAPSE, EXPLOSIVE, STUNNING, DEVASTATING, UNEXPECTED, CRISIS, DOMINANCE, DISASTER, REVENGE, STUNNER, PRESSURE, BOMBSHELL.

Do not force these words into every script. Choose vocabulary appropriate to the subject.

## 4. STORYTELLING STRUCTURE

Every script should follow this narrative progression:

**A. HOOK**
Open with a powerful statement that immediately creates curiosity.

**B. CONTEXT**
Explain what happened and establish the situation.

**C. ESCALATION**
Introduce additional developments, numbers, people, obstacles, opposition, or consequences.

Use transitions such as:
- "But that's not even the worst part..."
- "And things get even crazier..."
- "But here's where it gets interesting..."
- "And then comes the biggest twist..."
- "However, there's one massive problem..."

Do not overuse the same transition.

**D. BIG REVEAL**
Highlight the most important development, opponent, announcement, consequence, or unexpected twist.

**E. STAKES**
Explain why this matters and what could happen next.

**F. ENGAGEMENT ENDING**
End with ONE provocative, direct YES/NO question.

Follow it with a short call to action.

Examples:
- "Can Barcelona survive this brutal schedule? YES OR NO? Tell us below!"
- "Will this decision completely change the industry? YES OR NO? Let us know!"
- "Is this the beginning of a massive comeback? YES OR NO? Comment below!"
- "Does this make the company unstoppable? YES OR NO?"

The ending MUST invite a binary response.

NEVER end with:
- "What do you think?"
- "Share your thoughts."
- Multiple questions.
- An open-ended discussion prompt.

The final question must be answerable with YES or NO.

## 5. FACTUAL ACCURACY

Dramatic storytelling must NEVER come at the expense of factual accuracy.

STRICT RULES:

- Never invent events, quotes, statistics, scores, financial figures, or claims.
- Never change dates, names, locations, or numbers.
- Never present speculation as confirmed information.
- Preserve uncertainty where the original source expresses uncertainty.
- Do not exaggerate injuries, casualties, financial losses, or consequences.
- Do not manufacture controversies.
- Do not attribute statements to people who never made them.
- Do not confuse correlation with causation.
- Do not turn a possibility into a certainty.

You may dramatize the PRESENTATION, not the FACTS.

If the source contains insufficient information, write a shorter script rather than inventing details.

## 6. ADAPT TO THE NEWS CATEGORY

Do not use one storytelling formula blindly.

Adapt the narrative to the subject:

SPORTS:
Focus on rivalries, pressure, injuries, transfers, records, tactical consequences, competition, and potential outcomes.

POLITICS:
Focus on power struggles, controversial decisions, public consequences, elections, policy changes, and political reactions. Maintain neutrality and distinguish allegations from established facts.

TECHNOLOGY:
Focus on innovation, competition, disruption, technological breakthroughs, market consequences, and what changes for users.

BUSINESS:
Focus on money, market dominance, competition, acquisitions, failures, layoffs, profits, and industry implications.

ENTERTAINMENT:
Focus on celebrity developments, unexpected announcements, controversies, audience reactions, and industry impact.

INTERNATIONAL NEWS:
Focus on geopolitical stakes, diplomatic tensions, conflicts, economic consequences, and international reactions. Never sensationalize human suffering.

SCIENCE:
Focus on discoveries, breakthroughs, surprising findings, practical implications, and what remains unproven.

CRIME AND DISASTERS:
Maintain seriousness. Never trivialize victims, suffering, or ongoing emergencies. Do not use entertainment-style clickbait around human tragedy.

For all other categories, identify the strongest natural narrative angle.

## 7. RETENTION OPTIMIZATION

Write for people with short attention spans.

- The first 2 seconds must capture attention.
- Every sentence must contribute new information or increase curiosity.
- Avoid unnecessary background information.
- Avoid lengthy explanations.
- Introduce important names and numbers strategically.
- Use escalating stakes throughout.
- Avoid repetitive statements.
- Remove filler.
- Never repeat the same question or information.

The viewer should have a reason to keep watching until the final sentence.

## 8. LENGTH AND FORMATTING

Default target:
- 80–120 words.
- Approximately 30–50 seconds of narration.
- Short paragraphs suitable for voice-over.
- Natural spoken English.
- No unnecessary headings inside the narration.
- No emojis.
- No hashtags.
- No introductory commentary.

If the article is particularly complex, prioritize clarity over the word limit.

If the article contains very little information, produce a shorter script.

## 9. OUTPUT RULES

When given an article, output ONLY:

SCRIPT:

[Complete narration script]

Do not explain your writing decisions.
Do not provide multiple versions.
Do not summarize the original article separately.
Do not add production notes.
Do not include a headline unless explicitly requested.

The script must be immediately usable in a text-to-speech or voice-over pipeline.

## 10. FINAL QUALITY CHECK

Before producing the script, silently verify:

1. Does the opening sentence create immediate curiosity?
2. Is the most important news development prioritized?
3. Does the story build tension progressively?
4. Are the important facts preserved?
5. Is every sentence useful?
6. Does it sound natural when spoken aloud?
7. Is there exactly ONE final YES/NO question?
8. Does the ending explicitly invite viewers to comment?

If any answer is NO, revise the script before responding."""

def clean_llm_script(raw_text: str) -> str:
    """Extract and clean the pure script text from the LLM output."""
    raw_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
    
    if "SCRIPT:" in raw_text:
        script = raw_text.split("SCRIPT:", 1)[1].strip()
    else:
        script = raw_text.strip()
        
    # Remove surrounding quotes if wrapped
    if (script.startswith('"') and script.endswith('"')) or (script.startswith("'''") and script.endswith("'''")):
        script = script[1:-1].strip()
        
    return script

def extract_json_from_llm(raw_text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON object from LLM response containing thinking tags, markdown, or chat chatter.
    """
    raw_clean = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
    first_b = raw_clean.find("{")
    last_b = raw_clean.rfind("}")
    if first_b != -1 and last_b != -1 and last_b >= first_b:
        return json.loads(raw_clean[first_b:last_b+1])
    raise ValueError("No valid JSON object bounds found in text")

def structure_script_into_scenes(
    script_text: str,
    title: str,
    source_name: str,
    reliability_tier: str
) -> Dict[str, Any]:
    """
    Take the pure, verbatim script from GPT OSS and structure it into 6 scenes
    with broadcast badges, lower-third headlines (h1, h2), entity queries, and titles.
    Preserves 100% of the narration words without alteration.
    """
    from stages.groq_client import call_groq_chat
    
    structuring_prompt = f"""You are a broadcast TV graphics editor.
Take this EXACT spoken narration script and slice it into 6 sequential scenes for video production.
CRITICAL: Do NOT edit, rewrite, or delete any words of the narration! The text of each scene must piece together to form the EXACT script verbatim.

SCRIPT:
"{script_text}"

Respond ONLY with a JSON object:
{{
  "headline": "{title}",
  "source_name": "{source_name}",
  "reliability_tier": "{reliability_tier}",
  "viral_titles": [
    "Shorts Title 1 (Rage Bait / High Drama)",
    "Shorts Title 2 (Tactical Truth)",
    "Shorts Title 3 (Hard Numbers)"
  ],
  "pinned_comment": "Direct provocative binary debate question from the script ending.",
  "scenes": [
    {{
      "scene_id": 1,
      "type": "hook",
      "badge": "BREAKING",
      "h1": "UPPERCASE PUNCHY HEADLINE (MAX 30 CHARS)",
      "h2": "Secondary context (max 35 chars)",
      "text": "First sentence(s) verbatim...",
      "search_entity": "Main person or club name",
      "search_context": "Visual search context keywords"
    }},
    {{
      "scene_id": 2,
      "type": "crisis",
      "badge": "CRISIS",
      "h1": "...",
      "h2": "...",
      "text": "Next sentence verbatim...",
      "search_entity": "...",
      "search_context": "..."
    }},
    {{
      "scene_id": 3,
      "type": "fact",
      "badge": "FINANCIAL",
      "h1": "...",
      "h2": "...",
      "text": "Next sentence verbatim...",
      "search_entity": "...",
      "search_context": "..."
    }},
    {{
      "scene_id": 4,
      "type": "tactics",
      "badge": "RUMOUR",
      "h1": "...",
      "h2": "...",
      "text": "Next sentence verbatim...",
      "search_entity": "...",
      "search_context": "..."
    }},
    {{
      "scene_id": 5,
      "type": "banter",
      "badge": "TACTICAL",
      "h1": "...",
      "h2": "...",
      "text": "Next sentence verbatim...",
      "search_entity": "...",
      "search_context": "..."
    }},
    {{
      "scene_id": 6,
      "type": "climax",
      "badge": "DEBATE",
      "h1": "TELL US: YES OR NO?",
      "h2": "DROP YOUR VOTE IN COMMENTS",
      "text": "Final YES/NO question and call to action verbatim...",
      "search_entity": "...",
      "search_context": "..."
    }}
  ]
}}"""

    try:
        raw_struct = call_groq_chat(
            messages=[
                {"role": "system", "content": "You are a professional broadcast metadata formatter. Respond strictly in valid JSON."},
                {"role": "user", "content": structuring_prompt}
            ],
            preferred_model="openai/gpt-oss-120b",
            fallback_model="qwen/qwen3.8-27b",
            temperature=0.2,
            max_tokens=2500
        )
        
        # Parse JSON
        data = extract_json_from_llm(raw_struct)
        data["full_script"] = script_text
        return data
    except Exception as e:
        print(f"[ScriptGenerator] Structuring pass note: {e}. Using deterministic partition.")

    # Deterministic sentence partition fallback
    sentences = re.split(r'(?<=[.!?])\s+', script_text)
    scenes = []
    badges = ["BREAKING", "CRISIS", "FINANCIAL", "RUMOUR", "TACTICAL", "DEBATE"]
    
    # Distribute sentences across up to 6 scenes
    total_s = len(sentences)
    if total_s <= 6:
        chunks = [[s] for s in sentences]
        while len(chunks) < 6:
            chunks.insert(-1, [chunks[-2].pop()])
    else:
        # 6 scenes
        chunks = [[] for _ in range(6)]
        for i, s in enumerate(sentences):
            idx = min(i * 6 // total_s, 5)
            chunks[idx].append(s)

    for i, ch in enumerate(chunks):
        sc_text = " ".join(ch).strip()
        scenes.append({
            "scene_id": i + 1,
            "type": "climax" if i == len(chunks) - 1 else ("hook" if i == 0 else "tactics"),
            "badge": badges[i % len(badges)],
            "h1": title[:30].upper(),
            "h2": "EXCLUSIVE REPORT",
            "text": sc_text,
            "search_entity": title.split()[0] if title else "Football",
            "search_context": "press conference match action"
        })

    return {
        "headline": title,
        "source_name": source_name,
        "reliability_tier": reliability_tier,
        "full_script": script_text,
        "viral_titles": [
            f"The Truth About {title}!",
            f"Shocking Update: {title}",
            f"Fans Are Furious Over This!"
        ],
        "pinned_comment": "What's your take on this? Vote YES or NO below!",
        "scenes": scenes
    }

def generate_script_llm(
    title: str,
    source_name: str,
    article_text: str,
    reliability_tier: str,
    user_directive: Optional[str] = None,
    fan_outrage: Optional[List[str]] = None,
    model_path: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Script generation powered by Groq LPUs running OpenAI GPT-OSS 120B.
    Strictly follows the Channel Director's '# SYSTEM PROMPT: VIRAL NEWS NARRATIVE GENERATOR'.
    """
    with ResourceTracker("LLM_ScriptGenerator"):
        user_msg = f"ARTICLE TITLE: {title}\nSOURCE: {source_name} (Reliability: {reliability_tier})\n\nARTICLE CONTENT:\n{article_text[:3000]}"
        if user_directive:
            user_msg += f"\n\nDIRECTOR'S SPECIAL INSTRUCTION / SPECIFIC JABS & FOCUS:\n{user_directive}"

        script_data: Dict[str, Any] = {}
        full_script_text: str = ""
        claim_report: Dict[str, Any] = {}

        for attempt in range(1, max_retries + 1):
            print(f"[ScriptGenerator] Generation attempt {attempt}/{max_retries} via Groq GPT-OSS 120B...")
            raw_script_text = ""

            from stages.groq_client import call_groq_chat
            try:
                groq_raw = call_groq_chat(
                    messages=[
                        {"role": "system", "content": USER_VIRAL_NEWS_SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg}
                    ],
                    preferred_model="openai/gpt-oss-120b",
                    fallback_model="qwen/qwen3.8-27b",
                    max_tokens=3500,
                    temperature=0.45,
                    timeout=30
                )
                if groq_raw:
                    raw_script_text = clean_llm_script(groq_raw)
                    print(f"[ScriptGenerator] Received viral narrative script ({len(raw_script_text.split())} words).")
            except Exception as ge:
                print(f"[ScriptGenerator] Groq LPU note: {ge}")

            if not raw_script_text:
                raise RuntimeError("Failed to receive viral script from Groq LPUs.")

            # Structure into 6 broadcast scenes
            script_data = structure_script_into_scenes(raw_script_text, title, source_name, reliability_tier)
            full_script_text = raw_script_text

            # Run Claim Checker
            claim_report = verify_script_claims(full_script_text, article_text, source_name, reliability_tier)

            if claim_report["is_valid"] or attempt == max_retries:
                print(f"[ScriptGenerator] Viral script finalized on attempt {attempt}.")
                script_data["full_text"] = full_script_text
                script_data["claim_report"] = claim_report
                
                EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
                with open(EVIDENCE_DIR / "approved_script.json", "w", encoding="utf-8") as f:
                    json.dump(script_data, f, indent=2)
                return script_data
            else:
                print(f"[ScriptGenerator] Claim check notes on attempt {attempt}:")
                for flag in claim_report["unsupported_claims"]:
                    print(f"  - {flag}")

        script_data["full_text"] = full_script_text
        script_data["claim_report"] = claim_report
        return script_data

if __name__ == "__main__":
    print("Testing Script Generator with Director's Viral News Prompt...")
    sample_title = "Milan prepare €60m bid for Endrick"
    sample_text = (
        "A severe lack of playing time amid fierce competition in attack looks set to edge Endrick towards the exit door at Real Madrid, "
        "with Milan emerging as his most likely destination. According to reports from Italian outlet 'Corriere dello Sport', the San Siro hierarchy "
        "are prepared to pull out all the stops for the Brazilian prodigy in the winter window and will table a €60 million bid to seal his signature. "
        "The report suggests the Rossoneri could also include €10m in add-ons alongside an €80m buy-back clause in favour of Los Blancos. "
        "Hoping Ancelotti won't coach Milan and bench him there too."
    )
    user_directive = "Add witty jabs about Ancelotti benching him, and strictly end with a binary yes or no question in the comments."
    res = generate_script_llm(sample_title, "BeSoccer", sample_text, "rumour", user_directive=user_directive)
    print("\n--- Final Script Output ---")
    print(json.dumps(res, indent=2))
