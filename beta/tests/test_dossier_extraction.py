import sys
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from stages.scraped_story_adapter import scraped_story_to_dossier

test_stories = [
    {
        "headline": "Man Utd transfer news: Fulham defender Calvin Bassey is in talks over new contract amid Man Utd links - Paper Talk",
        "source": "Sky Sports",
        "raw_text": "Fulham defender Calvin Bassey is in talks over a new contract at Craven Cottage amid interest from Manchester United. The Nigerian international has impressed in the Premier League this season."
    },
    {
        "headline": "Transfer Centre LIVE! 'Real Madrid close to agreeing new contract with Bellingham'",
        "source": "Sky Sports News",
        "raw_text": "Real Madrid are close to agreeing a bumper new contract with Jude Bellingham. The English midfielder is set to commit his long term future to the Bernabeu."
    },
    {
        "headline": "Bayern Munich feels ‘gentlemen’s agreement’ on contract has been violated by Jamal Musiala’s camp",
        "source": "Bavarian Football Works",
        "raw_text": "Bayern Munich hierarchy are frustrated as Jamal Musiala contract negotiations hit a stumbling block amid interest from Manchester City and Real Madrid."
    }
]

for s in test_stories:
    dossier = scraped_story_to_dossier(s)
    print("--- DOSSIER ---")
    print(f"Headline: {dossier.main_headline}")
    print(f"Protagonist: {dossier.protagonist_name}")
    print(f"Clubs: {dossier.current_club} -> {dossier.pursuing_club}")
    print(f"Ticker: {dossier.ticker_text}")
