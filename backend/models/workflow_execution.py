"""
===============================================================================
WorkflowExecution モデル
───────────────────────────────────────────────
ワークフロー（AI エージェントやジョブの実行単位）の
開始時刻／終了時刻、ステータス、結果サマリーなどを永続化する
監査テーブルの ORM モデル。

複合 FK: (project_user_email, project_name) → agentbased.projects テーブル
主キー: wf_exec_key
===============================================================================
"""

from __future__ import annotations
from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, DateTime, Text, ForeignKeyConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt

if TYPE_CHECKING:
    from backend.models.project import Project


class WorkflowExecution(AsyncAttrs, Base):
    """ワークフロー実行ログを表す ORM モデル"""

    __tablename__ = "workflow_executions"
    __table_args__ = (
        # projects テーブルの複合 PK (user_email, name) を参照
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="workflow_executions_project_fkey",
        ),
        # スキーマ指定
        {"schema": "agentbased"},
    )

    # ── 主キー: テーブル上は wf_exec_key ────────────────────────
    workflow_execution_key: Mapped[int] = mapped_column(
        "wf_exec_key",
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主キー: ワークフロー実行レコードのシーケンスキー (wf_exec_key)",
    )

    # ── 複合外部キーとして参照するプロジェクト識別子 ─────────────
    project_user_email: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="参照プロジェクトの所有者メールアドレス (FK)",
    )
    project_name: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="参照プロジェクトの名前 (FK)",
    )

    # ── ワークフロー実行タイムスタンプ ────────────────────────
    start_time: Mapped[dt] = mapped_column(
        DateTime,
        nullable=False,
        comment="ワークフロー開始日時 (start_time)",
    )
    end_time: Mapped[dt] = mapped_column(
        DateTime,
        nullable=False,
        comment="ワークフロー終了日時 (end_time)",
    )

    # ── ステータス・結果サマリー ───────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="実行ステータス (例: PENDING, RUNNING, SUCCESS, FAILURE)",
    )
    summary: Mapped[str | None] = mapped_column(
        "summary",
        Text,
        nullable=True,
        comment="実行結果のサマリー・ログ (summary)",
    )

    # ── 作成日時 (テーブル定義にのみ存在) ───────────────────────
    created_at: Mapped[CreatedAt] = mapped_column(
        comment="レコード作成日時",
        server_default="CURRENT_TIMESTAMP",
    )

    # ── リレーション: Project への多対一 ────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="workflow_executions",
        lazy="selectin",
        doc="この実行が属するプロジェクトへの参照",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<WorkflowExecution "
            f"{self.project_user_email}/"
            f"{self.project_name}#"
            f"{self.workflow_execution_key} "
            f"({self.status})>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        status: str,
        start_time: dt,
        end_time: dt,
        summary: str | None = None,
    ) -> WorkflowExecution:
        """
        ファクトリメソッド:
        引数で受け取った開始／終了時刻、ステータス、サマリーを設定し、
        created_at は現在 UTC 時刻で自動セットする。
        """
        now = dt.now()
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            start_time=start_time,
            end_time=end_time,
            status=status,
            summary=summary,
            created_at=now,
        )
