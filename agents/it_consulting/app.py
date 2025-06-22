"""
agents.it_consulting_agent.app
────────────────────────────────────────────────────────────────────────────
IT コンサルティングエージェント (port 8005)
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from backend.telemetry import init_otel            # ★ 追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import AdviceRequest, AdviceResponse
from .services import generate_advice

ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="IT-Consulting Agent", version="1.0.0")

# OpenTelemetry
init_otel("it-consulting-agent", fastapi_app=app)       # ★ 追加 ★


@app.post("/advice", response_model=AdviceResponse)
@agent_endpoint(AdviceRequest, output_key="advice")
async def _advice(request_model: AdviceRequest):  # type: ignore[valid-type]
    """
    IT コンサル観点のアドバイス文を生成して返す。
    """
    return (await generate_advice(request_model))["advice"]


if __name__ == "__main__":
    uvicorn.run(
        "agents.it_consulting_agent.app:app",
        host="127.0.0.1",
        port=8005,
        reload=False,
        log_level="debug",
    )
