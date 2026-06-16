"""On-chain intelligence API routes."""
from fastapi import APIRouter
from app.repositories.whale_repo import WhaleRepository

router = APIRouter(prefix="/api/onchain", tags=["onchain"])

@router.get("/whales")
async def get_whales(limit: int = 20, min_usd: float = 500000, blockchain: str = None):
    return await WhaleRepository.get_recent(limit=limit, min_usd=min_usd, blockchain=blockchain)

@router.get("/stats")
async def get_stats():
    return await WhaleRepository.get_stats(hours=24)
