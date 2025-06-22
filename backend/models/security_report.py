# backend/models/security_report.py
"""
脆弱性診断レポートモデル
────────────────────────────────────────────────────────────
LLM によるセキュリティスキャン（OWASP Top10 等）の結果を保存する
「agentbased.security_reports」テーブルの ORM モデル。

■ テーブル定義
    • security_report_key   : bigint, 主キー, シーケンスで自動付与
    • project_user_email    : varchar(255), FK の一部
    • project_name          : varchar(255), FK の一部
    • report                : text, レポート本文 (Markdown / JSON など)
    • vulnerability_count   : integer, 検出された脆弱性件数
    • created_at            : timestamp, デフォルト CURRENT_TIMESTAMP
    • 外部キー
        - (project_user_email, project_name)
          → agentbased.projects(user_email, name) ON DELETE CASCADE
"""

from __future__ import annotations

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, Integer, Text as SAText, ForeignKeyConstraint, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt

if TYPE_CHECKING:
    from backend.models.project import Project


class SecurityReport(AsyncAttrs, Base):
    """脆弱性診断レポート"""

    __tablename__ = "security_reports"
    __table_args__ = (
        # 複合外部キー → agentbased.projects(user_email, name)
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="security_reports_project_user_email_project_name_fkey",
        ),
        {"schema": "agentbased"},
    )

    # ── プライマリキー ──────────────────────────────────────────
    security_report_key: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        server_default=func.nextval("agentbased.security_reports_security_report_key_seq"),
        comment="主キー。シーケンスで自動付与"
    )

    # ── FK 一部 ────────────────────────────────────────────────
    project_user_email: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="所有プロジェクトのユーザメールアドレス"
    )
    project_name: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="所有プロジェクト名"
    )

    # ── レポート本文・検出数 ─────────────────────────────────────
    report: Mapped[str | None] = mapped_column(
        SAText,
        nullable=True,
        comment="脆弱性レポート本文 (Markdown / JSON 等)"
    )
    vulnerability_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="検出された脆弱性件数"
    )

    # ── 作成日時 ───────────────────────────────────────────────
    created_at: Mapped[CreatedAt] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        comment="作成日時 (デフォルト CURRENT_TIMESTAMP)"
    )

    # ── リレーション ───────────────────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="security_reports",
        lazy="selectin",
        doc="このレポートが属するプロジェクト"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<SecurityReport key={self.security_report_key} "
            f"{self.project_user_email}/{self.project_name} "
            f"(count={self.vulnerability_count})>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        report: str | None = None,
        vulnerability_count: int | None = None,
    ) -> SecurityReport:
        """
        ファクトリメソッド:
        新規レポートを作成するときに使用。作成日時を自動付与します。
        """
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            report=report,
            vulnerability_count=vulnerability_count,
            created_at=dt.utcnow(),
        )
