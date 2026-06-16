"""Background task scheduler for Phase 1a collectors."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def start_collectors():
    from app.collectors.btc_whale_collector import collect as collect_btc
    from app.collectors.eth_whale_collector import collect as collect_eth
    from app.collectors.stablecoin_collector import collect as collect_stable
    
    scheduler.add_job(collect_btc, "interval", minutes=5, id="btc_whales")
    scheduler.add_job(collect_eth, "interval", minutes=5, id="eth_whales")
    scheduler.add_job(collect_stable, "interval", minutes=30, id="stablecoins")
    scheduler.start()
    print("[scheduler] Collectors started: BTC(5m), ETH(5m), Stablecoin(30m)")
