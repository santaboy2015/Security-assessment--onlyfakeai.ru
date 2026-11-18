import ssl, json, urllib.request, urllib.error, socket, time

ctx = ssl.create_default_context()
OPS = "https://ops.onlyfakeai.ru/api/auth/login"

def direct_login(email, pw):
    h = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    body = json.dumps({"email": email, "password": pw}).encode()
    r = urllib.request.Request(OPS, data=body, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=25, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, {}, str(e)

def tor_login(email, pw, port=9050):
    HOST = "ops.onlyfakeai.ru"
    s = socket.create_connection(("127.0.0.1", port), timeout=30)
    s.sendall(b"\x05\x01\x00")
    if s.recv(2) != b"\x05\x00":
        raise RuntimeError("socks")
    req = b"\x05\x01\x00\x03" + bytes([len(HOST)]) + HOST.encode() + (443).to_bytes(2, "big")
    s.sendall(req)
    r = s.recv(4)
    atyp = r[3]
    if atyp == 1:
        s.recv(6)
    elif atyp == 3:
        ln = s.recv(1)[0]
        s.recv(ln + 2)
    elif atyp == 4:
        s.recv(18)
    ss = ctx.wrap_socket(s, server_hostname=HOST)
    body = json.dumps({"email": email, "password": pw}).encode()
    raw = (f"POST /api/auth/login HTTP/1.1\r\nHost: {HOST}\r\n"
           "Content-Type: application/json\r\n"
           f"User-Agent: Mozilla/5.0\r\nContent-Length: {len(body)}\r\n"
           "Connection: close\r\n\r\n").encode() + body
    ss.sendall(raw)
    buf = b""
    while True:
        chunk = ss.recv(8192)
        if not chunk:
            break
        buf += chunk
    ss.close()
    head, _, rest = buf.partition(b"\r\n\r\n")
    status = int(head.split(b"\r\n", 1)[0].split()[1])
    hdrs = {}
    for line in head.split(b"\r\n")[1:]:
        if b":" in line:
            k, v = line.split(b":", 1)
            hdrs[k.strip().lower()] = v.strip()
    return status, hdrs, rest.decode("utf-8", "ignore")

probe = "limiter-b-" + str(int(time.time()) % 100000) + "@example.com"
print("=== tor attempt via kali tor 9050 (fresh IP) ===")
try:
    st2, hd2, b2 = tor_login(probe, "ProbeX9!")
    print(st2, "retry-after:", hd2.get("retry-after"), b2[:160])
except Exception as e:
    print("tor err:", str(e)[:150])

print("\n=== direct attempt right after (same window) ===")
st, hd, b = direct_login(probe, "ProbeX9!")
print(st, "retry-after:", hd.get("retry-after"), b[:160])

if st in (400, 401):
    print("\n>>> DIRECT STILL WORKS after tor attempt -> per-IP or counter not global")
else:
    print("\n>>> direct locked -> limiter is global")
