# agents/qa/models.py

"""
agents.qa_agent.models
────────────────────────────────────────────────────────────────────────────
自動テスト／品質保証エージェント ―― Pydantic モデル定義
"""
from __future__ import annotations

from pydantic import BaseModel, Field

class QARunRequest(BaseModel):
    """
    エージェント呼び出し時の入力モデル。
      • project_name : プロジェクト名
      • requirement  : 要件概要
      • code         : Python ソースコード全文
      • ui           : HTML/CSS 等（省略可）
      • model_name   : LLM モデル名
    """
    project_name: str = Field(..., description="プロジェクト名")
    requirement:  str = Field(..., description="機能要件の説明")
    code:         str = Field(..., description="生成済み Python ソースコード")
    ui:           str = Field("",  description="生成済み UI (HTML/CSS 等)")
    model_name:   str = Field("o4-mini-high", description="利用 LLM モデル名")


class QARunResponse(BaseModel):
    """
    エージェント応答モデル。
      • qa_report   : Markdown 形式の QA レポート（一番最後にテスト実行結果付き）
    """
    qa_report: str = Field(..., description="テスト実行結果を含む Markdown レポート")
