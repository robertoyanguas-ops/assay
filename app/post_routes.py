import time
from app.core import SECRET
from app.billing import claim_x402
_CW = [0]
import json
from app.engine import probe_target
from app.mcp_api import TOOLS, stripe_checkout
from app.service import crawl_seeds, preflight

def handle_post(S, p: str, b: dict, k: str, ip: str) -> tuple:
  if p == "/v1/billing/stripe-checkout": return stripe_checkout(b.get("amount_usd", 19.0))
  if p == "/v1/billing/claim-x402": return claim_x402(S, b.get("tx_hash",""))
  if p == "/v1/crawl":
    if k != SECRET and time.time()-_CW[0] < 45: return 429, {"error":"Crawl cooldown"}
    _CW[0] = time.time(); return 200, crawl_seeds(S, min(int(b.get("limit", 16)), 45))
  if p == "/mcp":
    m, i, pr = b.get("method"), b.get("id"), b.get("params") or {}
    if m == "initialize": return 200, {"jsonrpc":"2.0","id":i,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"assay","version":"0.4.2"}}}
    if m == "tools/list": return 200, {"jsonrpc":"2.0","id":i,"result":{"tools":TOOLS}}
    if m == "tools/call":
      ok, au = S.auth(k, ip)
      if not ok: return 402, au
      a = pr.get("arguments") or {}
      try:
        res = preflight(S, a) if pr.get("name")=="assay_preflight" else probe_target(S, a.get("target",""))
        return 200, {"jsonrpc":"2.0","id":i,"result":{"content":[{"type":"text","text":json.dumps(res)}],"isError":False}}
      except Exception as e:
        return 200, {"jsonrpc":"2.0","id":i,"result":{"content":[{"type":"text","text":str(e)}],"isError":True}}
    return 200, {"jsonrpc":"2.0","id":i,"result":{"resources":[],"prompts":[],"events":[]}}
  if p in ("/v1/preflight", "/v1/probe"):
    ok, au = S.auth(k, ip)
    if not ok: return 402, au
    try: return 200, (preflight(S, b) if p=="/v1/preflight" else probe_target(S, b.get("target","")))
    except ValueError as e: return 400, {"error":str(e)}
  return 404, {"error":"not found"}
