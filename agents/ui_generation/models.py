"""
agents.ui_generation.models
────────────────────────────────────────────────────────────────────────────
• UI 生成エージェントの Pydantic スキーマ定義。
• LangGraph ワークフローや他エージェントから呼び出す際の
  リクエスト / レスポンス・フォーマットを統一する。
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class UIGenRequest(BaseModel):
    project_name: str = Field(..., description="プロジェクト名")
    prompt: str = Field(..., description="フロントエンド要件／UX 指示")
    model_name: str = Field("o4-mini-high", description="利用する LLM モデル名")
    theme: str | None = Field(None, description="ダーク／ライトなどのテーマ指定")
    framework: str | None = Field(
        "vanilla", description="'bootstrap'|'tailwind'|'vanilla' など"
    )


class UIGenResponse(BaseModel):
    ui: str = Field(..., description="HTML + CSS（必要に応じて JS）")
