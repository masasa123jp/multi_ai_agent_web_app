"""
agents.ui_generation.app
────────────────────────────────────────────────────────────────────────────
UI 生成エージェント (port 8002)
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from backend.telemetry import init_otel            # ★ 追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import UIGenRequest, UIGenResponse
from .services import generate_ui

ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="UI Generation Agent", version="1.0.0")

# OpenTelemetry
init_otel("ui-generation-agent", fastapi_app=app)       # ★ 追加 ★


@app.post("/generate_ui", response_model=UIGenResponse)
@agent_endpoint(UIGenRequest, output_key="ui")
async def _generate_ui(request_model: UIGenRequest):  # type: ignore[valid-type]
    """
    フロントエンド要件を基に HTML/CSS を生成する。
    """
    result = await generate_ui(request_model)
    return result["ui"]


if __name__ == "__main__":
    uvicorn.run(
        "agents.ui_generation.app:app",
        host="127.0.0.1",
        port=8002,
        reload=False,
        log_level="debug",
    )
