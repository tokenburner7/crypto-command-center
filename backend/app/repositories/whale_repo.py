"""Whale transaction repository."""
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
