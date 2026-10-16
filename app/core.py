import hashlib, hmac, ipaddress, json, os, re, socket
from urllib.parse import urlparse

SECRET = os.getenv("ASSAY_SECRET") or os.getenv("AGENTDIET_ADMIN_KEY") or "assay_secret"
POISON = re.compile(r"(ignore (all |previous )?instructions|<system>|/etc/passwd|\.ssh/|id_rsa)", re.I)

def check_safe_url(raw: str) -> str:
  u = urlparse(str(raw or "").strip())
  if u.scheme not in ("http", "https") or not u.hostname: raise ValueError("Invalid URL")
  h = u.hostname.lower()
  if h in ("localhost", "metadata.google.internal", "metadata"): raise ValueError("Blocked host")
  for i in socket.getaddrinfo(h, u.port or 443):
    ip = ipaddress.ip_address(i[4][0])
    ip = ipaddress.IPv4Address(int(ip) & 0xffffffff) if str(ip).startswith("64:ff9b:") else ip
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
      raise ValueError("Blocked IP")
  return f"{u.scheme}://{u.netloc}{u.path}".rstrip("/")

def hash_tools(t: list) -> str:
  n = sorted([{"n":x.get("name",""),"d":x.get("description",""),"s":x.get("inputSchema") or {}} for x in (t or []) if isinstance(x,dict)], key=lambda x:x["n"])
  return "sha256:" + hashlib.sha256(json.dumps(n, sort_keys=True).encode()).hexdigest()

def scan_poison(t: list) -> list:
  return [f"{x.get('name','?')}:{POISON.search(json.dumps(x)).group(0)}" for x in (t or []) if isinstance(x,dict) and POISON.search(json.dumps(x))]

def sign_data(d: dict, p="asr_rcpt_") -> str:
  return p + hmac.new(SECRET.encode(), json.dumps(d, sort_keys=True).encode(), hashlib.sha256).hexdigest()[:32]
