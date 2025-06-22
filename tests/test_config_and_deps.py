# tests/test_config_and_deps.py
"""
backend/config/settings の環境変数パース、
backend/dependencies.get_db のセッション生成・クローズ検証
"""
import os
import pytest
from pydantic import ValidationError
from backend.config.settings import Settings
from backend.db.dependencies_async import get_db

def test_allow_origins_comma_and_json():
    os.environ["ALLOW_ORIGINS"] = "a.com,b.com"
    # 他必須 env を空設定
    keys = [
        "AGENT_CODE_URL","AGENT_UI_URL","AGENT_QA_URL","AGENT_SEC_URL",
        "AGENT_ITC_URL","AGENT_DBA_URL","AGENT_PM_URL","AGENT_STAKEHOLDER_URL","AGENT_PATCH_URL",
        "OPENAI_API_KEY","API_TYPE"
    ]
    for k in keys: os.environ[k] = ""
    with pytest.raises(ValidationError):
        Settings()

def test_get_db_session_close():
    gen = get_db()
    db = next(gen)
    assert hasattr(db, "close")
    db.close()
    gen.close()
