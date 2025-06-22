"""
============================================================
ITConsultingReport モデル
------------------------------------------------------------
■ 役割
    IT コンサルティングエージェントが出力したベストプラクティス提案を
    保管する「it_consulting_reports」テーブルの ORM モデル。
    Project と複合 FK で 1:N のリレーションを構成。
============================================================
"""

from __future__ import annotations
from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKeyConstraint, func, DateTime, text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt, UpdatedAt, Text

if TYPE_CHECKING:
    from backend.models.project import Project


class ITConsultingReport(AsyncAttrs, Base):
    """IT コンサルティング結果レポートを表す ORM モデル"""

    __tablename__ = "it_consulting_reports"
    __table_args__ = (
        # projects テーブルの複合 PK (user_email, name) を参照
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="fk_itreport_project",
        ),
        # スキーマ指定
        {"schema": "agentbased"},
    )

    # ── 複合 PK の一部: プロジェクト識別子 ────────────────────
    project_user_email: Mapped[PKStr] = mapped_column(
        String(255),
        primary_key=True,
        comment="参照プロジェクト所有者メールアドレス (FK)",
    )
    project_name: Mapped[PKStr] = mapped_column(
        String(255),
        primary_key=True,
        comment="参照プロジェクト名 (FK)",
    )

    # ── 主キー: テーブル上は it_consult_report_key ───────────────
    report_id: Mapped[int] = mapped_column(
        "it_consult_report_key",
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主キー: レポート識別子(it_consult_report_key)",
    )

    # ── レポート本体 ──────────────────────────────────────────
    consultant: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="コンサルタント名",
    )
    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="提案内容のテキスト",
    )

    # ── レコード作成／更新タイムスタンプ ────────────────────────
    created_at: Mapped[CreatedAt] = mapped_column(  # サーバデフォルトで CURRENT_TIMESTAMP
        comment="作成日時",
        server_default="CURRENT_TIMESTAMP",
    )

    updated_at: Mapped[dt] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        comment="レコード更新日時",
        server_default=func.now(),      # or text("CURRENT_TIMESTAMP")
        onupdate=func.now(),
    )

    # ── リレーション: Project への多対一 ────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="it_reports",
        lazy="selectin",
        doc="このレポートが属するプロジェクトへの参照",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ITReport {self.project_user_email}/"
            f"{self.project_name}#{self.report_id}>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        consultant: str,
        recommendation: str,
    ) -> ITConsultingReport:
        """
        ファクトリメソッド:
        created_at／updated_at を現在時刻でセットした新規インスタンスを返す。
        """
        now = dt.utcnow()
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            consultant=consultant,
            recommendation=recommendation,
            created_at=now,
            updated_at=now,
        )
