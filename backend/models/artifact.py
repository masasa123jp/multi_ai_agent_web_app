# backend/models/artifact.py
"""
Artifact モデル
────────────────────────────────────────────────────────────
プロジェクトに紐づく『アーティファクト』（生成物）を保存する
テーブル "agentbased.artifacts" の ORM モデル。

■ テーブル定義 (PostgreSQL):
    CREATE TABLE IF NOT EXISTS agentbased.artifacts (
        artifact_key           BIGINT NOT NULL DEFAULT nextval(
                                    'agentbased.artifacts_artifact_key_seq'::regclass
                                ),
        project_user_email     VARCHAR(255) NOT NULL,
        project_name           VARCHAR(255) NOT NULL,
        artifact_type          VARCHAR(50)  NOT NULL,
        content                TEXT,
        created_at             TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT artifacts_pkey
            PRIMARY KEY (artifact_key),
        CONSTRAINT artifacts_project_user_email_project_name_fkey
            FOREIGN KEY (project_user_email, project_name)
            REFERENCES agentbased.projects (user_email, name)
            ON DELETE CASCADE
    );
"""

from __future__ import annotations

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKeyConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt, Text

if TYPE_CHECKING:
    from backend.models.project import Project


class Artifact(AsyncAttrs, Base):
    """プロジェクト単位で生成・保存されるアーティファクトを表す ORM モデル"""

    __tablename__ = "artifacts"
    __table_args__ = (
        # 複合外部キー制約: (project_user_email, project_name) → projects の複合 PK
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="artifacts_project_user_email_project_name_fkey",
        ),
        {"schema": "agentbased"},
    )

    # ── 主キー: artifact_key ───────────────────────────────
    artifact_key: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主キー: artifacts.artifact_key シーケンス"
    )

    # ── 外部キー (projects.user_email, projects.name) ─────────
    project_user_email: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="参照プロジェクトの所有者メールアドレス"
    )
    project_name: Mapped[PKStr] = mapped_column(
        String(255),
        nullable=False,
        comment="参照プロジェクト名"
    )

    # ── 任意カラム ─────────────────────────────────────────
    artifact_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="アーティファクト種別 (例: 'log', 'report', 'diagram' 等)"
    )
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="アーティファクトの内容 (テキスト形式)"
    )
    created_at: Mapped[CreatedAt] = mapped_column(
        comment="レコード作成日時",
        server_default="CURRENT_TIMESTAMP"
    )

    # ── リレーション: Project ───────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="artifacts",
        lazy="selectin",
        doc="このアーティファクトが所属するプロジェクト"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Artifact "
            f"{self.project_user_email}/{self.project_name}"
            f"#{self.artifact_key} [{self.artifact_type}]>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        artifact_type: str,
        content: str | None = None,
    ) -> Artifact:
        """
        ファクトリメソッド:
        - created_at を現在 UTC 時刻で自動付与
        - Artifact インスタンスを生成して返す
        """
        now = dt.now()
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            artifact_type=artifact_type,
            content=content,
            created_at=now,
        )
