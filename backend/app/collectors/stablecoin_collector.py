"""Track stablecoin supply from DefiLlama with delta computation."""
import time
from app.services.http_client import APIClient
from app.repositories.stablecoin_repo import StablecoinRepository

llama = APIClient(base_url="https://stablecoins.llama.fi", rate_limit=0.5)
TRACKED = ["USDT", "USDC", "DAI", "USDe"]

async def collect():
    try:
        data = await llama.get("/stablecoins")
        pegged = data.get("peggedAssets", [])
        current = {}
        for asset in pegged:
            symbol = asset.get("symbol", "")
            if symbol in TRACKED:
                current[symbol] = {
                    "total_supply_usd": asset.get("circulating", {}).get("peggedUSD", 0),
                    "chains": ",".join(list(asset.get("chainBalances", {}).keys())[:5]),
                }
        
        previous = await StablecoinRepository.get_previous_supply()
        now = int(time.time())
        for symbol, data in current.items():
            prev = previous.get(symbol, data["total_supply_usd"])
            data["change_24h_usd"] = round(data["total_supply_usd"] - prev, 2)
            data["timestamp"] = now
        
        await StablecoinRepository.save_supply(current)
        print(f"[stablecoin] Updated {len(current)} stablecoins")
        return len(current)
    except Exception as e:
        print(f"[stablecoin] Error: {e}")
        return 0
