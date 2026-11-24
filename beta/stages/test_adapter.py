import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.stages.scraped_story_adapter import scraped_story_to_dossier

samples = [
    {
        'headline': 'Bellingham closing in on bumper new Real Madrid contract',
        'source': 'BeSoccer',
        'raw_text': 'Jude Bellingham is set to sign a massive contract renewal with Real Madrid worth €15M a year.'
    },
    {
        'headline': 'Barcelona revive interest in Bastoni',
        'source': 'BeSoccer',
        'raw_text': 'Barcelona are monitoring Inter Milan defender Alessandro Bastoni for a €70M summer move.'
    }
]

for s in samples:
    d = scraped_story_to_dossier(s)
    print(f"Headline: {d.main_headline}")
    print(f"Protagonist: {d.protagonist_name} | Club: {d.current_club} | Fee: {d.reported_base_fee}")
    print("---")
