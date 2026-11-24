import urllib.request
import json

urls = [
    "https://www.reddit.com/r/soccer.rss",
    "https://www.reddit.com/r/soccer/new.rss",
    "https://www.reddit.com/r/soccer/hot.json?limit=15",
]

for url in urls:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 FootballBot/2.0"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
            print(f"SUCCESS {url}: {len(data)} bytes")
            if url.endswith(".json"):
                js = json.loads(data.decode("utf-8"))
                posts = js.get("data", {}).get("children", [])
                for p in posts[:5]:
                    d = p.get("data", {})
                    print("  Reddit Post:", d.get("title"))
    except Exception as e:
        print(f"FAILED {url}: {e}")
