"""Crypto Command Center — FastAPI backend."""
import os
import secrets
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="Crypto Command Center", version="0.3.0")

# Security: CORS restricted to localhost (not wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security: CSP header
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data:;"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Security: WebSocket auth token (generated at startup)
WS_AUTH_TOKEN = secrets.token_urlsafe(32)
print(f"[security] WebSocket auth token: {WS_AUTH_TOKEN}")
print(f"[security] Connect with: ws://localhost:8000/ws?token={WS_AUTH_TOKEN}")

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
