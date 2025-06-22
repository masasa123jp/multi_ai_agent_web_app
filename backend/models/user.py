# backend/models/user.py
from __future__ import annotations

from typing import List
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncAttrs
from backend.models.core import Base, PKStr, CreatedAt, UpdatedAt

from typing import TYPE_CHECKING
# 循環 import を避ける型ヒント用 import
if TYPE_CHECKING:
    from backend.models.project import Project  # ✅ Project クラスは project.py で定義

class User(AsyncAttrs, Base):
    """ユーザ: email を主キーとした自然キー設計"""
    __tablename__ = "users"
    __table_args__ = {"schema": "agentbased"}

    email:       Mapped[PKStr]                  # 例: alice@example.com
    username:    Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role:        Mapped[str | None] = mapped_column(String(50))
    created_at:  Mapped[CreatedAt]
    updated_at:  Mapped[UpdatedAt]

    # --- relationships -------------------------------------------------
    projects: Mapped[List["Project"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
