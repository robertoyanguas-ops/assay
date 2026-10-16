import json, time, urllib.error as E, urllib.request as U
from app.core import check_safe_url
class _SR(U.HTTPRedirectHandler):
  def redirect_request(self,q,f,c,m,h,u): check_safe_url(u); return super().redirect_request(q,f,c,m,h,u)
_OP = U.build_opener(_SR())

def _req(url: str, data=None, to=6):
  t0 = time.time()
  q = U.Request(url, data=data, headers={"User-Agent":"Assay-Observatory/0.4 (+https://assay-207908449630.us-central1.run.app)","Referer":f"https://assay-207908449630.us-central1.run.app/?inspect={url}","Content-Type":"application/json","Accept":"application/json, text/event-stream"})
  try:
    with _OP.open(q, timeout=to) as r: return r.status, r.read().decode("utf-8","ignore"), round((time.time()-t0)*1000,1)
  except E.HTTPError as e: return e.code, e.read().decode("utf-8","ignore"), round((time.time()-t0)*1000,1)
  except Exception: return 0, "", round((time.time()-t0)*1000,1)

def _fetch_signals(raw: str):
  t = check_safe_url(raw); b = t[:-4] if t.endswith("/mcp") else t
  st, _, ms = _req(b); cs, cb, _ = _req(f"{b}/.well-known/agent-card.json")
  card = json.loads(cb) if cs==200 and cb.strip().startswith("{") else {}
  ms_s, mb, m_ms = _req(f"{b}/mcp", json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}).encode())
  for ln in (mb.splitlines() if "data:" in mb else []):
    if ln.startswith("data:"): mb = ln[5:].strip(); break
  mcp = json.loads(mb) if mb.strip().startswith("{") else {}
  return b, st, ms, card, ms_s, m_ms, (mcp.get("result") or {}).get("tools") or []

def badge_svg(gr: str, sc: int, r: int) -> str:
  c = "#10b981" if gr[:1]=="A" else ("#f59e0b" if gr in ("B","C") else "#ef4444")
  return f'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="20"><rect width="45" height="20" fill="#111"/><rect x="45" width="115" height="20" fill="{c}"/><g fill="#fff" font-size="11"><text x="5" y="14">Assay</text><text x="50" y="14">{gr} ({sc}) R:{r}</text></g></svg>'
