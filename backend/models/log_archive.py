# backend/models/log_archive.py
"""
LogArchive モデル（Async / SQLAlchemy 2.0）
────────────────────────────────────────────────────────────
* **目的**  
  1 つのワークフロー実行 (`WorkflowLog`) に束ねられた成果物
  (ZIP バンドル) を永続化する。

👀 **このファイルで解決したこと**
------------------------------------------------------------------
1. **旧 sync 版 `log_archive_model.py` との重複**  
   - 旧ファイルは *Flask-SQLAlchemy* + 同期 ORM／テーブル名
     `log_file_archives`。  
   - 本ファイルは **AsyncAttrs + declarative_base** に統一し、
     テーブル名を `log_archives` に統一。  
   - 旧ファイルは *PRIMARY KEY* として `log_archive_id` を使用して
     いたが、プロジェクト全体の基準に合わせ **PKInt alias
     （SERIAL/BIGSERIAL 相当）** に置換。

2. **filename 列の追加 (要件 No.6)**  
   - 旧ファイルに存在した `filename` 列を新 async 版にも追加し
     ファイル名を保存できるようにした。

3. **WorkflowLog とのリレーション**  
   - 新実装では `workflow_log_id` 外部キーを保持し、  
     `WorkflowLog.log_archives` (一対多) と相互参照。

4. **ユーザ & プロジェクト外部キー**  
   - `user_email` / `project_name` を保持し、将来
     `projects (user_email, name)` への FK を張れる構成に。
"""

from __future__ import annotations

from sqlalchemy import LargeBinary, String, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

from typing import TYPE_CHECKING

# ── 共通型エイリアス (PKInt = BIGSERIAL, CreatedAt = TIMESTAMP) ──
from backend.models.core import Base, PKInt, CreatedAt

# 型ヒント用循環 import 回避
if TYPE_CHECKING:  # pragma: no cover
    from backend.models.workflow_log import WorkflowLog

# ======================================================================
# メインモデル
# ======================================================================
class LogArchive(AsyncAttrs, Base):
    """
    `workflow_logs` に付随する ZIP アーカイブ (成果物一式)

    * **id**            … 主キー (BIGSERIAL)
    * **workflow_log_id** … 親 WorkflowLog への FK
    * **filename**      … 保存時ファイル名 (例: workflow_42.zip)
    * **zip_data**      … バイナリ (ZIP 全文)
    * **user_email**    … アーカイブ所有者 (ステータス閲覧用)
    * **project_name**  … プロジェクト名
    * **created_at**    … 登録日時
    """

    __table_args__ = {"schema": "agentbased"}
    __tablename__ = "log_archives"

    # ----- Columns -----------------------------------------------------
    id: Mapped[PKInt]  # PKInt = mapped_column(primary_key=True, autoincrement=True)
    workflow_log_id: Mapped[int] = mapped_column(
        ForeignKey("agentbased.workflow_logs.id", ondelete="CASCADE"),
        index=True,
        comment="親 WorkflowLog.id",
    )
    filename: Mapped[str | None] = mapped_column(
        String(255), comment="ZIP ファイル名 (任意)"
    )
    zip_data: Mapped[bytes] = mapped_column(
        LargeBinary, comment="ZIP バイナリ (成果物一式)"
    )
    user_email: Mapped[str | None] = mapped_column(
        String(255), comment="アップロードしたユーザ (FK 予定)"
    )
    project_name: Mapped[str | None] = mapped_column(
        String(255), comment="プロジェクト名 (FK 予定)"
    )
    created_at: Mapped[CreatedAt]

    # ----- Relationships ----------------------------------------------
    workflow_log: Mapped["WorkflowLog"] = relationship(
        back_populates="log_archives",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    # ----- String representation --------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LogArchive id={self.id} "
            f"workflow_log_id={self.workflow_log_id} "
            f"filename='{self.filename}'>"
        )
