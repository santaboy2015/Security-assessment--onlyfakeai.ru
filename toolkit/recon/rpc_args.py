import ssl, json, urllib.request, urllib.error

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()
tok = json.load(open("token.txt"))["access_token"]
uid = "23bd19c0-2588-4354-8ef1-fdc07ce1fd8c"

def rpc(name, body, token=tok):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY,
         "Authorization": f"Bearer {token}",
         "Content-Type": "application/json;charset=UTF-8"}
    data = json.dumps(body).encode()
    r = urllib.request.Request(f"{BASE}/rest/v1/rpc/{name}", data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

plan = "pro"
candidates = [
    {"p_user_id": uid, "p_plan": plan},
    {"p_target_user_id": uid, "p_plan": plan},
    {"p_target_id": uid, "p_plan": plan},
    {"p_user_id": uid, "p_plan_name": plan},
    {"p_user_id": uid, "p_plan": plan, "p_credits": 150},
    {"user_id": uid, "plan": plan},
    {"target_user_id": uid, "plan": plan},
    {"email": "rat4080probeewb44z@gmail.com", "plan": plan},
    {"p_email": "rat4080probeewb44z@gmail.com", "p_plan": plan},
    {"user_id": uid, "plan": plan, "credits": 150},
    {"p_user_id": uid, "p_plan": plan, "p_credits": 150},
]
for body in candidates:
    st, txt = rpc("grant_plan_credits", body)
    flag = "  <<<<<<<<<<<<<<< NOT 404!" if st != 404 else ""
    print(f"grant_plan_credits({json.dumps(body)[:90]}...) -> {st}{flag}")
    if st != 404:
        print("   ", txt[:300].replace("\n", " "))
