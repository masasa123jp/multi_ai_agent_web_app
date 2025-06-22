# backend/models/workflow_log.py
from __future__ import annotations

from typing import List

from sqlalchemy import Integer, LargeBinary, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, CreatedAt, PKInt
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # 遅延 import 用
    from backend.models.workflow_log_step import WorkflowLogStep
    from backend.models.log_archive import LogArchive


class WorkflowLog(AsyncAttrs, Base):
    """
    1 ワークフロー実行単位のメタデータ
    zip_data は完了後に ZIP でバンドルした成果物
    """
    __table_args__ = {"schema": "agentbased"}
    __tablename__ = "workflow_logs"

    id:           Mapped[PKInt]
    project_name: Mapped[str]  = mapped_column(String(256))
    requirement:  Mapped[str]  = mapped_column(Text)
    model:        Mapped[str | None] = mapped_column(String(50))
    max_cost:     Mapped[float | None]
    # ★ NEW: 最大ループ回数
    max_loops:    Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    zip_data:     Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at:   Mapped[CreatedAt]

    # ---------- children ----------
    steps: Mapped[List["WorkflowLogStep"]] = relationship(
        back_populates="workflow_log",
        cascade="all, delete-orphan",
        order_by="WorkflowLogStep.id",
    )
    log_archives: Mapped[List["LogArchive"]] = relationship(
        back_populates="workflow_log",
        cascade="all, delete-orphan",
        order_by="LogArchive.id",
    )
