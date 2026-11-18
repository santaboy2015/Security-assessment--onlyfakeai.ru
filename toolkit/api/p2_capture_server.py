import http.server, socketserver, time, sys
LOG = r"<WORKSPACE>\p2_capture.log"

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.time():.2f} GET {self.path} referer={self.headers.get('Referer')} ua={self.headers.get('User-Agent')}\n")
        body = b"ok"
        self.send_response(200); self.send_header("Content-Type", "text/plain"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", 8899), H) as httpd:
    print("capture server on 8899", flush=True)
    httpd.serve_forever()
