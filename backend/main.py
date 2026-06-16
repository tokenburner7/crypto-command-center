"""Crypto Command Center — FastAPI backend."""
from dotenv import load_dotenv; load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="Crypto Command Center", version="0.3.0")

app.add_middleware(CORSMiddleware, allow_origins=[
    "http://localhost:8000", "http://localhost:5173",
    "http://127.0.0.1:8000", "http://127.0.0.1:5173",
], allow_methods=["GET", "POST"], allow_headers=["*"])

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:; img-src 'self' data:;"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
app.add_middleware(SecurityHeadersMiddleware)

# === IMPORTS (after security config) ===
from app.database import init_db
from app.services.scheduler import start_collectors
from app.api.onchain import router as onchain_router
from app.api.stablecoin import router as stablecoin_router
from app.api.signals import router as signals_router, broadcast_full_state

# === API ROUTERS (before static mount) ===
app.include_router(onchain_router)
app.include_router(stablecoin_router)
app.include_router(signals_router)

@app.on_event("startup")
async def startup():
    try:
        await init_db()
        start_collectors()
        from app.services.scheduler import scheduler
        scheduler.add_job(broadcast_full_state, "interval", minutes=1, id="ws_broadcast")
        print("[startup] Ready")
    except Exception as e:
        print(f"[startup] FATAL: {e}"); import sys; sys.exit(1)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}

# === STATIC MOUNT (LAST) ===
from fastapi.staticfiles import StaticFiles
from pathlib import Path
fb = Path(__file__).parent.parent / "frontend" / "dist"
if fb.exists():
    app.mount("/", StaticFiles(directory=str(fb), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
