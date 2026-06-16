"""Collect whale ETH transactions from Etherscan (config-driven wallet list)."""
import json
import os
import time
from pathlib import Path
from app.services.http_client import APIClient
from app.repositories.whale_repo import WhaleRepository

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "exchange_wallets.json"
etherscan = APIClient(base_url="https://api.etherscan.io/api", rate_limit=0.2)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

_price_cache = {"eth": None, "ts": 0}

async def _eth_price():
    now = time.time()
    if _price_cache["eth"] and (now - _price_cache["ts"]) < 300:
        return _price_cache["eth"]
    data = await coingecko.get("/simple/price", params={"ids": "ethereum", "vs_currencies": "usd"})
    _price_cache["eth"] = data["ethereum"]["usd"]
    _price_cache["ts"] = now
    return _price_cache["eth"]

def _load_wallets():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    return cfg.get("eth_wallets", []), cfg.get("eth_min_value_usd", 500000)

async def collect():
    api_key = os.getenv("ETHERSCAN_API_KEY", "")
    wallets, min_usd = _load_wallets()
    price = await _eth_price()
    txs = []
    call_count = 0
    
    for wallet in wallets:
        try:
            params = {
                "module": "account", "action": "txlist",
                "address": wallet["address"], "page": 1, "offset": 5,
                "sort": "desc", "apikey": api_key,
            }
            data = await etherscan.get("", params=params)
            call_count += 1
            for tx in data.get("result", [])[:3]:
                value_eth = int(tx.get("value", 0)) / 1e18
                value_usd = value_eth * price
                if value_usd >= min_usd:
                    txs.append({
                        "tx_hash": tx["hash"],
                        "blockchain": "ethereum",
                        "from_address": tx.get("from"),
                        "to_address": tx.get("to"),
                        "amount_usd": round(value_usd, 2),
                        "asset": "ETH",
                        "timestamp": int(tx.get("timeStamp", time.time())),
                    })
        except Exception as e:
            print(f"[eth_whale] Error ({wallet['label']}): {e}")
    
    if txs:
        await WhaleRepository.save(txs)
        print(f"[eth_whale] Collected {len(txs)} whale txns from {call_count} API calls")
    return len(txs)
