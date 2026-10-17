import hashlib, hmac, time
from app.core import SECRET
def mint_pass(d=30, ts=None):
  e = str(int(ts or time.time())+d*86400)
  return f'asr_pass_{e}_{hmac.new(SECRET.encode(),e.encode(),hashlib.sha256).hexdigest()[:20]}'
import base64, json, os, urllib.parse as P, urllib.request as U
from app.core import sign_data

def _t(n, d, pr, r): return {"name":n,"title":n,"description":d,"annotations":{"readOnlyHint":False,"openWorldHint":True},"inputSchema":{"type":"object","properties":{k:{"type":"string","description":f"{k} for {n}"} for k in pr},"required":r,"additionalProperties":False}}
TOOLS = [
  _t("assay_preflight","Pre-flight check (liveness, MCP schema hash, rug-pull drift, tool poisoning) before paying an agent.",["target","expected_tools_hash"],["target"]),
  _t("assay_probe","Probe a live MCP/A2A/x402 endpoint and record observation.",["target"],["target"])
]

def agent_card(h: str) -> dict:
  c = {"name":"Assay","version":"0.1.0","protocol":"A2A/1.0","url":f"https://{h}","icon":f"https://{h}/logo.svg","mcp":f"https://{h}/mcp","skills":["preflight","probe","rugpull_ledger"]}
  c["signature"] = sign_data(c, "asr_sig_"); return c

def stripe_checkout(usd=19.0) -> tuple:
  sk = (os.getenv("ASSAY_STRIPE_SECRET_KEY") or os.getenv("AGENTDIET_STRIPE_SECRET_KEY") or "").strip()
  if not sk: return 503, {"error":"Stripe key missing"}
  k = "line_items[0][price_data]"
  d = P.urlencode({"mode":"payment","success_url":"https://assay-207908449630.us-central1.run.app/v1/billing/stripe-success?session_id={CHECKOUT_SESSION_ID}","cancel_url":"https://assay-207908449630.us-central1.run.app",f"{k}[currency]":"usd",f"{k}[unit_amount]":str(int(float(usd)*100)),f"{k}[product_data][name]":"Assay Pass","line_items[0][quantity]":"1"}).encode()
  au = base64.b64encode(f"{sk}:".encode()).decode()
  try:
    with U.urlopen(U.Request("https://api.stripe.com/v1/checkout/sessions", data=d, headers={"Authorization":f"Basic {au}"}), timeout=8) as r:
      s = json.loads(r.read().decode()); return 200, {"ok":True,"livemode":s.get("livemode"),"checkout_url":s.get("url")}
  except Exception as e: return 502, {"error":str(e)}

def stripe_verify(sid: str) -> tuple:
  sk = (os.getenv('ASSAY_STRIPE_SECRET_KEY') or os.getenv('AGENTDIET_STRIPE_SECRET_KEY') or '').strip()
  if not sk or not sid.startswith('cs_'): return 400, {'error':'Invalid session_id'}
  au = base64.b64encode(f'{sk}:'.encode()).decode()
  try:
    with U.urlopen(U.Request(f'https://api.stripe.com/v1/checkout/sessions/{P.quote(sid)}', headers={'Authorization':f'Basic {au}'}), timeout=8) as r:
      s = json.loads(r.read().decode()); return (200, {'ok':True,'api_key':mint_pass(30, s.get('created'))}) if s.get('payment_status')=='paid' else (402, {'error':'Unpaid'})
  except Exception as e: return 400, {'error':str(e)}

TOOLS.append(_t("assay_verify_delivery","Verify post-payment A2A/x402 delivery and mint signed SLA receipt.",["target","tx_hash","status_code"],*([["target"]] if _t.__code__.co_argcount>3 else [])))

from app.tdqs import TOOLS
