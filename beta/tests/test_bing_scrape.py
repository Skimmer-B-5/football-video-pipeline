import urllib.request
import re
import html
import json

url = 'https://www.bing.com/images/async?q=Calvin+Bassey+Fulham&first=0&count=35&mmasync=1'
req = urllib.request.Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
)
with urllib.request.urlopen(req) as resp:
    text = resp.read().decode('utf-8', errors='ignore')

matches = re.findall(r'm=[\'"](\{.*?\})[\'"]', text)
print(f"Total matches: {len(matches)}")
valid = 0
for idx, m in enumerate(matches):
    try:
        d = json.loads(html.unescape(m))
        murl = d.get("murl")
        title = d.get("t", "")
        if murl and murl.startswith("http"):
            valid += 1
            if valid <= 5:
                print(f"[{valid}] {title[:60]}")
                print(f"     URL: {murl[:80]}")
    except Exception as e:
        pass
print(f"Total valid media URLs: {valid}")
