"""
コスト情報のリアルタイム配信ハブ

─ 概要 ────────────────────────────────────
ワークフロー実行中の累積コストを WebSocket クライアント群へ
ブロードキャストするためのユーティリティ。

■ 使い方
  from backend.services.cost_hub import connect, disconnect, broadcast_cost

  # WebSocket 接続時
  await connect(websocket)

  # 各ステップ on_step() 内で
  await broadcast_cost(workflow_id, total_cost)

  # 接続クローズ時
  await disconnect(websocket)
"""

import asyncio
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket

# workflow_id ごとに接続中 WebSocket を管理
_subscribers: Dict[int, Set[WebSocket]] = defaultdict(set)
_lock = asyncio.Lock()


async def connect(workflow_id: int, ws: WebSocket) -> None:
    """
    新規 WS 接続を登録する。
    """
    async with _lock:
        _subscribers[workflow_id].add(ws)


async def disconnect(workflow_id: int, ws: WebSocket) -> None:
    """
    WS 切断時に登録を解除する。
    """
    async with _lock:
        subs = _subscribers.get(workflow_id)
        if subs and ws in subs:
            subs.remove(ws)
            if not subs:
                # 最後の一つならキーごと削除
                _subscribers.pop(workflow_id, None)


async def broadcast_cost(workflow_id: int, total_cost: float) -> None:
    """
    指定ワークフローの全接続へ {"cost": ...} を送信。
    失敗時には個別にログを出力し続行。
    """
    subs = list(_subscribers.get(workflow_id, []))
    payload = {"type": "cost_update", "total_cost": total_cost}
    for ws in subs:
        try:
            await ws.send_json(payload)
        except Exception:
            # 個別送信エラーでも他は継続
            # ここで切断を検知し、disconnect() を呼ぶのも良い
            continue
