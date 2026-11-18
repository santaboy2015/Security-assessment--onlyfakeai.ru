import ssl, urllib.request, re, hashlib

ctx = ssl.create_default_context()
seen = {}
for i in range(12):
    req = urllib.request.Request("https://ops.onlyfakeai.ru/login",
                                 headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            b = r.read()
    except Exception as e:
        print(i, "ERR", str(e)[:80])
        continue
    h = hashlib.sha256(b).hexdigest()[:16]
    t = b.decode("utf-8", "ignore")
    scripts = re.findall(r'<script[^>]+src="([^"]+)"', t)
    title = re.search(r"<title>([^<]*)</title>", t)
    key = h
    if key not in seen:
        seen[key] = {"count": 0, "scripts": scripts, "title": title.group(1) if title else "", "len": len(b)}
    seen[key]["count"] += 1
    print(i, h, len(b), (title.group(1) if title else "")[:30])

print("\n=== distinct variants ===")
for h, v in seen.items():
    print(h, "count=", v["count"], "len=", v["len"], "title=", v["title"])
    for s in v["scripts"]:
        print("   ", s)
