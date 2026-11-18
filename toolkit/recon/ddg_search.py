import ssl, urllib.request, urllib.parse, re, html

ctx = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0"}

queries = [
    '"onlyfakeai.ru"',
    '"admin@onlyfakeai.ru"',
    '"onlyfake@tuta.io"',
    '"onlyfake@onlyfakeai.ru"',
    'onlyfakeai github',
    '"onlyfake" telegram',
]
for q in queries:
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            t = r.read().decode("utf-8", "ignore")
        results = re.findall(r'result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', t)
        snips = re.findall(r'result__snippet[^>]*>(.*?)</a>', t, re.S)
        print(f"\n=== {q} ({len(results)} results) ===")
        for i, (href, title) in enumerate(results[:6]):
            title = re.sub(r"<[^>]+>", "", title)
            snip = html.unescape(re.sub(r"<[^>]+>", "", snips[i]))[:160] if i < len(snips) else ""
            print(f"- {html.unescape(title)[:90]}\n  {href[:120]}\n  {snip}")
    except Exception as e:
        print(q, "ERR", str(e)[:100])
