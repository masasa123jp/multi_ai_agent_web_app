from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, DateTime, ForeignKeyConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt, Text

if TYPE_CHECKING:
    from backend.models.project import Project


"""
===============================================================================
AgentTask モデル
────────────────────────────────────────────────────────────
AI エージェントが 1 回ジョブを実行するたびにレコードを生成し、
実行状況・結果を永続化する監査ログテーブル。

複合 FK: (project_user_email, project_name) → agentbased.projects テーブルの複合 PK
===============================================================================
"""
class AgentTask(AsyncAttrs, Base):
    """AI エージェントのタスク実行履歴を表す ORM モデル"""

    __tablename__ = "agent_tasks"
    __table_args__ = (
        # projects テーブルの複合 PK (user_email, name) を参照
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="fk_agenttask_project",
        ),
        # agentbased スキーマ配下に配置
        {"schema": "agentbased"},
    )

    # ── 主キー: agent_task_key ─────────────────────────────────
    agent_task_key: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主キー: agent_tasks.agent_task_key シーケンス"
    )

    # ── 複合外部キー: プロジェクト識別子 ──────────────────────
    project_user_email: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="参照プロジェクトの所有者メールアドレス"
    )
    project_name: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="参照プロジェクトの名前"
    )

    # ── 任意カラム: 実行種別・ステータス・結果・タイムスタンプ ──
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="エージェントの種類 (例: 'vulnerability_scan', 'data_migration' 等)"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="タスクの実行ステータス (例: 'pending', 'running', 'success', 'failure')"
    )
    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="タスクの実行結果 (JSON 文字列 or Markdown 等)"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="タスク実行開始日時"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="タスク実行完了日時"
    )
    created_at: Mapped[CreatedAt] = mapped_column(
        comment="レコード作成日時 (自動付与)"
    )

    # ── リレーション: Project ───────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="agent_tasks",
        lazy="selectin",
        doc="このタスクが紐づくプロジェクトへの参照"
    )

    def __repr__(self) -> str:  # pragma: no cover
        """デバッグ時にわかりやすく表示するリプレゼンテーション"""
        return (
            f"<AgentTask {self.project_user_email}/"
            f"{self.project_name}#"
            f"{self.agent_task_key}>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        agent_type: str,
        status: str,
        result: str | None = None,
    ) -> AgentTask:
        """
        ファクトリメソッド:
        タスクレコードの作成に必要な最低限の情報を受け取り、
        created_at を現在 UTC 時刻で自動付与する。
        """
        now = datetime.utcnow()
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            agent_type=agent_type,
            status=status,
            result=result,
            started_at=None,
            finished_at=None,
            created_at=now,
        )
