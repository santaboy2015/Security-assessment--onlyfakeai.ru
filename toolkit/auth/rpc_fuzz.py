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

print("=== RPC discovery (no args -> signature errors tell us params) ===")
rpc_names = [
    "get_total_counts", "grant_plan_credits", "grant_credits",
    "deduct_credits", "deduct_job_credits", "deduct_plan_credits",
    "deduct_attempt", "add_credits", "admin_grant_credits",
    "grant_admin", "make_admin", "is_admin", "get_admin_stats",
    "assign_plan", "set_plan", "update_plan",
    "check_plan_credits", "use_credits", "spend_credits",
]
for name in rpc_names:
    st, txt = req("POST", f"/rest/v1/rpc/{name}")
    print(f"\n--- rpc/{name} -> {st}")
    print(txt[:300].replace("\n", " ")[:300])

print("\n=== bucket names ===")
for b in ["photos", "avatars", "previews", "documents", "generated",
          "uploads", "images", "files", "public", "watermarked",
          "processed", "input", "output", "profile-photos"]:
    st, txt = req("GET", f"/storage/v1/bucket/{b}")
    print(f"bucket/{b} -> {st} {txt[:120]}")

print("\n=== storage list all ===")
st, txt = req("GET", "/storage/v1/bucket?limit=100")
print(st, txt[:400])
