import ssl, urllib.request, re

ctx = ssl.create_default_context()
base = "https://onlyfakeai.ru"
u = base + "/_next/static/chunks/webpack-3219caacd565a7bb.js"
req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
    t = r.read().decode("utf-8", "ignore")
print(len(t))
for m in re.finditer(r"buildId[^a-zA-Z0-9\-]+([a-zA-Z0-9\-]{5,})", t):
    print("buildId:", m.group(1))
# look for generator chunk references anywhere in webpack runtime
for m in re.finditer(r"[a-zA-Z0-9\-_/\[\]%]+generator[a-zA-Z0-9\-_/\[\]%]*", t):
    print("gen ref:", m.group(0))
