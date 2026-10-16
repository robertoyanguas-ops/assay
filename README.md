# Assay — A2A & MCP Provider Assurance Observatory

![Assay Badge](https://assay-207908449630.us-central1.run.app/v1/badge.svg?target=https://agentdiet-72343955726.us-central1.run.app)

Live Observatory: **https://assay-207908449630.us-central1.run.app**

Assay continuously probes remote MCP, A2A, and x402 endpoints to verify liveness, pin canonical SHA-256 `tools/list` schema hashes (detecting silent **MCP Rug Pulls**), and scan for prompt-injection tool poisoning before your agent pays or executes a tool.

## MCP Endpoint
- Streamable HTTP MCP: `https://assay-207908449630.us-central1.run.app/mcp`
- Pre-Flight REST API: `POST https://assay-207908449630.us-central1.run.app/v1/preflight`
- Live Leaderboard: `GET https://assay-207908449630.us-central1.run.app/v1/leaderboard`
