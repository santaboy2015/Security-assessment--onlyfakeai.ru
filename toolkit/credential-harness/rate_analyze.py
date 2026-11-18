import ssl, urllib.request, re

ctx = ssl.create_default_context()
base = "https://onlyfakeai.ru"
files = [
    "/_next/static/chunks/app/%5Blocale%5D/rate/page-af796a618e969b55.js",
    "/_next/static/chunks/app/%5Blocale%5D/shop/%5B%5B...params%5D%5D/page-eab1bba31e1ae7e0.js",
]
for f in files:
    req = urllib.request.Request(base + f, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        t = r.read().decode("utf-8", "ignore")
    print("=" * 20, f.split("/")[-1], len(t))
    for n in ["/api/", "stripe", "checkout", "payment", "webhook",
              "price", "pay", "credit", "plan", "telegram", "crypto"]:
        idxs = [m.start() for m in re.finditer(re.escape(n), t)]
        print(f"[{n}] x{len(idxs)}")
        for i in idxs[:2]:
            a = max(0, i - 250)
            z = min(len(t), i + 400)
            print("   ", t[a:z].replace("\n", " ")[:600])
    open(f.split("/")[-1], "w", encoding="utf-8").write(t)
