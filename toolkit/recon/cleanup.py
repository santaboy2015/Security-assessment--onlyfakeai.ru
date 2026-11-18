import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY,
         "Authorization": f"Bearer {token or KEY}",
         "Content-Type": "application/json;charset=UTF-8",
         "Prefer": "return=representation"}
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

for tf in ["token.txt", "token_sup.txt"]:
    sess = json.load(open(tf))
    tok = sess["access_token"]
    uid = sess["user"]["id"]
    st, txt = req("PATCH", f"/rest/v1/profiles?user_id=eq.{uid}",
                  body={"secret_key": None, "banned_by": None, "ban_reason": None},
                  token=tok)
    print(tf, uid, "->", st)
    print("   ", txt[:250])
