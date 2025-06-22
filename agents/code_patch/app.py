"""
agents.code_patch.app
────────────────────────────────────────────────────────────────────────────
コード修正エージェント (port 8009)
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from backend.telemetry import init_otel            # ★ 追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import PatchCodeRequest, PatchCodeResponse
from .services import patch_code

ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Patch Agent", version="1.0.0")

# OpenTelemetry
init_otel("code-patch-agent", fastapi_app=app)           # ★ 追加 ★


@app.post("/patch_code", response_model=PatchCodeResponse)
@agent_endpoint(PatchCodeRequest, output_key="patched_code")
async def _patch_code(req_model: PatchCodeRequest):  # type: ignore[valid-type]
    """
    受信したコードを LLM で修正し返却する。
    """
    return (await patch_code(req_model))["patched_code"]


if __name__ == "__main__":
    uvicorn.run(
        "agents.code_patch.app:app",
        host="127.0.0.1",
        port=8009,
        reload=False,
        log_level="debug",
    )
