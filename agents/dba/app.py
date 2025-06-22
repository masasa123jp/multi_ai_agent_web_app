"""
agents.dba_agent.app
────────────────────────────────────────────────────────────────────────────
DB 設計エージェント (port 8006)
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from backend.telemetry import init_otel            # ★ 追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import DesignSchemaRequest, DesignSchemaResponse
from .services import design_schema

ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="DBA Agent", version="1.0.0")

# OpenTelemetry
init_otel("dba-agent", fastapi_app=app)                  # ★ 追加 ★


@app.post("/design_schema", response_model=DesignSchemaResponse)
@agent_endpoint(DesignSchemaRequest, output_key="dba_script")
async def _design_schema(req_model: DesignSchemaRequest):  # type: ignore[valid-type]
    """
    DB スキーマを自動生成して返却する。
    """
    return (await design_schema(req_model))["dba_script"]


if __name__ == "__main__":
    uvicorn.run(
        "agents.dba_agent.app:app",
        host="127.0.0.1",
        port=8006,
        reload=False,
        log_level="debug",
    )
