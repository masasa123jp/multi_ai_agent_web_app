# agents/security/models.py

"""
agents.security_agent.models
────────────────────────────────────────────────────────────────────────────
Pydantic モデル定義：
- リクエスト：code, ui, model_name
- レスポンス：security_report （将来拡張で scan_summary を追加可）
"""
from __future__ import annotations

from pydantic import BaseModel, Field

class SecurityScanRequest(BaseModel):
    code:       str = Field(..., description="Python ソースコード全文")
    ui:         str = Field("",  description="生成済み UI (HTML/CSS/JS)",  max_length=100_000)
    model_name: str = Field("o4-mini-high", description="利用 LLM モデル名")

class SecurityScanResponse(BaseModel):
    security_report: str = Field(..., description="静的解析レポート (Markdown)")
    # 将来、構造化結果を追加する場合の例：
    # scan_summary: Optional[Dict[str, Any]] = Field(None, description="構造化スキャン結果")
