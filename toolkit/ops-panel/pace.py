import ssl, json, urllib.request, urllib.error, time

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def try_login(email, password):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Content-Type": "application/json;charset=UTF-8",
    }
    body = json.dumps({"email": email, "password": password}).encode()
    r = urllib.request.Request(BASE + "/auth/v1/token?grant_type=password", data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, ""
    except urllib.error.HTTPError as e:
        return e.code, ""

em = "rat4080probeewb44z@gmail.com"
print("=== 12 attempts at 2.5s spacing ===")
for i in range(12):
    st, _ = try_login(em, f"probeWrong{i}!")
    print(i, st, time.strftime("%H:%M:%S"))
    if st == 429:
        print("  backoff 20s")
        time.sleep(20)
    else:
        time.sleep(2.5)
