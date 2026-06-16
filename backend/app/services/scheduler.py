"""Background task scheduler for Phase 1a collectors."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def start_collectors():
    from app.collectors.btc_whale_collector import collect as collect_btc
    from app.collectors.eth_whale_collector import collect as collect_eth
    from app.collectors.stablecoin_collector import collect as collect_stable
    from app.collectors.sentiment_collector import collect as collect_sentiment
    from app.collectors.macro_collector import collect as collect_macro
    
    scheduler.add_job(collect_btc, "interval", minutes=5, id="btc_whales")
    scheduler.add_job(collect_eth, "interval", minutes=5, id="eth_whales")
    scheduler.add_job(collect_stable, "interval", minutes=30, id="stablecoins")
    scheduler.add_job(collect_sentiment, "interval", minutes=15, id="sentiment")
    scheduler.add_job(collect_macro, "interval", hours=1, id="macro")
    scheduler.start()
    print("[scheduler] Collectors: BTC(5m) ETH(5m) Stablecoin(30m) Sentiment(15m) Macro(1h)")
