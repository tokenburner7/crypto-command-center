"""Collect whale BTC transactions from Blockchain.info mempool."""
import time
from app.services.http_client import APIClient
from app.repositories.whale_repo import WhaleRepository

WHALE_THRESHOLD_USD = 1_000_000
client = APIClient(base_url="https://blockchain.info", rate_limit=0.5)
coingecko = APIClient(base_url="https://api.coingecko.com/api/v3", rate_limit=1)

_price_cache = {"btc": None, "ts": 0}

async def _btc_price():
    now = time.time()
    if _price_cache["btc"] and (now - _price_cache["ts"]) < 300:
        return _price_cache["btc"]
    data = await coingecko.get("/simple/price", params={"ids": "bitcoin", "vs_currencies": "usd"})
    _price_cache["btc"] = data["bitcoin"]["usd"]
    _price_cache["ts"] = now
    return _price_cache["btc"]

async def collect():
    try:
        data = await client.get("/unconfirmed-transactions?format=json")
        txs_data = data if isinstance(data, list) else data.get("txs", [])
        price = await _btc_price()
        txs = []
        for tx in txs_data[:50]:
            total_out = sum(o.get("value", 0) for o in tx.get("out", [])) / 1e8
            usd = total_out * price
            if usd >= WHALE_THRESHOLD_USD:
                inputs = tx.get("inputs", [])
                outputs = tx.get("out", [])
                from_addr = inputs[0].get("prev_out", {}).get("addr") if inputs else None
                to_addrs = [o.get("addr") for o in outputs if o.get("addr")]
                txs.append({
                    "tx_hash": tx["hash"],
                    "blockchain": "bitcoin",
                    "from_address": from_addr,
                    "to_address": to_addrs[0] if to_addrs else None,
                    "amount_usd": round(usd, 2),
                    "asset": "BTC",
                    "timestamp": int(tx.get("time", time.time())),
                })
        if txs:
            await WhaleRepository.save(txs)
            print(f"[btc_whale] Collected {len(txs)} whale txns (mempool)")
        return len(txs)
    except Exception as e:
        print(f"[btc_whale] Error: {e}")
        return 0
