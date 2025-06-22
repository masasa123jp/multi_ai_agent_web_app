# backend/models/api_usage_log.py
"""
APIUsageLog モデル（SQLAlchemy2.0 / Async 対応版）
──────────────────────────────────────────────
・OpenAI / Azure OpenAI など外部 API の利用状況を記録するテーブル  
・従来 Flask-SQLAlchemy 依存から脱却し、共通 ``Base`` を継承  
・BigSerial ⇒ PostgreSQL, BIGINT 自動採番（SQLite では INTEGER）  
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

from backend.models.core import Base, PKInt, CreatedAt, Text

# TYPE_CHECKING ブロックは現時点で不要（外部参照が無いため省略）


class APIUsageLog(AsyncAttrs, Base):
    """
    外部 API のトークン使用量／コストを記録するエンティティ。
    
    Columns
    -------
    api_usage_key : int
        主キー（BIGSERIAL）
    api_name : str
        呼び出した API 名（例: 'openai.chat.completions'）
    request_time : datetime
        リクエスト発行時刻（デフォルト: 現在時刻）
    tokens_used : int | None
        消費トークン数。計測不能な場合は NULL
    cost : Decimal | None
        課金額（USD 想定, 小数点以下 6 桁）
    details : str | None
        任意の追加情報（JSON 文字列など）
    created_at : datetime
        レコード生成時刻（``CreatedAt`` 型エイリアス）
    """

    __table_args__ = {"schema": "agentbased"}
    __tablename__ = "api_usage_logs"

    # ── カラム定義 ────────────────────────────────
    api_usage_key: Mapped[PKInt]
    api_name: Mapped[str] = mapped_column(String(100), nullable=False)
    request_time: Mapped[CreatedAt] = mapped_column(
        doc="リクエスト発行時刻（UTC）"
    )
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    details: Mapped[str | None] = mapped_column(Text)

    # created_at は ``CreatedAt`` 別名で定義済み（core.py）
    created_at: Mapped[CreatedAt]

    # ── 便利メソッド ───────────────────────────────
    def __repr__(self) -> str:
        """デバッグ時に読みやすい表現を返す"""
        return (
            f"<APIUsageLog id={self.api_usage_key} "
            f"api={self.api_name!r} tokens={self.tokens_used}>"
        )
