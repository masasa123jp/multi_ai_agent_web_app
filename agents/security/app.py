# agents/security/app.py

"""
agents.security_agent.app
────────────────────────────────────────────────────────────────────────────
セキュリティ診断エージェント (port 8004)
- リクエスト検証（code 必須、ui は省略可）
- scan_security サービス呼び出し
- 例外発生時は 400/500 を適切に返却
"""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI, HTTPException

from backend.telemetry import init_otel       # ★ OpenTelemetry 計測追加 ★

from common.utils import ensure_singleton
from common.logging_setup import setup_logging
from common.agent_http import agent_endpoint
from .models import SecurityScanRequest, SecurityScanResponse
from .services import scan_security

# プロセス重複防止 & ロギング初期化
ensure_singleton(__name__)
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Security Agent", version="1.0.0")
init_otel("security-agent", fastapi_app=app)  # OTEL 計測開始

@app.post("/scan_security", response_model=SecurityScanResponse)
@agent_endpoint(SecurityScanRequest, output_key="security_report")
async def _scan_security(req_model: SecurityScanRequest):  # type: ignore[valid-type]
    """
    生成コードの脆弱性診断を実行するエンドポイント。
    - code が空文字列の場合は 400 を返却
    """
    if not req_model.code.strip():
        logger.error("Security scan requested without source code")
        raise HTTPException(status_code=400, detail="code is required for security scan")
    # サービス層で LLM＋スキャナ実行
    report = await scan_security(req_model)
    return report["security_report"]

if __name__ == "__main__":
    uvicorn.run(
        "agents.security_agent.app:app",
        host="127.0.0.1",
        port=8004,
        reload=False,
        log_level="debug",
    )
