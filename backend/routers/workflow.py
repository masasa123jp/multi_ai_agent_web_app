# backend/routers/workflow.py

"""
AI マルチエージェント・ワークフローの REST / WebSocket ルーター

提供するエンドポイント:
  - POST  /api/workflow/async
      • クライアントからのワークフロー開始要求を受け付け、DB に記録して workflow_id を返却
  - WS    /api/projects/workflow/ws/{workflow_id}
      • 指定ワークフローを LangGraph で逐次実行
      • 各ステップ完了で通常メッセージおよび累積コストを送信
  - WS    /api/workflow/ws/{workflow_id}
      • 旧互換用ストリーム（agent_client 経由）
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, status
from pydantic import BaseModel, Field
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# ── 依存関数 ───────────────────────────────────────────────────────────────
from backend.db.dependencies_async import get_db, get_current_user

# ── ORM モデル ─────────────────────────────────────────────────────────────
from backend.models.workflow_log import WorkflowLog

# ── ワークフロー実行ロジック ─────────────────────────────────────────────────
from backend.orchestrator.langgraph_workflow import execute_workflow, set_on_step

# ── 累積コスト配信ハブ ─────────────────────────────────────────────────────
from backend.services.cost_hub import connect as cost_connect, disconnect as cost_disconnect, broadcast_cost

# ── 旧互換ストリーム ───────────────────────────────────────────────────────
from backend.services.agent_client import get_agent_stream

logger = logging.getLogger("backend.workflow")
router = APIRouter(prefix="/api")


class StartWorkflowRequest(BaseModel):
    """
    フロントエンドから受信するワークフロー開始パラメータ

      requirement   : 要件テキスト
      project_name  : プロジェクト名
      model         : 使用 AI モデル名
      max_cost      : 累積コスト上限 (USD)
      max_loops     : フィードバックループの最大回数
    """
    requirement: str
    project_name: str
    model: str = "o4-mini-high"
    max_cost: float = 1.0
    max_loops: int = Field(3, ge=1)


@router.post(
    "/workflow/async",
    status_code=status.HTTP_201_CREATED,
    summary="REST: ワークフロー開始",
    description="""
1. リクエストボディのパラメータを WorkflowLog に詰める  
2. DB に保存 → トランザクションコミット  
3. 生成された workflow_id を返却  
    """
)
async def start_workflow_async(
    req: StartWorkflowRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    REST エンドポイント: 
    ユーザ認証済みの状態でワークフロー要求を受け付け、DB に履歴登録します。
    """
    wf = WorkflowLog(
        requirement=req.requirement,
        project_name=req.project_name,
        model=req.model,
        max_cost=req.max_cost,
        max_loops=req.max_loops,
        user_email=current_user.email,
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)

    logger.info("Workflow %d recorded by %s", wf.id, current_user.email)
    return {"workflow_id": wf.id}


@router.websocket("/projects/workflow/ws/{workflow_id}")
async def workflow_ws(
    websocket: WebSocket,
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    WS: リアルタイム進捗＆コスト配信

    • 各ステップ完了で標準メッセージと累積コストを別チャネルで送信。
    • 最後に archive_id を送り、切断します。
    """
    await websocket.accept()
    await cost_connect(workflow_id, websocket)

    logger.info("WS connect workflow=%d session=%s", workflow_id, uuid4().hex[:8])

    async def send_json_safe(payload: dict[str, Any]) -> None:
        try:
            await websocket.send_json(payload)
        except Exception:
            logger.warning("Failed to send JSON on WS: %s", payload.get("step_name"))

    wf: WorkflowLog | None = await db.get(WorkflowLog, workflow_id)
    if wf is None:
        await send_json_safe({"error": "Invalid workflow_id"})
        await cost_disconnect(workflow_id, websocket)
        await websocket.close()
        return

    async def on_step(agent: str, step: str, data: Any) -> None:
        # 1) プログレス情報
        await send_json_safe({
            "current_agent": agent,
            "step_name":     step,
            "output_data":   data,
        })
        # 2) 累積コスト情報
        total = data.get("total_cost")
        if isinstance(total, (int, float)):
            await broadcast_cost(workflow_id, total)

    set_on_step(on_step)

    try:
        final_state = await execute_workflow(
            requirement=wf.requirement,
            project_name=wf.project_name,
            model=wf.model,
            max_cost=wf.max_cost,
            workflow_id=workflow_id,
            max_loops=wf.max_loops,
            mode="detail",
            on_step=on_step,
        )
        await send_json_safe({
            "current_agent": "orchestrator",
            "archive_id":    final_state.get("archive_id"),
        })
    except Exception:
        logger.exception("Workflow execution error (id=%d)", workflow_id)
        await send_json_safe({"error": "Internal workflow error"})
    finally:
        await cost_disconnect(workflow_id, websocket)
        await websocket.close()
        logger.info("WS closed workflow=%d", workflow_id)


@router.websocket("/workflow/ws/{workflow_id}")
async def ws_workflow(
    websocket: WebSocket,
    workflow_id: int,
):
    """
    WS: 旧互換テキストストリーム

    **Deprecated**: 従来クライアント互換用 WebSocket。
    agent_client.get_agent_stream を用いてテキストを逐次送出します。
    """
    await websocket.accept()
    try:
        async for msg in get_agent_stream(workflow_id):
            await websocket.send_text(msg)
    except Exception:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    else:
        await websocket.close()
