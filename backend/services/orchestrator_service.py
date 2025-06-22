# backend/services/orchestrator_service.py

"""
backend/services/orchestrator_service.py
─────────────────────────────────────────────────────────────────────────────
ワークフロー起動・管理を担うサービス層モジュール。

- ワークフローの非同期実行エントリポイント
- max_loops（再生成ループ最大回数）を受け取り、DBに保存
- LangGraph に max_loops を渡し、実行ループを制御
- 実行中のキャンセルや状態取得（拡張用フック）
- 入力パラメータのバリデーション
"""

from uuid import uuid4
from typing import Optional

import logging
from asyncio import create_task

from orchestrator.langgraph_workflow import execute_workflow
from backend.models.workflow_log import WorkflowLog
from backend.db.dependencies_async import get_db

logger = logging.getLogger(__name__)


async def start_workflow(
    requirement: str,
    project_name: str,
    model_name: str,
    max_cost: float,
    max_loops: int
) -> int:
    """
    ワークフローを起動し、workflow_id を返却
    1) DBにレコードを生成（max_loops を含む）
    2) バックグラウンドで langgraph を実行
    """

    # --- 1) 一意の workflow_id を生成し DB に保存 -------------------------
    # uuid4().int >> 64 で 64bit 整数化
    workflow_id = uuid4().int >> 64

    async with get_db() as session:
        # WorkflowLog モデルには max_cost, max_loops フィールドを追加しておくこと
        record = WorkflowLog(
            id=workflow_id,
            project_name=project_name,
            requirement=requirement,
            model_name=model_name,
            max_cost=max_cost,
            max_loops=max_loops,    # ここで max_loops を永続化
            status="PENDING"
        )
        session.add(record)
        await session.commit()

    # --- 2) バックグラウンド実行 ------------------------------------------
    async def _run():
        try:
            # LangGraph workflow を実行。max_loops を渡してフィードバックループを制御
            await execute_workflow(
                requirement=requirement,
                project_name=project_name,
                model_name=model_name,
                max_cost=max_cost,
                workflow_id=workflow_id,
                max_loops=max_loops,
                on_step=None  # コールバックは Controller 層で注入
            )

            # 成功時：ステータスを COMPLETED に更新
            async with get_db() as sess2:
                rec2 = await sess2.get(WorkflowLog, workflow_id)
                rec2.status = "COMPLETED"
                await sess2.commit()

        except Exception:
            logger.exception("Workflow %s failed", workflow_id)
            # 失敗時：ステータスを FAILED に更新
            async with get_db() as sess3:
                rec3 = await sess3.get(WorkflowLog, workflow_id)
                rec3.status = "FAILED"
                await sess3.commit()

    # 非同期タスクとして実行
    create_task(_run())

    return workflow_id


async def get_workflow_status(workflow_id: int) -> Optional[str]:
    """
    ワークフローの実行ステータス（PENDING/COMPLETED/FAILED）を取得
    """
    async with get_db() as session:
        rec = await session.get(WorkflowLog, workflow_id)
        return rec.status if rec else None
