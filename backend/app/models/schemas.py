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
    timestamp: int

class ExchangeVolume(BaseModel):
    exchange: str
    asset: str
    volume_usd: float
    timestamp: int

class StablecoinSupply(BaseModel):
    stablecoin: str
    total_supply_usd: float
    change_24h_usd: float = 0
    chains: Optional[str] = None
    timestamp: int

class SignalComponent(BaseModel):
    name: str
    score: float
    detail: str

class SignalConfluence(BaseModel):
    overall_score: float
    signal: str
    direction: str
    calibration_status: str
    calibration_progress: Optional[dict] = None
    narrative: Optional[str] = None
    components: list[SignalComponent]
    timestamp: int

class SentimentScore(BaseModel):
    source: str
    topic: Optional[str] = None
    score: float
    confidence: Optional[float] = None
    summary: Optional[str] = None
    baseline_fear_greed: Optional[float] = None
    url: Optional[str] = None
    timestamp: int

class MacroPoint(BaseModel):
    indicator: str
    value: float
    obs_date: Optional[str] = None
    timestamp: int
