# backend/server.py
"""
============================================================
 Agent Workflow API (FastAPI)
------------------------------------------------------------
 - OpenTelemetry 初期化／DB プール管理を lifespan で統合
 - Uvicorn 既定 LOGGING_CONFIG を継承しつつフォーマット統一
 - LoggingMiddleware で Request ID と処理時間を出力
 - CORS / GZip / バリデーション / 例外ハンドラを網羅
============================================================
"""

from __future__ import annotations

import logging.config
from contextlib import asynccontextmanager  # async context manager をインポート
from uuid import uuid4
from time import time

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, Request, Depends, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from uvicorn import Config, Server
from uvicorn.config import LOGGING_CONFIG as UVI_LOG_CFG

from backend.db.async_engine import db_lifespan
from backend.api_router import api_router
from backend.telemetry import init_otel
from backend.security.auth import TokenResponse, create_access_token
from fastapi.security import OAuth2PasswordRequestForm

# ── ロギング設定 ─────────────────────────────────────────────
LOGGING_CONFIG = UVI_LOG_CFG.copy()
LOGGING_CONFIG["formatters"]["default"]["fmt"] = (
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("backend.server")

# ── .env 読み込み ─────────────────────────────────────────────
load_dotenv(find_dotenv())

# ── Graceful Start/Shutdown (lifespan) ────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI のライフサイクルハンドラ (async context manager)。
    - OpenTelemetry 初期化
    - DB Engine のプール初期化／破棄
    """
    # 1) 分散トレーシングの初期化
    init_otel(app)
    # 2) DB Engine 起動／破棄
    async with db_lifespan(app):
        yield  # 必ず yield を含めて enter/exit を定義
    logger.info("Application shutdown complete")  # シャットダウン完了ログ

# ── FastAPI インスタンス ───────────────────────────────────────
app = FastAPI(
    title="Agent Workflow API",
    version="3.0.0",
    description="AI マルチエージェントワークフロー統合サーバ (FastAPI)",
    lifespan=lifespan,  # 修正した lifespan を渡す
)

# ── リクエスト/レスポンス ロギング ミドルウェア ─────────────────
class LoggingMiddleware(BaseHTTPMiddleware):
    """
    全リクエスト／レスポンスをログ出力するミドルウェア。
    - request_id を生成し、メソッド／パス／ボディを DEBUG レベルで出力
    - ステータスコードと処理時間を INFO レベルで出力
    """
    async def dispatch(self, request: Request, call_next):
        req_id = uuid4().hex[:8]
        request.state.request_id = req_id

        body = await request.body()
        snippet = body[:200] if body else b"-"
        logger.debug(f"[⇢{req_id}] {request.method} {request.url.path} body={snippet.decode(errors='ignore')}")

        start = time()
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(f"[{req_id}] Exception during request processing: {exc}")
            raise
        elapsed = (time() - start) * 1000
        logger.info(f"[⇠{req_id}] {request.method} {request.url.path} {response.status_code} {elapsed:.1f} ms")
        return response

# ミドルウェア登録
app.add_middleware(LoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8081"],
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

# ── ルータ登録 ────────────────────────────────────────────────
app.include_router(api_router)

# ── 開発用トークン発行エンドポイント ─────────────────────────────
@app.post("/api/auth/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def dev_token(form: OAuth2PasswordRequestForm = Depends()):
    """
    開発用 JWT 発行。
    form.username を sub にセットして返却。
    """
    return TokenResponse(access_token=create_access_token(sub=form.username), token_type="bearer")

# ── バリデーションエラー処理 ────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", "N/A")
    try:
        body = (await request.body()).decode(errors="ignore")
    except Exception:
        body = "<unreadable body>"
    logger.error(f"[{req_id}] Validation failed {request.method} {request.url.path} errors={exc.errors()} body={body}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# ── 全例外キャッチオール ───────────────────────────────────────
@app.exception_handler(Exception)
async def all_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.exception(f"[{req_id}] Unhandled error: {request.method} {request.url.path} - {exc}")
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        {"detail": "Internal Server Error"},
        status_code=500,
        headers={"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"},
    )

# ── スタンドアロン起動 ────────────────────────────────────────
if __name__ == "__main__":
    Server(
        Config(
            "backend.server:app",
            host="0.0.0.0",
            port=5000,
            log_config=LOGGING_CONFIG,
            log_level="info",
            reload=False,  # 開発時にのみ True にする
        )
    ).run()
