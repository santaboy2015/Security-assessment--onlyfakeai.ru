import ssl, json, urllib.request, urllib.error, base64

ctx = ssl.create_default_context()
KEY = "<publishable-key>"

def req(method, url, body=None, token=None, extra=None, key=None):
    h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0",
        "apikey": key or KEY,
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    if body is not None:
        h["Content-Type"] = "application/json"
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()

tok = json.load(open("token.txt"))["access_token"]

print("=== ops admin-users POST with regular user token (role check test) ===")
st, hd, b = req("POST", "https://ops.onlyfakeai.ru/api/admin-users",
                body={"email": "<probe>@dropmail.me", "password": "Xr9!kQ2#mZ7$pLw1"},
                token=tok)
print(st, b.decode("utf-8", "ignore")[:500])

print("\n=== ops admin-api-keys POST with regular token ===")
st, hd, b = req("POST", "https://ops.onlyfakeai.ru/api/admin-api-keys",
                body={"adminUserId": "test"}, token=tok)
print(st, b.decode("utf-8", "ignore")[:300])

print("\n=== photos bucket full listing via exact report format ===")
body = {"prefix": "", "limit": 100, "offset": 0,
        "sortBy": {"column": "name", "order": "asc"}}
st, hd, b = req("POST", "https://cdn.onlyfakeai.ru/storage/v1/object/list/photos", body=body)
print(st, len(b))
if st == 200:
    data = json.loads(b)
    print("entries:", len(data))
    names = [e["name"] for e in data if e["name"] != ".emptyFolderPlaceholder"]
    if names:
        print("first:", names[0], "last:", names[-1])
        ts = [int(n.split("_")[0]) for n in names if n.split("_")[0].isdigit()]
        if ts:
            print("min ts:", min(ts), "max ts:", max(ts))
else:
    print(b.decode("utf-8", "ignore")[:400])
