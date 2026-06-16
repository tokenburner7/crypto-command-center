"""Macro data repository."""
from app.database import get_db

class MacroRepository:
    @staticmethod
    async def save_indicators(data: list[dict]):
        db = await get_db()
        for d in data:
            await db.execute(
                "INSERT OR REPLACE INTO macro_data (indicator, value, obs_date, timestamp) VALUES (?, ?, ?, ?)",
                (d["indicator"], d["value"], d.get("obs_date"), d["timestamp"])
            )
        await db.commit()
        await db.close()
    
    @staticmethod
    async def get_latest():
        db = await get_db()
        cursor = await db.execute(
            "SELECT indicator, value, obs_date, MAX(timestamp) as timestamp FROM macro_data GROUP BY indicator"
        )
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]
    
    @staticmethod
    async def get_history(indicator: str = "BTC", hours: int = 168):
        db = await get_db()
        cursor = await db.execute(
            """SELECT * FROM macro_data WHERE indicator = ? 
               AND timestamp > strftime('%s', 'now') - ? ORDER BY timestamp ASC""",
            (indicator, hours * 3600)
        )
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]
