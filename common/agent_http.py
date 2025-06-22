# common/agent_http.py
# ───────────────────────────────
# FastAPI エージェントで使う HTTP クライアント & エンドポイントデコレータ
# 1. HTTP クライアント: post_json / post_json_sync
# 2. エージェント用デコレータ: agent_endpoint
#    - Pydantic モデルによる入力バリデーション
#    - 出力を指定のキーでラップ
#    - 例外時は統一 JSON レスポンス返却
# ───────────────────────────────

from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, Optional, Type, Callable
import httpx
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .exceptions import AgentHTTPError

logger = logging.getLogger("common.agent_http")

# ───────────────────────────────────────────────────
# HTTP クライアント部
# ───────────────────────────────────────────────────
_DEFAULT_TIMEOUT = 120.0  # 秒

async def _async_request(
    method: str,
    url: str,
    *,
    json: Dict[str, Any] | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    max_retries: int = 2,
) -> httpx.Response:
    backoff = 1.5
    attempt = 0
    last_exc: Optional[Exception] = None

    while attempt <= max_retries:
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as cli:
                resp = await cli.request(method, url, json=json)
                resp.raise_for_status()
                return resp
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_exc = e
            logger.warning(
                "[Attempt %d/%d] HTTP %s %s failed: %s",
                attempt + 1,
                max_retries + 1,
                method,
                url,
                e,
            )
            if attempt >= max_retries:
                if isinstance(e, httpx.HTTPStatusError):
                    raise AgentHTTPError(str(e), e.response) from e
                raise
            await asyncio.sleep(backoff ** attempt)
            attempt += 1

    # 通常ここへは来ない
    raise last_exc  # type: ignore

async def post_json(
    base_url: str,
    path: str,
    payload: Dict[str, Any],
    *,
    timeout: float = _DEFAULT_TIMEOUT,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    非同期 JSON POST → dict 返却。HTTP/JSON エラー時は AgentHTTPError 送出。
    """
    url = f"{base_url.rstrip('/')}{path}"
    resp = await _async_request("POST", url, json=payload, timeout=timeout, max_retries=max_retries)
    try:
        return resp.json()
    except Exception as e:
        logger.error("Invalid JSON from %s: %s", url, e, exc_info=True)
        raise AgentHTTPError("Invalid JSON in response", resp) from e

def post_json_sync(
    base_url: str,
    path: str,
    payload: Dict[str, Any],
    *,
    timeout: float = _DEFAULT_TIMEOUT,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    同期版 JSON POST。CLI や同期処理用。
    """
    return asyncio.run(post_json(base_url, path, payload, timeout=timeout, max_retries=max_retries))


# ───────────────────────────────────────────────────
# エージェントサーバ用デコレータ部
# ───────────────────────────────────────────────────
def agent_endpoint(
    request_model: Type[BaseModel],
    output_key: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    FastAPI エージェントアプリ内のエンドポイントを簡潔に定義するデコレータ。

    - リクエストボディを Pydantic でバリデーション
    - 戻り値を {output_key: result} 形式にラップして返却
    - 例外発生時は {"error": "..."} を 500 で返却
    """
    def decorator(func: Callable[[BaseModel], Any]) -> Callable[..., Any]:
        async def wrapper(request: Request) -> JSONResponse:
            try:
                # Pydantic モデルにパース
                payload = await request.json()
                req_model = request_model(**payload)

                # 実際のビジネスロジック呼び出し
                result = await func(req_model)

                # 辞書だったらマージ、それ以外は output_key でラップ
                if isinstance(result, dict):
                    return JSONResponse(result)
                return JSONResponse({output_key: result})
            except HTTPException:
                # FastAPI の HTTPException はそのまま伝播
                raise
            except Exception as e:
                logger.exception("Error in agent endpoint %s", func.__name__)
                return JSONResponse({"error": str(e)}, status_code=500)

        # FastAPI がエンドポイントとして認識できるように属性を付与
        wrapper.__name__ = func.__name__
        wrapper.__doc__  = func.__doc__
        return wrapper

    return decorator
