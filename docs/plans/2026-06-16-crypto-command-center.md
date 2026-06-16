# Crypto Command Center — Implementation Plan v3

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> **Revision:** v3 — incorporates Session 1 debate scope decisions + Session 1A resolutions.
> **Debate source:** `docs/debate/session-1-scope.md`, `docs/debate/session-1a-open-questions.md`

**Goal:** A unified web dashboard with on-chain whale tracking (BTC + ETH), stablecoin flow monitoring, and a 2-signal confluence engine — shipping in one week. Sentiment and macro panels follow in Week 2 as experimental opt-in features.

**Architecture:** FastAPI backend (Python 3.12) with async data ingestion, SQLite (WAL mode), repository layer (200-line budget), WebSocket live updates with auth token. React 18 + Vite frontend with TradingView Lightweight Charts and Tailwind CSS. SignalBar is the visual hero — dominant, narrative-driven, with full 4-state spectrum (CALIBRATING → WEAK → MODERATE → STRONG).

**Phase 1a (this week):** On-Chain (BTC + ETH) + Stablecoin + 2-signal SignalBar + security baseline + repository layer + degraded states. **12 tasks.**

**Phase 1b (next week):** Sentiment (Reddit + batched LLM) + Macro (FRED overlay). Experimental — opt-in toggles, excluded from SignalBar by default. **8 tasks.**

**Tech Stack:** Python 3.12, FastAPI, httpx, aiosqlite, Pydantic v2 / React 18, Vite 6, Tailwind CSS 4, lightweight-charts / APScheduler, OpenAI API (Phase 1b only)

---

## Phase 0: Security Baseline & Prerequisites

---

### Task 0.1: Security-first initial commit

**Objective:** Ship the security baseline as a standalone PR before any feature code. `.gitignore`, restricted CORS, WebSocket auth token generation, CSP header, `load_dotenv()`.

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `backend/.env.example`
- Create: `backend/main.py` (with security config)
- Create: `backend/app/__init__.py`

**Step 1: Write .gitignore**

`.gitignore`:
```
__pycache__/
*.py[cod]
venv/
*.egg-info/
dist/
*.db
*.db-journal
*.db-wal
.env
node_modules/
frontend/dist/
.DS_Store
.vscode/
.idea/
```

**Step 2: Write README.md**

`README.md`:
```markdown
# Crypto Command Center

Unified crypto dashboard: on-chain whale tracking (BTC + ETH), stablecoin flow monitoring, and real-time signal confluence.

## Quick Start
```bash
make install
make build
make run
# Open http://localhost:8000
```

## API Keys (optional)
Set in `backend/.env`. Free tiers work without most keys:

| Service | Key | Free Tier |
|---------|-----|-----------|
| Etherscan | `ETHERSCAN_API_KEY` | Free from etherscan.io |
| FRED | `FRED_API_KEY` | Free from stlouisfed.org |
| OpenAI | `OPENAI_API_KEY` | Needed for sentiment (Phase 1b) |
```

**Step 3: Create backend/.env.example**

`backend/.env.example`:
```
# Phase 1a
ETHERSCAN_API_KEY=
# Phase 1b (optional)
OPENAI_API_KEY=
FRED_API_KEY=
```

**Step 4: Write main.py with security-first config**

`backend/main.py`:
```python
"""Crypto Command Center — FastAPI backend."""
import os
import secrets
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="Crypto Command Center", version="0.3.0")

# Security: CORS restricted to localhost (not wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security: CSP header
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data:;"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Security: WebSocket auth token (generated at startup)
WS_AUTH_TOKEN = secrets.token_urlsafe(32)
print(f"[security] WebSocket auth token: {WS_AUTH_TOKEN}")
print(f"[security] Connect with: ws://localhost:8000/ws?token={WS_AUTH_TOKEN}")

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
```

**Step 5: Verify security config**

```bash
cd /Users/tn/dev/crypto-dashboard/backend
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn[standard] python-dotenv
python main.py &
sleep 2
# Verify CORS is restrictive
curl -s -H "Origin: https://evil.com" http://127.0.0.1:8000/api/health -I | grep -i access-control
# Expected: NO Access-Control-Allow-Origin header (blocked)
# Verify localhost works
curl -s -H "Origin: http://localhost:5173" http://127.0.0.1:8000/api/health -I | grep -i access-control
# Expected: Access-Control-Allow-Origin: http://localhost:5173
kill %1
```

**Step 6: Commit as standalone security PR**

```bash
cd /Users/tn/dev/crypto-dashboard
git add -A && git commit -m "security: baseline — CORS restricted, CSP header, WS auth token, .gitignore"
```

---

### Task 0.2: Project scaffold + frontend init

**Objective:** Create directory structure, install backend + frontend dependencies, verify Vite proxy.

**Files:**
- Create: directory tree
- Create: `backend/requirements.txt`
- Create: frontend scaffold (via Vite)

**Step 1: Create directories**

```bash
mkdir -p /Users/tn/dev/crypto-dashboard/backend/app/{api,models,services,collectors,repositories}
mkdir -p /Users/tn/dev/crypto-dashboard/backend/tests
touch /Users/tn/dev/crypto-dashboard/backend/app/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/api/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/models/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/services/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/collectors/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/repositories/__init__.py
```

**Step 2: Write requirements.txt**

`backend/requirements.txt`:
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
aiosqlite==0.20.0
pydantic==2.10.4
apscheduler==3.11.0
python-dotenv==1.0.1
# Phase 1b adds: openai==1.58.1
```

**Step 3: Install**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
pip install -r requirements.txt
```

**Step 4: Scaffold React frontend**

```bash
cd /Users/tn/dev/crypto-dashboard
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite lightweight-charts lucide-react
```

**Step 5: Vite config with proxy**

`frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true }
    }
  }
})
```

**Step 6: Verify**

```bash
cd /Users/tn/dev/crypto-dashboard/frontend && npm run dev &
sleep 3 && curl -s http://localhost:5173 | head -5
kill %1
```

**Step 7: Commit**

```bash
git add -A && git commit -m "chore: scaffold FastAPI + React/Vite/Tailwind project structure"
```

---

## Phase 1: Data Layer

---

### Task 1.1: Database schema with WAL mode + Pydantic models

**Objective:** SQLite schema for Phase 1a panels (whale_transactions, stablecoin_supply, exchange_volumes, signal_confluences), WAL mode, integer timestamps, json serialization for components.

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/schemas.py`

**Step 1: Write database.py**

`backend/app/database.py`:
```python
"""Async SQLite database with WAL mode."""
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ccc.db"

async def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db

async def init_db():
    db = await get_db()
    await db.execute("PRAGMA journal_mode=WAL")
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS whale_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT UNIQUE,
            blockchain TEXT NOT NULL,
            from_address TEXT,
            to_address TEXT,
            amount_usd REAL,
            asset TEXT,
            timestamp INTEGER NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        );
        
        CREATE TABLE IF NOT EXISTS exchange_volumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT NOT NULL,
            asset TEXT NOT NULL,
            volume_usd REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            UNIQUE(exchange, asset, timestamp)
        );
        
        CREATE TABLE IF NOT EXISTS stablecoin_supply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stablecoin TEXT NOT NULL,
            total_supply_usd REAL NOT NULL,
            change_24h_usd REAL DEFAULT 0,
            chains TEXT,
            timestamp INTEGER NOT NULL,
            UNIQUE(stablecoin, timestamp)
        );
        
        CREATE TABLE IF NOT EXISTS signal_confluences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            overall_score REAL NOT NULL,
            signal TEXT NOT NULL,
            direction TEXT NOT NULL,
            calibration_status TEXT NOT NULL DEFAULT 'calibrating',
            narrative TEXT,
            components TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        );
        
        -- Phase 1b tables (created now, populated later)
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            topic TEXT,
            score REAL NOT NULL,
            confidence REAL,
            summary TEXT,
            baseline_fear_greed REAL,
            url TEXT,
            timestamp INTEGER NOT NULL,
            UNIQUE(source, url, timestamp)
        );
        
        CREATE TABLE IF NOT EXISTS macro_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator TEXT NOT NULL,
            value REAL NOT NULL,
            obs_date TEXT,
            timestamp INTEGER NOT NULL,
            UNIQUE(indicator, timestamp)
        );
        
        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_whale_ts ON whale_transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_whale_chain ON whale_transactions(blockchain);
        CREATE INDEX IF NOT EXISTS idx_supply_ts ON stablecoin_supply(timestamp);
    """)
    await db.commit()
    await db.close()
```

**Key design notes:**
- `exchange_volumes` renamed from `exchange_flows` — honest labeling (Session 1 decision)
- `signal_confluences` includes `calibration_status` and `narrative` fields
- `sentiment_scores` includes `baseline_fear_greed` for Phase 1b comparison
- All Phase 1b tables created now — no schema migration needed later

**Step 2: Write Pydantic schemas**

`backend/app/models/schemas.py`:
```python
"""Pydantic models for API responses."""
from pydantic import BaseModel
from typing import Optional

class WhaleTransaction(BaseModel):
    tx_hash: str
    blockchain: str
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount_usd: float
    asset: str
    timestamp: int

class ExchangeVolume(BaseModel):
    exchange: str
    asset: str
    volume_usd: float
    timestamp: int

class StablecoinSupply(BaseModel):
    stablecoin: str
    total_supply_usd: float
    change_24h_usd: float = 0
    chains: Optional[str] = None
    timestamp: int

class SignalComponent(BaseModel):
    name: str
    score: float
    detail: str

class SignalConfluence(BaseModel):
    overall_score: float
    signal: str
    direction: str
    calibration_status: str
    calibration_progress: Optional[dict] = None
    narrative: Optional[str] = None
    components: list[SignalComponent]
    timestamp: int

# Phase 1b schemas
class SentimentScore(BaseModel):
    source: str
    topic: Optional[str] = None
    score: float
    confidence: Optional[float] = None
    summary: Optional[str] = None
    baseline_fear_greed: Optional[float] = None
    url: Optional[str] = None
    timestamp: int

class MacroPoint(BaseModel):
    indicator: str
    value: float
    obs_date: Optional[str] = None
    timestamp: int
```

**Step 3: Init and verify**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db()); print('OK')"
python -c "import aiosqlite, asyncio; db = asyncio.run(aiosqlite.connect('data/ccc.db')); rows = asyncio.run(db.execute_fetchall(\"SELECT name FROM sqlite_master WHERE type='table'\")); print([r[0] for r in rows]); asyncio.run(db.close())"
# Expected: ['whale_transactions', 'exchange_volumes', 'stablecoin_supply', 'signal_confluences', 'sentiment_scores', 'macro_data']
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: add SQLite schema with WAL mode — all Phase 1a + 1b tables"
```

---

### Task 1.2: Repository layer (200-line budget)

**Objective:** WhaleRepository + StablecoinRepository. The ONLY modules that touch SQLite. 200-line budget enforced — no raw SQL in collectors or API routes.

**Files:**
- Create: `backend/app/repositories/whale_repo.py`
- Create: `backend/app/repositories/stablecoin_repo.py`

**Step 1: Write WhaleRepository**

`backend/app/repositories/whale_repo.py`:
```python
"""Whale transaction repository — single source of truth for whale DB operations."""
from app.database import get_db

class WhaleRepository:
    @staticmethod
    async def save(txns: list[dict]):
        db = await get_db()
        for tx in txns:
            await db.execute(
                """INSERT OR IGNORE INTO whale_transactions 
                   (tx_hash, blockchain, from_address, to_address, amount_usd, asset, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (tx["tx_hash"], tx["blockchain"], tx["from_address"],
                 tx["to_address"], tx["amount_usd"], tx["asset"], tx["timestamp"])
            )
        await db.commit()
        await db.close()
    
    @staticmethod
    async def get_recent(limit: int = 20, min_usd: float = 500000, blockchain: str = None):
        db = await get_db()
        query = "SELECT * FROM whale_transactions WHERE amount_usd >= ?"
        params = [min_usd]
        if blockchain:
            query += " AND blockchain = ?"
            params.append(blockchain)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]
    
    @staticmethod
    async def get_stats(hours: int = 24):
        db = await get_db()
        cursor = await db.execute(
            """SELECT COUNT(*) as total, AVG(amount_usd) as avg_amount,
                      MAX(amount_usd) as max_amount
               FROM whale_transactions
               WHERE timestamp > strftime('%s', 'now') - ?""",
            (hours * 3600,)
        )
        row = await cursor.fetchone()
        await db.close()
        return dict(row) if row else {"total": 0, "avg_amount": 0, "max_amount": 0}
    
    @staticmethod
    async def count_recent(hours: int = 1):
        db = await get_db()
        cursor = await db.execute(
            "SELECT COUNT(*) as count, AVG(amount_usd) as avg_amount FROM whale_transactions WHERE timestamp > strftime('%s', 'now') - ?",
            (hours * 3600,)
        )
        row = await cursor.fetchone()
        await db.close()
        return dict(row)
```

**Step 2: Write StablecoinRepository**

`backend/app/repositories/stablecoin_repo.py`:
```python
"""Stablecoin supply repository."""
from app.database import get_db

class StablecoinRepository:
    @staticmethod
    async def save_supply(data: dict):
        """Save supply reading. data = {symbol: {total_supply_usd, change_24h_usd, chains, timestamp}}"""
        db = await get_db()
        for symbol, d in data.items():
            await db.execute(
                """INSERT OR REPLACE INTO stablecoin_supply 
                   (stablecoin, total_supply_usd, change_24h_usd, chains, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (symbol, d["total_supply_usd"], d.get("change_24h_usd", 0),
                 d.get("chains", ""), d["timestamp"])
            )
        await db.commit()
        await db.close()
    
    @staticmethod
    async def get_latest():
        db = await get_db()
        cursor = await db.execute(
            """SELECT stablecoin, total_supply_usd, change_24h_usd, chains,
                      MAX(timestamp) as timestamp
               FROM stablecoin_supply GROUP BY stablecoin"""
        )
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]
    
    @staticmethod
    async def get_previous_supply():
        """Get previous reading per stablecoin for delta computation."""
        db = await get_db()
        cursor = await db.execute(
            "SELECT stablecoin, total_supply_usd, MAX(timestamp) as ts FROM stablecoin_supply GROUP BY stablecoin"
        )
        rows = await cursor.fetchall()
        await db.close()
        return {r["stablecoin"]: r["total_supply_usd"] for r in rows}
    
    @staticmethod
    async def get_history(stablecoin: str = "USDT", hours: int = 168):
        db = await get_db()
        cursor = await db.execute(
            """SELECT * FROM stablecoin_supply 
               WHERE stablecoin = ? AND timestamp > strftime('%s', 'now') - ?
               ORDER BY timestamp ASC""",
            (stablecoin, hours * 3600)
        )
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]
```

**Step 3: Verify line count**

```bash
wc -l /Users/tn/dev/crypto-dashboard/backend/app/repositories/*.py
# Expected: ~150-180 lines total (within 200-line budget)
```

**Step 4: Write HTTP client (needed by collectors)**

`backend/app/services/http_client.py`:
```python
"""Shared async HTTP client with User-Agent and rate limiting."""
import asyncio
import time
import httpx
from typing import Optional

class RateLimiter:
    def __init__(self, calls_per_second: float = 1.0):
        self.rate = calls_per_second
        self.last_call = 0.0
    
    async def acquire(self):
        now = time.time()
        wait = max(0, (1.0 / self.rate) - (now - self.last_call))
        if wait > 0:
            await asyncio.sleep(wait)
        self.last_call = time.time()

class APIClient:
    def __init__(self, base_url: str = "", rate_limit: float = 1.0, timeout: int = 30):
        self.base_url = base_url
        self.limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self.default_headers = {
            "User-Agent": "CryptoCommandCenter/0.3 (personal dashboard)",
        }
    
    async def get(self, url: str, params: Optional[dict] = None, 
                  headers: Optional[dict] = None, retries: int = 3):
        await self.limiter.acquire()
        merged = {**self.default_headers, **(headers or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(retries):
                try:
                    resp = await client.get(f"{self.base_url}{url}", params=params, headers=merged)
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
```

**Step 5: Commit**

```bash
git add -A && git commit -m "feat: add repository layer (WhaleRepo + StablecoinRepo, 200-line budget) + HTTP client"
```

---

### Task 1.3: Exchange wallet config

**Objective:** Config-driven list of exchange wallet addresses for ETH whale tracking. Collector reads this, not hardcoded addresses.

**Files:**
- Create: `backend/config/exchange_wallets.json`

**Step 1: Write config**

`backend/config/exchange_wallets.json`:
```json
{
  "eth_wallets": [
    {"address": "0x28C6c06298d514Db089934071355E5743bf21d60", "label": "Binance 1", "chain": "ethereum"},
    {"address": "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549", "label": "Binance 2", "chain": "ethereum"},
    {"address": "0xDFd5293D8e347dFe59E90eFd55b2956a1343963d", "label": "Coinbase 1", "chain": "ethereum"},
    {"address": "0xdD2FD458Cdead6a2e8Cc22cE1ff4D77be4657f8A", "label": "Coinbase 2", "chain": "ethereum"},
    {"address": "0x267be1C1D684F78cb4F6a176C4911b741E4Ffdc0", "label": "Kraken 1", "chain": "ethereum"},
    {"address": "0xE92d1A43df510F82C66382592a047d288f85226f", "label": "Kraken 2", "chain": "ethereum"},
    {"address": "0x1Db92e2EeBC8E0c075a02BeA49a2935BcD2dFCF4", "label": "Bybit 1", "chain": "ethereum"},
    {"address": "0xF89d7B52dfad227C83506e415d59d4Ae09BdB7A8", "label": "Bybit 2", "chain": "ethereum"},
    {"address": "0x06959153B974D0D5fDfd87D561db6d8d4FA0bb0B", "label": "OKX 1", "chain": "ethereum"},
    {"address": "0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b", "label": "OKX 2", "chain": "ethereum"}
  ],
  "btc_tracked": true,
  "eth_min_value_usd": 500000
}
```

**Step 2: Verify config is valid JSON**

```bash
python3 -m json.tool /Users/tn/dev/crypto-dashboard/backend/config/exchange_wallets.json > /dev/null && echo "Valid JSON"
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add exchange wallet config for ETH whale tracking (10 wallets)"
```

---

## Phase 2: Collectors

---

### Task 2.1: BTC whale collector

**Objective:** Fetch unconfirmed large BTC transactions from Blockchain.info, parse addresses, store via WhaleRepository.

**Files:**
- Create: `backend/app/collectors/btc_whale_collector.py`

**Step 1: Write collector**

`backend/app/collectors/btc_whale_collector.py`:
```python
"""Collect whale BTC transactions from Blockchain.info mempool."""
import time
from app.services.http_client import APIClient
from app.repositories.whale_repo import WhaleRepository

WHALE_THRESHOLD_USD = 1_000_000
client = APIClient(base_url="https://blockchain.info", rate_limit=0.5)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

_price_cache = {"btc": None, "ts": 0}

async def _btc_price():
    now = time.time()
    if _price_cache["btc"] and (now - _price_cache["ts"]) < 300:
        return _price_cache["btc"]
    data = await coingecko.get("/simple/price", params={"ids": "bitcoin", "vs_currencies": "usd"})
    _price_cache["btc"] = data["bitcoin"]["usd"]
    _price_cache["ts"] = now
    return _price_cache["btc"]

async def collect():
    try:
        data = await client.get("/unconfirmed-transactions?format=json")
        txs_data = data if isinstance(data, list) else data.get("txs", [])
        price = await _btc_price()
        txs = []
        for tx in txs_data[:50]:
            total_out = sum(o.get("value", 0) for o in tx.get("out", [])) / 1e8
            usd = total_out * price
            if usd >= WHALE_THRESHOLD_USD:
                inputs = tx.get("inputs", [])
                outputs = tx.get("out", [])
                from_addr = inputs[0].get("prev_out", {}).get("addr") if inputs else None
                to_addrs = [o.get("addr") for o in outputs if o.get("addr")]
                txs.append({
                    "tx_hash": tx["hash"],
                    "blockchain": "bitcoin",
                    "from_address": from_addr,
                    "to_address": to_addrs[0] if to_addrs else None,
                    "amount_usd": round(usd, 2),
                    "asset": "BTC",
                    "timestamp": int(tx.get("time", time.time())),
                })
        if txs:
            await WhaleRepository.save(txs)
            print(f"[btc_whale] Collected {len(txs)} whale txns (mempool)")
        return len(txs)
    except Exception as e:
        print(f"[btc_whale] Error: {e}")
        return 0
```

**Step 2: Test**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.collectors.btc_whale_collector import collect; n = asyncio.run(collect()); print(f'Collected: {n}')"
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add BTC whale collector (Blockchain.info mempool)"
```

---

### Task 2.2: ETH whale collector (Etherscan, config-driven)

**Objective:** Fetch recent transactions for exchange wallets from Etherscan API, filter by USD value, store via WhaleRepository. Wallet list from config.

**Files:**
- Create: `backend/app/collectors/eth_whale_collector.py`

**Step 1: Write collector**

`backend/app/collectors/eth_whale_collector.py`:
```python
"""Collect whale ETH transactions from Etherscan (config-driven wallet list)."""
import json
import os
import time
from pathlib import Path
from app.services.http_client import APIClient
from app.repositories.whale_repo import WhaleRepository

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "exchange_wallets.json"
etherscan = APIClient(base_url="https://api.etherscan.io/api", rate_limit=0.2)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

_price_cache = {"eth": None, "ts": 0}

async def _eth_price():
    now = time.time()
    if _price_cache["eth"] and (now - _price_cache["ts"]) < 300:
        return _price_cache["eth"]
    data = await coingecko.get("/simple/price", params={"ids": "ethereum", "vs_currencies": "usd"})
    _price_cache["eth"] = data["ethereum"]["usd"]
    _price_cache["ts"] = now
    return _price_cache["eth"]

def _load_wallets():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    return cfg.get("eth_wallets", []), cfg.get("eth_min_value_usd", 500000)

async def collect():
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    wallets, min_usd = _load_wallets()
    price = await _eth_price()
    txs = []
    call_count = 0
    
    for wallet in wallets:
        try:
            params = {
                "module": "account", "action": "txlist",
                "address": wallet["address"], "page": 1, "offset": 5,
                "sort": "desc", "apikey": api_key,
            }
            data = await etherscan.get("", params=params)
            call_count += 1
            for tx in data.get("result", [])[:3]:
                value_eth = int(tx.get("value", 0)) / 1e18
                value_usd = value_eth * price
                if value_usd >= min_usd:
                    txs.append({
                        "tx_hash": tx["hash"],
                        "blockchain": "ethereum",
                        "from_address": tx.get("from"),
                        "to_address": tx.get("to"),
                        "amount_usd": round(value_usd, 2),
                        "asset": "ETH",
                        "timestamp": int(tx.get("timeStamp", time.time())),
                    })
        except Exception as e:
            print(f"[eth_whale] Error ({wallet['label']}): {e}")
    
    if txs:
        await WhaleRepository.save(txs)
        print(f"[eth_whale] Collected {len(txs)} whale txns from {call_count} API calls")
    return len(txs)
```

**Step 2: Test (requires ETHERSCAN_API_KEY in .env)**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.collectors.eth_whale_collector import collect; n = asyncio.run(collect()); print(f'Collected: {n}')"
```
**Note:** Test will work without API key (rate-limited but functional).

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add ETH whale collector (Etherscan, 10 config-driven wallets)"
```

---

### Task 2.3: Stablecoin supply collector (with deltas)

**Objective:** Fetch USDT/USDC/DAI/USDe supply from DefiLlama, compute 24h change, store via StablecoinRepository.

**Files:**
- Create: `backend/app/collectors/stablecoin_collector.py`

**Step 1: Write collector**

`backend/app/collectors/stablecoin_collector.py`:
```python
"""Track stablecoin supply from DefiLlama with delta computation."""
import time
from app.services.http_client import APIClient
from app.repositories.stablecoin_repo import StablecoinRepository

llama = APIClient(base_url="https://stablecoins.llama.fi", rate_limit=0.5)
TRACKED = ["USDT", "USDC", "DAI", "USDe"]

async def collect():
    try:
        data = await llama.get("/stablecoins")
        pegged = data.get("peggedAssets", [])
        current = {}
        for asset in pegged:
            symbol = asset.get("symbol", "")
            if symbol in TRACKED:
                current[symbol] = {
                    "total_supply_usd": asset.get("circulating", {}).get("peggedUSD", 0),
                    "chains": ",".join(list(asset.get("chainBalances", {}).keys())[:5]),
                }
        
        # Compute deltas from previous reading
        previous = await StablecoinRepository.get_previous_supply()
        now = int(time.time())
        for symbol, data in current.items():
            prev = previous.get(symbol, data["total_supply_usd"])
            data["change_24h_usd"] = round(data["total_supply_usd"] - prev, 2)
            data["timestamp"] = now
        
        await StablecoinRepository.save_supply(current)
        print(f"[stablecoin] Updated {len(current)} stablecoins")
        return len(current)
    except Exception as e:
        print(f"[stablecoin] Error: {e}")
        return 0
```

**Step 2: Test**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.collectors.stablecoin_collector import collect; n = asyncio.run(collect()); print(f'Updated: {n}')"
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add stablecoin supply collector with 24h delta computation"
```

---

### Task 2.4: Background scheduler

**Objective:** APScheduler running all three collectors on their intervals.

**Files:**
- Create: `backend/app/services/scheduler.py`

**Step 1: Write scheduler**

`backend/app/services/scheduler.py`:
```python
"""Background task scheduler for Phase 1a collectors."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def start_collectors():
    from app.collectors.btc_whale_collector import collect as collect_btc
    from app.collectors.eth_whale_collector import collect as collect_eth
    from app.collectors.stablecoin_collector import collect as collect_stable
    
    scheduler.add_job(collect_btc, "interval", minutes=5, id="btc_whales")
    scheduler.add_job(collect_eth, "interval", minutes=5, id="eth_whales")
    scheduler.add_job(collect_stable, "interval", minutes=30, id="stablecoins")
    scheduler.start()
    print("[scheduler] Collectors started: BTC(5m), ETH(5m), Stablecoin(30m)")
```

**Step 2: Connect to main.py**

Update `backend/main.py` — add after imports and before routes:

```python
from app.database import init_db
from app.services.scheduler import start_collectors

@app.on_event("startup")
async def startup():
    try:
        await init_db()
        start_collectors()
        print("[startup] Database ready, collectors running")
    except Exception as e:
        print(f"[startup] FATAL: {e}")
        import sys; sys.exit(1)
```

**Step 3: Verify scheduler starts**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python main.py &
sleep 5
# Check logs for collector output
kill %1
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: add background scheduler — BTC/ETH whales (5m), stablecoin (30m)"
```

---

## Phase 3: API Layer

---

### Task 3.1: On-Chain API endpoints

**Objective:** REST endpoints for whale transactions + exchange volumes + stats.

**Files:**
- Create: `backend/app/api/onchain.py`

**Step 1: Write routes**

`backend/app/api/onchain.py`:
```python
"""On-chain intelligence API routes."""
from fastapi import APIRouter, Query
from app.repositories.whale_repo import WhaleRepository

router = APIRouter(prefix="/api/onchain", tags=["onchain"])

@router.get("/whales")
async def get_whales(limit: int = 20, min_usd: float = 500000, blockchain: str = None):
    return await WhaleRepository.get_recent(limit=limit, min_usd=min_usd, blockchain=blockchain)

@router.get("/stats")
async def get_stats():
    return await WhaleRepository.get_stats(hours=24) 
```

**Step 2: Add to main.py**

```python
from app.api.onchain import router as onchain_router
app.include_router(onchain_router)  # BEFORE any static mount
```

**Step 3: Verify**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python main.py &
sleep 3
curl -s http://127.0.0.1:8000/api/onchain/whales?limit=3 | python3 -m json.tool
curl -s http://127.0.0.1:8000/api/onchain/stats
kill %1
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: add on-chain API endpoints (whales + stats)"
```

---

### Task 3.2: Stablecoin API endpoints

**Objective:** Supply + history endpoints.

**Files:**
- Create: `backend/app/api/stablecoin.py`

**Step 1: Write routes**

`backend/app/api/stablecoin.py`:
```python
"""Stablecoin flow API routes."""
from fastapi import APIRouter
from app.repositories.stablecoin_repo import StablecoinRepository

router = APIRouter(prefix="/api/stablecoin", tags=["stablecoin"])

@router.get("/supply")
async def get_supply():
    return await StablecoinRepository.get_latest()

@router.get("/history")
async def get_history(stablecoin: str = "USDT", hours: int = 168):
    return await StablecoinRepository.get_history(stablecoin=stablecoin, hours=hours)
```

**Step 2: Add to main.py**

```python
from app.api.stablecoin import router as stablecoin_router
app.include_router(stablecoin_router)
```

**Step 3: Verify + commit**

```bash
curl -s http://127.0.0.1:8000/api/stablecoin/supply | python3 -m json.tool
```

```bash
git add -A && git commit -m "feat: add stablecoin API endpoints (supply + history)"
```

---

### Task 3.3: Confluence engine (2-signal, CALIBRATING logic, 4 states, narrative)

**Objective:** Signal confluence engine for Phase 1a — whales + stablecoin only. Implements the Session 1A AND-gate calibration logic. Produces narrative summary.

**Files:**
- Create: `backend/app/services/confluence.py`

**Step 1: Write engine**

`backend/app/services/confluence.py`:
```python
"""2-signal confluence engine with calibration AND-gate and narrative generation."""
import json
import time
from app.repositories.whale_repo import WhaleRepository
from app.repositories.stablecoin_repo import StablecoinRepository
from app.database import get_db

WEIGHTS = {"whale_activity": 0.55, "stablecoin_flow": 0.45}

# Calibration thresholds (Session 1A)
MIN_DATA_POINTS = 100
MIN_RUNTIME_HOURS = 48
FRESHNESS_HOURS = 1

_start_time = time.time()

async def _check_calibration() -> dict:
    """Returns calibration status and progress."""
    whale_data = await WhaleRepository.count_recent(hours=99999)  # all-time
    supply_data = await StablecoinRepository.get_latest()
    
    whale_count = whale_data.get("count", 0) or 0
    supply_count = len(supply_data) * (await _estimate_supply_readings())
    
    runtime_hours = (time.time() - _start_time) / 3600
    
    # Freshness: at least one reading in last hour
    whale_fresh = await WhaleRepository.count_recent(hours=FRESHNESS_HOURS)
    supply_fresh = len(await StablecoinRepository.get_latest()) > 0
    
    conditions = {
        "whale_datapoints": {"met": whale_count >= MIN_DATA_POINTS, "current": whale_count, "target": MIN_DATA_POINTS},
        "stablecoin_datapoints": {"met": supply_count >= MIN_DATA_POINTS, "current": supply_count, "target": MIN_DATA_POINTS},
        "runtime": {"met": runtime_hours >= MIN_RUNTIME_HOURS, "current": round(runtime_hours, 1), "target": MIN_RUNTIME_HOURS},
        "freshness": {"met": (whale_fresh.get("count", 0) or 0) > 0 and supply_fresh},
    }
    
    all_met = all(c["met"] for c in conditions.values())
    return {
        "calibrated": all_met,
        "conditions_met": sum(1 for c in conditions.values() if c["met"]),
        "conditions_total": len(conditions),
        "conditions": conditions,
    }

async def _estimate_supply_readings():
    """Estimate stablecoin readings from DB record count."""
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(DISTINCT timestamp) as cnt FROM stablecoin_supply")
    row = await cursor.fetchone()
    await db.close()
    return row["cnt"] if row else 0

async def compute_confluence() -> dict:
    calibration = await _check_calibration()
    now = int(time.time())
    
    if not calibration["calibrated"]:
        return {
            "overall_score": 0.0,
            "signal": "CALIBRATING",
            "direction": "STABLE",
            "calibration_status": "calibrating",
            "calibration_progress": calibration,
            "narrative": _calibration_narrative(calibration),
            "components": [],
            "timestamp": now,
        }
    
    # Compute signals
    whale_score, whale_desc = await _whale_signal()
    stable_score, stable_desc = await _stablecoin_signal()
    
    overall = whale_score * WEIGHTS["whale_activity"] + stable_score * WEIGHTS["stablecoin_flow"]
    
    if overall > 0.65:
        signal = "STRONG"
    elif overall > 0.35:
        signal = "MODERATE"
    else:
        signal = "WEAK"
    
    # Direction
    db = await get_db()
    cursor = await db.execute("SELECT overall_score FROM signal_confluences WHERE calibration_status='calibrated' ORDER BY timestamp DESC LIMIT 1")
    prev = await cursor.fetchone()
    await db.close()
    prev_score = prev["overall_score"] if prev else overall
    delta = overall - prev_score
    direction = "RISING" if delta > 0.05 else "FALLING" if delta < -0.05 else "STABLE"
    
    components = [
        {"name": "Whale Activity", "score": round(whale_score, 2), "detail": whale_desc},
        {"name": "Stablecoin Flows", "score": round(stable_score, 2), "detail": stable_desc},
    ]
    
    narrative = _generate_narrative(whale_score, stable_score, signal, direction)
    
    # Store snapshot
    db = await get_db()
    await db.execute(
        "INSERT INTO signal_confluences (overall_score, signal, direction, calibration_status, narrative, components, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (round(overall, 3), signal, direction, "calibrated", narrative, json.dumps(components), now)
    )
    await db.commit()
    await db.close()
    
    return {
        "overall_score": round(overall, 3),
        "signal": signal,
        "direction": direction,
        "calibration_status": "calibrated",
        "narrative": narrative,
        "components": components,
        "timestamp": now,
    }

async def _whale_signal() -> tuple[float, str]:
    data = await WhaleRepository.count_recent(hours=1)
    count = data.get("count", 0) or 0
    avg = data.get("avg_amount", 0) or 0
    if count > 10 and avg > 5_000_000:
        return (0.8, f"{count} large txns, avg ${avg:,.0f}")
    elif count > 5:
        return (0.5, f"{count} significant txns")
    elif count > 0:
        return (0.2, f"{count} txns detected")
    return (0.0, "No recent whale activity")

async def _stablecoin_signal() -> tuple[float, str]:
    supply = await StablecoinRepository.get_latest()
    total = sum(s["total_supply_usd"] or 0 for s in supply)
    total_change = sum(s["change_24h_usd"] or 0 for s in supply)
    if total_change > 2_000_000_000:
        return (0.8, f"Supply growing fast (+${total_change/1e9:.1f}B), total ${total/1e9:.1f}B")
    elif total_change > 0:
        return (0.6, f"Supply growing (+${total_change/1e6:.0f}M), total ${total/1e9:.1f}B")
    elif total_change > -1_000_000_000:
        return (0.4, f"Supply stable, total ${total/1e9:.1f}B")
    else:
        return (0.2, f"Supply contracting (${total_change/1e9:.1f}B), total ${total/1e9:.1f}B")

def _calibration_narrative(cal: dict) -> str:
    met = cal["conditions_met"]
    total = cal["conditions_total"]
    return f"Calibrating ({met}/{total}): collecting data to establish signal baselines"

def _generate_narrative(whale: float, stable: float, signal: str, direction: str) -> str:
    parts = []
    if whale > 0.6:
        parts.append("Whales accumulating")
    elif whale > 0.3:
        parts.append("Moderate whale activity")
    else:
        parts.append("Whales quiet")
    
    if stable > 0.6:
        parts.append("stablecoin supply growing")
    elif stable > 0.3:
        parts.append("stablecoin supply stable")
    else:
        parts.append("stablecoin supply contracting")
    
    return f"{', '.join(parts)} — {signal} {direction}"
```

**Step 2: Test**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.services.confluence import compute_confluence; r = asyncio.run(compute_confluence()); import json; print(json.dumps(r, indent=2))"
# Expected during calibration: signal=CALIBRATING, calibration_progress populated
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add 2-signal confluence engine with AND-gate calibration and narrative generation"
```

---

### Task 3.4: Signals API + authenticated WebSocket

**Objective:** REST endpoint for confluence, history endpoint, WebSocket with token auth, broadcast all panel data.

**Files:**
- Create: `backend/app/api/signals.py`
- Modify: `backend/main.py` (add router + WS auth import)

**Step 1: Write signals API**

`backend/app/api/signals.py`:
```python
"""Signal API + authenticated WebSocket."""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.confluence import compute_confluence
from app.repositories.whale_repo import WhaleRepository
from app.repositories.stablecoin_repo import StablecoinRepository
from app.database import get_db
from main import WS_AUTH_TOKEN

router = APIRouter(tags=["signals"])

@router.get("/api/signals/confluence")
async def get_confluence():
    return await compute_confluence()

@router.get("/api/signals/history")
async def get_history(limit: int = 50):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM signal_confluences ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

connected_ws = set()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(None)):
    if token != WS_AUTH_TOKEN:
        await ws.close(code=4001, reason="Invalid token")
        return
    await ws.accept()
    connected_ws.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_ws.discard(ws)

async def broadcast_full_state():
    if not connected_ws:
        return
    confluence = await compute_confluence()
    whales = await WhaleRepository.get_recent(limit=5)
    stablecoins = await StablecoinRepository.get_latest()
    
    payload = json.dumps({"confluence": confluence, "whales": whales, "stablecoins": stablecoins})
    dead = set()
    for ws in connected_ws:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    connected_ws.difference_update(dead)
```

**Step 2: Add to main.py and scheduler**

```python
from app.api.signals import router as signals_router, broadcast_full_state
app.include_router(signals_router)

# In scheduler start_collectors():
from app.api.signals import broadcast_full_state
scheduler.add_job(broadcast_full_state, "interval", minutes=1, id="ws_broadcast")
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add signals API + authenticated WebSocket with token auth"
```

---

### Task 3.5: Final main.py assembly

**Objective:** All routers mounted BEFORE static mount. Correct order: API routers first, static mount last.

`backend/main.py` final structure:

```python
"""Crypto Command Center — FastAPI backend."""
import os, secrets
from dotenv import load_dotenv; load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="Crypto Command Center", version="0.3.0")

app.add_middleware(CORSMiddleware, allow_origins=[
    "http://localhost:8000", "http://localhost:5173",
    "http://127.0.0.1:8000", "http://127.0.0.1:5173",
], allow_methods=["GET", "POST"], allow_headers=["*"])

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:; img-src 'self' data:;"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
app.add_middleware(SecurityHeadersMiddleware)

WS_AUTH_TOKEN = secrets.token_urlsafe(32)
print(f"[security] WS token: {WS_AUTH_TOKEN}")

# === IMPORTS (after security config) ===
from app.database import init_db
from app.services.scheduler import start_collectors
from app.api.onchain import router as onchain_router
from app.api.stablecoin import router as stablecoin_router
from app.api.signals import router as signals_router, broadcast_full_state

# === API ROUTERS (before static mount) ===
app.include_router(onchain_router)
app.include_router(stablecoin_router)
app.include_router(signals_router)

@app.on_event("startup")
async def startup():
    try:
        await init_db()
        start_collectors()
        # Add WS broadcast
        from app.services.scheduler import scheduler
        scheduler.add_job(broadcast_full_state, "interval", minutes=1, id="ws_broadcast")
        print("[startup] Ready")
    except Exception as e:
        print(f"[startup] FATAL: {e}"); import sys; sys.exit(1)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}

# === STATIC MOUNT (LAST) ===
from fastapi.staticfiles import StaticFiles
from pathlib import Path
fb = Path(__file__).parent.parent / "frontend" / "dist"
if fb.exists():
    app.mount("/", StaticFiles(directory=str(fb), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
```

**Step 2: Full-stack verification**

```bash
cd /Users/tn/dev/crypto-dashboard
cd frontend && npm run build && cd ..
cd backend && source venv/bin/activate && python main.py &
sleep 3
curl -s http://127.0.0.1:8000/api/health
curl -s http://127.0.0.1:8000/api/signals/confluence | python3 -m json.tool | head -15
curl -s http://127.0.0.1:8000/ | head -5  # should serve React
kill %1
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: assemble all Phase 1a API routers with correct mount order"
```

---

## Phase 4: Frontend (Phase 1a)

---

### Task 4.1: Global CSS + Dashboard shell

**Objective:** Dark theme, responsive grid, SignalBar hero layout.

**Files:**
- Create: `frontend/src/index.css`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/components/Dashboard.jsx`
- Create: `frontend/src/components/Panel.jsx`

`frontend/src/index.css`:
```css
@import "tailwindcss";
:root {
  --bg-primary: #0a0a0f; --bg-card: #13131a; --border-color: #1e1e2e;
  --accent-cyan: #06b6d4; --accent-green: #10b981; --accent-amber: #f59e0b; --accent-red: #ef4444;
  --text-primary: #e2e8f0; --text-secondary: #94a3b8;
}
body { background: var(--bg-primary); color: var(--text-primary); font-family: 'Inter', system-ui, sans-serif; }
```

`frontend/src/components/Panel.jsx`:
```jsx
export default function Panel({ title, children, className = "" }) {
  return (
    <div className={`bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4 ${className}`}>
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">{title}</h2>
      {children}
    </div>
  );
}
```

`frontend/src/components/Dashboard.jsx`:
```jsx
import Panel from "./Panel";
import OnChainPanel from "./panels/OnChainPanel";
import StablecoinPanel from "./panels/StablecoinPanel";
import SignalBar from "./SignalBar";

export default function Dashboard() {
  return (
    <div className="min-h-screen p-4 md:p-6 max-w-7xl mx-auto">
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-cyan-400">Crypto Command Center</h1>
        <p className="text-slate-500 text-xs">On-Chain Intelligence · Stablecoin Flows</p>
      </header>
      <SignalBar />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <Panel title="On-Chain Intelligence"><OnChainPanel /></Panel>
        <Panel title="Stablecoin Flows"><StablecoinPanel /></Panel>
      </div>
    </div>
  );
}
```

`frontend/src/App.jsx`:
```jsx
import Dashboard from "./components/Dashboard";
export default function App() { return <Dashboard />; }
```

**Commit:**

```bash
git add -A && git commit -m "feat: create dashboard shell with SignalBar hero + 2-panel layout"
```

---

### Task 4.2: SignalBar component (4-state, calibration display, narrative, WS auth)

**Objective:** Dominant SignalBar with CALIBRATING/WEAK/MODERATE/STRONG, progress during calibration, narrative text, WebSocket with token auth.

**Files:**
- Create: `frontend/src/components/SignalBar.jsx`

**Step 1: Write SignalBar**

`frontend/src/components/SignalBar.jsx`:
```jsx
import { useState, useEffect } from "react";

const SIGNAL_STYLES = {
  CALIBRATING: "bg-slate-600 text-slate-300",
  STRONG: "bg-green-500 text-white",
  MODERATE: "bg-amber-500 text-white",
  WEAK: "bg-red-500 text-white",
};

const DIRECTION_ICONS = { RISING: "▲", FALLING: "▼", STABLE: "→" };
const DIRECTION_COLORS = { RISING: "text-green-400", FALLING: "text-red-400", STABLE: "text-slate-400" };

export default function SignalBar() {
  const [confluence, setConfluence] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Fetch initial state
    fetch("/api/signals/confluence").then(r => r.json()).then(setConfluence);
  }, []);

  useEffect(() => {
    // WebSocket with token auth — token fetched from dev server or hardcoded for dev
    const token = "DEV_TOKEN"; // In production, inject via env or fetch from /api/ws-token
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws?token=${token}`);
    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setConfluence(data.confluence);
    };
    ws.onclose = () => setWsConnected(false);
    return () => ws.close();
  }, []);

  const overall = confluence?.overall_score ?? 0;
  const signal = confluence?.signal ?? "CALIBRATING";
  const direction = confluence?.direction ?? "STABLE";
  const narrative = confluence?.narrative ?? "";
  const calibration = confluence?.calibration_progress;
  const isCalibrating = confluence?.calibration_status === "calibrating";

  return (
    <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4 md:p-6 mb-4">
      {/* Top row: badge + bar + percentage */}
      <div className="flex items-center gap-4">
        <div className={`px-3 py-1.5 rounded font-bold text-sm ${SIGNAL_STYLES[signal]}`}>
          {signal}
          {!isCalibrating && <span className={`ml-2 ${DIRECTION_COLORS[direction]}`}>{DIRECTION_ICONS[direction]}</span>}
        </div>
        
        <div className="flex-1">
          <div className="text-xs text-slate-500 mb-1">Confluence Score</div>
          {isCalibrating ? (
            <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
              <div className="h-full bg-slate-600 rounded-full transition-all duration-500"
                   style={{ width: `${(calibration?.conditions_met || 0) / (calibration?.conditions_total || 4) * 100}%` }} />
            </div>
          ) : (
            <div className="h-3 bg-[#1e1e2e] rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-red-500 via-amber-500 to-emerald-500 rounded-full transition-all duration-700"
                   style={{ width: `${(overall * 100).toFixed(0)}%` }} />
            </div>
          )}
        </div>
        
        <div className="text-2xl md:text-3xl font-mono font-bold text-cyan-400">
          {isCalibrating ? "--" : `${(overall * 100).toFixed(0)}%`}
        </div>
      </div>

      {/* Narrative */}
      {narrative && (
        <p className="mt-2 text-sm text-slate-300">{narrative}</p>
      )}

      {/* Calibration progress details */}
      {isCalibrating && calibration && (
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-500">
          {Object.entries(calibration.conditions || {}).map(([key, cond]) => (
            <div key={key} className={`text-center ${cond.met ? "text-green-400" : "text-slate-500"}`}>
              <div>{key.replace(/_/g, " ")}</div>
              <div className="font-mono">{cond.met ? "✓" : `${cond.current}/${cond.target}`}</div>
            </div>
          ))}
        </div>
      )}

      {/* Component scores (when calibrated) */}
      {!isCalibrating && confluence?.components?.length > 0 && (
        <div className="grid grid-cols-2 gap-2 mt-3 text-xs text-slate-400">
          {confluence.components.map((c) => (
            <div key={c.name} className="text-center" title={c.detail}>
              <div className="text-[10px] uppercase">{c.name}</div>
              <div className="font-mono text-white">{(c.score * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      )}

      {/* WS connection indicator */}
      <div className="mt-2 text-[10px] text-right">
        <span className={wsConnected ? "text-green-500" : "text-red-500"}>●</span>
        <span className="text-slate-600 ml-1">{wsConnected ? "live" : "polling"}</span>
      </div>
    </div>
  );
}
```

**Note:** The WebSocket token hardcoding is temporary for dev. In production, add a `/api/ws-token` endpoint that returns `WS_AUTH_TOKEN` (only accessible from localhost).

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add SignalBar with 4-state spectrum, calibration progress, narrative, WS auth"
```

---

### Task 4.3: On-Chain panel (BTC + ETH, auto-refresh, all states)

**Objective:** Whale tx table with blockchain filter, loading/error/empty states, 60s auto-refresh.

**Files:**
- Create: `frontend/src/components/panels/OnChainPanel.jsx`

`frontend/src/components/panels/OnChainPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

export default function OnChainPanel() {
  const [whales, setWhales] = useState([]);
  const [stats, setStats] = useState(null);
  const [chain, setChain] = useState(null); // null = all, "bitcoin", "ethereum"
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    const params = new URLSearchParams({ limit: "10", min_usd: "500000" });
    if (chain) params.set("blockchain", chain);
    
    Promise.all([
      fetch(`/api/onchain/whales?${params}`).then(r => r.json()),
      fetch("/api/onchain/stats").then(r => r.json()),
    ])
      .then(([w, s]) => { setWhales(w); setStats(s); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 60000); return () => clearInterval(t); }, [chain]);

  const formatUsd = (v) => v >= 1e9 ? `$${(v/1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : `$${v.toFixed(0)}`;

  return (
    <div>
      {/* Chain filter */}
      <div className="flex gap-2 mb-3">
        {[null, "bitcoin", "ethereum"].map(c => (
          <button key={c ?? "all"} onClick={() => { setChain(c); setLoading(true); }}
                  className={`text-xs px-2 py-1 rounded ${chain === c ? "bg-cyan-500/20 text-cyan-400" : "bg-[#1e1e2e] text-slate-400 hover:text-white"}`}>
            {c ? c[0].toUpperCase() + c.slice(1) : "All"}
          </button>
        ))}
      </div>

      {/* Stats */}
      {stats && (
        <div className="flex gap-3 mb-3 text-xs">
          <span className="text-slate-500">24h: <b className="text-cyan-400">{stats.total}</b></span>
          <span className="text-slate-500">Max: <b className="text-white">{formatUsd(stats.max_amount)}</b></span>
        </div>
      )}

      {/* Content */}
      {loading && <p className="text-slate-500 text-xs">Loading...</p>}
      {error && <p className="text-red-400 text-xs">Error: {error}</p>}
      {!loading && !error && whales.length === 0 && <p className="text-slate-600 text-xs">No whale activity in this window</p>}
      {!loading && !error && whales.length > 0 && (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {whales.map(w => (
            <div key={w.tx_hash} className="flex justify-between text-xs border-b border-[#1e1e2e] pb-1">
              <span className="text-slate-500 w-12">{w.blockchain === "ethereum" ? "Ξ" : "₿"}</span>
              <span className="text-slate-400 font-mono flex-1 truncate">{w.tx_hash.slice(0, 12)}...</span>
              <span className="text-cyan-400 font-mono">{formatUsd(w.amount_usd)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Commit:**

```bash
git add -A && git commit -m "feat: add on-chain panel with BTC/ETH filter, auto-refresh, full state handling"
```

---

### Task 4.4: Stablecoin panel (supply bars, deltas, auto-refresh)

**Objective:** Stablecoin supply bars with 24h change indicators, auto-refresh, all states.

**Files:**
- Create: `frontend/src/components/panels/StablecoinPanel.jsx`

`frontend/src/components/panels/StablecoinPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

const COLORS = { USDT: "#26a17b", USDC: "#2775ca", DAI: "#fab005", USDe: "#6366f1" };

export default function StablecoinPanel() {
  const [supply, setSupply] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    fetch("/api/stablecoin/supply")
      .then(r => r.json())
      .then(data => { setSupply(data); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 60000); return () => clearInterval(t); }, []);

  const maxSupply = Math.max(...supply.map(s => s.total_supply_usd || 0), 1);

  if (loading) return <p className="text-slate-500 text-xs">Loading...</p>;
  if (error) return <p className="text-red-400 text-xs">Error: {error}</p>;
  if (!supply.length) return <p className="text-slate-600 text-xs">No supply data yet — collecting...</p>;

  return (
    <div className="space-y-3">
      {supply.map(s => (
        <div key={s.stablecoin}>
          <div className="flex justify-between text-xs mb-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ background: COLORS[s.stablecoin] || "#6366f1" }} />
              <span className="text-slate-400">{s.stablecoin}</span>
            </div>
            <span className="text-white font-mono">${(s.total_supply_usd / 1e9).toFixed(1)}B</span>
            {s.change_24h_usd !== 0 && (
              <span className={`font-mono text-xs ${s.change_24h_usd > 0 ? "text-green-400" : "text-red-400"}`}>
                {s.change_24h_usd > 0 ? "+" : ""}${(Math.abs(s.change_24h_usd) / 1e6).toFixed(0)}M
              </span>
            )}
          </div>
          <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all"
                 style={{ width: `${((s.total_supply_usd || 0) / maxSupply) * 100}%`, background: COLORS[s.stablecoin] || "#6366f1" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Commit:**

```bash
git add -A && git commit -m "feat: add stablecoin panel with supply bars, 24h deltas, and auto-refresh"
```

---

### Task 4.5: Makefile + production build

**Objective:** Fixed Makefile with direct venv paths, build + run commands.

**Files:**
- Create: `Makefile`

`Makefile`:
```makefile
.PHONY: install dev build run

VENV_PYTHON = backend/venv/bin/python
VENV_PIP = backend/venv/bin/pip

install:
	cd backend && python3 -m venv venv
	$(VENV_PIP) install -r backend/requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && $(VENV_PYTHON) main.py

dev-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

run:
	cd backend && $(VENV_PYTHON) main.py
```

**Build and verify:**

```bash
cd /Users/tn/dev/crypto-dashboard
make build
make run &
sleep 3
curl -s http://127.0.0.1:8000/api/health
curl -s http://127.0.0.1:8000/ | head -5
kill %1
```

**Commit:**

```bash
git add -A && git commit -m "feat: add Makefile with production build and run commands"
```

---

## Phase 1b: Experimental Panels (Week 2)

---

### Task 5.1: Sentiment collector (Reddit + batched OpenAI)

**Objective:** Fetch Reddit posts, score via single batched OpenAI call or expanded keyword fallback. Store with Fear & Greed baseline.

**Files:**
- Create: `backend/app/collectors/sentiment_collector.py`
- Create: `backend/app/repositories/sentiment_repo.py`

**Key differences from Phase 1a collectors:**
- Fetches Fear & Greed Index from alternative.me API as baseline
- Batched OpenAI call (40 posts → 1 API call)
- Stores `baseline_fear_greed` alongside score for comparison
- User-Agent header included (from HTTP client default)

**Test:**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
pip install openai
python -c "import asyncio; from app.collectors.sentiment_collector import collect; n = asyncio.run(collect()); print(f'Collected: {n}')"
```

---

### Task 5.2: Macro collector (FRED + CoinGecko)

**Objective:** Fetch DXY, FEDFUNDS, GOLD, SP500 + BTC/ETH prices. Proper error handling — skip on failure, never insert 0.0.

**Files:**
- Create: `backend/app/collectors/macro_collector.py`
- Create: `backend/app/repositories/macro_repo.py`

---

### Task 5.3: Sentiment + Macro API endpoints

**Objective:** API routes for sentiment scores/trend and macro latest/history. Chart-ready data.

**Files:**
- Create: `backend/app/api/sentiment.py`
- Create: `backend/app/api/macro.py`

---

### Task 5.4: Experimental panel infrastructure

**Objective:** Opt-in toggle component, confidence indicator, experimental label. Reusable for both Sentiment and Macro panels.

**Files:**
- Create: `frontend/src/components/ExperimentalToggle.jsx`

`frontend/src/components/ExperimentalToggle.jsx`:
```jsx
import { useState } from "react";

export default function ExperimentalToggle({ label, children }) {
  const [enabled, setEnabled] = useState(false);
  
  if (!enabled) {
    return (
      <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">{label}</h3>
            <p className="text-xs text-amber-500 mt-1">⚡ Experimental — opt-in to enable</p>
          </div>
          <button onClick={() => setEnabled(true)}
                  className="px-3 py-1.5 bg-amber-500/20 text-amber-400 rounded text-xs hover:bg-amber-500/30 transition-colors">
            Enable
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">{label}</h3>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-amber-500">EXPERIMENTAL</span>
          <button onClick={() => setEnabled(false)}
                  className="text-xs text-slate-500 hover:text-slate-300">Disable</button>
        </div>
      </div>
      {children}
    </div>
  );
}
```

---

### Task 5.5: Sentiment panel (experimental, Fear & Greed baseline)

**Objective:** Gauge + baseline comparison + post list. Wrapped in ExperimentalToggle.

**Files:**
- Create: `frontend/src/components/panels/SentimentPanel.jsx`

---

### Task 5.6: Macro panel (experimental, chart overlay, no correlation)

**Objective:** TradingView chart with BTC/DXY overlay, ResizeObserver, indicator chips. Wrapped in ExperimentalToggle. No correlation number.

**Files:**
- Create: `frontend/src/components/panels/MacroPanel.jsx`

---

### Task 5.7: Dashboard update — add experimental panels

**Objective:** Add Sentiment and Macro panels below Phase 1a panels, excluded from SignalBar, wrapped in ExperimentalToggle.

**Modify:** `frontend/src/components/Dashboard.jsx`

---

### Task 5.8: Cipher's data flow audit

**Objective:** Review Sentiment + Macro data flows before Phase 1b ships. Verify no API key leakage through frontend, no hardcoded secrets, no insecure WebSocket data exposure.

---

## Implementation Notes

### Phase 1a Task Summary

| # | Task | Key Deliverable |
|---|------|----------------|
| 0.1 | Security baseline | CORS, CSP, WS token, .gitignore |
| 0.2 | Project scaffold | Dirs, deps, Vite, Tailwind |
| 1.1 | Database schema | WAL mode, all tables, Pydantic models |
| 1.2 | Repository layer | WhaleRepo + StablecoinRepo (≤200 lines) |
| 1.3 | Exchange wallet config | 10 ETH wallets in JSON config |
| 2.1 | BTC whale collector | Blockchain.info mempool |
| 2.2 | ETH whale collector | Etherscan, config-driven wallets |
| 2.3 | Stablecoin collector | DefiLlama with 24h deltas |
| 2.4 | Background scheduler | APScheduler, all collectors |
| 3.1 | On-Chain API | /api/onchain/whales + /stats |
| 3.2 | Stablecoin API | /api/stablecoin/supply + /history |
| 3.3 | Confluence engine | 2-signal, AND-gate calibration, 4 states, narrative |
| 3.4 | Signals API + WS | REST + authenticated WebSocket |
| 3.5 | Final main.py | Router assembly, static mount |
| 4.1 | Dashboard shell | Dark theme, 2-panel grid, SignalBar hero |
| 4.2 | SignalBar | 4-state, calibration progress, narrative, WS auth |
| 4.3 | On-Chain panel | BTC/ETH filter, auto-refresh, all states |
| 4.4 | Stablecoin panel | Supply bars, 24h deltas, auto-refresh |
| 4.5 | Makefile | Build + run + install |

### Design Decisions (from Debate)

| Decision | Source | Implementation |
|----------|--------|---------------|
| Scope: On-Chain + Stablecoin in Phase 1a | Session 1 | 12 tasks this week |
| Sentiment + Macro = experimental, Phase 1b | Session 1 | Opt-in toggles, excluded from SignalBar |
| CALIBRATING → live: AND(100pts, 48h, fresh) | Session 1A | `_check_calibration()` in confluence.py |
| WEAK state ships in v1 | Session 1A | 4-state SignalBar from day one |
| Grey bar during calibration | Session 1A | Color spectrum activates post-calibration |
| Multi-chain from day one (BTC + ETH) | Session 1 | Dual collector, blockchain filter in panel |
| Repository layer, 200-line budget | Session 1 | WhaleRepo + StablecoinRepo |
| Exchange "flows" renamed to "volumes" | Session 1 | `exchange_volumes` table, honest labeling |
| Correlation endpoint killed | Session 1 | Deferred to v2 |
| Security baseline = standalone first PR | Session 1 | Task 0.1 ships before any feature code |
| Exchange wallets in config, not hardcoded | Session 1A | `config/exchange_wallets.json` |
| Narrative summary in SignalBar | Session 1 | `_generate_narrative()` in confluence.py |

### Running the Dashboard

```bash
cd /Users/tn/dev/crypto-dashboard
make install   # first time only
make build     # build React
make run       # start on http://127.0.0.1:8000
```
