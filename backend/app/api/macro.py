"""Macro overlay API routes."""
from fastapi import APIRouter
from app.repositories.macro_repo import MacroRepository

router = APIRouter(prefix="/api/macro", tags=["macro"])

@router.get("/latest")
async def get_latest():
    return await MacroRepository.get_latest()

@router.get("/history")
async def get_history(indicator: str = "BTC", hours: int = 168):
    return await MacroRepository.get_history(indicator=indicator, hours=hours)
