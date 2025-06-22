# backend/models/system_log.py
"""
SystemLog モデル  (DDL: system_logs)
────────────────────────────────────────────────────────────────────────────
アプリケーション全体で共通利用する “ファイア・アンド・フォーゲット” 型
ログテーブル。任意のコンテキストで `SystemLog.create(level,msg)` を呼ぶだけで
DB へ非同期 insert できる軽量ユーティリティを持つ。
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import ClassVar

from sqlalchemy import String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

from backend.models.core import Base, PKInt, CreatedAt

_log = logging.getLogger(__name__)


class SystemLog(AsyncAttrs, Base):
    """system_logs"""
    __table_args__ = {"schema": "agentbased"}
    __tablename__ = "system_logs"

    # ─── 主キー ───────────────────────────────────────────
    log_key: Mapped[PKInt]

    # ─── 本体 ─────────────────────────────────────────────
    log_level: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)

    created_at: Mapped[CreatedAt]

    # ─── クラスユーティリティ ─────────────────────────────
    _LEVEL_MAP: ClassVar[dict[int, str]] = {
        logging.DEBUG:   "DEBUG",
        logging.INFO:    "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR:   "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        level: int,
        message: str,
    ) -> "SystemLog":
        """
        任意の場所で呼んで非同期 INSERT。

        Parameters
        ----------
        session : AsyncSession
            呼び出し側の DB セッション。
        level : int
            logging モジュールの数値レベル。
        message : str
            保存したいメッセージ文字列。
        """
        log = cls(
            log_level=cls._LEVEL_MAP.get(level, "INFO"),
            message=message,
        )
        session.add(log)
        await session.commit()
        _log.debug("SystemLog saved id=%s level=%s", log.log_key, log.log_level)
        return log
