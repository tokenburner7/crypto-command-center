"""Sentiment score repository."""
from app.database import get_db

class SentimentRepository:
    @staticmethod
    async def save_scores(scores: list[dict]):
        db = await get_db()
        for s in scores:
            await db.execute(
                """INSERT OR IGNORE INTO sentiment_scores 
                   (source, topic, score, confidence, summary, baseline_fear_greed, url, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (s["source"], s.get("topic", "crypto"), s["score"], s.get("confidence"),
                 s.get("summary", ""), s.get("baseline_fear_greed"), s["url"], s["timestamp"])
            )
        await db.commit()
        await db.close()
    
    @staticmethod
    async def get_recent(limit: int = 30, source: str = None):
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
    
    @staticmethod
    async def get_trend(hours: int = 24):
        db = await get_db()
        cursor = await db.execute(
            """SELECT AVG(score) as avg_score, COUNT(*) as count,
                      MIN(score) as min_score, MAX(score) as max_score,
                      AVG(baseline_fear_greed) as avg_baseline
               FROM sentiment_scores
               WHERE timestamp > strftime('%s', 'now') - ?""",
            (hours * 3600,)
        )
        row = await cursor.fetchone()
        await db.close()
        return dict(row) if row else {"avg_score": 0, "count": 0, "avg_baseline": None}
