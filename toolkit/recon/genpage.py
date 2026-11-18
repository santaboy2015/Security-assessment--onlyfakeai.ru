import ssl, urllib.request, re

ctx = ssl.create_default_context()
for path in ["/generator", "/en/generator", "/history", "/en/history"]:
    url = "https://onlyfakeai.ru" + path
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0",
        "Accept": "text/html",
    })
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            b = r.read()
        t = b.decode("utf-8", "ignore")
        print("=" * 10, path, r.status, len(t))
        scripts = re.findall(r'<script[^>]+src="([^"]+)"', t)
        for s in scripts:
            if "chunks/app" in s:
                print("  chunk:", s)
    except Exception as e:
        print(path, "ERR", str(e)[:120])
