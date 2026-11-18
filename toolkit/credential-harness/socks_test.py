import socket, ssl, json, time

HOST = "cdn.onlyfakeai.ru"

def socks_connect(proxy=("127.0.0.1", 9050), auth=None, timeout=25):
    s = socket.create_connection(proxy, timeout=timeout)
    s.sendall(b"\x05\x01\x00")  # no-auth
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
        s.recv(4 + 2)
    elif atyp == 3:
        ln = s.recv(1)[0]
        s.recv(ln + 2)
    elif atyp == 4:
        s.recv(16 + 2)
    return s

s = socks_connect()
ctx = ssl.create_default_context()
ss = ctx.wrap_socket(s, server_hostname=HOST)
body = json.dumps({"email": "rat4080probeewb44z@gmail.com", "password": "wrongPassX1!"}).encode()
raw = (f"POST /auth/v1/token?grant_type=password HTTP/1.1\r\nHost: {HOST}\r\n"
       "Content-Type: application/json\r\n"
       "apikey: <publishable-key>\r\n"
       f"User-Agent: Mozilla/5.0\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n").encode() + body
ss.sendall(raw)
buf = b""
while True:
    chunk = ss.recv(4096)
    if not chunk:
        break
    buf += chunk
head = buf.split(b"\r\n\r\n")[0].decode()
print(head.split("\r\n")[0])
print(buf[:600].decode("utf-8", "ignore")[-300:])
ss.close()
