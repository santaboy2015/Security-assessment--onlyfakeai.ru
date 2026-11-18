import ssl, json, urllib.request, urllib.error

ctx = ssl.create_default_context()

def req(method, url, body=None, token=None, extra=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    if body is not None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, str(e)

B = "https://onlyfakeai.ru"
paths = [
    ("GET", "/api/supabase/health"),
    ("GET", "/api/supabase/rest/v1/"),
    ("GET", "/api/supabase/rest/v1/profiles?select=*&limit=1"),
    ("GET", "/api/supabase/auth/v1/health"),
    ("GET", "/api/supabase/auth/v1/settings"),
    ("POST", "/api/supabase/rest/v1/rpc/get_total_counts"),
    ("GET", "/api/supabase"),
]
for m, p in paths:
    st, hd, txt = req(m, B + p)
    print(f"{m} {p} -> {st}")
    print("   ", txt[:350].replace("\n", " ")[:350])
