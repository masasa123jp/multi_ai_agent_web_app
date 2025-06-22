"""
agents.it_consulting_agent.models
────────────────────────────────────────────────────────────────────────────
• IT コンサルティングエージェントの Pydantic スキーマ。
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class AdviceRequest(BaseModel):
    prompt: str = Field(..., description="相談内容／課題文")
    project_name: str = Field(..., description="プロジェクト名")
    model_name: str = Field("o4-mini-high", description="LLM モデル名")


class AdviceResponse(BaseModel):
    advice: str = Field(..., description="ベストプラクティス提案（Markdown）")
