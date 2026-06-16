# Crypto Command Center

Unified crypto dashboard: on-chain whale tracking (BTC + ETH), stablecoin flow monitoring, and real-time signal confluence.

## Quick Start

```bash
make install
make build
make run
# Open http://localhost:8000
```

## API Keys (optional)

Set in `backend/.env`. Free tiers work without most keys:

| Service | Key | Free Tier |
|---------|-----|-----------|
| Etherscan | `ETHERSCAN_API_KEY` | Free from etherscan.io |
| FRED | `FRED_API_KEY` | Free from stlouisfed.org |
| OpenAI | `OPENAI_API_KEY` | Needed for sentiment (Phase 1b) |
