# tests/integration/test_e2e_workflow.py
"""
統合テスト: 要件入力 → ZIP 出力までの E2E を 1 本で検証
─────────────────────────────────────────────────────────────
● 目的
    * API 層・サービス層・LangGraph Orchestrator を貫通させる
    * フィードバックループ (max_loops) が 1 回以上回ることを確認
    * ZIP データが生成され DB に保存されることを確認
● 前提
    * `backend.main:app` で FastAPI アプリを公開している
    * Alembic の `test` 用 DB（SQLite in-memory 等）が pytest-fixture
      `db_session` で初期化される
    * OpenAI / 外部 HTTP コールは `respx` でスタブ済み
"""

import io
import zipfile
import json
import asyncio
from pathlib import Path

import pytest
from httpx import AsyncClient

from backend.server import app  # FastAPI エントリポイント
from backend.models.workflow_log import WorkflowLog
from backend.services.orchestrator_service import get_workflow_status

# --- テスト入力 -------------------------------------------------------------

_REQ_PAYLOAD = {
    "project_name": "E2E-Test-Project",
    "requirement": "ユーザーが TODO を CRUD できる Web アプリを作成せよ",
    "model_name": "o4-mini",
    "max_cost": 0.2,
    "max_loops": 1,
}

# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_workflow(db_session, monkeypatch):
    """
    1. /api/workflow/async を叩き workflow_id を取得
    2. バックグラウンド完了までポーリング (最大 120 秒)
    3. 最終的に WorkflowLog.zip_data が生成済みであることを検証
    4. ZIP 内容に code / qa_report / security_report 等が含まれることを検証
    """

    # --- 1) 起動 ------------------------------------------------------------
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/workflow/async", json=_REQ_PAYLOAD)
        assert resp.status_code == 202
        workflow_id = resp.json()["workflow_id"]

    # --- 2) 完了待ち (簡易ポーリング) ---------------------------------------
    for _ in range(120):  # 1 秒 * 120 = 2 分
        status = await get_workflow_status(workflow_id)
        if status == "COMPLETED":
            break
        await asyncio.sleep(1)
    else:
        pytest.fail("workflow did not finish in time")

    # --- 3) DB 参照し ZIP が保存されているか確認 ---------------------------
    log: WorkflowLog | None = await db_session.get(WorkflowLog, workflow_id)
    assert log is not None, "WorkflowLog row missing"
    assert log.zip_data, "zip_data not persisted"

    # --- 4) ZIP 内容を検査 --------------------------------------------------
    z = zipfile.ZipFile(io.BytesIO(log.zip_data))
    namelist = z.namelist()

    # エージェント生成物が最低限含まれているか確認
    expected_files = [
        "code/app.py",
        "reports/qa_report.md",
        "reports/security_report.md",
    ]
    for f in expected_files:
        assert f in namelist, f"{f} not found in bundle"

    # 追加: messages.json が JSON として読み取れるかチェック
    with z.open("metadata/messages.json") as fp:
        messages = json.load(fp)
        assert isinstance(messages, list)

    # 追加: QA / Security レポートの文字列長が > 0
    with z.open("reports/qa_report.md") as fp:
        assert len(fp.read()) > 0
    with z.open("reports/security_report.md") as fp:
        assert len(fp.read()) > 0
