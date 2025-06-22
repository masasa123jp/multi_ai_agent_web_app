# backend/api/projects.py

import json
import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.db.dependencies_async import get_db
from backend.orchestrator.langgraph_workflow import execute as execute_full_workflow

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

class ProjectRequest(BaseModel):
    requirement: str
    project_name: str
    model: str | None = None
    max_cost: float | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    max_loops: int = Field(3, ge=1, description="最大フィードバックループ回数")  # ← 追加

@router.post(
    "/workflow",
    summary="LLM ワークフローを実行（逐次ストリーム）",
    response_description="JSONL ストリーム",
)
async def run_workflow(
    req: ProjectRequest,
    db: Session = Depends(get_db),
):
    params = req.model_dump()  # Pydantic v2 の場合
    if params["max_loops"] < 1:
        raise HTTPException(status_code=422, detail="max_loops は 1 以上である必要があります")

    async def _runner():
        # execute_full_workflow は async generator を返す想定
        async for chunk in execute_full_workflow(db, params):
            yield json.dumps(chunk, ensure_ascii=False) + "\n"

    headers = {"X-Accel-Buffering": "no"}
    return StreamingResponse(
        _runner(),
        media_type="application/jsonl",
        headers=headers,
    )
