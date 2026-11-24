import urllib.request
import xml.etree.ElementTree as ET

url = "https://news.google.com/rss/search?q=(transfer+OR+bid+OR+contract)+site:skysports.com+OR+site:bbc.com+OR+site:theguardian.com+when:2d&hl=en-GB&gl=GB&ceid=GB:en"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 FootballBot/2.0"
}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = resp.read()
        root = ET.fromstring(data)
        items = root.findall(".//item")
        print(f"✅ Filtered Tier-1 Outlets: {len(items)} items")
        for i, it in enumerate(items[:8], 1):
            title = it.findtext("title", "").strip()
            source = it.findtext("source", "").strip()
            print(f"  {i}. [{source}] {title}")
except Exception as e:
    print(f"❌ Error: {e}")
