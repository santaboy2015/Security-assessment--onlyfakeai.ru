import ssl, json, urllib.request, urllib.error

BASE = "https://ops.onlyfakeai.ru"
ctx = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0"}

def req(method, path, token=None, body=None, extra=None):
    url = BASE + path
    h = dict(UA)
    if token: h["Authorization"] = f"Bearer {token}"
    if body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    else:
        data = None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

paths = [
    ("GET", "/api/auth/verify"),
    ("GET", "/api/admin-users"),
    ("GET", "/api/profiles?page=1&pageSize=10"),
    ("GET", "/api/jobs?page=1&pageSize=10"),
    ("GET", "/api/jobs/stats"),
    ("GET", "/api/analytics?timeframe=day"),
    ("GET", "/api/analytics/admin-activity"),
    ("GET", "/api/admin-api-keys?adminUserId=1"),
    ("GET", "/login.html"),
    ("GET", "/login"),
    ("GET", "/api/auth/login"),
    ("GET", "/health"),
    ("GET", "/api/health"),
]

for m, p in paths:
    st, body = req(m, p)
    print(f"\n=== {m} {p} -> {st}")
    print(body[:400].replace("\n", " ")[:400])
