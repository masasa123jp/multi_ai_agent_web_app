# backend/db/async_engine.py

"""
非同期 SQLAlchemy Engine／Session 生成ユーティリティ。

• アプリケーション全体で共有する AsyncEngine を生成
• async_session_factory: セッションファクトリ (expire_on_commit=False)
• db_lifespan(): FastAPI Lifespan ハンドラ (起動／終了時のリソース管理)
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# ── 環境変数から DB 接続情報を取得 ─────────────────────────
PG_USER = settings.pg_user
PG_PW   = settings.pg_pw
PG_HOST = settings.pg_host
PG_PORT = settings.pg_port
PG_DB   = settings.pg_db

SCHEMA  = settings.pg_schema

def _build_db_url() -> str:
    """postgresql+asyncpg 用 URL を動的生成"""
    return f"postgresql+asyncpg://{PG_USER}:{PG_PW}@{PG_HOST}:{PG_PORT}/{PG_DB}"

print(_build_db_url())

# ── AsyncEngine (singleton) ────────────────────────────────
engine = create_async_engine(
    _build_db_url(),
    echo=False,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": SCHEMA}},
)

# ── Session Factory ────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

# ── FastAPI Lifespan ハンドラ ──────────────────────────────
@asynccontextmanager
async def db_lifespan(app: FastAPI):
    """
    FastAPI の lifespan ハンドラ。
    アプリ起動時は DB Pool 初期化（必要なら追加ロジックを記載）
    アプリ終了時に engine.dispose() で全接続を解放
    """
    try:
        yield
    finally:
        await engine.dispose()
