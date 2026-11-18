import ssl, urllib.request, urllib.error, urllib.parse, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
BASE = "https://onlyfakeai.ru"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}

def get(url, extra=None):
    h = dict(UA)
    if extra: h.update(extra)
    r = urllib.request.Request(url, headers=h, method="GET")
    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener(NoRedir)
    try:
        with opener.open(r, timeout=25) as resp:
            body = resp.read(4096).decode("utf-8", "ignore")
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(4096).decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, str(e)

evil = "https://evil.example/pwn"
paths = ["/", "/login", "/en/login", "/en", "/generator", "/auth/callback", "/auth/confirm",
         "/api/auth/telegram-oidc/callback", "/api/auth/telegram-oidc/start", "/api/auth/login",
         "/api/auth/callback"]
params = ["next", "redirect", "redirect_url", "redirectTo", "redirect_to", "returnTo", "return",
          "return_url", "continue", "url", "to", "target", "r", "callback", "callbackUrl", "location"]
hits = []
for p in paths:
    for q in params:
        u = BASE + p + ("&" if "?" in p else "?") + q + "=" + urllib.parse.quote(evil, safe="")
        st, hd, body = get(u)
        loc = hd.get("Location") or hd.get("location") or ""
        interesting = (300 <= st < 400 and loc) or "evil.example" in body[:4000]
        if interesting:
            hits.append((p, q, st, loc[:160]))
            print(f"[HIT] {p} ?{q} -> {st} loc={loc[:160]}")
        time.sleep(0.25)
print("done hits:", len(hits))

# also check redirects on the home page for locale logic + trailing-slash variants
for u in [BASE + "/?locale=evil", BASE + "/en?locale=evil", BASE + "/../evil", BASE + "//evil.example/"]:
    st, hd, body = get(u)
    loc = hd.get("Location") or ""
    print(f"[home] {u} -> {st} loc={loc[:140]}")
    time.sleep(0.3)
