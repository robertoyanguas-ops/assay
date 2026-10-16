import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from app.post_routes import handle_post
from app.routes import handle_get
from app.store import AssayStore

S = AssayStore()

class H(BaseHTTPRequestHandler):
  def log_message(self, *a): pass
  def _ip(self): return (self.headers.get("X-Forwarded-For") or "").split(",")[-1].strip() or self.client_address[0]
  def _k(self, b):
    q, a = parse_qs(urlparse(self.path).query), (((b.get("params") or {}).get("arguments") or {}) if isinstance(b,dict) else {})
    h = self.headers.get
    return (h("X-Assay-Key") or h("X-Payment-Proof") or (h("Authorization") or "").replace("Bearer ","") or (q.get("assayApiKey") or q.get("api_key") or [""])[0] or (b.get("api_key") if isinstance(b,dict) else "") or a.get("api_key") or h("X-Agent-Id") or "").strip()
  def _j(self, c, d, ct="application/json"):
    raw = d.encode() if isinstance(d, str) else json.dumps(d).encode()
    self.send_response(c); self.send_header("Content-Type", ct); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(raw)
  def do_GET(self):
    u = urlparse(self.path); self._j(*handle_get(S, u.path, parse_qs(u.query), self.headers.get("Host","localhost")))
  def do_POST(self):
    n = min(int(self.headers.get("Content-Length") or 0), 65536)
    try: b = json.loads(self.rfile.read(n).decode() or "{}") if n else {}
    except Exception: return self._j(400, {"error":"Invalid JSON"})
    c, d = handle_post(S, urlparse(self.path).path, b, self._k(b), self._ip()); self._j(c, d)

if __name__ == "__main__": ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080"))), H).serve_forever()
