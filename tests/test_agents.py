# tests/test_agents.py
"""
各 FastAPI エージェント（CodeGen, UIGen, QA, Patch, DBA, ITC, PM, Security, Stakeholder）の
エンドポイント検証
"""
import pytest
from fastapi.testclient import TestClient

# Code Generation Agent
import agents.code_generation.app as code_mod
code_client = TestClient(code_mod.app)

def test_generate_code_minimal():
    res = code_client.post("/generate_code", json={"project_name":"P","prompt":"x"})
    assert res.status_code == 200
    assert "code" in res.json()

# UI Generation Agent
import agents.ui_generation.app as ui_mod
ui_client = TestClient(ui_mod.app)

def test_generate_ui_minimal():
    res = ui_client.post("/generate_ui", json={"project_name":"P","prompt":"x"})
    assert res.status_code == 200
    assert "ui" in res.json()

# QA Agent
import agents.qa.app as qa_mod
qa_client = TestClient(qa_mod.app)

def test_run_qa_validation_error():
    res = qa_client.post("/run_qa", json={"project_name":"P","requirement":"R","code":"","ui":""})
    assert res.status_code == 400

# Patch Agent
import agents.code_patch.app as patch_mod
patch_client = TestClient(patch_mod.app)

def test_patch_code_minimal():
    res = patch_client.post("/patch_code", json={
        "source_code":"print('h')",
        "instructions":"add comment",
        "model_name":"o4-mini"
    })
    assert res.status_code == 200
    assert "patched_code" in res.json()

# DBA Agent
import agents.dba.app as dba_mod
dba_client = TestClient(dba_mod.app)

def test_design_schema_minimal():
    res = dba_client.post("/design_schema", json={
        "project_name":"P","prompt":"create table","model_name":"o3-mini"
    })
    assert res.status_code == 200
    assert "sql_script" in res.json()

# IT Consulting Agent
import agents.it_consulting.app as it_mod
it_client = TestClient(it_mod.app)

def test_advice_minimal():
    res = it_client.post("/advice", json={"project_name":"P","prompt":"advise"})
    assert res.status_code == 200
    assert "recommendation" in res.json()

# Project Manager Agent
import agents.project_manager.app as pm_mod
pm_client = TestClient(pm_mod.app)

def test_schedule_validation_error():
    res = pm_client.post("/schedule", json={"project_name":"P"})
    assert res.status_code in (400, 422)

# Security Agent
import agents.security.app as sec_mod
sec_client = TestClient(sec_mod.app)

def test_scan_security_validation_error():
    res = sec_client.post("/scan_security", json={"model_name":"o4-mini"})
    assert res.status_code in (400, 422)

# Stakeholder Agent
import agents.stakeholder.app as st_mod
st_client = TestClient(st_mod.app)

def test_collect_feedback_validation_error():
    res = st_client.post("/collect_feedback", json={"mode":"detail"})
    assert res.status_code == 400
