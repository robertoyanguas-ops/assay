P = {
  "target": {"type":"string","minLength":8,"maxLength":512,"description":"Public HTTPS URL of the remote MCP server, A2A agent, or x402 endpoint to inspect (e.g. 'https://tandem.ac/mcp'). Private and loopback IPs are blocked."},
  "expected_tools_hash": {"type":"string","minLength":0,"maxLength":128,"description":"Optional 64-char SHA-256 hex digest of the canonical MCP tools/list schema from mcp-lock.json. If set and the live hash differs, verdict is 'deny'."},
  "tx_hash": {"type":"string","minLength":0,"maxLength":128,"description":"On-chain payment transaction hash (0x Base USDC hash or base58 Solana signature) to bind into the signed SLA receipt."},
  "status_code": {"type":"string","minLength":0,"maxLength":8,"description":"HTTP status code returned by the paid endpoint (e.g. '200', '502', '504'). Codes >= 500 trigger verdict='sla_breach_confirmed'."},
}
def _t(n, t, d, ks):
  return {"name":n,"title":t,"description":d,"annotations":{"title":t,"readOnlyHint":False,"destructiveHint":False,"idempotentHint":True,"openWorldHint":True},"inputSchema":{"type":"object","properties":{k:P[k] for k in ks},"required":["target"],"additionalProperties":False}}
TOOLS = [
  _t("assay_preflight","Pre-Flight MCP & A2A Security Gate","Evaluate a remote MCP, A2A, or x402 endpoint before calling or paying it. Probes live JSON-RPC reachability, hashes tools/list (SHA-256), checks expected_tools_hash for silent rug-pull drift, and scans for prompt-injection poisoning. Returns {verdict ('allow'|'warn'|'deny'), reason, receipt ('asr_rcpt_...'), dossier}. Use before tool execution or payment; for post-payment disputes use assay_verify_delivery; for raw telemetry indexing without policy gating use assay_probe. First 5 calls/IP free.",["target","expected_tools_hash"]),
]
TOOLS += [
  _t("assay_probe","Record Live Endpoint Conformance Observation","Execute a live HTTP, A2A agent-card, and MCP tools/list probe against a target URL and record the observation in the Assay Observatory ledger without pre-flight policy gating. Returns the updated dossier {target, grade ('A+' to 'F'), score (0-100), mcp_tools, tools_hash, rug_pulls, poison_flags, latency_ms, receipt}. Use to index a server or refresh leaderboard telemetry; for allow/deny gating or hash pinning use assay_preflight. First 5 calls/IP free.",["target"]),
  _t("assay_verify_delivery","Verify Post-Payment x402 Delivery & Mint SLA Receipt","Independently probe a paid x402/A2A provider after payment to verify delivery or confirm an SLA breach. Combines reported status_code with a live probe and binds tx_hash into an HMAC-SHA256 receipt. Returns {verdict ('delivery_verified'|'sla_breach_confirmed'), sla_breach, grade, score, sla_receipt ('asr_sla_...')}. Use only after paying a provider; before payment use assay_preflight. First 5 calls/IP free.",["target","tx_hash","status_code"]),
]
