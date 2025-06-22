# backend/security/auth.py

"""
============================================================
JWT 認証ユーティリティモジュール
------------------------------------------------------------
• パスワードのハッシュ化／検証（bcrypt via passlib）
• JWT アクセストークンの作成／デコード（python-jose）
• FastAPI の OAuth2PasswordBearer を用いたトークン取得
============================================================
"""

import datetime
import logging
import os
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from backend.config.settings import get_settings  # 設定からシークレットなどを取得

# ── 設定／定数 ─────────────────────────────────────────────
settings = get_settings()
SECRET_KEY = settings.jwt_secret                     # 本番では必ず強力な値を環境変数で設定
ALGORITHM  = "HS256"                                 # JWT の署名アルゴリズム
# トークン有効期間（分）は環境変数または設定から取得
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

# ── ロガー設定 ────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── FastAPI 用 OAuth2 スキーマ ────────────────────────────────
# /api/auth/login エンドポイントで JWT を発行しているため、tokenUrl を合わせる
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ── パスワードハッシュ用コンテキスト ───────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Pydantic モデル定義 ───────────────────────────────────────
class TokenResponse(BaseModel):
    """
    /api/auth/login が返却するトークン情報モデル。
    - access_token: JWT 本体
    - token_type:   固定で "bearer"
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    JWT デコード後のペイロードモデル。
    - sub: JWT subject (ユーザ識別子として email を利用)
    - exp: 有効期限 (Unix タイムスタンプ or datetime)
    """
    sub: str
    exp: int


class UserPayload(BaseModel):
    """
    デコード後に最終的に返却するユーザ情報モデル。
    - email: 認証済みユーザのメールアドレス
    - role:  ユーザのロール（省略時は "user"）
    """
    email: str
    role: str = "user"


# ── パスワード関連ユーティリティ ───────────────────────────────
def hash_password(password: str) -> str:
    """
    平文パスワードから bcrypt ハッシュを生成。
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    平文パスワードとハッシュを照合。
    """
    return pwd_context.verify(password, hashed)


# ── JWT トークン作成／検証 ───────────────────────────────────
def create_access_token(
    subject: str,
    extra: Optional[dict[str, Any]] = None
) -> str:
    """
    JWT を生成し文字列で返却。
    - subject(sub) にユーザ識別子 (email)
    - exp に現在時刻 + ACCESS_TOKEN_EXPIRE_MINUTES
    - extra を渡すとペイロードにマージされる（例: role 情報等）
    """
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)  # ここで role 等を追加
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> UserPayload:
    """
    JWT をデコードし、型チェック後に UserPayload を返却。
    - 署名検証、期限切れチェックを含む
    - Pydantic で構造チェック
    - エラー時は 401 Unauthorized を返却
    """

    print("In decode_access_token 1")
    try:
        # 1) 署名検証・期限チェック
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        logger.warning("JWT decode error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print("In decode_access_token 2")
    try:
        # 2) ペイロード構造検証 (sub, exp)
        payload = TokenPayload(**data)
    except ValidationError as e:
        logger.warning("JWT payload validation error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print("In decode_access_token 3")
    # 3) UserPayload に変換して返却（role をペイロードから取得）
    user_role = data.get("role", "user")
    return UserPayload(email=payload.sub, role=user_role)


def get_current_token(
    token: str = Depends(oauth2_scheme)
) -> UserPayload:
    """
    FastAPI の依存関数として利用。
    - Authorization ヘッダーの Bearer トークンを取得
    - decode_access_token を呼び出して UserPayload を返却
    """
    return decode_access_token(token)
