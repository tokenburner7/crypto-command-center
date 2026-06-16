"""Collect macro indicators from FRED and CoinGecko."""
import time
import os
from app.services.http_client import APIClient
from app.repositories.macro_repo import MacroRepository

fred = APIClient(base_url="https://api.stlouisfed.org/fred", rate_limit=0.5)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

FRED_SERIES = {
    "DXY": "DTWEXBGS",
    "FEDFUNDS": "FEDFUNDS",
    "GOLD": "GOLDAMGBD228NLBR",
    "SP500": "SP500",
}

async def fetch_fred_series(series_id: str) -> dict | None:
    api_key = os.getenv("FRED_API_KEY", "")
    params = {"series_id": series_id, "sort_order": "desc", "limit": 1, "file_type": "json"}
    if api_key:
        params["api_key"] = api_key
    try:
        data = await fred.get("/series/observations", params=params)
        obs = data.get("observations", [])
        if obs and obs[0].get("value") not in (".", "N/A", None, ""):
            return {"value": float(obs[0]["value"]), "obs_date": obs[0]["date"]}
    except Exception as e:
        print(f"[macro] FRED error ({series_id}): {e}")
    return None

async def fetch_crypto_prices():
    try:
        data = await coingecko.get(
            "/simple/price",
            params={"ids": "bitcoin,ethereum", "vs_currencies": "usd"}
        )
        return {
            "BTC": data.get("bitcoin", {}).get("usd"),
            "ETH": data.get("ethereum", {}).get("usd"),
        }
    except Exception as e:
        print(f"[macro] CoinGecko error: {e}")
        return {}

async def collect():
    now = int(time.time())
    indicators = []
    
    for name, series_id in FRED_SERIES.items():
        result = await fetch_fred_series(series_id)
        if result is not None:
            indicators.append({
                "indicator": name,
                "value": result["value"],
                "obs_date": result["obs_date"],
                "timestamp": now,
            })
    
    prices = await fetch_crypto_prices()
    for asset, price in prices.items():
        if price:
            indicators.append({
                "indicator": asset,
                "value": price,
                "timestamp": now,
            })
    
    if indicators:
        await MacroRepository.save_indicators(indicators)
        print(f"[macro] Collected {len(indicators)} indicators")
    return len(indicators)
