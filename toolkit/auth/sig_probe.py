import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, extra=None, raw=None):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "X-Client-Info": "supabase-js/2.49.4",
    }
    if extra:
        h.update(extra)
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

print("=== signature discovery via empty-object calls ===")
for fn in ["grant_plan_credits", "deduct_credits", "is_admin", "get_total_counts"]:
    for payload in [None, {}, {"p": None}]:
        st, txt = req("POST", f"/rest/v1/rpc/{fn}", body=payload)
        print(f"\n--- rpc/{fn} body={payload} -> {st}")
        print(txt[:500].replace("\n", " ")[:500])

print("\n=== auth surface ===")
st, txt = req("GET", "/auth/v1/settings")
print("settings", st, txt[:400])
st, txt = req("GET", "/auth/v1/user")
print("user(anon)", st, txt[:200])

print("\n=== profiles schema peek via 406/errors ===")
for path in [
    "/rest/v1/profiles?select=id,email&limit=1",
    "/rest/v1/profiles?select=*&limit=1",
    "/rest/v1/jobs?select=*&limit=1",
]:
    st, txt = req("GET", path)
    print(path, "->", st, txt[:300].replace("\n", " ")[:300])
