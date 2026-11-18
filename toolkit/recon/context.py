import ssl, urllib.request, re

ctx = ssl.create_default_context()
base = "https://onlyfakeai.ru"
files = [
    "/_next/static/chunks/app/%5Blocale%5D/layout-7ad3dad986f259e9.js",
    "/_next/static/chunks/app/%5Blocale%5D/page-7ec00b8de687c57f.js",
    "/_next/static/chunks/3660-b0d70753c10786e1.js",
    "/_next/static/chunks/2009-7ef334d50f21d53f.js",
]
for f in files:
    req = urllib.request.Request(base + f, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        t = r.read().decode("utf-8", "ignore")
    for m in re.finditer(r"Supabase environment variables", t):
        a = max(0, m.start() - 700)
        z = min(len(t), m.end() + 700)
        print("=" * 30, f)
        print(t[a:z])
        print()
