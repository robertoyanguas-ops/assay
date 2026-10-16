from app.billing import LOGO_SVG
from app.ui import render_home
import json
from app.engine import probe_target
from app.mcp_api import TOOLS, agent_card, stripe_checkout, stripe_verify
from app.prober import badge_svg
from app.service import crawl_seeds, preflight

def handle_get(S, p: str, q: dict, h: str) -> tuple:
  t = (q.get("target") or [""])[0].rstrip("/")
  if p in ("/health","/v1/health","/healthz"):
    with S._c() as c: n, o = c.execute("SELECT COUNT(*),COALESCE(SUM(rug_pulls),0) FROM endpoints").fetchone(), c.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    return 200, {"status":"ok","service":"assay","endpoints":n[0],"observations":o,"rug_pulls":n[1]}, "application/json"
  if p in ("/logo.svg","/favicon.ico"): return 200, LOGO_SVG, "image/svg+xml"
  if p in ("/.well-known/mcp-config","/.well-known/mcp.json"): return 200, {"configSchema":{"type":"object","properties":{"assayApiKey":{"type":"string","title":"Assay Pass Key (Optional)","description":"Leave blank for 25 free calls, or enter asr_pass_... from https://assay-207908449630.us-central1.run.app ($19 Stripe / $0.005 Base & Solana USDC)."}}}}, "application/json"
  if p == "/llms.txt": return 200, "Assay A2A Observatory\nMCP: https://assay-207908449630.us-central1.run.app/mcp\n", "text/plain"
  if p == "/v1/billing/stripe-success": return (*stripe_verify((q.get("session_id") or [""])[0]), "application/json")
  if p in ("/.well-known/agent-card.json","/.well-known/agent.json"): return 200, agent_card(h), "application/json"
  if p == "/v1/dossier":
    with S._c() as c: r, obs = c.execute("SELECT dossier FROM endpoints WHERE target=?", (t,)).fetchone(), [dict(x) for x in c.execute("SELECT ts,drift,note FROM observations WHERE target=? ORDER BY id DESC LIMIT 20", (t,))]
    return (200 if r else 404), {"dossier":json.loads(r["dossier"]) if r else None,"observations":obs}, "application/json"
  if p == "/v1/badge.svg":
    with S._c() as c: r = c.execute("SELECT dossier FROM endpoints WHERE target=?", (t,)).fetchone()
    d = json.loads(r["dossier"]) if r else {"grade":"?","score":0,"rug_pulls":0}
    return 200, badge_svg(d["grade"], d["score"], d["rug_pulls"]), "image/svg+xml"
  with S._c() as c: rows = [json.loads(r["dossier"]) for r in c.execute("SELECT dossier FROM endpoints ORDER BY score DESC, probes DESC LIMIT 200")]
  if p=="/" and not q.get("format"): return 200, render_home(rows), "text/html; charset=utf-8"
  return 200, {"service":"Assay Observatory","count":len(rows),"leaderboard":rows}, "application/json"
