import urllib.request
import json

test_urls = [
    # Barlow Condensed
    "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-SemiBold.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-Bold.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-ExtraBold.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-Black.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/OFL.txt",
    # Inter
    "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter-Regular.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/static/Inter-Regular.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/static/Inter_18pt-Regular.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/static/Inter_24pt-Regular.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/static/Inter_28pt-Regular.ttf",
    "https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/Inter-Regular.woff2",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt",
    # IBM Plex Mono
    "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-Medium.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-SemiBold.ttf",
    "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/OFL.txt"
]

for u in test_urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            print(f"OK ({resp.status}): {u} - {len(data)} bytes")
    except Exception as e:
        print(f"ERR: {u} - {e}")
