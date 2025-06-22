# backend/models/core.py
"""
全モデルの共通設定
────────────────────────────────────────
* Base  : DeclarativeBase（backend.db.base 内に定義）
* type_ : Annotated[int | str] などをまとめておくと
         各モデルの import が簡潔になる
"""
from __future__ import annotations

import datetime as _dt
from typing import Annotated

from sqlalchemy import String, Text, LargeBinary, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base  # DeclarativeBase

# 共通型エイリアス（可読性向上）
PKInt      = Annotated[int,  mapped_column(primary_key=True)]
PKStr      = Annotated[str,  mapped_column(String(255), primary_key=True)]
CreatedAt  = Annotated[_dt.datetime, mapped_column(default=_dt.datetime.now)]
UpdatedAt  = Annotated[_dt.datetime, mapped_column(
    default=_dt.datetime.now,
    onupdate=_dt.datetime.now
)]
