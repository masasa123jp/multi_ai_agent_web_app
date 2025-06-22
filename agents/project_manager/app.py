"""
agents.project_manager_agent.app
────────────────────────────────────────────────────────────────────────────
プロジェクト管理エージェント (port 8007)
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from backend.telemetry import init_otel            # ★ 追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import ScheduleRequest, ScheduleResponse
from .services import create_schedule

ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Project-Manager Agent", version="1.0.0")

# OpenTelemetry
init_otel("project-manager-agent", fastapi_app=app)      # ★ 追加 ★


@app.post("/schedule", response_model=ScheduleResponse)
@agent_endpoint(ScheduleRequest, output_key="schedule")
async def _schedule(req_model: ScheduleRequest):  # type: ignore[valid-type]
    """
    プロジェクトスケジュールを生成して返却する。
    """
    return (await create_schedule(req_model))["schedule"]


if __name__ == "__main__":
    uvicorn.run(
        "agents.project_manager_agent.app:app",
        host="127.0.0.1",
        port=8007,
        reload=False,
        log_level="debug",
    )
