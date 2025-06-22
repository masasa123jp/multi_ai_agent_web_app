"""
agents.project_manager_agent.models
────────────────────────────────────────────────────────────────────────────
アジャイル型スケジュールを生成する PM エージェント ―― データモデル
"""
from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class ScheduleRequest(BaseModel):
    """
    入力モデル:
      • project_name : プロジェクト名
      • timeline     : 要件やハイレベルマイルストーンの説明
      • model_name   : LLM モデル名
    """
    project_name: str
    timeline: dict = Field(..., description="要件や現状フィードバック概要")
    model_name: str = Field("o4-mini-high", description="LLM モデル名")


class Milestone(BaseModel):
    """
    内部表現用: 1 マイルストーン
      • name    : 名称
      • start   : YYYY-MM-DD
      • end     : YYYY-MM-DD
      • owners  : 担当者 (複数可)
    """
    name: str
    start: str
    end: str
    owners: List[str]


class ScheduleResponse(BaseModel):
    """
    応答モデル: CSV テキスト or オブジェクトでも可。
    LangGraph では単純テキストで扱うためここは str としておく。
    """
    schedule: str = Field(..., description="CSV 形式のスプリントスケジュール")
