from concurrent.futures import ThreadPoolExecutor
import json
from app.engine import probe_target
from app.prober import _req

SEEDS = [f"https://{s}-72343955726.us-central1.run.app" for s in ("agentdiet","x402-broker","prompt-guard","json-repair","serp-extract","llms-generator","github-audit","company-enrich","sec-intel","domain-osint","email-verify","arxiv-digest","shopify-spy","x402-audit","onchain-risk","token-intel")]

def preflight(store, b: dict) -> dict:
  d = probe_target(store, b.get("target", ""))
  exp = (b.get("expected_tools_hash") or "").strip()
  if d["poison_flags"]: v, r = "deny", "Tool poisoning detected"
  elif d["rug_pulls"] > 0 or (exp and d["tools_hash"] != exp): v, r = "deny", "MCP schema drift (rug-pull) detected"
  elif d["grade"] == "F": v, r = "deny", "Unreachable or failed conformance"
  elif d["score"] < 70 or d["confidence"] == "LOW": v, r = "warn", "Live endpoint verified; history building"
  else: v, r = "allow", "Verified live endpoint with clean schema hash"
  return {"verdict": v, "reason": r, "dossier": d, "receipt": d["receipt"]}

def crawl_seeds(store, limit=6) -> dict:
  urls = list(SEEDS)
  for reg in ("https://registry.modelcontextprotocol.io/v0/servers?limit=80", "https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources?limit=80"):
    st, body, _ = _req(reg, to=12)
    if st == 200 and body.strip().startswith("{"):
      d = json.loads(body)
      for s in (d.get("servers") or d.get("resources") or []):
        u = s.get("resource") or s.get("url") or ((s.get("server", s).get("remotes") or [{}])[0].get("url", ""))
        if isinstance(u, str) and u.startswith("https://") and u not in urls: urls.append(u)
  with store._c() as c: sn = {r['target']:r['probes'] for r in c.execute('SELECT target,probes FROM endpoints')}
  urls = list(dict.fromkeys(urls + list(sn.keys()))); urls.sort(key=lambda u: sn.get(u.rstrip('/'), 0))
  def _sp(u):
    try: return probe_target(store, u, False)
    except Exception: return None
  with ThreadPoolExecutor(max_workers=6) as x: out = [r for r in x.map(_sp, urls[:int(limit)]) if r]
  store.sync()
  return {"discovered": len(urls), "probed": len(out), "results": out}
