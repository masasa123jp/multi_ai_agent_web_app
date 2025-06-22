# backend/routers/auth.py

"""
Authentication router module for FastAPI.

Provides:
  - POST /api/auth/login: OAuth2 login endpoint accepting form data (email/password),
    verifies credentials against the database, issues a JWT access token,
    and sets it as an HTTPOnly cookie for browser clients.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.db.dependencies_async import get_db
from backend.models.user import User as UserModel
from backend.security.auth import (
    create_access_token,  # 統一された JWT 発行ロジック
    verify_password,      # bcrypt ハッシュ検証
    TokenResponse,        # Pydantic レスポンスモデル
)

# ── ロガー設定 ─────────────────────────────────────────────────
logger = logging.getLogger("backend.auth")
logger.setLevel(logging.INFO)

# ── API ルータ定義 ─────────────────────────────────────────────
auth_router = APIRouter(
    prefix="",
    tags=["auth"],
    responses={
        401: {"description": "Unauthorized"},
        500: {"description": "Server Error"},
    },
)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="ユーザの認証＆JWT発行",
    description="""
OAuth2PasswordRequestForm.username に email、.password に平文パスワードを期待します。

処理フロー:
1. フォームデータから email/password を取得  
2. DB から User レコードを検索  
3. パスワードハッシュを検証  
4. JWT を生成し、HTTPOnly クッキーにセット  
5. レスポンスボディにトークンを返却  
    """,
)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """
    ユーザ認証エンドポイント。

    - 認証成功時は 200 を返し、アクセストークンをボディ＆クッキーにセット
    - 認証失敗時は 401 を返却
    """
    # リクエスト毎に生成される request_id（ログ追跡用）
    request_id = getattr(request.state, "request_id", "N/A")
    logger.info(f"[{request_id}] Login attempt: email='{form_data.username}'")

    # 1) DB からユーザを検索
    result = await session.execute(
        select(UserModel).where(UserModel.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"[{request_id}] User not found: '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2) パスワード検証（bcrypt via passlib）
    if not verify_password(form_data.password, user.password_hash):
        logger.warning(f"[{request_id}] Incorrect password for '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3) JWT の生成（sub: email, exp: 設定済み TTL）
    try:
        # ユーザ固有の role を extra に渡す
        access_token = create_access_token(
                subject=user.email,
                extra={"role": user.role}
            )
    except Exception as e:
        logger.error(f"[{request_id}] Token generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token generation failed",
        )

    # 4) HTTPOnly Cookie にトークンをセット（ブラウザ クライアント向け）
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="lax",
    )

    logger.info(f"[{request_id}] Login successful for '{form_data.username}'")
    # 5) レスポンスボディにアクセストークンを返却
    return TokenResponse(access_token=access_token)
