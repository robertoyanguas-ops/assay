#!/usr/bin/env python3
import json, os, re, sys, urllib.request as U
B, K = os.getenv("ASSAY_URL", "https://assay-207908449630.us-central1.run.app"), os.getenv("ASSAY_API_KEY", "")
m, c = (sys.argv[1] if len(sys.argv)>1 else "lock"), (sys.argv[2] if len(sys.argv)>2 else "server.json")
urls = sorted(set(u.rstrip("/") for u in re.findall(r'https://[^\s"\'<>]+', open(c).read()) if "schema" not in u))
old = json.load(open("mcp-lock.json")).get("pins", {}) if os.path.exists("mcp-lock.json") else {}
pins, bad = {}, 0
for u in urls:
  q = U.Request(f"{B}/v1/preflight", data=json.dumps({"target":u,"expected_tools_hash":old.get(u,{}).get("tools_hash","")}).encode(), headers={"Content-Type":"application/json","X-Assay-Key":K})
  with U.urlopen(q, timeout=20) as r: d = json.loads(r.read().decode())
  s = d["dossier"]; pins[u] = {"grade":s["grade"],"score":s["score"],"tools":s["mcp_tools"],"tools_hash":s["tools_hash"],"receipt":d["receipt"]}
  print(f"[{d['verdict'].upper()}] {u} -> {s['grade']} ({s['score']}) hash={str(s['tools_hash'])[:10]} rcpt={d['receipt'][:16]}")
  bad += (d["verdict"] == "deny")
json.dump({"schema":"assay-mcp-lock/v1","pins":pins}, open("mcp-lock.json","w"), indent=2)
sys.exit(1 if m=="verify" and bad else 0)
