# Crypto Command Center — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** A single unified web dashboard combining on-chain intelligence, AI-powered sentiment analysis, macro/crypto overlay, and stablecoin flow tracking — with a signal confluence engine that surfaces high-conviction moments.

**Architecture:** FastAPI backend (Python 3.12) with async data ingestion from 8+ public APIs, SQLite persistence, WebSocket live updates. React 18 + Vite frontend with TradingView Lightweight Charts and Tailwind CSS. Four panel components + a signal overlay bar. Backend serves the built React app as static files — single deployable unit.

**Tech Stack:** Python 3.12, FastAPI, httpx, aiosqlite, Pydantic v2 / React 18, Vite 6, Tailwind CSS 4, lightweight-charts (TradingView), Recharts / APScheduler, OpenAI API (sentiment)

---

### Phase 0: Project Scaffold

---

### Task 0.1: Create project structure and initialize repos

**Objective:** Create the monorepo with backend and frontend directories, initialize git, install core dependencies.

**Files:**
- Create: `crypto-dashboard/backend/requirements.txt`
- Create: `crypto-dashboard/backend/main.py`
- Create: `crypto-dashboard/frontend/` (via Vite)
- Create: `crypto-dashboard/README.md`

**Step 1: Create directory and git init**

```bash
mkdir -p /Users/tn/dev/crypto-dashboard/backend/app/{api,models,services,collectors}
mkdir -p /Users/tn/dev/crypto-dashboard/backend/tests
cd /Users/tn/dev/crypto-dashboard && git init
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

**Step 4: Create minimal FastAPI main.py**

`backend/main.py`:
```python
"""Crypto Command Center — FastAPI backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Crypto Command Center", version="0.1.0")

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

**Step 5: Verify backend starts**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
timeout 5 python main.py 2>&1 || true
# Expected: "Uvicorn running on http://0.0.0.0:8000"
```

**Step 6: Scaffold React frontend**

```bash
cd /Users/tn/dev/crypto-dashboard
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite lightweight-charts recharts lucide-react
```

**Step 7: Configure Tailwind**

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

**Step 8: Commit**

```bash
cd /Users/tn/dev/crypto-dashboard
git add -A && git commit -m "chore: scaffold project with FastAPI backend + React/Vite frontend"
```

---

### Phase 1: Data Layer

---

### Task 1.1: Create database schema and connection module

**Objective:** Set up SQLite schema for all four panels with aiosqlite async wrapper.

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/schemas.py`

**Step 1: Write database module**

`backend/app/database.py`:
```python
"""Async SQLite database module."""
import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "ccc.db"

async def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    return db

async def init_db():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS whale_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT UNIQUE,
            blockchain TEXT NOT NULL,
            from_address TEXT,
            to_address TEXT,
            amount_usd REAL,
            asset TEXT,
            timestamp REAL NOT NULL,
            created_at REAL DEFAULT (strftime('%s', 'now'))
        );
        
        CREATE TABLE IF NOT EXISTS exchange_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT NOT NULL,
            asset TEXT NOT NULL,
            inflow_usd REAL,
            outflow_usd REAL,
            net_flow_usd REAL,
            timestamp REAL NOT NULL,
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
            timestamp REAL NOT NULL,
            UNIQUE(source, url, timestamp)
        );
        
        CREATE TABLE IF NOT EXISTS macro_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp REAL NOT NULL,
            UNIQUE(indicator, timestamp)
        );
        
        CREATE TABLE IF NOT EXISTS stablecoin_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stablecoin TEXT NOT NULL,
            event_type TEXT NOT NULL,
            amount REAL,
            chain TEXT,
            tx_hash TEXT UNIQUE,
            timestamp REAL NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS signal_confluences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_type TEXT NOT NULL,
            strength REAL NOT NULL,
            components TEXT,
            description TEXT,
            timestamp REAL NOT NULL
        );
        
        -- Indexes for time-range queries
        CREATE INDEX IF NOT EXISTS idx_whale_ts ON whale_transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_sentiment_ts ON sentiment_scores(timestamp);
        CREATE INDEX IF NOT EXISTS idx_macro_ts ON macro_data(timestamp);
        CREATE INDEX IF NOT EXISTS idx_stablecoin_ts ON stablecoin_events(timestamp);
    """)
    await db.commit()
    await db.close()
```

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
    timestamp: float

class ExchangeFlow(BaseModel):
    exchange: str
    asset: str
    inflow_usd: float
    outflow_usd: float
    net_flow_usd: float
    timestamp: float

class SentimentScore(BaseModel):
    source: str
    topic: Optional[str] = None
    score: float
    confidence: Optional[float] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    timestamp: float

class MacroPoint(BaseModel):
    indicator: str
    value: float
    timestamp: float

class StablecoinEvent(BaseModel):
    stablecoin: str
    event_type: str
    amount: Optional[float] = None
    chain: Optional[str] = None
    tx_hash: Optional[str] = None
    timestamp: float

class SignalConfluence(BaseModel):
    signal_type: str
    strength: float
    components: list[str]
    description: str
    timestamp: float
```

**Step 3: Write database init script**

`backend/init_db.py`:
```python
"""Initialize the database."""
import asyncio
from app.database import init_db
asyncio.run(init_db())
print("Database initialized.")
```

**Step 4: Run init and verify**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python init_db.py
python3 -c "import aiosqlite, asyncio; asyncio.run(aiosqlite.connect('data/ccc.db')); print('OK')"
# Expected: Database initialized.  OK
```

**Step 5: Commit**

```bash
cd /Users/tn/dev/crypto-dashboard
git add -A && git commit -m "feat: add SQLite schema and Pydantic models for all 4 panels"
```

---

### Task 1.2: Create async HTTP client with rate limiting

**Objective:** Shared httpx client with retry logic, rate limiting, and API key management.

**Files:**
- Create: `backend/app/services/http_client.py`
- Create: `backend/.env.example`

**Step 1: Write HTTP client**

`backend/app/services/http_client.py`:
```python
"""Shared async HTTP client with retry and rate limiting."""
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
    
    async def get(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None, retries: int = 3):
        await self.limiter.acquire()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(retries):
                try:
                    resp = await client.get(f"{self.base_url}{url}", params=params, headers=headers)
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
```

**Step 2: Create .env example**

`backend/.env.example`:
```
# API Keys (optional — many sources work without keys on free tier)
ETHERSCAN_API_KEY=
WHALE_ALERT_API_KEY=
OPENAI_API_KEY=
X_BEARER_TOKEN=
NEWSAPI_KEY=
FRED_API_KEY=
COINGECKO_API_KEY=
```

**Step 3: Verify**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "from app.services.http_client import APIClient; print('Import OK')"
# Expected: Import OK
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: add async HTTP client with rate limiting"
```

---

### Phase 2: On-Chain Intelligence Panel

---

### Task 2.1: Whale transaction collector

**Objective:** Fetch large transactions from Blockchain.com and Whale Alert APIs, store in DB.

**Files:**
- Create: `backend/app/collectors/whale_collector.py`

**Step 1: Write collector**

`backend/app/collectors/whale_collector.py`:
```python
"""Collect whale transactions from Blockchain.com and Whale Alert."""
import asyncio
import time
import os
from app.database import get_db
from app.services.http_client import APIClient

WHALE_THRESHOLD_USD = 1_000_000  # $1M+

blockchain_client = APIClient(base_url="https://blockchain.info", rate_limit=0.5)

async def fetch_blockchain_large_txs():
    """Fetch latest large BTC transactions from Blockchain.info."""
    try:
        data = await blockchain_client.get("/unconfirmed-transactions?format=json")
        txs = []
        for tx in data[:50]:  # limit to 50
            total_out = sum(out.get("value", 0) for out in tx.get("out", [])) / 1e8
            usd_value = total_out * await _get_btc_price()
            if usd_value >= WHALE_THRESHOLD_USD:
                txs.append({
                    "tx_hash": tx["hash"],
                    "blockchain": "bitcoin",
                    "amount_usd": round(usd_value, 2),
                    "asset": "BTC",
                    "timestamp": tx.get("time", time.time()),
                })
        return txs
    except Exception as e:
        print(f"Blockchain.info error: {e}")
        return []

_price_cache = {"btc": None, "btc_ts": 0}

async def _get_btc_price():
    now = time.time()
    if _price_cache["btc_ts"] and (now - _price_cache["btc_ts"]) < 300:
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
        try:
            await db.execute(
                """INSERT OR IGNORE INTO whale_transactions 
                   (tx_hash, blockchain, amount_usd, asset, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (tx["tx_hash"], tx["blockchain"], tx["amount_usd"], tx["asset"], tx["timestamp"])
            )
        except Exception:
            pass
    await db.commit()
    await db.close()

async def collect_whales():
    """Main collector — call every 5 minutes."""
    txs = await fetch_blockchain_large_txs()
    if txs:
        await save_whale_txs(txs)
        print(f"Collected {len(txs)} whale txns")
    return len(txs)
```

**Step 2: Test standalone run**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "
import asyncio
from app.collectors.whale_collector import collect_whales
asyncio.run(collect_whales())
"
# Expected: Collected N whale txns (or 0 if no large txns right now)
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add whale transaction collector (Blockchain.info)"
```

---

### Task 2.2: Exchange flow collector (DefiLlama)

**Objective:** Fetch CEX/DEX inflows and outflows from DefiLlama API.

**Files:**
- Create: `backend/app/collectors/exchange_collector.py`

**Step 1: Write collector**

`backend/app/collectors/exchange_collector.py`:
```python
"""Collect exchange flow data from DefiLlama."""
import time
from app.database import get_db
from app.services.http_client import APIClient

llama = APIClient(base_url="https://api.llama.fi", rate_limit=0.5)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

async def fetch_exchange_flows():
    """Fetch net flows for major BTC exchanges."""
    try:
        # DefiLlama doesn't have a direct CEX flow endpoint,
        # but we can approximate via their volume data
        data = await llama.get("/overview/dexs")
        # For real CEX flows, we use the CoinGecko exchange volume endpoint
        exchanges = ["Binance", "Coinbase", "Kraken", "Bybit", "OKX"]
        results = []
        for ex in exchanges:
            try:
                vol_data = await coingecko.get(
                    "/exchanges", 
                    params={"per_page": 10}
                )
                results.append({
                    "exchange": ex,
                    "asset": "BTC",
                    "inflow_usd": 0.0,  # placeholder — real data needs on-chain analysis
                    "outflow_usd": 0.0,
                    "net_flow_usd": 0.0,
                    "timestamp": time.time()
                })
            except Exception:
                continue
        return results
    except Exception as e:
        print(f"Exchange flow error: {e}")
        return []

async def collect_exchange_flows():
    flows = await fetch_exchange_flows()
    if flows:
        db = await get_db()
        for f in flows:
            await db.execute(
                """INSERT OR REPLACE INTO exchange_flows 
                   (exchange, asset, inflow_usd, outflow_usd, net_flow_usd, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f["exchange"], f["asset"], f["inflow_usd"], f["outflow_usd"], f["net_flow_usd"], f["timestamp"])
            )
        await db.commit()
        await db.close()
    return len(flows)
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add exchange flow collector skeleton (DefiLlama/CoinGecko)"
```

---

### Task 2.3: On-Chain API endpoints + background scheduler

**Objective:** Wire up FastAPI routes for on-chain data and start APScheduler for collectors.

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

@router.get("/flows")
async def get_exchange_flows(limit: int = 50):
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
from app.collectors.whale_collector import collect_whales
from app.collectors.exchange_collector import collect_exchange_flows

scheduler = AsyncIOScheduler()

def start_collectors():
    scheduler.add_job(collect_whales, "interval", minutes=5, id="whales")
    scheduler.add_job(collect_exchange_flows, "interval", minutes=15, id="flows")
    scheduler.start()
```

**Step 3: Update main.py to mount router and start scheduler**

Modify `backend/main.py` — add after `app = FastAPI(...)`:

```python
from app.api.onchain import router as onchain_router
from app.database import init_db
from app.services.scheduler import start_collectors

app.include_router(onchain_router)

@app.on_event("startup")
async def startup():
    await init_db()
    start_collectors()
```

**Step 4: Verify API works**

```bash
# In one terminal:
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python main.py &
sleep 3
curl -s http://localhost:8000/api/onchain/whales | python3 -m json.tool | head -20
curl -s http://localhost:8000/api/onchain/stats
# Expected: JSON arrays/objects with whale data
kill %1
```

**Step 5: Commit**

```bash
git add -A && git commit -m "feat: add on-chain API endpoints and background scheduler"
```

---

### Phase 3: AI Sentiment Aggregator

---

### Task 3.1: Reddit + News sentiment collector

**Objective:** Fetch crypto-related posts from Reddit and news, run LLM sentiment scoring.

**Files:**
- Create: `backend/app/collectors/sentiment_collector.py`

**Step 1: Write sentiment collector**

`backend/app/collectors/sentiment_collector.py`:
```python
"""Collect and score crypto sentiment from Reddit, news, X."""
import asyncio
import time
import json
import os
from app.database import get_db
from app.services.http_client import APIClient

# Free Reddit JSON API — no auth needed for public subreddits
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
                "created_utc": d["created_utc"],
            })
        return results
    except Exception as e:
        print(f"Reddit error ({subreddit}): {e}")
        return []

async def score_sentiment(text: str) -> dict:
    """Score sentiment using OpenAI or keyword fallback."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "Score crypto sentiment from -1 (extremely bearish) to 1 (extremely bullish). Return JSON: {\"score\": float, \"topic\": str, \"summary\": str}"
            }, {
                "role": "user",
                "content": text[:1000]
            }],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    else:
        # Keyword fallback
        bullish = ["bullish", "moon", "pump", "breakout", "rally", "buy", "long", "green"]
        bearish = ["bearish", "dump", "crash", "collapse", "sell", "short", "red", "fear"]
        text_lower = text.lower()
        b_count = sum(1 for w in bullish if w in text_lower)
        a_count = sum(1 for w in bearish if w in text_lower)
        total = b_count + a_count
        score = (b_count - a_count) / max(total, 1)
        return {"score": round(score, 3), "topic": "crypto", "summary": text[:200]}

async def collect_sentiment():
    posts = []
    for sub in CRYPTO_SUBREDDITS:
        posts.extend(await fetch_reddit_posts(sub, limit=10))
    
    db = await get_db()
    count = 0
    for post in posts:
        text = f"{post['title']}\n{post['text']}"
        sentiment = await score_sentiment(text)
        try:
            await db.execute(
                """INSERT OR IGNORE INTO sentiment_scores 
                   (source, topic, score, confidence, summary, url, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("reddit", sentiment.get("topic", "crypto"),
                 sentiment["score"], None,
                 sentiment.get("summary", ""),
                 post["url"], post["created_utc"])
            )
            count += 1
        except Exception:
            pass
    
    await db.commit()
    await db.close()
    return count
```

**Step 2: Test**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.collectors.sentiment_collector import collect_sentiment; print(asyncio.run(collect_sentiment()))"
# Expected: N (number of posts collected)
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add Reddit sentiment collector with LLM/keyword scoring"
```

---

### Task 3.2: Sentiment API + scheduler integration

**Objective:** FastAPI routes + add to scheduler.

**Files:**
- Create: `backend/app/api/sentiment.py`
- Modify: `backend/main.py`
- Modify: `backend/app/services/scheduler.py`

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

**Step 2: Add to main.py**

Add in main.py:
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

**Step 4: Verify**

```bash
curl -s http://localhost:8000/api/sentiment/trend | python3 -m json.tool
```

**Step 5: Commit**

```bash
git add -A && git commit -m "feat: add sentiment API endpoints and scheduler job"
```

---

### Phase 4: Macro × Crypto Overlay

---

### Task 4.1: Macro data collector (FRED + Yahoo Finance)

**Objective:** Fetch DXY, Fed funds rate, gold, S&P 500, and overlay with BTC.

**Files:**
- Create: `backend/app/collectors/macro_collector.py`

**Step 1: Write macro collector**

`backend/app/collectors/macro_collector.py`:
```python
"""Collect macro indicators from FRED and Yahoo Finance."""
import time
import os
from app.database import get_db
from app.services.http_client import APIClient

fred = APIClient(base_url="https://api.stlouisfed.org/fred", rate_limit=0.5)
yahoo = APIClient(base_url="https://query1.finance.yahoo.com/v8/finance", rate_limit=0.5)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

FRED_SERIES = {
    "DXY": "DTWEXBGS",      # Trade-weighted USD index
    "FEDFUNDS": "FEDFUNDS", # Fed funds rate
    "GOLD": "GOLDAMGBD228NLBR",  # Gold fixing price
    "SP500": "SP500",       # S&P 500
}

async def fetch_fred_series(series_id: str) -> float:
    api_key = os.getenv("FRED_API_KEY", "")
    params = {"series_id": series_id, "sort_order": "desc", "limit": 1, "file_type": "json"}
    if api_key:
        params["api_key"] = api_key
    try:
        data = await fred.get("/series/observations", params=params)
        obs = data.get("observations", [])
        if obs:
            return float(obs[0]["value"])
    except Exception as e:
        print(f"FRED error ({series_id}): {e}")
    return 0.0

async def fetch_crypto_prices():
    """Fetch BTC and ETH prices in USD."""
    try:
        data = await coingecko.get(
            "/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd"}
        )
        return {
            "BTC": data.get("bitcoin", {}).get("usd", 0),
            "ETH": data.get("ethereum", {}).get("usd", 0),
        }
    except Exception:
        return {"BTC": 0, "ETH": 0}

async def collect_macro():
    now = time.time()
    db = await get_db()
    
    # Fetch FRED data
    for name, series_id in FRED_SERIES.items():
        value = await fetch_fred_series(series_id)
        if value:
            await db.execute(
                "INSERT OR REPLACE INTO macro_data (indicator, value, timestamp) VALUES (?, ?, ?)",
                (name, value, now)
            )
    
    # Fetch crypto prices as macro indicators
    prices = await fetch_crypto_prices()
    for asset, price in prices.items():
        await db.execute(
            "INSERT OR REPLACE INTO macro_data (indicator, value, timestamp) VALUES (?, ?, ?)",
            (asset, price, now)
        )
    
    await db.commit()
    await db.close()
    return len(FRED_SERIES) + len(prices)
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add macro data collector (FRED + CoinGecko)"
```

---

### Task 4.2: Macro API endpoints + scheduler

**Objective:** Routes + integration.

**Files:**
- Create: `backend/app/api/macro.py`
- Modify: `backend/main.py`, `backend/app/services/scheduler.py`

**Step 1: Macro API routes**

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
        """SELECT indicator, value, MAX(timestamp) as timestamp 
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
```

**Step 2: Add to main.py**

```python
from app.api.macro import router as macro_router
app.include_router(macro_router)
```

**Step 3: Add to scheduler**

```python
from app.collectors.macro_collector import collect_macro
scheduler.add_job(collect_macro, "interval", hours=1, id="macro")
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: add macro overlay API endpoints and hourly collector"
```

---

### Phase 5: Stablecoin Flow Tracker

---

### Task 5.1: Stablecoin collector (DefiLlama stablecoin endpoint)

**Objective:** Track USDT/USDC mint/burn events and total supply changes.

**Files:**
- Create: `backend/app/collectors/stablecoin_collector.py`

**Step 1: Write collector**

`backend/app/collectors/stablecoin_collector.py`:
```python
"""Track stablecoin supply and flows from DefiLlama."""
import time
from app.database import get_db
from app.services.http_client import APIClient

llama = APIClient(base_url="https://stablecoins.llama.fi", rate_limit=0.5)

async def fetch_stablecoin_supply():
    """Fetch total stablecoin supply by chain."""
    try:
        data = await llama.get("/stablecoins")
        pegged = data.get("peggedAssets", [])
        results = []
        for asset in pegged:
            if asset.get("symbol") in ["USDT", "USDC", "DAI", "USDe"]:
                results.append({
                    "stablecoin": asset["symbol"],
                    "total_circulating": asset.get("circulating", {}).get("peggedUSD", 0),
                    "chains": list(asset.get("chainBalances", {}).keys()),
                })
        return results
    except Exception as e:
        print(f"Stablecoin API error: {e}")
        return []

async def fetch_stablecoin_events():
    """Fetch recent mint/burn events — approximated from supply changes."""
    try:
        # DefiLlama stablecoin endpoint gives current state
        # For historical events, we track deltas between runs
        data = await llama.get("/stablecoin/chains")
        events = []
        now = time.time()
        for chain_data in data[:10]:
            events.append({
                "stablecoin": "USDT",
                "event_type": "supply_update",
                "amount": chain_data.get("totalCirculatingUSD", {}).get("peggedUSD", 0),
                "chain": chain_data.get("name", "unknown"),
                "timestamp": now,
            })
        return events
    except Exception as e:
        print(f"Stablecoin events error: {e}")
        return []

async def collect_stablecoins():
    now = time.time()
    db = await get_db()
    count = 0
    
    supply = await fetch_stablecoin_supply()
    for s in supply:
        await db.execute(
            """INSERT OR REPLACE INTO stablecoin_events 
               (stablecoin, event_type, amount, chain, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (s["stablecoin"], "supply", s["total_circulating"], ",".join(s["chains"][:5]), now)
        )
        count += 1
    
    events = await fetch_stablecoin_events()
    for e in events:
        await db.execute(
            """INSERT OR IGNORE INTO stablecoin_events 
               (stablecoin, event_type, amount, chain, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (e["stablecoin"], e["event_type"], e["amount"], e["chain"], e["timestamp"])
        )
        count += 1
    
    await db.commit()
    await db.close()
    return count
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add stablecoin flow collector (DefiLlama)"
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

@router.get("/events")
async def get_stablecoin_events(limit: int = 30, stablecoin: str = None):
    db = await get_db()
    query = "SELECT * FROM stablecoin_events"
    params = []
    if stablecoin:
        query += " WHERE stablecoin = ?"
        params.append(stablecoin)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

@router.get("/supply")
async def get_current_supply():
    db = await get_db()
    cursor = await db.execute(
        """SELECT stablecoin, amount, chain, MAX(timestamp) as timestamp 
           FROM stablecoin_events 
           WHERE event_type = 'supply'
           GROUP BY stablecoin"""
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]
```

**Step 2: Add to main.py + scheduler**

Same pattern as previous — add router import and `app.include_router`, add scheduler job:
```python
from app.collectors.stablecoin_collector import collect_stablecoins
scheduler.add_job(collect_stablecoins, "interval", minutes=30, id="stablecoins")
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add stablecoin API endpoints and 30-min collector"
```

---

### Phase 6: Signal Confluence Engine

---

### Task 6.1: Confluence scoring engine

**Objective:** Combine signals from all four panels into a unified score with alert thresholds.

**Files:**
- Create: `backend/app/services/confluence.py`

**Step 1: Write engine**

`backend/app/services/confluence.py`:
```python
"""Signal confluence engine — combines all four panels into actionable signals."""
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
    # More whales + higher amounts = bullish accumulation signal
    if count > 10 and avg > 5_000_000:
        return (0.8, f"High whale activity: {count} txns, avg ${avg:,.0f}")
    elif count > 5:
        return (0.5, f"Moderate whale activity: {count} txns")
    elif count > 0:
        return (0.2, f"Low whale activity: {count} txns")
    return (0.0, "No recent whale activity")

async def compute_sentiment_score() -> tuple[float, str]:
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
    return (max(0, avg), f"Sentiment: {avg:+.2f} over {count} posts")

async def compute_macro_score() -> tuple[float, str]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT indicator, MAX(value) as value
           FROM macro_data 
           WHERE indicator IN ('DXY', 'FEDFUNDS', 'BTC')
           GROUP BY indicator"""
    )
    rows = {r["indicator"]: r["value"] for r in await cursor.fetchall()}
    await db.close()
    
    dxy = rows.get("DXY", 100)
    # Weakening DXY (< 100) is bullish for BTC
    dxy_signal = 0.7 if dxy < 100 else 0.5 if dxy < 105 else 0.3
    return (dxy_signal, f"DXY: {dxy:.1f}")

async def compute_stablecoin_score() -> tuple[float, str]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT stablecoin, SUM(amount) as total
           FROM stablecoin_events
           WHERE event_type = 'supply'
           AND timestamp > strftime('%s', 'now') - 86400
           GROUP BY stablecoin"""
    )
    rows = await cursor.fetchall()
    await db.close()
    total = sum(r["total"] or 0 for r in rows)
    # Growing stablecoin supply = buying power entering
    if total > 200_000_000_000:
        return (0.7, f"Stablecoin supply growing: ${total:,.0f}")
    return (0.4, f"Stablecoin supply stable: ${total:,.0f}")

async def compute_confluence() -> dict:
    """Compute overall confluence score with component breakdown."""
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
    
    return {
        "overall": round(overall, 3),
        "components": components,
        "signal": "STRONG" if overall > 0.6 else "MODERATE" if overall > 0.3 else "WEAK",
    }
```

**Step 2: Test**

```bash
cd /Users/tn/dev/crypto-dashboard/backend && source venv/bin/activate
python -c "import asyncio; from app.services.confluence import compute_confluence; print(asyncio.run(compute_confluence()))"
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add signal confluence engine with weighted scoring"
```

---

### Task 6.2: Confluence API + WebSocket

**Objective:** REST endpoint for confluence + WebSocket for live push.

**Files:**
- Create: `backend/app/api/signals.py`
- Modify: `backend/main.py`

**Step 1: Confluence + WebSocket routes**

`backend/app/api/signals.py`:
```python
"""Signal confluence API + WebSocket."""
import json
import asyncio
from fastapi import APIRouter, WebSocket
from app.services.confluence import compute_confluence

router = APIRouter(prefix="/api/signals", tags=["signals"])

@router.get("/confluence")
async def get_confluence():
    return await compute_confluence()

# WebSocket management
connected_ws = set()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_ws.add(ws)
    try:
        while True:
            data = await ws.receive_text()  # keep alive
            if data == "ping":
                result = await compute_confluence()
                await ws.send_text(json.dumps(result))
    except Exception:
        pass
    finally:
        connected_ws.discard(ws)

async def broadcast_confluence():
    """Push latest confluence to all connected WebSocket clients."""
    if not connected_ws:
        return
    result = await compute_confluence()
    dead = set()
    for ws in connected_ws:
        try:
            await ws.send_text(json.dumps(result))
        except Exception:
            dead.add(ws)
    connected_ws.difference_update(dead)
```

**Step 2: Add to main.py**

```python
from app.api.signals import router as signals_router, broadcast_confluence
app.include_router(signals_router)

# Add broadcast to scheduler
# In scheduler.py, add:
# scheduler.add_job(broadcast_confluence, "interval", minutes=2, id="broadcast")
```

**Step 3: Commit**

```bash
git add -A && git commit -m "feat: add confluence API endpoint and WebSocket broadcast"
```

---

### Phase 7: Frontend Dashboard

---

### Task 7.1: Dashboard shell + layout

**Objective:** Create the React dashboard shell with four panel grid and dark theme.

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

**Step 3: Dashboard grid**

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
    <div className="min-h-screen p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-cyan-400">Crypto Command Center</h1>
        <p className="text-slate-500 text-sm">On-Chain · Sentiment · Macro · Stablecoin</p>
      </header>
      
      <SignalBar />
      
      <div className="grid grid-cols-2 gap-4 mt-4">
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

export default function App() {
  return <Dashboard />;
}
```

**Step 5: Verify frontend starts**

```bash
cd /Users/tn/dev/crypto-dashboard/frontend && npm run dev &
sleep 3
curl -s http://localhost:5173 | head -20
kill %1
# Expected: HTML response
```

**Step 6: Commit**

```bash
git add -A && git commit -m "feat: create dashboard shell with 4-panel grid layout"
```

---

### Task 7.2: Signal bar component (WebSocket live)

**Objective:** Top bar showing confluence score with live WebSocket updates.

**Files:**
- Create: `frontend/src/components/SignalBar.jsx`

**Step 1: Write SignalBar with WebSocket hook**

`frontend/src/components/SignalBar.jsx`:
```jsx
import { useState, useEffect } from "react";

const SIGNAL_COLORS = {
  STRONG: "bg-green-500",
  MODERATE: "bg-amber-500",
  WEAK: "bg-red-500",
};

export default function SignalBar() {
  const [confluence, setConfluence] = useState(null);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws`);
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setConfluence(data);
    };
    setWs(socket);
    return () => socket.close();
  }, []);

  // Also fetch initial state via REST
  useEffect(() => {
    fetch("/api/signals/confluence")
      .then((r) => r.json())
      .then(setConfluence);
  }, []);

  const overall = confluence?.overall ?? 0;
  const signal = confluence?.signal ?? "WEAK";

  return (
    <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4 mb-4">
      <div className="flex items-center gap-4">
        <div className={`px-3 py-1 rounded font-bold text-sm text-white ${SIGNAL_COLORS[signal]}`}>
          {signal}
        </div>
        <div className="flex-1">
          <div className="text-xs text-slate-500 mb-1">Confluence Score</div>
          <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 transition-all duration-500"
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
              <div>{c.name}</div>
              <div className="font-mono text-white">{Math.round(c.score * 100)}%</div>
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
git add -A && git commit -m "feat: add live signal confluence bar with WebSocket"
```

---

### Task 7.3: On-Chain panel component

**Objective:** Table of recent whale transactions with amount and asset.

**Files:**
- Create: `frontend/src/components/panels/OnChainPanel.jsx`

**Step 1: Write component**

`frontend/src/components/panels/OnChainPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

export default function OnChainPanel() {
  const [whales, setWhales] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch("/api/onchain/whales?limit=5&min_usd=500000")
      .then((r) => r.json())
      .then(setWhales);
    fetch("/api/onchain/stats")
      .then((r) => r.json())
      .then(setStats);
  }, []);

  const formatUsd = (v) =>
    v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : `$${v.toFixed(0)}`;

  return (
    <div>
      {stats && (
        <div className="flex gap-3 mb-3 text-xs">
          <span className="text-slate-500">24h whales: <b className="text-cyan-400">{stats.total_whales}</b></span>
          <span className="text-slate-500">Max: <b className="text-white">{formatUsd(stats.max_amount)}</b></span>
        </div>
      )}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {whales.map((w) => (
          <div key={w.tx_hash} className="flex justify-between text-xs border-b border-[#1e1e2e] pb-1">
            <span className="text-slate-400 font-mono">{w.tx_hash.slice(0, 10)}...</span>
            <span className="text-cyan-400 font-mono">{formatUsd(w.amount_usd)}</span>
            <span className="text-slate-500">{w.asset}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add on-chain panel with whale tx table"
```

---

### Task 7.4: Sentiment panel component

**Objective:** Gauge showing aggregate sentiment with recent posts.

**Files:**
- Create: `frontend/src/components/panels/SentimentPanel.jsx`

**Step 1: Write component**

`frontend/src/components/panels/SentimentPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

export default function SentimentPanel() {
  const [trend, setTrend] = useState(null);
  const [posts, setPosts] = useState([]);

  useEffect(() => {
    fetch("/api/sentiment/trend")
      .then((r) => r.json())
      .then(setTrend);
    fetch("/api/sentiment/scores?limit=5")
      .then((r) => r.json())
      .then(setPosts);
  }, []);

  const score = trend?.avg_score ?? 0;
  const gaugeAngle = (score + 1) * 90; // -1=0°, 0=90°, 1=180°

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <div className="relative w-16 h-8 overflow-hidden">
          <div className="absolute bottom-0 left-0 w-full h-16 rounded-t-full bg-[#1e1e2e]">
            <div
              className="absolute bottom-0 left-1/2 w-1 h-8 bg-cyan-400 origin-bottom transition-transform duration-500"
              style={{ transform: `rotate(${gaugeAngle - 90}deg)` }}
            />
          </div>
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs font-bold text-white">
            {score > 0 ? "🐂" : score < 0 ? "🐻" : "➖"}
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-500">
            {trend?.count ?? 0} posts · avg {(score * 100).toFixed(0)}%
          </div>
        </div>
      </div>
      <div className="space-y-1 max-h-40 overflow-y-auto">
        {posts.map((p, i) => (
          <div key={i} className="text-xs border-b border-[#1e1e2e] pb-1">
            <div className="flex justify-between">
              <span className={`font-mono ${p.score > 0 ? "text-green-400" : "text-red-400"}`}>
                {(p.score * 100).toFixed(0)}%
              </span>
              <span className="text-slate-500">{p.source}</span>
            </div>
            <div className="text-slate-400 truncate">{p.summary}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add sentiment panel with gauge and post list"
```

---

### Task 7.5: Macro overlay panel component

**Objective:** Multi-line chart with DXY, BTC, Gold, S&P overlayed.

**Files:**
- Create: `frontend/src/components/panels/MacroPanel.jsx`

**Step 1: Write component with TradingView charts**

`frontend/src/components/panels/MacroPanel.jsx`:
```jsx
import { useState, useEffect, useRef } from "react";
import { createChart } from "lightweight-charts";

export default function MacroPanel() {
  const chartRef = useRef(null);
  const [latest, setLatest] = useState([]);

  useEffect(() => {
    fetch("/api/macro/latest")
      .then((r) => r.json())
      .then(setLatest);
  }, []);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 220,
      layout: { background: { color: "#13131a" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#1e1e2e" }, horzLines: { color: "#1e1e2e" } },
      timeScale: { timeVisible: false },
    });

    Promise.all([
      fetch("/api/macro/history?indicator=BTC&hours=168").then((r) => r.json()),
      fetch("/api/macro/history?indicator=DXY&hours=168").then((r) => r.json()),
    ]).then(([btc, dxy]) => {
      const btcSeries = chart.addLineSeries({ color: "#f7931a", lineWidth: 2 });
      const dxySeries = chart.addLineSeries({ color: "#06b6d4", lineWidth: 1 });
      btcSeries.setData(btc.map((d) => ({ time: d.timestamp, value: d.value })));
      dxySeries.setData(dxy.map((d) => ({ time: d.timestamp, value: d.value })));
    });

    return () => chart.remove();
  }, []);

  const indicators = { DXY: "💵", SP500: "📈", GOLD: "🥇", FEDFUNDS: "🏦", BTC: "₿", ETH: "Ξ" };

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
      <div ref={chartRef} className="w-full" />
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add macro overlay panel with TradingView chart"
```

---

### Task 7.6: Stablecoin panel component

**Objective:** Bar chart of stablecoin supply + recent events table.

**Files:**
- Create: `frontend/src/components/panels/StablecoinPanel.jsx`

**Step 1: Write component**

`frontend/src/components/panels/StablecoinPanel.jsx`:
```jsx
import { useState, useEffect } from "react";

export default function StablecoinPanel() {
  const [supply, setSupply] = useState([]);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    fetch("/api/stablecoin/supply").then((r) => r.json()).then(setSupply);
    fetch("/api/stablecoin/events?limit=5").then((r) => r.json()).then(setEvents);
  }, []);

  const COLORS = { USDT: "#26a17b", USDC: "#2775ca", DAI: "#fab005", USDe: "#6366f1" };

  const maxSupply = Math.max(...supply.map((s) => s.amount), 1);

  return (
    <div>
      <div className="space-y-2 mb-3">
        {supply.map((s) => (
          <div key={s.stablecoin}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">{s.stablecoin}</span>
              <span className="text-white font-mono">${(s.amount / 1e9).toFixed(1)}B</span>
            </div>
            <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${(s.amount / maxSupply) * 100}%`, background: COLORS[s.stablecoin] || "#6366f1" }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="text-xs space-y-1 max-h-24 overflow-y-auto">
        {events.filter((e) => e.event_type !== "supply").slice(0, 5).map((e, i) => (
          <div key={i} className="flex justify-between border-b border-[#1e1e2e] pb-1">
            <span className="text-slate-400">{e.stablecoin} · {e.event_type}</span>
            <span className="text-cyan-400 font-mono">${(e.amount / 1e6).toFixed(1)}M</span>
            <span className="text-slate-500">{e.chain}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add -A && git commit -m "feat: add stablecoin panel with supply bars and events"
```

---

### Phase 8: Integration & Polish

---

### Task 8.1: Production build setup

**Objective:** FastAPI serves the built React app as static files. Add build scripts.

**Files:**
- Modify: `backend/main.py`
- Create: `Makefile`

**Step 1: Update main.py to serve frontend**

Add to `backend/main.py`:
```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Serve React build in production
frontend_build = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
```

**Step 2: Create Makefile**

`Makefile`:
```makefile
.PHONY: install dev build

install:
	cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev:
	cd backend && source venv/bin/activate && python main.py &
	cd frontend && npm run dev

build:
	cd frontend && npm run build

run:
	cd backend && source venv/bin/activate && python main.py

test:
	cd backend && source venv/bin/activate && python -m pytest tests/ -v
```

**Step 3: Build and verify full stack**

```bash
cd /Users/tn/dev/crypto-dashboard
make build
make run &
sleep 3
curl -s http://localhost:8000/ | head -5
curl -s http://localhost:8000/api/health
# Expected: HTML from React build + {"status":"ok"}
kill %1
```

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: production build setup — FastAPI serves React static files"
```

---

### Task 8.2: GitHub repo + initial push

**Objective:** Push to GitHub as `tokenburner7/crypto-command-center`.

**Step 1: Create remote and push**

```bash
cd /Users/tn/dev/crypto-dashboard
gh repo create crypto-command-center --public --source=. --remote=origin --push
# Expected: Repository created, code pushed
```

**Step 2: Verify**

```bash
gh repo view tokenburner7/crypto-command-center --web
```

**Step 3: Commit**

```bash
# Already committed and pushed above
```

---

## Implementation Notes

### Data Source Tiers

| Tier | APIs Used | Auth Required |
|------|-----------|---------------|
| **Free (works now)** | Reddit JSON, DefiLlama, CoinGecko, Blockchain.info, FRED | None (or free key) |
| **Enhanced (recommended)** | OpenAI (sentiment), Whale Alert, Etherscan, X API, NewsAPI | API keys in `.env` |

### Known Gaps to Fill Later

1. **Whale Alert API** — real-time whale alerts for all chains (free tier: 10 calls/min)
2. **X/Twitter sentiment** — via `xurl` tool or X API for crypto influencer tracking
3. **Real exchange flow data** — needs on-chain address tagging (Glassnode free tier or Arkham)
4. **Narrative detection** — LLM-powered topic clustering across posts
5. **Alerting** — push notifications (Telegram bot) when confluence hits STRONG

### Running the Dashboard

```bash
cd /Users/tn/dev/crypto-dashboard
make build    # build React frontend
make run      # start FastAPI on :8000
# Open http://localhost:8000
```
