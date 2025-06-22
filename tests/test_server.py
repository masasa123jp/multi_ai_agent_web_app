# tests/test_server.py
"""
統合サーバ (backend/server.py) の /api/workflow/async エンドポイント動作確認
"""
from fastapi.testclient import TestClient
from backend.server import app

def test_start_workflow_async():
    client = TestClient(app)
    payload = {"requirement":"r","project_name":"p","model":"o4-mini","max_cost":0.1}
    res = client.post("/api/workflow/async", json=payload)
    assert res.status_code == 201
    assert "workflow_id" in res.json()
