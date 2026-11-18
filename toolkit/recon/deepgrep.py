import ssl, urllib.request, re

ctx = ssl.create_default_context()
base = "https://onlyfakeai.ru"
files = [
    "/_next/static/chunks/app/%5Blocale%5D/layout-7ad3dad986f259e9.js",
    "/_next/static/chunks/app/%5Blocale%5D/page-7ec00b8de687c57f.js",
    "/_next/static/chunks/2991-c196a5c0a00c6df4.js",
    "/_next/static/chunks/6874-ae139413c77a2f7e.js",
    "/_next/static/chunks/7148-bf45b30fb81d4cc1.js",
    "/_next/static/chunks/3063-01ba4a574264f858.js",
    "/_next/static/chunks/3660-b0d70753c10786e1.js",
    "/_next/static/chunks/2009-7ef334d50f21d53f.js",
    "/_next/static/chunks/851-4b3e5b84db45aa6c.js",
    "/_next/static/chunks/1684-ff3992de2ad3eae9.js",
    "/_next/static/chunks/4bd1b696-1fc9c04a2f3113b7.js",
]

pats = {
    "jwt": r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}",
    "subhost": r"[a-z0-9\-]{15,}\.supabase\.(co|in|red)",
    "envurl": r"NEXT_PUBLIC_SUPABASE_[A-Z_]+[\"'`\s:,=\[]+[\"'`]([^\"'`]{10,140})[\"'`]",
    "supabaseUrl": r"supabaseUrl[\"'`\s:,=\[]+[\"'`]([^\"'`]{10,140})[\"'`]",
    "createclient": r"createClient\([^)]{0,200}",
}

for f in files:
    req = urllib.request.Request(base + f, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            b = r.read()
    except Exception as e:
        print(f, "ERR", e)
        continue
    t = b.decode("utf-8", "ignore")
    print("=" * 20, f, len(t))
    for name, pat in pats.items():
        hits = re.findall(pat, t)
        uniq = list(dict.fromkeys(hits))[:6]
        for h in uniq:
            print(f"  [{name}]", str(h)[:200])
