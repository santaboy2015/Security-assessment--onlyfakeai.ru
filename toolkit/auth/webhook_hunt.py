import ssl, urllib.request, re, json

ctx = ssl.create_default_context()
base = "https://onlyfakeai.ru"
files = [
    "/_next/static/chunks/app/%5Blocale%5D/generator/page-bf5f8970043f7336.js",
    "/_next/static/chunks/app/%5Blocale%5D/layout-7ad3dad986f259e9.js",
    "/_next/static/chunks/3660-b0d70753c10786e1.js",
    "/_next/static/chunks/2009-7ef334d50f21d53f.js",
]

needles = ["webhook", "stripe", "checkout", "payment", "price",
           "grant_plan", "generations", "credits", "plan"]

for f in files:
    req = urllib.request.Request(base + f, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        t = r.read().decode("utf-8", "ignore")
    for n in needles:
        idxs = [m.start() for m in re.finditer(re.escape(n), t)]
        for i in idxs[:2]:
            a = max(0, i - 300)
            z = min(len(t), i + 500)
            seg = t[a:z].replace("\n", " ")
            if "fetch" in seg or "/api/" in seg or "http" in seg or "grant" in seg:
                print("=" * 10, f.split("/")[-1][:30], f"[{n}]")
                print(seg[:700])
                print()
                break
