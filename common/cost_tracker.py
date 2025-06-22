# common/cost_tracker.py

"""
============================================================
API 呼び出しコストの集計・記録ユーティリティ
------------------------------------------------------------
このモジュールは、各種 AI ワークフローや HTTP API 呼び出しに伴って発生する
コストをデータベースに永続化する関数を提供します。

主な機能：
  • JWT トークンをデコードしてユーザ識別子 (email) を取得
  • 非同期 SQLAlchemy セッション (async_session_factory) を用いたトランザクション管理
  • コストレコードエントリ (CostLog モデル) の生成・保存
  • エラー時のロギング

使い方例：
    from common.cost_tracker import record as record_cost
    await record_cost(workflow_id, "openai.chat", 0.0023, "Bearer <JWT>")
============================================================
"""

import logging
from typing import Mapping, Any

# 非同期セッションファクトリを直接インポート
from backend.db.async_engine import async_session_factory
# JWT デコード関数を正しい名前でインポート
from backend.security.auth import decode_access_token  
from backend.models.cost_log import CostLog   # CostLog: workflow_id, user_email, api_name, cost, timestamp などを持つ ORM モデル

logger = logging.getLogger(__name__)


async def record(
    workflow_id: int,
    api_name: str,
    cost: float,
    token: str,
) -> None:
    """
    DB にコストレコードを追加する。

    Parameters
    ----------
    workflow_id : int
        対象ワークフローの識別子
    api_name : str
        呼び出した API 名称（例："openai.chat"）
    cost : float
        発生したコスト (USD)
    token : str
        `Authorization` ヘッダに含まれる "Bearer <JWT>" 文字列
    """
    # 1) "Bearer " プレフィックスを除去し、純粋な JWT 部分を取得
    raw_token = token.split(" ", 1)[1] if token.lower().startswith("bearer ") else token

    # 2) JWT をデコードしてペイロードを取得 (sub: email フィールドを参照)
    try:
        payload: Mapping[str, Any] = decode_access_token(raw_token)
        user_email = payload.get("sub")
        if not user_email:
            raise ValueError("Token payload missing 'sub' claim")
    except Exception as exc:
        logger.error("コスト記録失敗: トークンデコードエラー (%s)", exc)
        raise

    # 3) 非同期セッションを用いたトランザクション管理下でコストを永続化
    #    async_session_factory() は AsyncSession を生成するファクトリ
    async with async_session_factory() as session:
        try:
            # session.begin() コンテキストで commit/rollback を自動管理
            async with session.begin():
                cost_entry = CostLog(
                    workflow_id=workflow_id,
                    user_email=user_email,
                    api_name=api_name,
                    cost=cost,
                )
                session.add(cost_entry)
            # 正常終了時は自動的にコミットされる
            logger.info(
                "コスト記録成功: workflow=%s user=%s api=%s cost=%.6f",
                workflow_id, user_email, api_name, cost
            )
        except Exception:
            # 異常時は自動的にロールバックされる
            logger.exception(
                "コスト記録中に例外発生: workflow=%s user=%s api=%s",
                workflow_id, user_email, api_name
            )
            raise
