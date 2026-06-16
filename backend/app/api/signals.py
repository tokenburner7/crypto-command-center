"""Signal API + WebSocket."""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.confluence import compute_confluence
from app.repositories.whale_repo import WhaleRepository
from app.repositories.stablecoin_repo import StablecoinRepository
from app.database import get_db

router = APIRouter(tags=["signals"])

@router.get("/api/signals/confluence")
async def get_confluence():
    return await compute_confluence()

@router.get("/api/signals/history")
async def get_history(limit: int = 50):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM signal_confluences ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]

connected_ws = set()

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_ws.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_ws.discard(ws)

async def broadcast_full_state():
    if not connected_ws:
        return
    confluence = await compute_confluence()
    whales = await WhaleRepository.get_recent(limit=5)
    stablecoins = await StablecoinRepository.get_latest()
    
    payload = json.dumps({"confluence": confluence, "whales": whales, "stablecoins": stablecoins})
    dead = set()
    for ws in connected_ws:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    connected_ws.difference_update(dead)
