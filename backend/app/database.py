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
        
        CREATE INDEX IF NOT EXISTS idx_whale_ts ON whale_transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_whale_chain ON whale_transactions(blockchain);
        CREATE INDEX IF NOT EXISTS idx_supply_ts ON stablecoin_supply(timestamp);
    """)
    await db.commit()
    await db.close()
