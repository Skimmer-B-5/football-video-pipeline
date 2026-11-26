"""
# PROVENANCE: Copied from stages/meme_vault.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Stage: Dynamic Football Meme Vault & History Tracker
Provides 25+ iconic football meme personalities, witty contextual roast lines,
and persistent anti-repetition tracking so no meme or image is spammed repeatedly.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
MEME_HISTORY_FILE = EVIDENCE_DIR / "meme_history.json"
IMAGE_HISTORY_FILE = EVIDENCE_DIR / "used_images_history.json"

MEME_CATALOG = [
    {
        "key": "mourinho_if_i_speak",
        "entity": "Jose Mourinho",
        "context": "if I speak I am in big trouble meme",
        "punchlines": [
            "Even Jose Mourinho would prefer not to speak about this.",
            "If Jose Mourinho speaks about this, he is in big trouble.",
            "Mourinho just put his headphones on and walked out."
        ],
        "search_queries": [
            "Jose Mourinho if I speak meme",
            "Jose Mourinho headphones press conference meme",
            "Jose Mourinho binoculars meme"
        ],
        "sfx": "vine_boom"
    },
    {
        "key": "maguire_confusion",
        "entity": "Harry Maguire",
        "context": "confused hands on hips meme",
        "punchlines": [
            "Harry Maguire's no-look defending looks coordinated next to this.",
            "Even Harry Maguire is looking confused at this tactical disaster.",
            "Maguire tackling his own teammate made more sense than this."
        ],
        "search_queries": [
            "Harry Maguire confused meme face",
            "Harry Maguire no look defending meme",
            "Harry Maguire hands on hips funny meme"
        ],
        "sfx": "hit_marker"
    },
    {
        "key": "pep_overthinking",
        "entity": "Pep Guardiola",
        "context": "head in hands overthinking meme",
        "punchlines": [
            "Pep Guardiola is holding his head in total agony.",
            "Pep is already overthinking how to exploit this mess.",
            "Guardiola drank three bottles of water just watching this."
        ],
        "search_queries": [
            "Pep Guardiola head in hands meme",
            "Pep Guardiola overthinking funny face",
            "Pep Guardiola touchline stressed meme"
        ],
        "sfx": "vine_boom"
    },
    {
        "key": "boehly_contracts",
        "entity": "Todd Boehly",
        "context": "Chelsea executive box spreadsheet meme",
        "punchlines": [
            "Todd Boehly is already preparing an eight-year contract.",
            "Boehly just offered a billion pounds and a decade deal.",
            "Todd Boehly's spreadsheet is crying right now."
        ],
        "search_queries": [
            "Todd Boehly Chelsea executive box meme",
            "Todd Boehly funny face meme",
            "Todd Boehly signing meme"
        ],
        "sfx": "pop_click"
    },
    {
        "key": "darwin_chaos",
        "entity": "Darwin Nunez",
        "context": "chaos face hitting post meme",
        "punchlines": [
            "Darwin Nunez hits the post with more precision than this.",
            "Darwin's chaotic energy cannot explain this boardroom circus.",
            "Even Darwin Nunez would give this a confused thumbs up."
        ],
        "search_queries": [
            "Darwin Nunez funny face meme",
            "Darwin Nunez thumbs up meme",
            "Darwin Nunez chaos meme"
        ],
        "sfx": "hit_marker"
    },
    {
        "key": "ancelotti_eyebrow",
        "entity": "Carlo Ancelotti",
        "context": "raised eyebrow meme",
        "punchlines": [
            "Carlo Ancelotti raised one eyebrow and ended the debate.",
            "Ancelotti didn't even need to raise an eyebrow for this.",
            "Carlo Ancelotti's eyebrow just climbed into row Z."
        ],
        "search_queries": [
            "Carlo Ancelotti raised eyebrow meme",
            "Carlo Ancelotti eyebrow funny face",
            "Carlo Ancelotti eyebrow press conference"
        ],
        "sfx": "pop_click"
    },
    {
        "key": "ronaldo_statue",
        "entity": "Cristiano Ronaldo",
        "context": "bronze bust statue meme",
        "punchlines": [
            "Even Cristiano's bronze airport statue looks less distorted.",
            "Ronaldo's famous bust has better tactical awareness.",
            "Cristiano Ronaldo looked at this and whispered: factos."
        ],
        "search_queries": [
            "Cristiano Ronaldo bronze bust statue meme",
            "Cristiano Ronaldo factos meme",
            "Cristiano Ronaldo meme face funny"
        ],
        "sfx": "vine_boom"
    },
    {
        "key": "messi_bobo",
        "entity": "Lionel Messi",
        "context": "que miras bobo interview meme",
        "punchlines": [
            "Messi looked at this and said: que miras bobo.",
            "Not even prime Messi could dribble past this financial ruin.",
            "Messi is staring into space wondering who approved this."
        ],
        "search_queries": [
            "Lionel Messi que miras bobo meme",
            "Lionel Messi staring into space meme",
            "Lionel Messi drinking mate meme"
        ],
        "sfx": "vine_boom"
    },
    {
        "key": "antony_fidget",
        "entity": "Antony",
        "context": "360 fidget spinner meme",
        "punchlines": [
            "Antony's 360 spin creates fewer useless circles than this board.",
            "Still spinning faster than Antony in the corner flag.",
            "Antony just spun around three times in tribute."
        ],
        "search_queries": [
            "Antony fidget spin meme funny",
            "Antony Manchester United spinning meme",
            "Antony funny face meme"
        ],
        "sfx": "hit_marker"
    },
    {
        "key": "neymar_rolling",
        "entity": "Neymar",
        "context": "rolling on pitch meme",
        "punchlines": [
            "Neymar rolled twelve times just reading this headline.",
            "Rolling across the pitch faster than Neymar at the World Cup.",
            "Even Neymar's dramatic tumble looks dignified compared to this."
        ],
        "search_queries": [
            "Neymar rolling on grass meme",
            "Neymar funny dive meme",
            "Neymar World Cup roll meme"
        ],
        "sfx": "pop_click"
    },
    {
        "key": "mudryk_miss",
        "entity": "Mykhailo Mudryk",
        "context": "shot flying over stadium meme",
        "punchlines": [
            "Mudryk's missed shot landed closer to earth than this plan.",
            "Sometimes the chaos just happens, as Mudryk would say.",
            "Aiming higher into the clouds than a Mudryk half-volley."
        ],
        "search_queries": [
            "Mykhailo Mudryk meme funny",
            "Mudryk missed shot into sky meme",
            "Mudryk gym selfie meme"
        ],
        "sfx": "hit_marker"
    },
    {
        "key": "bale_nap",
        "entity": "Gareth Bale",
        "context": "sleeping on bench face mask meme",
        "punchlines": [
            "Gareth Bale took a nap on the bench and missed nothing.",
            "Wales. Golf. Sleeping on the bench. In that exact order.",
            "Bale put his face mask over his eyes and went to sleep."
        ],
        "search_queries": [
            "Gareth Bale sleeping on bench face mask meme",
            "Gareth Bale Wales Golf Madrid banner meme",
            "Gareth Bale golf swing funny meme"
        ],
        "sfx": "pop_click"
    },
    {
        "key": "klopp_boom",
        "entity": "Jurgen Klopp",
        "context": "teeth grinning boom laugh meme",
        "punchlines": [
            "Jurgen Klopp let out a booming laugh from his holiday villa.",
            "Klopp's gleaming smile couldn't hide the comedy of this deal.",
            "Klopp said BOOM and walked into the sunset."
        ],
        "search_queries": [
            "Jurgen Klopp boom laugh meme",
            "Jurgen Klopp big teeth smile meme",
            "Jurgen Klopp funny face meme"
        ],
        "sfx": "pop_click"
    },
    {
        "key": "wenger_coat",
        "entity": "Arsene Wenger",
        "context": "sleeping bag coat zipper struggle meme",
        "punchlines": [
            "Arsene Wenger is still struggling with his giant coat zipper.",
            "Wenger almost signed this entire disaster fifteen years ago.",
            "Wenger looked at this balance sheet and zipped his coat up."
        ],
        "search_queries": [
            "Arsene Wenger coat zipper struggle meme",
            "Arsene Wenger I almost signed him meme",
            "Arsene Wenger funny stadium meme"
        ],
        "sfx": "pop_click"
    },
    {
        "key": "simeone_rage",
        "entity": "Diego Simeone",
        "context": "sideline wild manic screaming meme",
        "punchlines": [
            "Diego Simeone is sprinting down the touchline in wild fury.",
            "Simeone's dark touchline rage is pure poetry next to this.",
            "Even Cholo Simeone cannot defend this level of chaos."
        ],
        "search_queries": [
            "Diego Simeone crazy touchline reaction meme",
            "Diego Simeone funny shouting meme",
            "Diego Simeone celebration meme"
        ],
        "sfx": "vine_boom"
    },
    {
        "key": "yamal_homework",
        "entity": "Lamine Yamal",
        "context": "doing high school homework in hotel meme",
        "punchlines": [
            "Lamine Yamal finished his geometry homework faster than this board.",
            "Yamal is taking secondary school exams while this club falls apart.",
            "Even Yamal's homework teacher gave this an F minus."
        ],
        "search_queries": [
            "Lamine Yamal doing homework meme",
            "Lamine Yamal school books meme",
            "Lamine Yamal funny celebration meme"
        ],
        "sfx": "hit_marker"
    },
    {
        "key": "palmer_shiver",
        "entity": "Cole Palmer",
        "context": "cold shivering celebration meme",
        "punchlines": [
            "Cole Palmer is looking freezing cold at this absolute dumpster fire.",
            "Palmer shivered once and created more danger than this entire squad.",
            "Cold Palmer just checked the temperature: absolute zero."
        ],
        "search_queries": [
            "Cole Palmer cold celebration meme",
            "Cole Palmer shivering funny meme",
            "Cole Palmer cold arms crossed meme"
        ],
        "sfx": "pop_click"
    },
    {
        "key": "haaland_zen",
        "entity": "Erling Haaland",
        "context": "robot yoga meditation pitch meme",
        "punchlines": [
            "Erling Haaland sat down in yoga meditation to escape this madness.",
            "The Norwegian robot just powered down in utter disbelief.",
            "Haaland screamed into the referee's face in sheer solidarity."
        ],
        "search_queries": [
            "Erling Haaland yoga meditation celebration meme",
            "Erling Haaland screaming referee face meme",
            "Erling Haaland funny robot meme"
        ],
        "sfx": "vine_boom"
    }
]

def load_meme_history() -> List[str]:
    """Load list of recently used meme keys."""
    if MEME_HISTORY_FILE.exists():
        try:
            with open(MEME_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def record_meme_usage(meme_keys: List[str]):
    """Record used meme keys to prevent consecutive repetition."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    history = load_meme_history()
    for k in meme_keys:
        history.append(k)
    # Keep only the last 15 memes in history
    history = history[-15:]
    with open(MEME_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def pick_fresh_memes(count: int = 1, exclude_entities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Selects 1 or 2 fresh, diverse memes that were NOT used recently
    and do not clash with the primary headline entities.
    """
    history = set(load_meme_history())
    exclude_ents = [e.lower() for e in (exclude_entities or [])]

    # Filter out recently used and entity clashes
    available = [
        m for m in MEME_CATALOG
        if m["key"] not in history and not any(e in m["entity"].lower() for e in exclude_ents)
    ]

    # If pool exhausted, allow any meme not clashing with main entity
    if len(available) < count:
        available = [
            m for m in MEME_CATALOG
            if not any(e in m["entity"].lower() for e in exclude_ents)
        ]

    chosen = random.sample(available, min(count, len(available)))
    record_meme_usage([m["key"] for m in chosen])
    return chosen

def load_image_history() -> Dict[str, Any]:
    """Load persistent dictionary of used image hashes and URLs."""
    if IMAGE_HISTORY_FILE.exists():
        try:
            with open(IMAGE_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"hashes": [], "urls": []}
    return {"hashes": [], "urls": []}

def record_used_image(img_hash: str, url: str):
    """Persist used image hash and URL to prevent reuse across multiple videos."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    history = load_image_history()
    if img_hash and img_hash not in history["hashes"]:
        history["hashes"].append(img_hash)
    if url and url not in history["urls"]:
        history["urls"].append(url)

    # Keep last 150 images in memory
    history["hashes"] = history["hashes"][-150:]
    history["urls"] = history["urls"][-150:]
    with open(IMAGE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def is_image_previously_used(img_hash: str, url: str) -> bool:
    """Check if an image hash or URL has been used in previous runs."""
    history = load_image_history()
    return (img_hash in history.get("hashes", [])) or (url in history.get("urls", []))
