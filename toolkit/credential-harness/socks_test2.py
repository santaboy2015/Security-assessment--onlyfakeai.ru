import socket, ssl, json

HOST = "cdn.onlyfakeai.ru"

def socks_connect(proxy=("127.0.0.1", 9050), timeout=30):
    s = socket.create_connection(proxy, timeout=timeout)
    s.sendall(b"\x05\x01\x00")
    r = s.recv(2)
    if r != b"\x05\x00":
        raise RuntimeError(f"auth rejected: {r!r}")
    req = b"\x05\x01\x00\x03" + bytes([len(HOST)]) + HOST.encode() + (443).to_bytes(2, "big")
    s.sendall(req)
    r = s.recv(4)
    if len(r) < 4 or r[1] != 0:
        raise RuntimeError(f"connect failed: {r!r}")
    atyp = r[3]
    if atyp == 1:
        s.recv(6)
    elif atyp == 3:
        ln = s.recv(1)[0]
        s.recv(ln + 2)
    elif atyp == 4:
        s.recv(18)
    return s

for attempt in range(3):
    try:
        s = socks_connect()
        ctx = ssl.create_default_context()
        ss = ctx.wrap_socket(s, server_hostname=HOST)
        body = json.dumps({"email": "rat4080probeewb44z@gmail.com", "password": "wrongPassX1!"}).encode()
        raw = (f"POST /auth/v1/token?grant_type=password HTTP/1.1\r\nHost: {HOST}\r\n"
               "Content-Type: application/json\r\n"
               "apikey: <publishable-key>\r\n"
               "Accept: application/json\r\n"
               f"User-Agent: Mozilla/5.0\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode() + body
        ss.sendall(raw)
        buf = b""
        while True:
            chunk = ss.recv(8192)
            if not chunk:
                break
            buf += chunk
        ss.close()
        status = buf.split(b"\r\n", 1)[0].decode()
        body_txt = buf.split(b"\r\n\r\n", 1)[-1].decode("utf-8", "ignore")
        print(f"attempt {attempt}: {status}")
        print("body:", body_txt[:400])
        break
    except Exception as e:
        print(f"attempt {attempt} ERR: {str(e)[:120]}")
