# common/exceptions.py
# ─────────────────────────────────────────────────────────────
# 共通の例外クラスを集約するモジュール
# いずれか 1 つにまとめておくことで、上位層から一括ハンドリングできる。
# ─────────────────────────────────────────────────────────────
from __future__ import annotations

import httpx


class AgentHTTPError(RuntimeError):
    """
    エージェント呼び出し時の HTTP 層エラーを表す例外。

    * message … str() で人間可読メッセージ
    * response … 失敗した httpx.Response オブジェクト
    """

    def __init__(self, message: str, response: httpx.Response) -> None:
        super().__init__(message)
        self.response: httpx.Response = response
        # レスポンス本文をそのまま持つと巨大になる場合があるので length だけ保持
        self.body_size: int = len(response.content or b"")

    @property
    def status_code(self) -> int:
        return self.response.status_code

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{self.__class__.__name__}("
            f"status={self.status_code}, "
            f"url={self.response.url!s}, "
            f"body_size={self.body_size}B)"
        )
