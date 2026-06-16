"""Sentiment analysis API routes."""
from fastapi import APIRouter
from app.repositories.sentiment_repo import SentimentRepository

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])

@router.get("/scores")
async def get_scores(limit: int = 30, source: str = None):
    return await SentimentRepository.get_recent(limit=limit, source=source)

@router.get("/trend")
async def get_trend(hours: int = 24):
    return await SentimentRepository.get_trend(hours=hours)
