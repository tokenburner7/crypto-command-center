"""Stablecoin supply repository."""
from app.database import get_db

class StablecoinRepository:
    @staticmethod
    async def save_supply(data: dict):
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
