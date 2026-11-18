import ssl, urllib.request, re

ctx = ssl.create_default_context()
base = "https://onlyfakeai.ru"
files = [
    "/_next/static/chunks/app/%5Blocale%5D/generator/page-bf5f8970043f7336.js",
    "/_next/static/chunks/app/%5Blocale%5D/history/page-1e30815bf7857f72.js",
]
for f in files:
    req = urllib.request.Request(base + f, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        t = r.read().decode("utf-8", "ignore")
    print("=" * 20, f, len(t))
    for n in ["/api/", "FormData", "fetch(", "upload", "generate", "country",
              "doc_type", "document_type", "multipart", "supabase", "rpc",
              "signature", "watermark", "no-watermark", "preview"]:
        idxs = [m.start() for m in re.finditer(re.escape(n), t)]
        if idxs:
            print(f"[{n}] x{len(idxs)}")
    open(f.split("/")[-1], "w", encoding="utf-8").write(t)
