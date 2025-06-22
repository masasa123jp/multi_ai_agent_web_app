# agents/code_generation/app.py

"""
agents.code_generation.app
────────────────────────────────────────────────────────────────────────────
ソースコード生成エージェント (port 8001)

- singleton ロックで多重起動を防止
- 共通ログ設定を初期化
- OpenTelemetry によるトレース計装
- エンドポイント `/generate_code` で CodeGenRequest を受け付け
  → services.generate_code に委譲し、CodeGenResponse を返却
"""
from __future__ import annotations

import logging
import uvicorn
from fastapi import FastAPI

from backend.telemetry import init_otel                 # OpenTelemetry 初期化
from common.utils import ensure_singleton                 # 多重起動防止ユーティリティ
from common.logging_setup import setup_logging            # ロギング設定
from common.agent_http import agent_endpoint              # エンドポイント共通前処理

from .models import CodeGenRequest, CodeGenResponse       # 入出力スキーマ定義
from .services import generate_code                       # コード生成ロジック

# ---------- プロセス二重起動防止 ----------
ensure_singleton(__name__)

# ---------- ログ設定 ----------
setup_logging()
logger = logging.getLogger(__name__)

# ---------- FastAPI アプリ初期化 ----------
app = FastAPI(
    title="Code Generation Agent",
    version="1.0.0",
    description="LLM を用いて Python コードを自動生成するエージェントサービス"
)

# ---------- OpenTelemetry 計装 ----------
init_otel(
    service_name="code-generation-agent",
    fastapi_app=app
)

@app.post(
    "/generate_code", 
    response_model=CodeGenResponse,
    summary="コード生成",
    description="要件・DBスキーマ・UI設計を踏まえた Python コードを生成し返却"
)
@agent_endpoint(
    request_model=CodeGenRequest,
    output_key="code"
)
async def _generate_code(request_model: CodeGenRequest):  # type: ignore[valid-type]
    """
    生成AIを呼び出し、Pythonソースコードを返却するエンドポイント

    - リクエスト: CodeGenRequest (project_name, prompt, model_name, db_schema, ui_design)
    - レスポンス: CodeGenResponse (code)
    """
    # サービス層に処理を委譲し、コード文字列を取得
    result = await generate_code(request_model)
    return result["code"]

if __name__ == "__main__":
    # 単体起動用: python -m agents.code_generation.app で起動可能
    uvicorn.run(
        "agents.code_generation.app:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level="debug",
    )