# common/utils.py
"""
共通ユーティリティモジュール

- ロギングセットアップ
- ensure_singleton : PID ファイルによる多重起動防止
- handle_errors / run_with_timeout : 例外 & タイムアウト制御

2025-05-01  Race condition fix / Windows & POSIX 両対応
"""

from __future__ import annotations

import atexit
import asyncio
import logging
import os
import sys
import tempfile
from functools import wraps
from typing import Optional

import psutil  # プロセス生存確認用 (pip install psutil)

try:
    # POSIX ロック (Windows では ImportError)
    import fcntl  # type: ignore
except ImportError:  # pragma: win32-no-cover
    fcntl = None  # Windows では flock 不可

import structlog
from fastapi import HTTPException

# ────────────────────────────────────────────
# ロギング初期化
# ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()


# ────────────────────────────────────────────
# PID ファイルベース Singleton ロック
# ────────────────────────────────────────────
def ensure_singleton(app_name: str, *, pid_dir: Optional[str] = None) -> None:
    """
    同一ホストで ``app_name`` が二重起動しないように PID ファイルでロックする。

    Parameters
    ----------
    app_name : str
        エージェント名や ``__name__`` など、一意になる名前。
    pid_dir : str | None
        PID ファイル格納ディレクトリ。未指定時は OS のテンポラリ領域
        (`tempfile.gettempdir()`).
    """
    pid_dir = pid_dir or tempfile.gettempdir()  # 標準の tmp ディレクトリ&#8203;:contentReference[oaicite:5]{index=5}
    os.makedirs(pid_dir, exist_ok=True)

    pid_file = os.path.join(pid_dir, f"{app_name}.pid")
    current_pid = os.getpid()

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY  # 排他生成&#8203;:contentReference[oaicite:6]{index=6}
    try:
        # ── 排他生成に成功 → 新規起動 ────────────────────
        fd = os.open(pid_file, flags, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            fp.write(str(current_pid))
        logger.info("PID file created: %s (pid=%d)", pid_file, current_pid)

        # 追加: POSIX ファイルロック
        if fcntl:  # pragma: posix-only
            fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 非ブロッキング排他&#8203;:contentReference[oaicite:7]{index=7}

    except FileExistsError:
        # ── 既存 PID ファイルがある場合 ─────────────────
        try:
            with open(pid_file, "r", encoding="utf-8") as fp:
                old_pid = int(fp.read().strip() or "0")
        except (ValueError, OSError):
            old_pid = 0

        if old_pid and psutil.pid_exists(old_pid):  # まだ生存&#8203;:contentReference[oaicite:8]{index=8}
            raise RuntimeError(
                f"[ensure_singleton] '{app_name}' は既に起動中です (PID={old_pid})"
            )

        # スタレ PID → 上書き再生成
        logger.warning(
            "Stale PID file detected (%s, pid=%s). Replacing with current pid=%d",
            pid_file,
            old_pid or "unknown",
            current_pid,
        )
        with open(pid_file, "w", encoding="utf-8") as fp:
            fp.write(str(current_pid))

    # ── 正常終了時のクリーンアップ ───────────────────────
    def _cleanup() -> None:
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
                logger.debug("PID file removed: %s", pid_file)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to remove PID file %s: %s", pid_file, exc)

    atexit.register(_cleanup)
    logger.info("Singleton lock acquired for '%s' (pid=%d)", app_name, current_pid)


# ────────────────────────────────────────────
# 共通デコレータ & ヘルパ
# ────────────────────────────────────────────
def handle_errors(func):
    """
    任意の sync / async 関数をラップし、例外を FastAPI `HTTPException` に変換する。
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except HTTPException:
            raise
        except Exception:
            import traceback

            detail = traceback.format_exc()
            raise HTTPException(status_code=500, detail=detail)

    return wrapper


async def run_with_timeout(coro_or_future, timeout_sec: int = 120):
    """
    指定コルーチン / Future をタイムアウト付きで ``await`` するユーティリティ。

    - ネストされたコルーチンは再帰的に解決
    - タイムアウト時は ``504 Gateway Timeout``
    """
    try:
        logger.debug("AI call start", timeout_sec=timeout_sec)
        result = await asyncio.wait_for(coro_or_future, timeout=timeout_sec)

        # 返却値が coroutine の場合、追加で await
        if asyncio.iscoroutine(result):
            logger.debug("Unwrapping nested coroutine result")
            result = await result

        logger.debug("AI call succeeded", timeout_sec=timeout_sec)
        return result

    except asyncio.TimeoutError:
        logger.error("AI call timeout", timeout_sec=timeout_sec)
        raise HTTPException(status_code=504, detail="timeout")

    except Exception:  # pragma: no cover
        logger.exception("AI call error")
        raise HTTPException(status_code=500, detail="internal error")
