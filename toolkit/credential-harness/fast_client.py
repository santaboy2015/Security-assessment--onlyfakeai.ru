#!/usr/bin/env python3
# Minimal keep-alive HTTPS client for CDN probing (stdlib only; no requests dependency).
import http.client, json, time

class FastHTTP:
    def __init__(self, host, apikey, ua=None, extra_headers=None):
        self.host = host
        self.apikey = apikey
        self.headers = {
            "apikey": apikey,
            "User-Agent": ua or ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                 "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://onlyfakeai.ru",
            "Referer": "https://onlyfakeai.ru/",
        }
        if extra_headers:
            self.headers.update(extra_headers)
        self.conn = None
        self.requests = 0
        self.errors = 0

    def _connect(self):
        self.conn = http.client.HTTPSConnection(self.host, 443, timeout=15)

    def request(self, method, path, body=None, headers=None, retries=2):
        h = dict(self.headers)
        if headers:
            h.update(headers)
        data = None
        if body is not None:
            if isinstance(body, (dict, list)):
                data = json.dumps(body).encode()
                h.setdefault("Content-Type", "application/json")
            elif isinstance(body, str):
                data = body.encode()
            else:
                data = body
        last = ("ERR", "")
        for _ in range(retries + 1):
            try:
                if self.conn is None:
                    self._connect()
                self.conn.request(method, path, body=data, headers=h)
                resp = self.conn.getresponse()
                raw = resp.read()
                self.requests += 1
                return resp.status, raw.decode("utf-8", "replace"), dict(resp.getheaders())
            except Exception as e:
                last = ("ERR", repr(e))
                self.errors += 1
                try:
                    if self.conn: self.conn.close()
                except Exception:
                    pass
                self.conn = None
                time.sleep(0.6)
        return last[0], last[1], {}
