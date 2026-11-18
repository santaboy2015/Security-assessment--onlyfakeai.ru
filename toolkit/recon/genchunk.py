import ssl, urllib.request, re

ctx = ssl.create_default_context()
base = "https://onlyfakeai.ru"
u = base + "/_next/static/chunks/app/%5Blocale%5D/layout-7ad3dad986f259e9.js"
req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
    t = r.read().decode("utf-8", "ignore")
open("layout_chunk.js", "w", encoding="utf-8").write(t)
print("layout chunk", len(t))
for pat in [r"generator/[a-zA-Z0-9\-_\[\]%\.]+\.js",
            r"[a-zA-Z0-9\-_\[\]%]*page-[a-f0-9]{16}\.js",
            r"\"/(generator|history|shop|cart)[^\"]*\""]:
    hits = set(re.findall(pat, t))
    print(pat, "->", list(hits)[:12])
