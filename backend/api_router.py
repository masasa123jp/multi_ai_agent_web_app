# backend/api_router.py

from fastapi import APIRouter
# ---- 各ルータを import (循環参照を避けるため後段で include) ----
from backend.routers import (
    workflow,
    logs,
    health,
    auth as auth_router_module,
    profile as profile_router_module,
)
# API 全体の共通プレフィックスを /api に設定
api_router = APIRouter(prefix="/api")

# ─────────────────────────────────────────────────────────────────
# 各機能ルータを include_router でマウント
#  1. workflow: ワークフロー実行・管理
#  2. logs: 実行履歴／ログ取得
#  3. health: ヘルスチェック
#  4. auth: 認証 (login/register/token)
#  5. profile: 認証後ユーザー情報取得
# ─────────────────────────────────────────────────────────────────

# 各機能ルータをマウント
api_router.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
api_router.include_router(logs.router,     prefix="/logs",     tags=["logs"])
api_router.include_router(health.router,   prefix="/health",   tags=["health"])
api_router.include_router(auth_router_module.auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(profile_router_module.router,    prefix="/profile", tags=["profile"])