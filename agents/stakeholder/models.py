# agents/stakeholder/models.py

"""
Stakeholder エージェント用の Pydantic モデル定義

- FeedbackContext: フィードバック文のリストをルートモデルで表現
- CollectFeedbackRequest: フィードバック収集 API のリクエスト
- CollectFeedbackResponse: フィードバック収集 API のレスポンス
"""

from typing import List

from pydantic import BaseModel
from pydantic.root_model import RootModel  # 最新の推奨インポートパス


class FeedbackContext(RootModel[List[str]]):
    """
    フィードバック文のリストを表す RootModel。
    Pydantic v2 では __root__ の代わりに RootModel を使い、
    トップレベル JSON 配列としてシリアライズできます。
    """
    root: List[str]

    model_config = {
        "json_schema_extra": {
            "title": "FeedbackContext",
            "description": "List of feedback strings as the root."
        },
        # ルートモデルをトップレベル配列として扱う
        "ser_json_by_alias": True,
        "populate_by_name": True,
        "alias_generator": None,
    }


class CollectFeedbackRequest(BaseModel):
    """
    /collect_feedback エンドポイントへのリクエストボディ。
    - feedback_context: ユーザーからのフィードバック文リスト
    - mode            : 詳細 or サマリー などの動作モード
    - model_name      : 使用する LLM の識別子
    """
    feedback_context: FeedbackContext
    mode: str
    model_name: str

    model_config = {
        "json_schema_extra": {
            "title": "CollectFeedbackRequest",
            "description": "Request schema for collecting stakeholder feedback."
        }
    }


class UsageInfo(BaseModel):
    """
    レスポンスに含まれる usage フィールドの構造体例。
    total_tokens などを想定。
    """
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int

    model_config = {
        "json_schema_extra": {
            "title": "UsageInfo",
            "description": "Token usage details."
        }
    }


class CollectFeedbackResponse(BaseModel):
    """
    /collect_feedback エンドポイントから返却するレスポンスモデル。
    - summary    : フィードバックの要約テキスト
    - usage      : モデル利用量の情報
    - model_name : 実際に使用したモデル名
    """
    summary: str
    usage: UsageInfo
    model_name: str

    model_config = {
        "json_schema_extra": {
            "title": "CollectFeedbackResponse",
            "description": "Response schema for stakeholder feedback collection."
        }
    }
