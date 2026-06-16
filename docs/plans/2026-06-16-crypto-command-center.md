# Crypto Command Center — Implementation Plan v2

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.
> **Revision:** v2 — incorporates adversarial review fixes for data correctness, signal integrity, and production readiness.

**Goal:** A single unified web dashboard combining on-chain intelligence, AI-powered sentiment analysis, macro/crypto overlay, and stablecoin flow tracking — with a signal confluence engine that surfaces high-conviction moments with directional awareness.

**Architecture:** FastAPI backend (Python 3.12) with async data ingestion from 8+ public APIs, SQLite (WAL mode) persistence, WebSocket live updates for all panels. React 18 + Vite frontend with TradingView Lightweight Charts and Tailwind CSS. Four panel components + a signal overlay bar. Backend serves the built React app as static files — single deployable unit.

**Tech Stack:** Python 3.12, FastAPI, httpx, aiosqlite, Pydantic v2 / React 18, Vite 6, Tailwind CSS 4, lightweight-charts (TradingView) / APScheduler, OpenAI API (sentiment, batched)

---

### Phase 0: Prerequisites & Scaffold

---

### Task 0.1: Create .gitignore, README, and environment setup

**Objective:** Prevent committing build artifacts, document the project, and wire up dotenv loading before any code is written.

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `backend/.env.example`

**Step 1: Write .gitignore**

`.gitignore`:
```
# Python
__pycache__/
*.py[cod]
venv/
*.egg-info/
dist/

# Database
*.db
*.db-journal
*.db-wal

# Environment
.env

# Node
node_modules/
frontend/dist/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

**Step 2: Write README.md**

`README.md`:
```markdown
# Crypto Command Center

A unified dashboard for crypto market intelligence: on-chain whale tracking, AI-powered sentiment analysis, macro/crypto correlation overlay, and stablecoin flow monitoring — with a real-time signal confluence engine.

## Quick Start

```bash
make install
make build
make run
# Open http://localhost:8000
```

## API Keys (optional)

Set in `backend/.env`. Most sources work on free tiers without keys:

| Service | Key | Free Tier |
|---------|-----|-----------|
| OpenAI | `OPENAI_API_KEY` | Needed for sentiment scoring |
| FRED | `FRED_API_KEY` | Free from stlouisfed.org |
| Etherscan | `ETHERSCAN_API_KEY` | Free from etherscan.io |
```

**Step 3: Create backend/.env.example**

`backend/.env.example`:
```
# Copy to .env and fill in (optional — free tiers work without most)
OPENAI_API_KEY=
FRED_API_KEY=
ETHERSCAN_API_KEY=
# Future: X_BEARER_TOKEN, WHALE_ALERT_API_KEY, NEWSAPI_KEY
```

**Step 4: Commit**

```bash
cd /Users/tn/dev/crypto-dashboard
git add -A && git commit -m "chore: add .gitignore, README, and env template"
```

---

### Task 0.2: Create project structure and initialize dependencies

**Objective:** Create the monorepo with backend and frontend directories, install core dependencies with macOS-compatible verification.

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`

**Step 1: Create directory structure**

```bash
mkdir -p /Users/tn/dev/crypto-dashboard/backend/app/{api,models,services,collectors}
mkdir -p /Users/tn/dev/crypto-dashboard/backend/tests
```

**Step 2: Create backend requirements.txt**

`backend/requirements.txt`:
```
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
aiosqlite==0.20.0
pydantic==2.10.4
apscheduler==3.11.0
openai==1.58.1
python-dotenv==1.0.1
```

**Step 3: Install backend dependencies**

```bash
cd /Users/tn/dev/crypto-dashboard/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Step 4: Create minimal FastAPI main.py with dotenv loading**

`backend/main.py`:
```python
"""Crypto Command Center — FastAPI backend."""
from dotenv import load_dotenv
load_dotenv()  # Must be first — loads .env before any os.getenv calls

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Crypto Command Center", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**Step 5: Verify backend starts (macOS-compatible)**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python main.py &
sleep 3
curl -s http://localhost:8000/api/health
# Expected: {"status":"ok"}
kill %1
```

**Step 6: Scaffold React frontend**

```bash
cd /Users/tn/dev/crypto-dashboard
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite lightweight-charts lucide-react
```

**Step 7: Configure Tailwind + Vite proxy**

`frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://localhost:8000', '/ws': { target: 'ws://localhost:8000', ws: true } } }
})
```

**Step 8: Verify frontend starts**

```bash
cd /Users/tn/dev/crypto-dashboard/frontend && npm run dev &
sleep 3
curl -s http://localhost:5173 | head -5
kill %1
# Expected: HTML response with Vite dev server
```

**Step 9: Commit**

```bash
cd /Users/tn/dev/crypto-dashboard
git add -A && git commit -m "chore: scaffold project with FastAPI + React/Vite + Tailwind"
```

---

### Phase 1: Data Layer

---

### Task 1.1: Create database schema and connection module (WAL mode)

**Objective:** Set up SQLite schema with WAL mode for concurrent reads/writes, integer timestamps for safe UNIQUE constraints, and proper JSON serialization.

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/schemas.py`

**Step 1: Write database module with WAL mode**

`backend/app/database.py`:
```python
"""Async SQLite database module with WAL mode."""
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
        
        CREATE TABLE IF NOT EXISTS exchange_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT NOT NULL,
            asset TEXT NOT NULL,
            inflow_usd REAL,
            outflow_usd REAL,
            net_flow_usd REAL,
            timestamp INTEGER NOT NULL,
            UNIQUE(exchange, asset, timestamp)
        );
        
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            topic TEXT,
            score REAL NOT NULL,
            confidence REAL,
            summary TEXT,
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
            components TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        );
        
        -- Indexes for time-range queries
        CREATE INDEX IF NOT EXISTS idx_whale_ts ON whale_transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_sentiment_ts ON sentiment_scores(timestamp);
        CREATE INDEX IF NOT EXISTS idx_macro_ts ON macro_data(timestamp);
        CREATE INDEX IF NOT EXISTS idx_supply_ts ON stablecoin_supply(timestamp);
    """)
    await db.commit()
    await db.close()
```

**Key fixes from v1:**
- `PRAGMA journal_mode=WAL` — prevents writer-reader contention
- `INTEGER` timestamps (not REAL) — safe for UNIQUE constraints
- `signal_confluences.components` is TEXT — will use `json.dumps()` on write
- `stablecoin_events` renamed to `stablecoin_supply` — single schema, no duplicates
- `change_24h_usd` field for supply delta tracking
- `obs_date` on macro_data for FRED observation dates

**Step 2: Write Pydantic models**

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

class ExchangeFlow(BaseModel):
    exchange: str
    asset: str
    inflow_usd: float
    outflow_usd: float
    net_flow_usd: float
    timestamp: int

class SentimentScore(BaseModel):
    source: str
    topic: Optional[str] = None
    score: float
    confidence: Optional[float] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    timestamp: int

class MacroPoint(BaseModel):
    indicator: str
    value: float
    obs_date: Optional[str] = None
    timestamp: int

class StablecoinSupply(BaseModel):
    stablecoin: str
    total_supply_usd: float
    change_24h_usd: float = 0
    chains: Optional[str] = None
    timestamp: int

class SignalConfluence(BaseModel):
    overall_score: float
    signal: str
    direction: str
    components: list[dict]
    timestamp: int
```

**Step 3: Create init script**

`backend/init_db.py`:
```python
"""Initialize the database."""
import asyncio
from app.database import init_db
asyncio.run(init_db())
print("Database initialized with WAL mode.")
```

**Step 4: Run init and verify**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python init_db.py
python -c "import aiosqlite, asyncio; db = asyncio.run(aiosqlite.connect('data/ccc.db')); print('WAL:', asyncio.run(db.execute_fetchall('PRAGMA journal_mode'))); asyncio.run(db.close())"
# Expected: Database initialized with WAL mode.  WAL: [('wal',)]
```

**Step 5: Add __init__.py files**

```bash
touch /Users/tn/dev/crypto-dashboard/backend/app/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/api/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/models/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/services/__init__.py
touch /Users/tn/dev/crypto-dashboard/backend/app/collectors/__init__.py
```

**Step 6: Commit**

```bash
git add -A && git commit -m "feat: add SQLite schema with WAL mode, integer timestamps, and Pydantic v2 models"
```

---

### Task 1.2: Create async HTTP client with rate limiting

**Objective:** Shared httpx client with retry logic, rate limiting, and User-Agent headers required by APIs like Reddit.

**Files:**
- Create: `backend/app/services/http_client.py`

**Step 1: Write HTTP client with default User-Agent**

`backend/app/services/http_client.py`:
```python
"""Shared async HTTP client with retry, rate limiting, and headers."""
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
    def __init__(self, base_url: str = "", rate_limit: float = 1.0, 
                 timeout: int = 30, extra_headers: Optional[dict] = None):
        self.base_url = base_url
        self.limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self.default_headers = {
            "User-Agent": "CryptoCommandCenter/0.2 (personal dashboard; contact via repo)",
            **(extra_headers or {}),
        }
    
    async def get(self, url: str, params: Optional[dict] = None, 
                  headers: Optional[dict] = None, retries: int = 3):
        await self.limiter.acquire()
        merged_headers = {**self.default_headers, **(headers or {})}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(retries):
                try:
                    resp = await client.get(f"{self.base_url}{url}", 
                                           params=params, headers=merged_headers)
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
```

**Step 2: Verify**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "from app.services.http_client import APIClient; c = APIClient(); print('Headers:', c.default_headers); print('Import OK')"
# Expected: Headers include User-Agent
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add async HTTP client with User-Agent header and rate limiting"
```

---

### Phase 2: On-Chain Intelligence Panel

---

### Task 2.1: Whale transaction collector (with address parsing)

**Objective:** Fetch large unconfirmed BTC transactions from Blockchain.info mempool, parse from/to addresses, filter by USD threshold, and store with proper address data.

**Files:**
- Create: `backend/app/collectors/whale_collector.py`

**Step 1: Write collector with address parsing**

`backend/app/collectors/whale_collector.py`:
```python
"""Collect whale transactions from Blockchain.info mempool."""
import time
from app.database import get_db
from app.services.http_client import APIClient

WHALE_THRESHOLD_USD = 1_000_000  # $1M+

blockchain_client = APIClient(base_url="https://blockchain.info", rate_limit=0.5)

async def fetch_blockchain_large_txs():
    """Fetch large unconfirmed BTC transactions from the mempool."""
    try:
        data = await blockchain_client.get("/unconfirmed-transactions?format=json")
        txs_data = data if isinstance(data, list) else data.get("txs", [])
        txs = []
        for tx in txs_data[:50]:
            # Parse outputs
            outputs = tx.get("out", [])
            total_out = sum(out.get("value", 0) for out in outputs) / 1e8
            usd_value = total_out * await _get_btc_price()
            if usd_value >= WHALE_THRESHOLD_USD:
                # Parse from/to from inputs/outputs
                from_addr = None
                to_addrs = []
                inputs = tx.get("inputs", [])
                if inputs:
                    from_addr = inputs[0].get("prev_out", {}).get("addr")
                for out in outputs:
                    addr = out.get("addr")
                    if addr:
                        to_addrs.append(addr)
                
                txs.append({
                    "tx_hash": tx["hash"],
                    "blockchain": "bitcoin",
                    "from_address": from_addr,
                    "to_address": to_addrs[0] if to_addrs else None,
                    "amount_usd": round(usd_value, 2),
                    "asset": "BTC",
                    "timestamp": int(tx.get("time", time.time())),
                })
        return txs
    except Exception as e:
        print(f"[whale_collector] Blockchain.info error: {e}")
        return []

_price_cache = {"btc": None, "btc_ts": 0}

async def _get_btc_price():
    now = time.time()
    if _price_cache["btc"] and (now - _price_cache["btc_ts"]) < 300:
        return _price_cache["btc"]
    client = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)
    data = await client.get("/simple/price", params={"ids": "bitcoin", "vs_currencies": "usd"})
    price = data["bitcoin"]["usd"]
    _price_cache["btc"] = price
    _price_cache["btc_ts"] = now
    return price

async def save_whale_txs(txs: list[dict]):
    db = await get_db()
    for tx in txs:
        await db.execute(
            """INSERT OR IGNORE INTO whale_transactions 
               (tx_hash, blockchain, from_address, to_address, amount_usd, asset, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tx["tx_hash"], tx["blockchain"], tx["from_address"], tx["to_address"],
             tx["amount_usd"], tx["asset"], tx["timestamp"])
        )
    await db.commit()
    await db.close()

async def collect_whales():
    """Main collector — call every 5 minutes. Returns count of new whale txns."""
    txs = await fetch_blockchain_large_txs()
    if txs:
        await save_whale_txs(txs)
        print(f"[whale_collector] Collected {len(txs)} whale txns (mempool)")
    return len(txs)
```

**Step 2: Test standalone run**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.collectors.whale_collector import collect_whales; n = asyncio.run(collect_whales()); print(f'Collected: {n}')"
# Expected: Collected N whale txns (mempool) — may be 0 during low activity
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add whale tx collector with address parsing (Blockchain.info mempool)"
```

---

### Task 2.2: Exchange activity collector

**Objective:** Fetch exchange volume data from CoinGecko as a proxy for exchange activity (real on-chain flows require tagged addresses — v2).

**Files:**
- Create: `backend/app/collectors/exchange_collector.py`

**Step 1: Write collector with real data**

`backend/app/collectors/exchange_collector.py`:
```python
"""Collect exchange activity from CoinGecko exchange volume data."""
import time
from app.database import get_db
from app.services.http_client import APIClient

coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

async def fetch_exchange_volumes():
    """Fetch 24h BTC volume for major exchanges."""
    try:
        # Get exchange list with volume data
        data = await coingecko.get("/exchanges", params={"per_page": 20})
        target_exchanges = {"Binance", "Coinbase Exchange", "Kraken", "Bybit", "OKX"}
        results = []
        now = int(time.time())
        for ex in data[:20]:
            name = ex.get("name", "")
            if name in target_exchanges:
                vol_btc = ex.get("trade_volume_24h_btc", 0)
                # Convert BTC volume to USD estimate
                btc_price = await _get_btc_price()
                vol_usd = vol_btc * btc_price
                results.append({
                    "exchange": name,
                    "asset": "BTC",
                    "volume_usd": round(vol_usd, 2),
                    "timestamp": now,
                })
        return results
    except Exception as e:
        print(f"[exchange_collector] Error: {e}")
        return []

_price_cache = {"btc": None, "btc_ts": 0}

async def _get_btc_price():
    now = time.time()
    if _price_cache["btc"] and (now - _price_cache["btc_ts"]) < 300:
        return _price_cache["btc"]
    data = await coingecko.get("/simple/price", params={"ids": "bitcoin", "vs_currencies": "usd"})
    price = data["bitcoin"]["usd"]
    _price_cache["btc"] = price
    _price_cache["btc_ts"] = now
    return price

async def collect_exchange_volumes():
    volumes = await fetch_exchange_volumes()
    if volumes:
        db = await get_db()
        for v in volumes:
            await db.execute(
                """INSERT OR REPLACE INTO exchange_flows 
                   (exchange, asset, inflow_usd, outflow_usd, net_flow_usd, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (v["exchange"], v["asset"], v["volume_usd"], 0.0, v["volume_usd"], v["timestamp"])
            )
        await db.commit()
        await db.close()
    return len(volumes)
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add exchange volume collector (CoinGecko, on-chain flows pending v2)"
```

---

### Task 2.3: On-Chain API endpoints + background scheduler

**Objective:** Wire up FastAPI routes and start APScheduler for collectors.

**Files:**
- Create: `backend/app/api/onchain.py`
- Create: `backend/app/services/scheduler.py`
- Modify: `backend/main.py`

**Step 1: Write on-chain API routes**

`backend/app/api/onchain.py`:
```python
"""On-chain intelligence API routes."""
from fastapi import APIRouter
from app.database import get_db

router = APIRouter(prefix="/api/onchain", tags=["onchain"])

@router.get("/whales")
async def get_whale_txs(limit: int = 20, min_usd: float = 500000):
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM whale_transactions 
           WHERE amount_usd >= ? 
           ORDER BY timestamp DESC LIMIT ?""",
        (min_usd, limit)
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

@router.get("/exchanges")
async def get_exchange_volumes(limit: int = 10):
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM exchange_flows ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

@router.get("/stats")
async def get_onchain_stats():
    db = await get_db()
    cursor = await db.execute(
        """SELECT 
             COUNT(*) as total_whales,
             AVG(amount_usd) as avg_amount,
             MAX(amount_usd) as max_amount
           FROM whale_transactions
           WHERE timestamp > strftime('%s', 'now') - 86400"""
    )
    stats = dict(await cursor.fetchone())
    await db.close()
    return stats
```

**Step 2: Write scheduler**

`backend/app/services/scheduler.py`:
```python
"""Background task scheduler for data collectors."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def start_collectors():
    from app.collectors.whale_collector import collect_whales
    from app.collectors.exchange_collector import collect_exchange_volumes
    
    scheduler.add_job(collect_whales, "interval", minutes=5, id="whales")
    scheduler.add_job(collect_exchange_volumes, "interval", minutes=15, id="exchanges")
    scheduler.start()
```

**Step 3: Update main.py — mount router AND scheduler**

Modify `backend/main.py` — the imports at the top, the router includes BEFORE any static mount:

```python
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.services.scheduler import start_collectors
from app.api.onchain import router as onchain_router

app = FastAPI(title="Crypto Command Center", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routers MUST be mounted BEFORE any static file mount
app.include_router(onchain_router)

@app.on_event("startup")
async def startup():
    try:
        await init_db()
        start_collectors()
        print("[startup] Database initialized, collectors started")
    except Exception as e:
        print(f"[startup] FATAL: {e}")
        import sys; sys.exit(1)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**Step 4: Verify**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python main.py &
sleep 3
curl -s http://localhost:8000/api/onchain/whales | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/onchain/stats
kill %1
```

**Step 5: Commit**

```bash
git add -A && git commit -m "feat: add on-chain API endpoints with startup error handling and scheduler"
```

---

### Phase 3: AI Sentiment Aggregator

---

### Task 3.1: Reddit sentiment collector (with User-Agent + batched LLM calls)

**Objective:** Fetch crypto posts from Reddit, score sentiment via batched OpenAI call or keyword fallback. User-Agent header set to avoid 429s.

**Files:**
- Create: `backend/app/collectors/sentiment_collector.py`

**Step 1: Write collector**

`backend/app/collectors/sentiment_collector.py`:
```python
"""Collect and score crypto sentiment from Reddit."""
import json
import os
from app.database import get_db
from app.services.http_client import APIClient

# Reddit requires a descriptive User-Agent — provided by APIClient default
reddit = APIClient(base_url="https://www.reddit.com", rate_limit=0.5)

CRYPTO_SUBREDDITS = ["CryptoCurrency", "Bitcoin", "ethereum", "CryptoMarkets"]

async def fetch_reddit_posts(subreddit: str, limit: int = 25):
    try:
        data = await reddit.get(f"/r/{subreddit}/hot.json", params={"limit": limit})
        posts = data.get("data", {}).get("children", [])
        results = []
        for p in posts:
            d = p["data"]
            results.append({
                "title": d["title"],
                "text": d.get("selftext", "")[:500],
                "score": d["score"],
                "num_comments": d["num_comments"],
                "url": f"https://reddit.com{d['permalink']}",
                "created_utc": int(d["created_utc"]),
            })
        return results
    except Exception as e:
        print(f"[sentiment] Reddit error ({subreddit}): {e}")
        return []

async def score_sentiment_batch(posts: list[dict]) -> list[dict]:
    """Score all posts in a single batched OpenAI call, or keyword fallback."""
    if not posts:
        return []
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            # Prepare all posts as a single prompt
            posts_text = "\n---\n".join(
                f"[{i}] {p['title']}\n{p['text'][:300]}" 
                for i, p in enumerate(posts)
            )
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": (
                        "Score crypto sentiment for each post from -1 (extremely bearish) "
                        "to 1 (extremely bullish). Return JSON: "
                        '{"scores": [{"index": int, "score": float, "topic": str, "summary": str}]}'
                    )
                }, {
                    "role": "user",
                    "content": posts_text[:8000]
                }],
                response_format={"type": "json_object"},
            )
            result = json.loads(resp.choices[0].message.content)
            return result.get("scores", [])
        except Exception as e:
            print(f"[sentiment] OpenAI error, falling back to keywords: {e}")
    
    # Keyword fallback with expanded crypto-specific terms
    return [keyword_score(p, i) for i, p in enumerate(posts)]

def keyword_score(post: dict, index: int) -> dict:
    bullish = ["bullish", "moon", "pump", "breakout", "rally", "buy", "long", "green",
               "wagmi", "ape", "bid", "accumulation", "undervalued", "bottom", "surge",
               "rocket", "ath", "break", "upside"]
    bearish = ["bearish", "dump", "crash", "collapse", "sell", "short", "red", "fear",
               "rekt", "ngmi", "jeet", "capitulation", "liquidated", "top", "correction",
               "bubble", "dead", "rug", "scam"]
    text = f"{post['title']} {post['text']}".lower()
    b_count = sum(1 for w in bullish if w in text)
    a_count = sum(1 for w in bearish if w in text)
    total = b_count + a_count
    score = (b_count - a_count) / max(total, 1)
    return {
        "index": index,
        "score": round(score, 3),
        "topic": "crypto",
        "summary": post["title"][:200],
    }

async def collect_sentiment():
    posts = []
    for sub in CRYPTO_SUBREDDITS:
        posts.extend(await fetch_reddit_posts(sub, limit=10))
    
    if not posts:
        return 0
    
    scores = await score_sentiment_batch(posts)
    db = await get_db()
    count = 0
    for s in scores:
        idx = s.get("index", 0)
        if idx < len(posts):
            post = posts[idx]
            await db.execute(
                """INSERT OR IGNORE INTO sentiment_scores 
                   (source, topic, score, confidence, summary, url, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("reddit", s.get("topic", "crypto"),
                 s["score"], None,
                 s.get("summary", ""),
                 post["url"], post["created_utc"])
            )
            count += 1
    
    await db.commit()
    await db.close()
    return count
```

**Step 2: Test**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.collectors.sentiment_collector import collect_sentiment; n = asyncio.run(collect_sentiment()); print(f'Collected: {n} posts')"
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add Reddit sentiment collector with batched LLM + expanded keyword fallback"
```

---

### Task 3.2: Sentiment API + scheduler integration

**Objective:** FastAPI routes + add to scheduler.

**Files:**
- Create: `backend/app/api/sentiment.py`
- Modify: `backend/main.py`, `backend/app/services/scheduler.py`

**Step 1: Sentiment API routes**

`backend/app/api/sentiment.py`:
```python
"""Sentiment analysis API routes."""
from fastapi import APIRouter
from app.database import get_db

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])

@router.get("/scores")
async def get_scores(limit: int = 30, source: str = None):
    db = await get_db()
    query = "SELECT * FROM sentiment_scores"
    params = []
    if source:
        query += " WHERE source = ?"
        params.append(source)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

@router.get("/trend")
async def get_sentiment_trend(hours: int = 24):
    db = await get_db()
    cursor = await db.execute(
        """SELECT 
             AVG(score) as avg_score,
             COUNT(*) as count,
             MIN(score) as min_score,
             MAX(score) as max_score
           FROM sentiment_scores
           WHERE timestamp > strftime('%s', 'now') - ?""",
        (hours * 3600,)
    )
    row = await cursor.fetchone()
    await db.close()
    return dict(row) if row else {"avg_score": 0, "count": 0}
```

**Step 2: Add to main.py (BEFORE any static mount)**

```python
from app.api.sentiment import router as sentiment_router
app.include_router(sentiment_router)
```

**Step 3: Add to scheduler.py**

In `start_collectors()`:
```python
from app.collectors.sentiment_collector import collect_sentiment
scheduler.add_job(collect_sentiment, "interval", minutes=15, id="sentiment")
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: add sentiment API endpoints and 15-min scheduler job"
```

---

### Phase 4: Macro × Crypto Overlay

---

### Task 4.1: Macro data collector (FRED + CoinGecko, with proper error handling)

**Objective:** Fetch DXY, Fed funds rate, gold, S&P 500 from FRED, overlay with BTC/ETH from CoinGecko. Store observation dates. Skip insertion on failure (never insert 0.0).

**Files:**
- Create: `backend/app/collectors/macro_collector.py`

**Step 1: Write collector**

`backend/app/collectors/macro_collector.py`:
```python
"""Collect macro indicators from FRED and CoinGecko."""
import time
import os
from app.database import get_db
from app.services.http_client import APIClient

fred = APIClient(base_url="https://api.stlouisfed.org/fred", rate_limit=0.5)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

FRED_SERIES = {
    "DXY": "DTWEXBGS",
    "FEDFUNDS": "FEDFUNDS",
    "GOLD": "GOLDAMGBD228NLBR",
    "SP500": "SP500",
}

async def fetch_fred_series(series_id: str) -> dict | None:
    """Returns {"value": float, "obs_date": str} or None on failure."""
    api_key = os.getenv("FRED_API_KEY", "")
    params = {"series_id": series_id, "sort_order": "desc", "limit": 1, "file_type": "json"}
    if api_key:
        params["api_key"] = api_key
    try:
        data = await fred.get("/series/observations", params=params)
        obs = data.get("observations", [])
        if obs and obs[0].get("value") not in (".", "N/A", None, ""):
            return {"value": float(obs[0]["value"]), "obs_date": obs[0]["date"]}
    except Exception as e:
        print(f"[macro] FRED error ({series_id}): {e}")
    return None

async def fetch_crypto_prices():
    try:
        data = await coingecko.get(
            "/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd"}
        )
        return {
            "BTC": data.get("bitcoin", {}).get("usd"),
            "ETH": data.get("ethereum", {}).get("usd"),
        }
    except Exception as e:
        print(f"[macro] CoinGecko error: {e}")
        return {}

async def collect_macro():
    now = int(time.time())
    db = await get_db()
    inserted = 0
    
    for name, series_id in FRED_SERIES.items():
        result = await fetch_fred_series(series_id)
        if result is not None:
            await db.execute(
                "INSERT OR REPLACE INTO macro_data (indicator, value, obs_date, timestamp) VALUES (?, ?, ?, ?)",
                (name, result["value"], result["obs_date"], now)
            )
            inserted += 1
    
    prices = await fetch_crypto_prices()
    for asset, price in prices.items():
        if price:
            await db.execute(
                "INSERT OR REPLACE INTO macro_data (indicator, value, timestamp) VALUES (?, ?, ?)",
                (asset, price, now)
            )
            inserted += 1
    
    await db.commit()
    await db.close()
    return inserted
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add macro data collector with proper error handling and obs dates"
```

---

### Task 4.2: Macro API endpoints + scheduler

**Objective:** Routes + integration.

**Files:**
- Create: `backend/app/api/macro.py`
- Modify: `backend/main.py`, `backend/app/services/scheduler.py`

**Step 1: Macro API routes with correlation endpoint**

`backend/app/api/macro.py`:
```python
"""Macro overlay API routes."""
from fastapi import APIRouter
from app.database import get_db

router = APIRouter(prefix="/api/macro", tags=["macro"])

@router.get("/latest")
async def get_latest_macro():
    db = await get_db()
    cursor = await db.execute(
        """SELECT indicator, value, obs_date, MAX(timestamp) as timestamp 
           FROM macro_data GROUP BY indicator"""
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

@router.get("/history")
async def get_macro_history(indicator: str = "BTC", hours: int = 168):
    db = await get_db()
    cursor = await db.execute(
        """SELECT * FROM macro_data 
           WHERE indicator = ? 
           AND timestamp > strftime('%s', 'now') - ?
           ORDER BY timestamp ASC""",
        (indicator, hours * 3600)
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

@router.get("/correlation")
async def get_correlation(pair: str = "BTC-DXY", hours: int = 168):
    """Compute Pearson correlation between two indicators."""
    a, b = pair.split("-")
    db = await get_db()
    cursor = await db.execute(
        """SELECT indicator, value, timestamp FROM macro_data 
           WHERE indicator IN (?, ?) AND timestamp > strftime('%s', 'now') - ?
           ORDER BY timestamp ASC""",
        (a, b, hours * 3600)
    )
    rows = await cursor.fetchall()
    await db.close()
    
    # Align by timestamp bucket (1h)
    from collections import defaultdict
    buckets = defaultdict(dict)
    for r in rows:
        bucket = r["timestamp"] // 3600
        buckets[bucket][r["indicator"]] = r["value"]
    
    vals_a, vals_b = [], []
    for bucket in sorted(buckets.keys()):
        if a in buckets[bucket] and b in buckets[bucket]:
            vals_a.append(buckets[bucket][a])
            vals_b.append(buckets[bucket][b])
    
    if len(vals_a) < 3:
        return {"pair": pair, "correlation": None, "data_points": len(vals_a)}
    
    mean_a = sum(vals_a) / len(vals_a)
    mean_b = sum(vals_b) / len(vals_b)
    num = sum((va - mean_a) * (vb - mean_b) for va, vb in zip(vals_a, vals_b))
    den = (sum((v - mean_a)**2 for v in vals_a) * sum((v - mean_b)**2 for v in vals_b)) ** 0.5
    r = num / den if den else 0
    return {"pair": pair, "correlation": round(r, 4), "data_points": len(vals_a)}
```

**Step 2: Add to main.py and scheduler**

Same pattern — add router import and `app.include_router()`. In scheduler:
```python
from app.collectors.macro_collector import collect_macro
scheduler.add_job(collect_macro, "interval", hours=1, id="macro")
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add macro overlay API with correlation endpoint"
```

---

### Phase 5: Stablecoin Flow Tracker

---

### Task 5.1: Stablecoin supply collector (with deltas, single schema)

**Objective:** Track USDT/USDC/DAI/USDe supply from DefiLlama, compute 24h change deltas, single insertion path.

**Files:**
- Create: `backend/app/collectors/stablecoin_collector.py`

**Step 1: Write collector with delta computation**

`backend/app/collectors/stablecoin_collector.py`:
```python
"""Track stablecoin supply and 24h changes from DefiLlama."""
import time
from app.database import get_db
from app.services.http_client import APIClient

llama = APIClient(base_url="https://stablecoins.llama.fi", rate_limit=0.5)

TRACKED_STABLECOINS = ["USDT", "USDC", "DAI", "USDe"]

async def fetch_stablecoin_supply():
    """Fetch current stablecoin supply from DefiLlama."""
    try:
        data = await llama.get("/stablecoins")
        pegged = data.get("peggedAssets", [])
        results = {}
        for asset in pegged:
            symbol = asset.get("symbol", "")
            if symbol in TRACKED_STABLECOINS:
                circulating = asset.get("circulating", {}).get("peggedUSD", 0)
                chains = list(asset.get("chainBalances", {}).keys())
                results[symbol] = {
                    "stablecoin": symbol,
                    "total_supply_usd": circulating,
                    "chains": chains,
                }
        return results
    except Exception as e:
        print(f"[stablecoin] API error: {e}")
        return {}

async def collect_stablecoins():
    now = int(time.time())
    db = await get_db()
    
    # Get current supply
    current = await fetch_stablecoin_supply()
    
    # Get previous reading (24h ago or most recent)
    cursor = await db.execute(
        """SELECT stablecoin, total_supply_usd, MAX(timestamp) as ts
           FROM stablecoin_supply GROUP BY stablecoin"""
    )
    prev_rows = await cursor.fetchall()
    previous = {r["stablecoin"]: r["total_supply_usd"] for r in prev_rows}
    
    count = 0
    for symbol, data in current.items():
        prev_supply = previous.get(symbol, data["total_supply_usd"])
        change_24h = data["total_supply_usd"] - prev_supply
        await db.execute(
            """INSERT OR REPLACE INTO stablecoin_supply 
               (stablecoin, total_supply_usd, change_24h_usd, chains, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (symbol, data["total_supply_usd"], round(change_24h, 2),
             ",".join(data["chains"][:5]), now)
        )
        count += 1
    
    await db.commit()
    await db.close()
    return count
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add stablecoin supply collector with 24h delta computation"
```

---

### Task 5.2: Stablecoin API + scheduler

**Objective:** Routes + integration.

**Files:**
- Create: `backend/app/api/stablecoin.py`
- Modify: `backend/main.py`, `backend/app/services/scheduler.py`

**Step 1: Stablecoin API routes**

`backend/app/api/stablecoin.py`:
```python
"""Stablecoin flow API routes."""
from fastapi import APIRouter
from app.database import get_db

router = APIRouter(prefix="/api/stablecoin", tags=["stablecoin"])

@router.get("/supply")
async def get_current_supply():
    db = await get_db()
    cursor = await db.execute(
        """SELECT stablecoin, total_supply_usd, change_24h_usd, chains,
                  MAX(timestamp) as timestamp 
           FROM stablecoin_supply GROUP BY stablecoin"""
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

@router.get("/history")
async def get_supply_history(stablecoin: str = "USDT", hours: int = 168):
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

**Step 2: Add to main.py and scheduler**

```python
from app.api.stablecoin import router as stablecoin_router
app.include_router(stablecoin_router)

# scheduler:
from app.collectors.stablecoin_collector import collect_stablecoins
scheduler.add_job(collect_stablecoins, "interval", minutes=30, id="stablecoins")
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add stablecoin supply API with history endpoint"
```

---

### Phase 6: Signal Confluence Engine

---

### Task 6.1: Confluence scoring engine (FIXED — all bugs resolved)

**Objective:** Combine signals from all four panels with directional awareness. Correct the three critical bugs: sentiment not zeroed, stablecoin uses latest supply, macro uses all indicators.

**Files:**
- Create: `backend/app/services/confluence.py`

**Step 1: Write corrected engine**

`backend/app/services/confluence.py`:
```python
"""Signal confluence engine — combines all four panels with directional awareness."""
import json
from app.database import get_db

WEIGHTS = {
    "whale_activity": 0.20,
    "sentiment": 0.25,
    "macro_alignment": 0.25,
    "stablecoin_flow": 0.30,
}

async def compute_whale_score() -> tuple[float, str]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT COUNT(*) as count, AVG(amount_usd) as avg_amount
           FROM whale_transactions 
           WHERE timestamp > strftime('%s', 'now') - 3600"""
    )
    row = await cursor.fetchone()
    await db.close()
    count = row["count"] or 0
    avg = row["avg_amount"] or 0
    if count > 10 and avg > 5_000_000:
        return (0.8, f"High whale activity: {count} txns, avg ${avg:,.0f}")
    elif count > 5:
        return (0.5, f"Moderate whale activity: {count} txns")
    elif count > 0:
        return (0.2, f"Low whale activity: {count} txns")
    return (0.0, "No recent whale activity")

async def compute_sentiment_score() -> tuple[float, str]:
    """FIXED: Negative sentiment LOWERS the score (no max(0, avg) clamp)."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT AVG(score) as avg_score, COUNT(*) as count
           FROM sentiment_scores
           WHERE timestamp > strftime('%s', 'now') - 7200"""
    )
    row = await cursor.fetchone()
    await db.close()
    avg = row["avg_score"] or 0
    count = row["count"] or 0
    # Map [-1, 1] to [0, 1] for consistent scoring
    # avg=-1 → 0.0 (extreme fear), avg=0 → 0.5 (neutral), avg=1 → 1.0 (extreme greed)
    normalized = (avg + 1) / 2
    return (round(normalized, 3), f"Sentiment: {avg:+.2f} over {count} posts")

async def compute_macro_score() -> tuple[float, str]:
    """FIXED: Uses all indicators, not just DXY."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT indicator, value FROM macro_data 
           WHERE indicator IN ('DXY', 'FEDFUNDS', 'GOLD', 'SP500')
           AND timestamp > strftime('%s', 'now') - 86400
           GROUP BY indicator HAVING MAX(timestamp)"""
    )
    rows = {r["indicator"]: r["value"] for r in await cursor.fetchall()}
    await db.close()
    
    signals = []
    details = []
    
    # DXY: weakening USD = bullish for crypto
    dxy = rows.get("DXY", 100)
    if dxy < 100:
        signals.append(0.8)
        details.append(f"DXY {dxy:.1f} (weak)")
    elif dxy < 105:
        signals.append(0.5)
        details.append(f"DXY {dxy:.1f} (neutral)")
    else:
        signals.append(0.3)
        details.append(f"DXY {dxy:.1f} (strong)")
    
    # Fed Funds: lower rates = bullish
    fed = rows.get("FEDFUNDS", 5)
    if fed < 3:
        signals.append(0.8)
        details.append(f"Rates {fed:.2f}% (low)")
    elif fed < 5:
        signals.append(0.5)
        details.append(f"Rates {fed:.2f}% (moderate)")
    else:
        signals.append(0.3)
        details.append(f"Rates {fed:.2f}% (high)")
    
    # Gold: rising gold often precedes BTC moves
    gold = rows.get("GOLD", 2000)
    if gold > 2500:
        signals.append(0.7)
        details.append(f"Gold ${gold:,.0f} (elevated)")
    else:
        signals.append(0.5)
        details.append(f"Gold ${gold:,.0f}")
    
    # SP500: risk-on environment
    sp500 = rows.get("SP500", 5000)
    if sp500 > 5500:
        signals.append(0.7)
        details.append(f"SP500 {sp500:,.0f} (risk-on)")
    else:
        signals.append(0.5)
        details.append(f"SP500 {sp500:,.0f}")
    
    score = sum(signals) / len(signals) if signals else 0.5
    return (round(score, 3), " | ".join(details))

async def compute_stablecoin_score() -> tuple[float, str]:
    """FIXED: Uses latest supply reading per stablecoin, not SUM of all readings."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT stablecoin, total_supply_usd, change_24h_usd,
                  MAX(timestamp) as timestamp
           FROM stablecoin_supply 
           WHERE timestamp > strftime('%s', 'now') - 86400
           GROUP BY stablecoin"""
    )
    rows = await cursor.fetchall()
    await db.close()
    
    total_supply = sum(r["total_supply_usd"] or 0 for r in rows)
    total_change = sum(r["change_24h_usd"] or 0 for r in rows)
    
    # Growing supply = buying power entering market
    if total_change > 2_000_000_000:  # +$2B in 24h
        return (0.8, f"Supply growing fast (+${total_change/1e9:.1f}B), total ${total_supply/1e9:.1f}B")
    elif total_change > 0:
        return (0.6, f"Supply growing (+${total_change/1e6:.0f}M), total ${total_supply/1e9:.1f}B")
    elif total_change > -1_000_000_000:
        return (0.4, f"Supply stable, total ${total_supply/1e9:.1f}B")
    else:
        return (0.2, f"Supply contracting (${total_change/1e9:.1f}B), total ${total_supply/1e9:.1f}B")

async def compute_confluence() -> dict:
    """Compute overall confluence with directional awareness."""
    whale_score, whale_desc = await compute_whale_score()
    sentiment_score, sent_desc = await compute_sentiment_score()
    macro_score, macro_desc = await compute_macro_score()
    stable_score, stable_desc = await compute_stablecoin_score()
    
    overall = (
        whale_score * WEIGHTS["whale_activity"] +
        sentiment_score * WEIGHTS["sentiment"] +
        macro_score * WEIGHTS["macro_alignment"] +
        stable_score * WEIGHTS["stablecoin_flow"]
    )
    
    components = [
        {"name": "Whale Activity", "score": round(whale_score, 2), "detail": whale_desc},
        {"name": "Sentiment", "score": round(sentiment_score, 2), "detail": sent_desc},
        {"name": "Macro", "score": round(macro_score, 2), "detail": macro_desc},
        {"name": "Stablecoin Flows", "score": round(stable_score, 2), "detail": stable_desc},
    ]
    
    if overall > 0.65:
        signal = "STRONG"
    elif overall > 0.35:
        signal = "MODERATE"
    else:
        signal = "WEAK"
    
    # Get previous score for directional awareness
    db = await get_db()
    cursor = await db.execute(
        "SELECT overall_score FROM signal_confluences ORDER BY timestamp DESC LIMIT 1"
    )
    prev = await cursor.fetchone()
    await db.close()
    prev_score = prev["overall_score"] if prev else overall
    delta = overall - prev_score
    if delta > 0.05:
        direction = "RISING"
    elif delta < -0.05:
        direction = "FALLING"
    else:
        direction = "STABLE"
    
    result = {
        "overall_score": round(overall, 3),
        "signal": signal,
        "direction": direction,
        "components": components,
        "timestamp": int(__import__("time").time()),
    }
    
    # Store historical snapshot
    db = await get_db()
    await db.execute(
        "INSERT INTO signal_confluences (overall_score, signal, direction, components, timestamp) VALUES (?, ?, ?, ?, ?)",
        (result["overall_score"], result["signal"], result["direction"],
         json.dumps(result["components"]), result["timestamp"])
    )
    await db.commit()
    await db.close()
    
    return result
```

**Step 2: Verify the three fixes work**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.services.confluence import compute_confluence; r = asyncio.run(compute_confluence()); import json; print(json.dumps(r, indent=2))"
# Verify: sentiment score is between 0-1 (not always ≥0.5), stablecoin shows a reasonable number, macro has 4-part details
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add corrected confluence engine with directional awareness and historical storage"
```

---

### Task 6.2: Confluence API + unified WebSocket (all panels live)

**Objective:** REST endpoint for confluence + WebSocket pushes ALL panel data, not just confluence.

**Files:**
- Create: `backend/app/api/signals.py`
- Modify: `backend/main.py`

**Step 1: Unified WebSocket + REST routes**

`backend/app/api/signals.py`:
```python
"""Signal confluence API + unified WebSocket for all panels."""
import json
from fastapi import APIRouter, WebSocket
from app.services.confluence import compute_confluence
from app.database import get_db

router = APIRouter(tags=["signals"])

@router.get("/api/signals/confluence")
async def get_confluence():
    return await compute_confluence()

@router.get("/api/signals/history")
async def get_signal_history(limit: int = 50):
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM signal_confluences ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

# WebSocket management
connected_ws = set()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_ws.add(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive
            # Client can send "ping" or "refresh" to get full state
    except Exception:
        pass
    finally:
        connected_ws.discard(ws)

async def broadcast_full_state():
    """Push confluence + all panel summaries to every connected client."""
    if not connected_ws:
        return
    
    confluence = await compute_confluence()
    db = await get_db()
    
    # Gather panel snapshots
    w_cursor = await db.execute(
        "SELECT * FROM whale_transactions ORDER BY timestamp DESC LIMIT 5"
    )
    whales = [dict(r) for r in await w_cursor.fetchall()]
    
    s_cursor = await db.execute(
        "SELECT AVG(score) as avg_score, COUNT(*) as count FROM sentiment_scores WHERE timestamp > strftime('%s', 'now') - 7200"
    )
    sentiment = dict(await s_cursor.fetchone())
    
    m_cursor = await db.execute(
        "SELECT indicator, value FROM macro_data WHERE indicator IN ('DXY','BTC','SP500','GOLD') GROUP BY indicator HAVING MAX(timestamp)"
    )
    macro = {r["indicator"]: r["value"] for r in await m_cursor.fetchall()}
    
    sc_cursor = await db.execute(
        "SELECT stablecoin, total_supply_usd, change_24h_usd FROM stablecoin_supply GROUP BY stablecoin HAVING MAX(timestamp)"
    )
    stablecoins = [dict(r) for r in await sc_cursor.fetchall()]
    
    await db.close()
    
    payload = json.dumps({
        "confluence": confluence,
        "whales": whales,
        "sentiment": sentiment,
        "macro": macro,
        "stablecoins": stablecoins,
    })
    
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
git add -A && git commit -m "feat: add unified WebSocket broadcasting all panel data every 60s"
```

---

### Phase 7: Frontend Dashboard

---

### Task 7.1: Dashboard shell + responsive layout

**Objective:** Create the React dashboard shell with 2×2 grid, dark theme, responsive stacking.

**Files:**
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/components/Dashboard.jsx`
- Create: `frontend/src/components/Panel.jsx`

**Step 1: Write global CSS with Tailwind**

`frontend/src/index.css`:
```css
@import "tailwindcss";

:root {
  --bg-primary: #0a0a0f;
  --bg-card: #13131a;
  --border-color: #1e1e2e;
  --accent-cyan: #06b6d4;
  --accent-green: #10b981;
  --accent-red: #ef4444;
  --accent-amber: #f59e0b;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, sans-serif;
}
```

**Step 2: Panel component**

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

**Step 3: Dashboard grid — responsive**

`frontend/src/components/Dashboard.jsx`:
```jsx
import Panel from "./Panel";
import OnChainPanel from "./panels/OnChainPanel";
import SentimentPanel from "./panels/SentimentPanel";
import MacroPanel from "./panels/MacroPanel";
import StablecoinPanel from "./panels/StablecoinPanel";
import SignalBar from "./SignalBar";

export default function Dashboard() {
  return (
    <div className="min-h-screen p-4 md:p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-cyan-400">Crypto Command Center</h1>
        <p className="text-slate-500 text-sm">On-Chain · Sentiment · Macro · Stablecoin</p>
      </header>
      
      <SignalBar />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <Panel title="On-Chain Intelligence"><OnChainPanel /></Panel>
        <Panel title="AI Sentiment"><SentimentPanel /></Panel>
        <Panel title="Macro × Crypto"><MacroPanel /></Panel>
        <Panel title="Stablecoin Flows"><StablecoinPanel /></Panel>
      </div>
    </div>
  );
}
```

**Step 4: App.jsx entry**

`frontend/src/App.jsx`:
```jsx
import Dashboard from "./components/Dashboard";
export default function App() { return <Dashboard />; }
```

**Step 5: Commit**

```bash
git add -A && git commit -m "feat: create responsive dashboard shell with 2x2 grid"
```

---

### Task 7.2: Signal bar with WebSocket live updates + directional awareness

**Objective:** Top bar showing confluence score, direction (RISING/FALLING/STABLE), and component breakdown.

**Files:**
- Create: `frontend/src/components/SignalBar.jsx`

**Step 1: Write SignalBar**

`frontend/src/components/SignalBar.jsx`:
```jsx
import { useState, useEffect } from "react";

const SIGNAL_COLORS = {
  STRONG: "bg-green-500",
  MODERATE: "bg-amber-500",
  WEAK: "bg-red-500",
};

const DIRECTION_ICONS = {
  RISING: "▲",
  FALLING: "▼",
  STABLE: "→",
};

export default function SignalBar() {
  const [confluence, setConfluence] = useState(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setConfluence(data.confluence);
    };
    return () => socket.close();
  }, []);

  useEffect(() => {
    fetch("/api/signals/confluence")
      .then((r) => r.json())
      .then(setConfluence);
  }, []);

  const overall = confluence?.overall_score ?? 0;
  const signal = confluence?.signal ?? "WEAK";
  const direction = confluence?.direction ?? "STABLE";

  return (
    <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4 mb-4">
      <div className="flex items-center gap-4">
        <div className={`px-3 py-1 rounded font-bold text-sm text-white ${SIGNAL_COLORS[signal]}`}>
          {signal} <span className="ml-1">{DIRECTION_ICONS[direction]}</span>
        </div>
        <div className="flex-1">
          <div className="text-xs text-slate-500 mb-1">Confluence Score</div>
          <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-red-500 via-amber-500 to-emerald-500 transition-all duration-500"
              style={{ width: `${(overall * 100).toFixed(0)}%` }}
            />
          </div>
        </div>
        <div className="text-2xl font-mono font-bold text-cyan-400">
          {(overall * 100).toFixed(0)}%
        </div>
      </div>
      {confluence?.components && (
        <div className="grid grid-cols-4 gap-2 mt-3 text-xs text-slate-400">
          {confluence.components.map((c) => (
            <div key={c.name} className="text-center" title={c.detail}>
              <div className="text-[10px] uppercase">{c.name}</div>
              <div className="font-mono text-white">{(c.score * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add signal bar with WebSocket live updates and directional arrows"
```

---

### Task 7.3: On-Chain panel with auto-refresh, loading, and error states

**Objective:** Table of recent whale transactions with auto-refresh (60s) and proper UI states.

**Files:**
- Create: `frontend/src/components/panels/OnChainPanel.jsx`

**Step 1: Write component**

`frontend/src/components/panels/OnChainPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

export default function OnChainPanel() {
  const [whales, setWhales] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    Promise.all([
      fetch("/api/onchain/whales?limit=5&min_usd=500000").then((r) => r.json()),
      fetch("/api/onchain/stats").then((r) => r.json()),
    ])
      .then(([w, s]) => { setWhales(w); setStats(s); setError(null); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 60000); return () => clearInterval(t); }, []);

  const formatUsd = (v) =>
    v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : `$${v.toFixed(0)}`;

  if (loading) return <p className="text-slate-500 text-xs">Loading...</p>;
  if (error) return <p className="text-red-400 text-xs">Error: {error}</p>;

  return (
    <div>
      {stats && (
        <div className="flex gap-3 mb-3 text-xs">
          <span className="text-slate-500">24h whales: <b className="text-cyan-400">{stats.total_whales}</b></span>
          <span className="text-slate-500">Max: <b className="text-white">{formatUsd(stats.max_amount)}</b></span>
        </div>
      )}
      {whales.length === 0 ? (
        <p className="text-slate-600 text-xs">No whale activity in this window</p>
      ) : (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {whales.map((w) => (
            <div key={w.tx_hash} className="flex justify-between text-xs border-b border-[#1e1e2e] pb-1">
              <span className="text-slate-400 font-mono">{w.tx_hash.slice(0, 10)}...</span>
              <span className="text-cyan-400 font-mono">{formatUsd(w.amount_usd)}</span>
              <span className="text-slate-500">{w.asset}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add on-chain panel with auto-refresh, loading, error, and empty states"
```

---

### Task 7.4: Sentiment panel with auto-refresh and states

**Objective:** Gauge showing aggregate sentiment with recent posts. Uses same state pattern.

**Files:**
- Create: `frontend/src/components/panels/SentimentPanel.jsx`

**Step 1: Write component**

`frontend/src/components/panels/SentimentPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

export default function SentimentPanel() {
  const [trend, setTrend] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    Promise.all([
      fetch("/api/sentiment/trend").then((r) => r.json()),
      fetch("/api/sentiment/scores?limit=5").then((r) => r.json()),
    ])
      .then(([t, p]) => { setTrend(t); setPosts(p); setError(null); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 60000); return () => clearInterval(t); }, []);

  if (loading) return <p className="text-slate-500 text-xs">Loading...</p>;
  if (error) return <p className="text-red-400 text-xs">Error: {error}</p>;

  const score = trend?.avg_score ?? 0;
  const gaugeAngle = (score + 1) * 90;

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <div className="relative w-16 h-8 overflow-hidden">
          <div className="absolute bottom-0 left-0 w-full h-16 rounded-t-full bg-[#1e1e2e]">
            <div
              className="absolute bottom-0 left-1/2 w-1 h-8 bg-gradient-to-t from-red-500 via-amber-400 to-green-400 origin-bottom transition-transform duration-500"
              style={{ transform: `rotate(${gaugeAngle - 90}deg)` }}
            />
          </div>
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs font-bold text-white">
            {score > 0.1 ? "🐂" : score < -0.1 ? "🐻" : "➖"}
          </div>
        </div>
        <div className="text-xs text-slate-500">
          {trend?.count ?? 0} posts · {(score * 100).toFixed(0)}% net
        </div>
      </div>
      {posts.length === 0 ? (
        <p className="text-slate-600 text-xs">No sentiment data yet</p>
      ) : (
        <div className="space-y-1 max-h-40 overflow-y-auto">
          {posts.map((p, i) => (
            <div key={i} className="text-xs border-b border-[#1e1e2e] pb-1">
              <div className="flex justify-between">
                <span className={`font-mono ${p.score > 0 ? "text-green-400" : p.score < 0 ? "text-red-400" : "text-slate-400"}`}>
                  {(p.score * 100).toFixed(0)}%
                </span>
                <span className="text-slate-500">{p.source}</span>
              </div>
              <div className="text-slate-400 truncate">{p.summary}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add sentiment panel with auto-refresh and full state handling"
```

---

### Task 7.5: Macro overlay panel with TradingView chart + ResizeObserver

**Objective:** Multi-line chart with DXY, BTC overlay, correlation display, responsive resize.

**Files:**
- Create: `frontend/src/components/panels/MacroPanel.jsx`

**Step 1: Write component**

`frontend/src/components/panels/MacroPanel.jsx`:
```jsx
import { useState, useEffect, useRef, useCallback } from "react";
import { createChart } from "lightweight-charts";

export default function MacroPanel() {
  const chartRef = useRef(null);
  const containerRef = useRef(null);
  const [latest, setLatest] = useState([]);
  const [correlation, setCorrelation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLatest = useCallback(() => {
    fetch("/api/macro/latest").then((r) => r.json()).then(setLatest).catch(() => {});
    fetch("/api/macro/correlation?pair=BTC-DXY&hours=168").then((r) => r.json()).then(setCorrelation).catch(() => {});
  }, []);

  useEffect(() => {
    fetchLatest();
    const t = setInterval(fetchLatest, 300000); // 5 min
    return () => clearInterval(t);
  }, [fetchLatest]);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 220,
      layout: { background: { color: "#13131a" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#1e1e2e" }, horzLines: { color: "#1e1e2e" } },
      timeScale: { timeVisible: false },
      rightPriceScale: { borderColor: "#1e1e2e" },
      crosshair: { mode: 0 },
    });

    Promise.all([
      fetch("/api/macro/history?indicator=BTC&hours=168").then((r) => r.json()),
      fetch("/api/macro/history?indicator=DXY&hours=168").then((r) => r.json()),
    ]).then(([btc, dxy]) => {
      const btcSeries = chart.addLineSeries({
        color: "#f7931a", lineWidth: 2,
        priceFormat: { type: "price", minMove: 0.01 },
      });
      const dxySeries = chart.addLineSeries({
        color: "#06b6d4", lineWidth: 1,
        priceScaleId: "dxy",
      });
      chart.priceScale("dxy").applyOptions({ borderColor: "#06b6d4", textColor: "#06b6d4" });
      btcSeries.setData(btc.map((d) => ({ time: Math.floor(d.timestamp), value: d.value })));
      dxySeries.setData(dxy.map((d) => ({ time: Math.floor(d.timestamp), value: d.value })));
      setLoading(false);
    }).catch((e) => { setError(e.message); setLoading(false); });

    const observer = new ResizeObserver(() => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    });
    observer.observe(containerRef.current);

    return () => { observer.disconnect(); chart.remove(); };
  }, []);

  const indicators = { DXY: "💵", SP500: "📈", GOLD: "🥇", FEDFUNDS: "🏦", BTC: "₿", ETH: "Ξ" };

  if (error) return <p className="text-red-400 text-xs">Chart error: {error}</p>;

  return (
    <div>
      <div className="flex gap-2 mb-2 flex-wrap">
        {latest.map((d) => (
          <div key={d.indicator} className="bg-[#1e1e2e] px-2 py-1 rounded text-xs">
            <span>{indicators[d.indicator] || ""}</span>{" "}
            <span className="text-slate-400">{d.indicator}</span>{" "}
            <span className="text-white font-mono">
              {d.value > 1000 ? `$${d.value.toLocaleString()}` : d.value.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
      {correlation && (
        <div className="text-xs text-slate-500 mb-1">
          BTC↔DXY correlation:{" "}
          <span className={correlation.correlation < -0.5 ? "text-green-400" : "text-amber-400"}>
            {correlation.correlation?.toFixed(2) ?? "N/A"}
          </span>
        </div>
      )}
      {loading && <p className="text-slate-500 text-xs">Loading chart...</p>}
      <div ref={containerRef} className="w-full" />
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add macro panel with TradingView chart, ResizeObserver, and DXY correlation"
```

---

### Task 7.6: Stablecoin panel with auto-refresh and states

**Objective:** Bar chart of stablecoin supply with 24h change indicators.

**Files:**
- Create: `frontend/src/components/panels/StablecoinPanel.jsx`

**Step 1: Write component**

`frontend/src/components/panels/StablecoinPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

export default function StablecoinPanel() {
  const [supply, setSupply] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    fetch("/api/stablecoin/supply")
      .then((r) => r.json())
      .then((data) => { setSupply(data); setError(null); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 60000); return () => clearInterval(t); }, []);

  const COLORS = { USDT: "#26a17b", USDC: "#2775ca", DAI: "#fab005", USDe: "#6366f1" };
  const maxSupply = Math.max(...supply.map((s) => s.total_supply_usd || 0), 1);

  if (loading) return <p className="text-slate-500 text-xs">Loading...</p>;
  if (error) return <p className="text-red-400 text-xs">Error: {error}</p>;
  if (supply.length === 0) return <p className="text-slate-600 text-xs">No supply data yet</p>;

  return (
    <div>
      <div className="space-y-2">
        {supply.map((s) => (
          <div key={s.stablecoin}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">{s.stablecoin}</span>
              <span className="text-white font-mono">${(s.total_supply_usd / 1e9).toFixed(1)}B</span>
              {s.change_24h_usd !== 0 && (
                <span className={`font-mono ${s.change_24h_usd > 0 ? "text-green-400" : "text-red-400"}`}>
                  {s.change_24h_usd > 0 ? "+" : ""}${(Math.abs(s.change_24h_usd) / 1e6).toFixed(0)}M
                </span>
              )}
            </div>
            <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${((s.total_supply_usd || 0) / maxSupply) * 100}%`,
                  background: COLORS[s.stablecoin] || "#6366f1"
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add stablecoin panel with supply bars, 24h deltas, and auto-refresh"
```

---

### Phase 8: Integration, Build & Ship

---

### Task 8.1: Production build setup (fixed Makefile + correct mount order)

**Objective:** FastAPI serves the built React app as static files. Fixed Makefile with direct venv Python paths. Static mount AFTER all API routers.

**Files:**
- Modify: `backend/main.py` (add static mount at END)
- Create: `Makefile`

**Step 1: Add static file mount at the VERY END of main.py**

At the **bottom** of `backend/main.py`, after ALL `app.include_router()` calls:

```python
# Static file mount — MUST be last, after all API routers
from fastapi.staticfiles import StaticFiles
from pathlib import Path

frontend_build = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
```

**Step 2: Create fixed Makefile**

`Makefile`:
```makefile
.PHONY: install dev build run test clean

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

test:
	cd backend && $(VENV_PYTHON) -m pytest tests/ -v

clean:
	rm -rf frontend/dist backend/data/*.db backend/__pycache__ backend/app/**/__pycache__
```

**Step 3: Build and verify full stack**

```bash
cd /Users/tn/dev/crypto-dashboard
make build
make run &
sleep 3
# Test API still works (not shadowed by static mount)
curl -s http://localhost:8000/api/health
# Expected: {"status":"ok"}
curl -s http://localhost:8000/api/signals/confluence | python3 -m json.tool | head -10
# Test frontend served
curl -s http://localhost:8000/ | head -5
# Expected: HTML from React build
kill %1
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: production build setup with fixed Makefile and correct static mount order"
```

---

### Task 8.2: Final main.py — all routers assembled

**Objective:** Ensure main.py has ALL router includes in the correct order: API routers first, then static mount.

`backend/main.py` — final structure:
```python
"""Crypto Command Center — FastAPI backend."""
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.services.scheduler import start_collectors

# Import all routers
from app.api.onchain import router as onchain_router
from app.api.sentiment import router as sentiment_router
from app.api.macro import router as macro_router
from app.api.stablecoin import router as stablecoin_router
from app.api.signals import router as signals_router, broadcast_full_state

app = FastAPI(title="Crypto Command Center", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ALL API routers before static mount
app.include_router(onchain_router)
app.include_router(sentiment_router)
app.include_router(macro_router)
app.include_router(stablecoin_router)
app.include_router(signals_router)

@app.on_event("startup")
async def startup():
    try:
        await init_db()
        start_collectors()
        print("[startup] Ready — all collectors running")
    except Exception as e:
        print(f"[startup] FATAL: {e}")
        import sys; sys.exit(1)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Static file mount — MUST be LAST
from fastapi.staticfiles import StaticFiles
from pathlib import Path
frontend_build = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**Step 2: Verify full stack again**

Same verification as Task 8.1 — ensure API and frontend both work.

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: assemble all routers in correct order — API before static mount"
```

---

### Task 8.3: GitHub repo + push

**Objective:** Push to GitHub as `tokenburner7/crypto-command-center`.

```bash
cd /Users/tn/dev/crypto-dashboard
gh repo create crypto-command-center --public --source=. --remote=origin --push
gh repo view tokenburner7/crypto-command-center --web
```

---

## Implementation Notes

### Bug Fixes Applied (from adversarial review)

| Bug | Fix |
|-----|-----|
| `max(0, avg)` deleting bearish sentiment | Normalize to [0,1] range preserving negative signals |
| `SUM(amount)` on duplicate supply readings | `GROUP BY stablecoin` + latest reading only |
| `compute_macro_score` ignoring 3/4 indicators | Now uses DXY, FEDFUNDS, GOLD, SP500 with weighted components |
| Exchange flow stub with all zeroes | CoinGecko exchange volumes as proxy (v1) |
| from_address/to_address always NULL | Parsed from Blockchain.info inputs/outputs |
| Reddit 429 without User-Agent | APIClient now includes default User-Agent |
| 40 sequential OpenAI calls | Batched into single LLM call |
| Hardcoded "USDT" in stablecoin events | Single schema with per-stablecoin tracking |
| Static mount shadowing API routes | Mount AFTER all routers |
| Makefile `source` in sub-shell | Direct `venv/bin/python` paths |
| `.env` never loaded | `load_dotenv()` at top of `main.py` |
| `0.0` inserted on FRED failure | Returns `None`, skipped on insert |
| No directional awareness | `direction` field: RISING/FALLING/STABLE |
| No `.gitignore` | Added with node_modules, venv, *.db, .env |
| Missing WAL mode | `PRAGMA journal_mode=WAL` in init |
| `REAL` timestamps on UNIQUE | Changed to `INTEGER` |

### Data Sources

| Tier | APIs Used | Auth Required |
|------|-----------|---------------|
| **Free (works now)** | Reddit JSON, DefiLlama, CoinGecko, Blockchain.info, FRED | Free FRED key |
| **Enhanced (recommended)** | OpenAI (sentiment, batched) | `OPENAI_API_KEY` in `.env` |

### Future Enhancements (v2+)

1. **X/Twitter sentiment** — integrate `xurl` tool or X API for CT influencer tracking
2. **Whale Alert API** — real-time multi-chain whale alerts
3. **On-chain exchange flows** — Glassnode/Arkham address tagging for real inflow/outflow
4. **Telegram alerting** — cronjob fires when confluence crosses STRONG threshold
5. **Narrative detection** — LLM topic clustering to identify emerging narratives
6. **Percentile-based thresholds** — replace hardcoded magic numbers with rolling percentile baselines

### Running the Dashboard

```bash
cd /Users/tn/dev/crypto-dashboard
make install   # first time: create venv + install deps
make build     # build React frontend
make run       # start FastAPI on :8000
# Open http://localhost:8000
```
