"""
agents.code_patch.models
────────────────────────────────────────────────────────────────────────────
「生成済みコードをパッチ（修正）する」エージェント用の Pydantic モデル定義。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PatchCodeRequest(BaseModel):
    """
    入力値:
      • source_code   : 既存の Python ソースコード全文
      • instructions  : ステークホルダー／QA などからの改善指示
      • model_name    : LLM モデル名（デフォルト: o4-mini-high）
    """
    source_code: str = Field(..., description="既存 Python コード")
    instructions: str = Field(
        ...,
        description="機能追加・バグ修正などの自然言語指示（日本語可）"
    )
    model_name: str = Field("o4-mini-high", description="使用する LLM モデル名")


class PatchCodeResponse(BaseModel):
    """
    応答値:
      • patched_code : 適用済みの新しいソースコード全文
    """
    patched_code: str = Field(..., description="パッチ適用後のソースコード全文")