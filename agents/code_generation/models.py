# agents/code_generation/models.py

"""
agents.code_generation.models
────────────────────────────────────────────────────────────────────────────
• Pydantic モデルでリクエスト／レスポンススキーマを定義。
• agent_http.agent_endpoint デコレータで入力検証を自動化。
"""

from __future__ import annotations
from pydantic import BaseModel, Field

class CodeGenRequest(BaseModel):
    """
    POST /generate_code のリクエストスキーマ
    - project_name: プロジェクト名
    - prompt: 要件説明文(自然言語)
    - model_name: 生成AIモデル名 (デフォルト: o4-mini-high)
    - db_schema: 事前に設計されたDDL (省略可)
    - ui_design: UI HTML/CSS コード (省略可)
    """
    project_name: str           = Field(..., description="プロジェクト名")
    prompt:       str           = Field(..., description="自然言語での要件説明")
    model_name:   str           = Field("o4-mini-high", description="使用する生成AIモデル")
    db_schema:    str | None    = Field(None, description="既存DBスキーマ(DDL)")
    ui_design:    str | None    = Field(None, description="既存UI設計(HTML/CSS)")

class CodeGenResponse(BaseModel):
    """
    POST /generate_code のレスポンススキーマ
    - code: 生成されたPythonソースコード本文
    """
    code: str = Field(..., description="生成されたソースコード")
