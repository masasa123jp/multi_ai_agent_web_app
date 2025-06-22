"""
backend/services/zip_service.py
--------------------------------
生成物一式を “完全インメモリ” で ZIP 化するユーティリティ。

* TemporaryDirectory + shutil.make_archive を使う従来方式は
  不要な I/O が多く、Docker-volume でも race しやすかった。
* BytesIO & zipfile に置き換え、高速化と安全性を両立。
"""
# ▲▲ 修正開始
import json
import logging
import zipfile
from io import BytesIO
from typing import Dict

logger = logging.getLogger(__name__)


def build_zip_bundle(workflow_id: int, state: Dict[str, str]) -> bytes:
    """
    LangGraph の最終 state を受け取り、ワークフロー単位の ZIP を生成して返す。

    Parameters
    ----------
    workflow_id : int
        ワークフロー ID（ZIP 内のディレクトリ名に使用）
    state : Dict[str, str]
        コード／UI など生成物。キーは下記の通り固定：
            - code, patched_code, ui, dba_script, qa_report, security_report

    Returns
    -------
    bytes
        ZIP バイト列（StreamingResponse 等にそのまま渡せる）
    """
    # ― ZIP はメモリ上で生成する
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        base_dir = f"workflow_{workflow_id}"

        # 個別ファイルを書き込む
        mapping = [
            ("code", "py"),
            ("patched_code", "py"),
            ("ui", "html"),
            ("dba_script", "sql"),
            ("qa_report", "md"),
            ("security_report", "md"),
        ]
        for key, ext in mapping:
            if state.get(key):
                path_in_zip = f"{base_dir}/{key}.{ext}"
                zf.writestr(path_in_zip, state[key])
                logger.debug("Added %s to bundle", path_in_zip)

        # metadata.json も同梱
        metadata_path = f"{base_dir}/metadata.json"
        zf.writestr(metadata_path, json.dumps(state, ensure_ascii=False, indent=2))
        logger.debug("Added %s to bundle", metadata_path)

    buf.seek(0)
    logger.info("ZIP bundle for workflow %d generated (%d bytes)", workflow_id, buf.getbuffer().nbytes)
    return buf.getvalue()
# ▲▲ 修正終了
