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
