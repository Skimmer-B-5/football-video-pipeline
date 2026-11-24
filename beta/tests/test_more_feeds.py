import urllib.request
import xml.etree.ElementTree as ET

candidate_feeds = [
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Football Espana", "https://www.football-espana.net/feed"),
    ("Get German Football News", "https://www.getfootballnewsgermany.com/feed/"),
    ("Get French Football News", "https://www.getfootballnewsfrance.com/feed/"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("Transfermarkt News", "https://www.transfermarkt.com/rss/news"),
    ("OneFootball", "https://onefootball.com/en/news/rss"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 FootballBot/2.0"
}

for name, url in candidate_feeds:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
            root = ET.fromstring(data)
            items = root.findall(".//item")
            print(f"✅ {name}: {len(items)} items")
            if items:
                first_title = items[0].findtext("title", "").strip()
                first_date = items[0].findtext("pubDate", "").strip()
                print(f"   Latest: {first_title} ({first_date})")
    except Exception as e:
        print(f"❌ {name}: {e}")
