# backend/models/workflow_log_step.py
from __future__ import annotations

from sqlalchemy import Integer, String, JSON, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from backend.models.core import Base, CreatedAt, PKInt

from typing import TYPE_CHECKING
# 循環 import を避ける型ヒント用 import
if TYPE_CHECKING:
    from backend.models.workflow_log import WorkflowLog  # ✅ WorkflowLog クラスは workflow_log.py で定義

class WorkflowLogStep(AsyncAttrs, Base):
    """LangGraph の各ステップ結果"""

    __table_args__ = {"schema": "agentbased"}
    __tablename__ = "workflow_log_steps"

    id:             Mapped[PKInt]
    workflow_log_id: Mapped[int] = mapped_column(
        ForeignKey("agentbased.workflow_logs.id", ondelete="CASCADE"), index=True
    )
    step_name:      Mapped[str] = mapped_column(String(128))
    result_text:    Mapped[dict] = mapped_column(JSON)
    seconds_elapsed: Mapped[float | None] = mapped_column(Float)
    error_message:   Mapped[str | None] = mapped_column(Text)
    created_at:     Mapped[CreatedAt]

    workflow_log: Mapped["WorkflowLog"] = relationship(back_populates="steps")
