import hashlib, hmac, os, shutil, sqlite3, threading, time
GDB = '/mnt/gcs/assay.db'
from app.core import SECRET

LIM = int(os.getenv("ASSAY_FREE_CALLS", "25"))
X402 = {"price_usd":0.005,"base_usdc":"0xec5275d5b03bc390fca63d902d0b2d0db2eb5573","solana_usdc":"Dq7fuKy4tGsKeQcDh4oVFjTTkbmfQpS1LTrnFxqd339L"}

class AssayStore:
  def __init__(self, p=None):
    self.path, self.lock = p or os.getenv("ASSAY_DB_PATH","/tmp/assay.db"), threading.Lock()
    if not p and os.path.exists(GDB) and not os.path.exists(self.path): shutil.copy2(GDB, self.path)
    with self.lock, self._c() as c:
      for t in ("endpoints(target PRIMARY KEY,score INT,probes INT,rug_pulls INT,tools_hash,dossier)","observations(id INTEGER PRIMARY KEY,target,ts INT,drift INT,note)","wallets(id PRIMARY KEY,used INT)"):
        c.execute(f"CREATE TABLE IF NOT EXISTS {t}")
  def _c(self):
    c = sqlite3.connect(self.path, timeout=15); c.row_factory = sqlite3.Row; return c
  def auth(self, k: str, ip: str) -> tuple:
    k = (k or "").strip()
    if k.startswith("asr_pass_"):
      p = k.split("_")
      ok = len(p)==4 and p[2].isdigit() and int(p[2])>time.time() and hmac.compare_digest(p[3], hmac.new(SECRET.encode(),p[2].encode(),hashlib.sha256).hexdigest()[:20])
      return (True,{"mode":"pass"}) if ok else (False,{"error":"Invalid asr_pass_","x402":X402})
    a = "ip_" + hashlib.sha256((ip or "127.0.0.1").encode()).hexdigest()[:12]
    with self.lock, self._c() as c:
      r = c.execute("SELECT used FROM wallets WHERE id=?", (a,)).fetchone()
      u = int(r["used"]) if r else 0
      if u >= LIM: return False, {"error":"402 Payment Required","x402":X402}
      c.execute("INSERT INTO wallets VALUES(?,1) ON CONFLICT(id) DO UPDATE SET used=used+1", (a,))
      return True, {"mode":"free","left":LIM-u-1}

  def sync(self):
    if os.path.isdir('/mnt/gcs') and os.path.exists(self.path): shutil.copy2(self.path, GDB)
