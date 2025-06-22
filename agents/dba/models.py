"""
agents.dba_agent.models
────────────────────────────────────────────────────────────────────────────
PostgreSQL 用の DB スキーマ設計エージェント ―― 入出力スキーマ定義
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class DesignSchemaRequest(BaseModel):
    """
    入力モデル:
      • prompt        : 要件（自然言語）
      • project_name  : プロジェクト名
      • model_name    : 使用する LLM（デフォルト: o4-mini-high）
    """
    prompt: str = Field(..., description="業務要件・データ要件の説明")
    project_name: str = Field(..., description="プロジェクト名")
    model_name: str = Field("o4-mini-high", description="利用する LLM モデル名")


class DesignSchemaResponse(BaseModel):
    """
    応答モデル:
      • dba_script : 生成された SQL (DDL + サンプル INSERT 等)
    """
    dba_script: str = Field(..., description="DDL および初期データの SQL スクリプト")
