import ssl, json, urllib.request, urllib.error, urllib.parse, time

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"

def req(method, url, body=None, token=None, extra=None, follow=False):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY, "Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    if extra: h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener(NoRedir if not follow else urllib.request.HTTPRedirectHandler)
    try:
        with opener.open(r, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, str(e)

def show(tag, st, hd, body, n=320):
    loc = hd.get("Location") or hd.get("location") or ""
    print(f"[{tag}] {st} loc={loc[:200]} body={body[:n].replace(chr(10),' ')}")

print("===== 1. settings / health =====")
st, hd, b = req("GET", SUPA + "/auth/v1/settings")
show("settings", st, hd, b, 1200)
st, hd, b = req("GET", SUPA + "/auth/v1/health")
show("health", st, hd, b)

print("\n===== 2. verify redirect_to allow-list oracle (bogus token, GET) =====")
variants = [
    "https://evil.example/cb",
    "https://onlyfakeai.ru",
    "https://onlyfakeai.ru/",
    "https://onlyfakeai.ru/login",
    "https://onlyfakeai.ru.evil.example/cb",
    "https://onlyfakeai.ru@evil.example/cb",
    "https://cdn.onlyfakeai.ru/",
    "https://ops.onlyfakeai.ru/",
    "//evil.example/cb",
    "http://onlyfakeai.ru/",
    "https://onlyfakeai.ru/#/evil",
    "https://onlyfakeai.ru/?x=1",
]
for rt in variants:
    q = urllib.parse.quote(rt, safe="")
    st, hd, b = req("GET", SUPA + f"/auth/v1/verify?token=definitelybogus123&type=recovery&redirect_to={q}")
    show("verify rt=" + rt, st, hd, b, 200)
    time.sleep(0.4)

print("\n===== 3. oauth server endpoints (new supabase feature) =====")
for m, p in [
    ("GET", "/auth/v1/.well-known/oauth-authorization-server"),
    ("GET", "/.well-known/oauth-authorization-server"),
    ("GET", "/auth/v1/oauth/authorize"),
    ("GET", "/auth/v1/oauth/authorize?client_id=test&response_type=code&redirect_uri=https%3A%2F%2Fevil.example%2Fcb&scope=openid"),
    ("GET", "/auth/v1/oauth/clients"),
    ("POST", "/auth/v1/oauth/clients"),
    ("GET", "/auth/v1/oauth/token"),
    ("POST", "/auth/v1/oauth/token"),
    ("GET", "/auth/v1/oauth/consent"),
    ("GET", "/auth/v1/oauth/userinfo"),
]:
    st, hd, b = req(m, SUPA + p, body={} if m == "POST" else None)
    show(f"{m} {p}", st, hd, b, 260)
    time.sleep(0.35)

print("\n===== 4. SCIM / SSO / admin / invite / residual =====")
for m, p, body in [
    ("GET", "/auth/v1/scim/v2/Users", None),
    ("GET", "/auth/v1/sso/saml/metadata", None),
    ("POST", "/auth/v1/invite", {"email": "<probe>@dropmail.me"}),
    ("GET", "/auth/v1/admin/users", None),
    ("GET", "/auth/v1/admin/factors", None),
    ("GET", "/auth/v1/factors", None),
    ("GET", "/auth/v1/user", None),
    ("PUT", "/auth/v1/user", {"email": "<probe>@dropmail.me"}),
    ("GET", "/auth/v1/authorize?provider=email", None),
    ("POST", "/auth/v1/magiclink", {"email": "<probe>@dropmail.me"}),
    ("POST", "/auth/v1/otp", {"email": "<probe>@dropmail.me", "create_user": False}),
    ("POST", "/auth/v1/recover", {"email": "<probe>@dropmail.me"}),
]:
    st, hd, b = req(m, SUPA + p, body=body)
    show(f"{m} {p}", st, hd, b, 260)
    time.sleep(0.5)
