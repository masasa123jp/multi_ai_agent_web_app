# agents/qa/app.py

"""
agents.qa_agent.app
────────────────────────────────────────────────────────────────────────────
QA エージェント (port 8003)
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI, HTTPException

from backend.telemetry import init_otel            # ★ 追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import QARunRequest, QARunResponse
from .services import run_qa

# 多重起動防止・ロギング初期化
ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="QA Agent", version="1.0.0")

# OpenTelemetry 計測開始
init_otel("qa-agent", fastapi_app=app)

@app.post("/run_qa", response_model=QARunResponse)
@agent_endpoint(QARunRequest, output_key="qa_report")
async def _run_qa(req_model: QARunRequest):  # type: ignore[valid-type]
    """
    テスト計画を実行し、QA レポートを生成するエンドポイント。
    """
    # 入力バリデーション
    if not req_model.code.strip():
        logger.error("No source code provided for QA")
        raise HTTPException(status_code=400, detail="code is required")
    # QA レポート生成
    result = await run_qa(req_model)
    return result["qa_report"]

if __name__ == "__main__":
    uvicorn.run(
        "agents.qa_agent.app:app",
        host="127.0.0.1",
        port=8003,
        reload=False,
        log_level="debug",
    )
