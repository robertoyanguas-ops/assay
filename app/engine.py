import json, time
from app.core import hash_tools, scan_poison, sign_data
from app.prober import _fetch_signals

def probe_target(store, raw: str, sync=True) -> dict:
  b, st, ms, card, ms_s, m_ms, tools = _fetch_signals(raw)
  th, poison = (hash_tools(tools) if tools else ""), scan_poison(tools)
  ok, now = int((200<=st<500) or st==402 or bool(tools) or bool(card)), int(time.time())
  with store.lock, store._c() as c:
    p = c.execute("SELECT * FROM endpoints WHERE target=?", (b,)).fetchone()
    pr, rugs = (int(p["probes"]) if p else 0) + 1, (int(p["rug_pulls"]) if p else 0)
    drift = int(bool(p and p["tools_hash"] and th and p["tools_hash"] != th)); rugs += drift
    sc = (35 if ok and ms<900 else (20 if ok else 0)) + (25 if tools else 0) + (10 if card else 0) + max(0, 30 - rugs*20 - len(poison)*25)
    gr = "F" if not ok or poison else ("A+" if sc>=92 else "A" if sc>=85 else "B" if sc>=70 else "C" if sc>=55 else "D")
    dos = {"target":b,"name":b.split("//")[-1],"grade":gr,"score":sc,"confidence":"HIGH" if pr>=10 else ("MEDIUM" if pr>=3 else "LOW"),"probes":pr,"latency_ms":m_ms if tools else ms,"http_status":st,"mcp_tools":len(tools),"tools_hash":th,"a2a_card":bool(card),"x402_gated":st==402 or ms_s==402,"rug_pulls":rugs,"poison_flags":poison,"last_seen":now}
    dos["receipt"] = sign_data({"target":b,"grade":gr,"score":sc,"tools_hash":th,"ts":now})
    c.execute("INSERT OR REPLACE INTO endpoints VALUES(?,?,?,?,?,?)", (b, sc, pr, rugs, th, json.dumps(dos)))
    c.execute("INSERT INTO observations(target,ts,drift,note) VALUES(?,?,?,?)", (b, now, drift, f"HTTP {st} tools={len(tools)}"))
  if sync: store.sync()
  return dos
