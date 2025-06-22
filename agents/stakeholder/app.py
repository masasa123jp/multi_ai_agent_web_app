"""
agents.stakeholder_agent.app
────────────────────────────────────────────────────────────────────────────
ステークホルダー・フィードバック収集エージェント (port 8008)
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from backend.telemetry import init_otel            # ★ 追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import CollectFeedbackRequest, CollectFeedbackResponse
from .services import summarize_feedback

ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Stakeholder Agent", version="1.0.0")

# OpenTelemetry
init_otel("stakeholder-agent", fastapi_app=app)          # ★ 追加 ★


@app.post("/collect_feedback", response_model=CollectFeedbackResponse)
@agent_endpoint(CollectFeedbackRequest, output_key="feedback_summary")
async def _collect_feedback(request_model: CollectFeedbackRequest):  # type: ignore[valid-type]
    """
    フィードバックを要約して返却する。
    """
    return (await summarize_feedback(request_model))["feedback_summary"]


if __name__ == "__main__":
    uvicorn.run(
        "agents.stakeholder_agent.app:app",
        host="127.0.0.1",
        port=8008,
        reload=False,
        log_level="debug",
    )
