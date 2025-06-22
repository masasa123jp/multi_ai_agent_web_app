"""
Brotli > GZip > no-compression の順で自動選択
"""
import brotli
import gzip
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_BR_QUALITY = int(__import__("os").getenv("BR_QUALITY", "4"))

class CompressionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        resp: Response = await call_next(request)
        if resp.headers.get("content-encoding"):
            # 既にエンコード済み
            return resp

        accept = request.headers.get("accept-encoding", "")
        raw = resp.body if isinstance(resp.body, bytes) else resp.body.encode()

        if "br" in accept:
            resp.body = brotli.compress(raw, quality=_BR_QUALITY)
            resp.headers["content-encoding"] = "br"
        elif "gzip" in accept:
            resp.body = gzip.compress(raw)
            resp.headers["content-encoding"] = "gzip"

        resp.headers["content-length"] = str(len(resp.body))
        return resp
