# common/logging_setup.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    """
    標準出力へログを出力するハンドラを設定し、
    Uvicorn のアクセス・エラーロガーにも同一ハンドラを適用します。
    """
    # ルートロガー設定
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Uvicorn のロガーにも同じハンドラをセット
    for uv_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_log = logging.getLogger(uv_name)
        uv_log.handlers = logging.getLogger().handlers
        uv_log.setLevel(getattr(logging, level))
