import urllib.request
import xml.etree.ElementTree as ET

candidate_feeds = [
    ("The Guardian Transfers", "https://www.theguardian.com/football/transfers/rss"),
    ("The Guardian Main", "https://www.theguardian.com/football/rss"),
    ("Sky Sports Transfer Centre", "https://www.skysports.com/rss/12040"),
    ("Sky Sports News", "https://www.skysports.com/rss/11095"),
    ("BBC Sport Football", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("Football365 Transfers", "https://www.football365.com/transfers/feed"),
    ("90min Posts", "https://www.90min.com/posts.rss"),
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
            print(f"✅ {name} ({url}): {len(items)} items, {len(data)} bytes")
            if items:
                first_title = items[0].findtext("title", "").strip()
                first_date = items[0].findtext("pubDate", "").strip()
                print(f"   Latest: {first_title} ({first_date})")
    except Exception as e:
        print(f"❌ {name} ({url}): {e}")
