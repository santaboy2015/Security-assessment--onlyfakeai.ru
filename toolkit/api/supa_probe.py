import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, extra=None):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "X-Client-Info": "supabase-js/2.49.4",
    }
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, str(e)

def show(method, path, body=None, extra=None):
    st, hd, txt = req(method, path, body, extra)
    print(f"\n=== {method} {path} -> {st}")
    print(txt[:600].replace("\n", " ")[:600])
    return st, txt

# auth/config endpoints
show("GET", "/auth/v1/health")
show("GET", "/rest/v1/")
show("GET", "/rest/v1/?select=*")
show("GET", "/rest/v1/profiles?select=*&limit=2")
show("GET", "/rest/v1/jobs?select=*&limit=2")
show("GET", "/rest/v1/admins?select=*&limit=5")
show("GET", "/rest/v1/admin_activity?select=*&limit=2")
show("POST", "/rest/v1/rpc/get_total_counts")
show("GET", "/storage/v1/bucket")
show("GET", "/storage/v1/bucket/photos")
