# backend/models/dba_design.py
"""
DBADesign モデル
────────────────────────────────────────────────────────────
LLM が生成したデータベース設計スキーマを保存するテーブル「dba_designs」の ORM モデル。

■ テーブル定義（PostgreSQL）
  CREATE TABLE IF NOT EXISTS agentbased.dba_designs (
      dba_design_key BIGINT NOT NULL DEFAULT nextval(
          'agentbased.dba_designs_dba_design_key_seq'::regclass
      ),
      project_user_email VARCHAR(255) NOT NULL,
      project_name VARCHAR(255) NOT NULL,
      design_schema TEXT,
      created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT dba_designs_pkey PRIMARY KEY (dba_design_key),
      CONSTRAINT dba_designs_project_user_email_project_name_fkey
        FOREIGN KEY (project_user_email, project_name)
        REFERENCES agentbased.projects (user_email, name)
        ON DELETE CASCADE
  );
"""

from __future__ import annotations

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, ForeignKeyConstraint, Text as SA_Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt

if TYPE_CHECKING:
    from backend.models.project import Project


class DBADesign(AsyncAttrs, Base):
    """
    DBA 設計モデル
    - LLM によって生成された DB スキーマ（DDL など）を
      プロジェクト単位で保存する。
    - 複合外部キー (project_user_email, project_name) → projects テーブル
    """
    __tablename__ = "dba_designs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="dba_designs_project_fkey"
        ),
        {"schema": "agentbased"},
    )

    # ── 主キー: dba_design_key ─────────────────────────
    dba_design_key: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主キー: dba_designs.dba_design_key シーケンス"
    )

    # ── 複合外部キーとして参照するプロジェクト識別子 ───
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

    # ── 任意カラム ────────────────────────────────────
    design_schema: Mapped[str | None] = mapped_column(
        SA_Text,
        nullable=True,
        comment="データベース設計スキーマ (DDL や ER 図 JSON 等)"
    )
    created_at: Mapped[CreatedAt] = mapped_column(
        comment="レコード作成日時",
        server_default="CURRENT_TIMESTAMP"
    )

    # ── リレーション: Project ─────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="dba_designs",
        lazy="selectin",
        doc="この設計が紐づくプロジェクト"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<DBADesign "
            f"{self.project_user_email}/{self.project_name} "
            f"#{self.dba_design_key}>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        design_schema: str | None = None,
    ) -> DBADesign:
        """
        ファクトリメソッド:
        created_at を現在 UTC 時刻で自動付与する。
        """
        now = dt.utcnow()
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            design_schema=design_schema,
            created_at=now,
        )
