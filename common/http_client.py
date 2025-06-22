"""
再利用可能な httpx.AsyncClient (keep-alive & HTTP/2)
"""
import httpx
from typing import AsyncGenerator

_client: httpx.AsyncClient | None = None

async def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(http2=True, timeout=60)
    return _client

async def lifespan(app):
    """
    FastAPI の lifespan イベントでコネクションを生存させる
    """
    yield
    if _client and not _client.is_closed:
        await _client.aclose()
