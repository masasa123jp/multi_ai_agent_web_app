from __future__ import annotations
from datetime import datetime as dt
from typing import List, TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt, UpdatedAt, Text

if TYPE_CHECKING:
    from backend.models.agent_task import AgentTask
    from backend.models.artifact import Artifact
    from backend.models.stakeholder_feedback import StakeholderFeedback
    from backend.models.test_result import TestResult
    from backend.models.security_report import SecurityReport
    from backend.models.it_consulting_report import ITConsultingReport
    from backend.models.dba_design import DBADesign
    from backend.models.file_attachment import FileAttachment
    from backend.models.workflow_execution import WorkflowExecution
    from backend.models.user import User

class Project(AsyncAttrs, Base):
    """
    ユーザが作成する『プロジェクト』を表す ORM モデル。
    - スキーマ：agentbased
    - 複合プライマリキー (user_email, name)
    - 各種子テーブルとの 1:N 双方向リレーション
    """
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("user_email", "name", name="uq_project_user_email_name"),
        {"schema": "agentbased", "sqlite_autoincrement": False},
    )

    # ── 複合プライマリキー ─────────────────────────────
    user_email: Mapped[PKStr] = mapped_column(
        ForeignKey("agentbased.users.email", ondelete="CASCADE"),
        primary_key=True,
        comment="所有ユーザのメールアドレス"
    )
    name: Mapped[PKStr] = mapped_column(
        String(255),
        primary_key=True,
        comment="プロジェクト名 (ユーザ内で一意)"
    )

    # ── 任意カラム ──────────────────────────────────
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[CreatedAt]   # 自動付与される作成日時
    updated_at: Mapped[UpdatedAt]   # 自動付与される更新日時

    # ── 子テーブルとのリレーション ───────────────────────
    agent_tasks: Mapped[List["AgentTask"]] = relationship(
        "AgentTask",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="エージェントタスク一覧"
    )
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="アーティファクト一覧"
    )
    feedbacks: Mapped[List["StakeholderFeedback"]] = relationship(
        "StakeholderFeedback",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="フィードバック一覧"
    )
    test_results: Mapped[List["TestResult"]] = relationship(
        "TestResult",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="テスト結果一覧"
    )
    security_reports: Mapped[List["SecurityReport"]] = relationship(
        "SecurityReport",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="セキュリティレポート一覧"
    )
    it_reports: Mapped[List["ITConsultingReport"]] = relationship(
        "ITConsultingReport",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="ITコンサルティングレポート一覧"
    )
    dba_designs: Mapped[List["DBADesign"]] = relationship(
        "DBADesign",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="DBA設計一覧"
    )
    file_attachments: Mapped[List["FileAttachment"]] = relationship(
        "FileAttachment",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="ファイル添付一覧"
    )
    workflow_executions: Mapped[List["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        doc="ワークフロー実行一覧"
    )

    # ── User との N:1 リレーション ────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
        lazy="selectin",
        doc="所有ユーザ情報"
    )

    def __repr__(self) -> str:
        return f"<Project {self.user_email}/{self.name}>"

    @classmethod
    def create(
        cls, *,
        user_email: str,
        name: str,
        description: str | None = None
    ):
        """ファクトリ: 作成・更新日時を自動付与"""
        now = dt.now()
        return cls(
            user_email=user_email,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )
