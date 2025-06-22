# backend/db/dependencies_async.py

"""
============================================================
FastAPI 依存関数定義モジュール
------------------------------------------------------------
• get_db: リクエスト単位で非同期 DB セッションを生成
• get_current_user: Bearer JWT を検証し、DB からユーザを取得
• db_lifespan: FastAPI アプリのライフサイクルハンドラを再エクスポート
============================================================
"""

from typing import AsyncIterator, Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.async_engine import async_session_factory, db_lifespan
from backend.models.user import User
from backend.security.auth import decode_access_token, UserPayload

# OAuth2PasswordBearer で Authorization ヘッダをパース (auto_error=False でエラーを自前処理)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    FastAPI エンドポイントの Depends で利用する非同期 DB セッション生成器。
    リクエストごとにセッションを開き、処理完了後に自動でクローズされる。
    """
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    """
    Cookie または Authorization ヘッダの Bearer トークンから
    認証済みユーザを取得する FastAPI の依存関数。

    フロー:
      1. Authorization ヘッダを優先してトークンを取得
      2. ヘッダにトークンがなければ、Cookie ("access_token") を確認
      3. トークンをデコードして UserPayload.email を取得
      4. DB から対応するユーザレコードを取得し返却
      5. いずれかで失敗すれば 401 Unauthorized を返す
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1) Authorization ヘッダから Bearer トークン取得
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]

    # 2) ヘッダにトークンがなければ Cookie を参照
    if not token:
        raw = request.cookies.get("access_token")
        if raw and raw.lower().startswith("bearer "):
            token = raw.split(" ", 1)[1]

    # トークン未取得なら認証失敗
    if not token:
        raise credentials_exception

    # 3) トークンをデコードし、UserPayload.email を取得
    try:
        payload: UserPayload = decode_access_token(token)
        print(payload)
        email = payload.email
    except HTTPException:
        # decode_access_token 内で 401 を投げているため、そのまま伝播
        raise
    except Exception:
        # 想定外のエラーも 401 として扱う
        raise credentials_exception

    # 4) DB からユーザを検索
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise credentials_exception

    # 5) 認証済ユーザモデルを返却
    return user


# ── 再エクスポート ────────────────────────────────────────────
# FastAPI アプリの lifespan に設定できるように
__all__ = ["get_db", "get_current_user", "db_lifespan"]
