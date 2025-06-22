# backend/routers/profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.dependencies_async import get_db, get_current_user
from backend.models import User

router = APIRouter(
    prefix="",
    tags=["profile"],
)

@router.get("/", summary="ログイン中ユーザーのプロファイル取得")
async def read_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    認証済みユーザーの情報を返却
      - email, username, created_at など
    """
    # current_user は get_current_user で保証済み
    return {
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat(),
        # 必要に応じて他のプロパティも追加
    }
