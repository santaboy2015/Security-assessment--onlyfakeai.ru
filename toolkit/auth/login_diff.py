import ssl, urllib.request, difflib

ctx = ssl.create_default_context()
docs = []
for i in range(2):
    req = urllib.request.Request("https://ops.onlyfakeai.ru/login",
                                 headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        docs.append(r.read().decode("utf-8", "ignore"))

a = docs[0].splitlines()
b = docs[1].splitlines()
print("lines:", len(a), len(b))
diffs = [d for d in difflib.unified_diff(a, b, lineterm="") if d.startswith(("+", "-")) and not d.startswith(("+++", "---"))]
for d in diffs[:20]:
    print(d[:300])
print("diff count:", len(diffs))
