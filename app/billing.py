import json, urllib.request as U
from app.mcp_api import mint_pass

LOGO_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#090d16"/><path d="M32 8L51 16V32C51 45 42 54 32 58C22 54 13 45 13 32V16Z" fill="#0b1324" stroke="#38bdf8" stroke-width="3"/><path d="M23 32L29 38L41 24" fill="none" stroke="#10b981" stroke-width="5"/><circle cx="32" cy="19" r="2.5" fill="#f59e0b"/></svg>'

def _rpc(u, m, p):
  q = U.Request(u, data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(), headers={"Content-Type":"application/json","User-Agent":"Assay/0.4"})
  with U.urlopen(q, timeout=8) as r: return json.loads(r.read().decode()).get("result") or {}

def claim_x402(S, tx: str) -> tuple:
  tx = (tx or "").strip()
  if len(tx) < 32: return 400, {"error":"Invalid tx_hash"}
  with S.lock, S._c() as c:
    if c.execute("SELECT 1 FROM wallets WHERE id=?", (f"tx_{tx}",)).fetchone(): return 409, {"error":"Already claimed"}
  try:
    if tx.startswith("0x") and len(tx)==66:
      r = _rpc("https://mainnet.base.org", "eth_getTransactionReceipt", [tx])
      ok = r.get("status")=="0x1" and any(l.get("address","").lower()=="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913" and len(l.get("topics") or [])>=3 and l["topics"][2].lower().endswith("ec5275d5b03bc390fca63d902d0b2d0db2eb5573") and int(l.get("data") or "0x0",16)>=5000 for l in (r.get("logs") or []))
    else:
      r = _rpc("https://api.mainnet-beta.solana.com", "getTransaction", [tx, {"encoding":"jsonParsed","maxSupportedTransactionVersion":0}])
      m = r.get("meta") or {}; sb = lambda a: sum(int((x.get("uiTokenAmount") or {}).get("amount") or 0) for x in (a or []) if x.get("owner")=="Dq7fuKy4tGsKeQcDh4oVFjTTkbmfQpS1LTrnFxqd339L" and x.get("mint")=="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
      ok = bool(r) and m.get("err") is None and (sb(m.get("postTokenBalances"))-sb(m.get("preTokenBalances")))>=5000
  except Exception as e: return 502, {"error":str(e)}
  if not ok: return 402, {"error":"Unverified payment"}
  with S.lock, S._c() as c: c.execute("INSERT INTO wallets VALUES(?,1)", (f"tx_{tx}",))
  S.sync(); return 200, {"ok":True,"api_key":mint_pass(30)}
