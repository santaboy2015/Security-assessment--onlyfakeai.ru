import ssl, urllib.request, re

ctx = ssl.create_default_context()
for path in ["/rate", "/en/rate", "/shop", "/en/shop"]:
    url = "https://onlyfakeai.ru" + path
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 Chrome/140.0", "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            t = r.read().decode("utf-8", "ignore")
        print(path, r.status, len(t))
        for s in re.findall(r'<script[^>]+src="([^"]+)"', t):
            if "chunks/app" in s:
                print("  ", s)
    except Exception as e:
        print(path, "ERR", str(e)[:100])
