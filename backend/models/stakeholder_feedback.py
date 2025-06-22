"""
============================================================
StakeholderFeedback モデル
------------------------------------------------------------
■ 役割
    ステークホルダーからのフィードバック（レビュー・要望）を
    「agentbased.stakeholder_feedback」テーブルに保存する ORM モデル。

    ・feedback_key: 自動採番 BIGINT 主キー
    ・project_user_email / project_name: projects テーブルとの複合外部キー（CASCADE）
    ・stakeholder: フィードホルダー名
    ・feedback: フィードバック本文
    ・created_at: 登録日時（デフォルトで CURRENT_TIMESTAMP）
    ・updated_at: 更新日時（デフォルトで CURRENT_TIMESTAMP、更新時に自動更新）
============================================================
"""

from __future__ import annotations
from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    String,
    Text as SAText,
    ForeignKeyConstraint,
    func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt, UpdatedAt

if TYPE_CHECKING:
    from backend.models.project import Project


class StakeholderFeedback(AsyncAttrs, Base):
    """ステークホルダーからのレビュー・要望を表す ORM モデル"""

    __tablename__ = "stakeholder_feedback"
    __table_args__ = (
        # projects テーブルの複合 PK (user_email, name) を参照する外部キー
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="fk_feedback_project",
        ),
        # スキーマ指定
        {"schema": "agentbased"},
    )

    # ── 複合外部キーの一部: プロジェクト識別子 ───────────────────
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

    # ── 主キー: テーブル上は feedback_key ────────────────────────
    feedback_key: Mapped[int] = mapped_column(
        "feedback_key",
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主キー: フィードバック識別子 (BIGINT 自動採番)",
    )

    # ── ステークホルダー名／フィードバック本文 ──────────────────
    stakeholder: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="ステークホルダー名",
    )
    feedback: Mapped[str] = mapped_column(
        SAText,
        nullable=True,
        comment="フィードバック本文",
    )

    # ── レコード作成／更新タイムスタンプ ────────────────────────
    created_at: Mapped[CreatedAt] = mapped_column(
        comment="登録日時",
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[UpdatedAt] = mapped_column(
        comment="更新日時",
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # ── リレーション: Project への多対一 ────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="feedbacks",
        lazy="selectin",
        doc="このフィードバックが属するプロジェクトへの参照",
    )

    def __repr__(self) -> str:
        """デバッグ時の簡易表示"""
        return (
            f"<StakeholderFeedback "
            f"{self.project_user_email}/"
            f"{self.project_name}#"
            f"{self.feedback_key}>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        stakeholder: str | None = None,
        feedback: str | None = None,
    ) -> StakeholderFeedback:
        """
        ファクトリメソッド:
        引数で受け取ったステークホルダー情報・フィードバックを設定し、
        created_at/updated_at を現在 UTC 時刻でセットした新規インスタンスを返す。
        """
        now = dt.utcnow()
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            stakeholder=stakeholder,
            feedback=feedback,
            created_at=now,
            updated_at=now,
        )
