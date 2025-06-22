"""
TestResult モデル
────────────────────────────────────────────────────────────
LLM テスト実行の結果（QA レポート、カバレッジ）を保存する
"agentbased.test_results" テーブルの ORM モデル。

■ テーブル定義（PostgreSQL）
  CREATE TABLE IF NOT EXISTS agentbased.test_results (
      test_result_key BIGINT NOT NULL DEFAULT nextval(
          'agentbased.test_results_test_result_key_seq'::regclass
      ),
      project_user_email VARCHAR(255) NOT NULL,
      project_name VARCHAR(255) NOT NULL,
      qa_report TEXT,
      test_coverage NUMERIC(5,2),
      created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
      CONSTRAINT test_results_pkey PRIMARY KEY (test_result_key),
      CONSTRAINT test_results_project_user_email_project_name_fkey
        FOREIGN KEY (project_user_email, project_name)
        REFERENCES agentbased.projects (user_email, name)
        ON DELETE CASCADE
  );
"""

from __future__ import annotations

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, Numeric, Text as SA_Text, ForeignKeyConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.core import Base, PKStr, CreatedAt

if TYPE_CHECKING:
    from backend.models.project import Project


class TestResult(AsyncAttrs, Base):
    """
    テスト結果モデル
    - LLM が生成した QA レポートやテストカバレッジを
      プロジェクト単位で保存する。
    - 複合外部キー (project_user_email, project_name) → projects テーブル
    """
    __tablename__ = "test_results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["project_user_email", "project_name"],
            ["agentbased.projects.user_email", "agentbased.projects.name"],
            ondelete="CASCADE",
            name="test_results_project_fkey",
        ),
        {"schema": "agentbased"},
    )

    # ── 主キー: test_result_key ─────────────────────────
    test_result_key: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主キー: test_results.test_result_key シーケンス"
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
    qa_report: Mapped[str | None] = mapped_column(
        SA_Text,
        nullable=True,
        comment="QA レポート (Markdown / JSON など)"
    )
    test_coverage: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="テストカバレッジ (%)"
    )

    created_at: Mapped[CreatedAt] = mapped_column(
        comment="レコード作成日時",
        server_default="CURRENT_TIMESTAMP"
    )

    # ── リレーション: Project ─────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="test_results",
        lazy="selectin",
        doc="この結果が紐づくプロジェクト"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<TestResult "
            f"{self.project_user_email}/{self.project_name} "
            f"#{self.test_result_key}>"
        )

    @classmethod
    def create(
        cls,
        *,
        project_user_email: str,
        project_name: str,
        qa_report: str | None = None,
        test_coverage: float | None = None,
    ) -> TestResult:
        """
        ファクトリメソッド:
        created_at を現在時刻で自動付与する。
        """
        now = dt.now()
        return cls(
            project_user_email=project_user_email,
            project_name=project_name,
            qa_report=qa_report,
            test_coverage=test_coverage,
            created_at=now,
        )
