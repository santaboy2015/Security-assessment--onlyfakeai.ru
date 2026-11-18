import ssl, json, urllib.request, urllib.error, time

BASE = "https://cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

def token_grant(email, password):
    h = {
        "User-Agent": "Mozilla/5.0",
        "apikey": KEY,
        "Content-Type": "application/json;charset=UTF-8",
    }
    body = json.dumps({"email": email, "password": password}).encode()
    r = urllib.request.Request(BASE + "/auth/v1/token?grant_type=password", data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

# my own throwaway account - hammer wrong passwords, watch for 429
email = "rat4080probeewb44z@gmail.com"
print("=== rate limit probe: 12 rapid wrong-password attempts ===")
for i in range(12):
    st, txt = token_grant(email, f"wrongpass{i}X!")
    short = txt[:120].replace("\n", " ")
    print(f"{i:02d} -> {st} {short}")
    if st == 429:
        print("429 seen - throttled. window:", i)
        break
