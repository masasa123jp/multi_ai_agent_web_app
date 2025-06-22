# backend/core/logging.py

import structlog
import logging
import sys

# structlog 用のタイムスタンパーを利用
structlog.configure(
    processors=[
        # 1) ログレベルを追加
        structlog.stdlib.add_log_level,
        # 2) タイムスタンプを ISO フォーマットで付与
        structlog.processors.TimeStamper(fmt="iso"),
        # 3) JSON 出力
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(sys.stdout),
)

# 外部モジュールからは log.info(), log.error() を利用
log = structlog.get_logger()
