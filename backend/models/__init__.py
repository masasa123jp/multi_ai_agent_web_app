# backend/models/__init__.py
"""
モデル一括エクスポートモジュール
────────────────────────────────────────────────────────────
外部コードが `backend.models` を import するだけで **すべての Domain
Model**・`Base` (SQLAlchemy metadata) を利用できる “Facade”。

利点
-----
* import 記述を 1 行に集約  
  `from backend.models import User, Project, Artifact` など。
* Alembic マイグレーションや FastAPI アプリ初期化時の
  `Base.metadata` 取得も `from backend.models import Base` で一貫。
* `__all__` を明示し IDE 補完 & 型チェック精度を向上。
* ルートでの副作用（テーブル定義外の処理）は禁止し
  循環 import を防止。

注意
-----
各モデルファイル内で `relationship()` を張っているため、
ここでは **import だけ** を行い、追加ロジックは置かない。
"""

from __future__ import annotations

# ── メタデータ (必ず最初に再エクスポート) ────────────────
from backend.models.core import Base  # noqa: F401

# ── Domain Models (アルファベット順) ─────────────────────
from backend.models.agent_task import AgentTask  # noqa: F401
from backend.models.api_usage_log import APIUsageLog  # noqa: F401
from backend.models.artifact import Artifact  # noqa: F401
from backend.models.cost_log import CostLog  # noqa: F401
from backend.models.dba_design import DBADesign  # noqa: F401
from backend.models.file_attachment import FileAttachment  # noqa: F401
from backend.models.it_consulting_report import ITConsultingReport  # noqa: F401
from backend.models.log_archive import LogArchive  # noqa: F401
from backend.models.project import Project  # noqa: F401
from backend.models.security_report import SecurityReport  # noqa: F401
from backend.models.stakeholder_feedback import StakeholderFeedback  # noqa: F401
from backend.models.system_log import SystemLog  # noqa: F401
from backend.models.test_result import TestResult  # noqa: F401
from backend.models.user import User  # noqa: F401
from backend.models.workflow_execution import WorkflowExecution  # noqa: F401
from backend.models.workflow_log import WorkflowLog  # noqa: F401
from backend.models.workflow_log_step import WorkflowLogStep  # noqa: F401

# ── 公開シンボル一覧 ────────────────────────────────────
__all__: list[str] = [
    # メタデータ
    "Base",
    # エンティティ
    "User",
    "Project",
    "AgentTask",
    "Artifact",
    "FileAttachment",
    "StakeholderFeedback",
    "TestResult",
    "SecurityReport",
    "ITConsultingReport",
    "DBADesign",
    "SystemLog",
    "APIUsageLog",
    "CostLog",
    "WorkflowExecution",
    "WorkflowLog",
    "WorkflowLogStep",
    "LogArchive",
]
