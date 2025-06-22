# tests/test_common.py
"""
Agents.common.agent_base、common.ai_service、common.translation_service、
common/logging_setup、backend/core/cost_tracker に関するユーティリティ＆単体テスト
"""
import pytest
import asyncio
import os
import logging
from unittest.mock import patch

# --- agent_base ---
from common.utils import handle_errors, run_with_timeout
from fastapi import HTTPException

async def dummy(x):
    return x + 1

@handle_errors
async def raises_value_error():
    raise ValueError("boom")

@pytest.mark.asyncio
async def test_run_with_timeout_success():
    result = await run_with_timeout(dummy(2), timeout_sec=1)
    assert result == 3

@pytest.mark.asyncio
async def test_run_with_timeout_timeout():
    with pytest.raises(HTTPException) as exc:
        await run_with_timeout(asyncio.sleep(0.2), timeout_sec=0.1)
    assert exc.value.status_code == 504

@pytest.mark.asyncio
async def test_handle_errors_converts_exception():
    with pytest.raises(HTTPException) as exc:
        await raises_value_error()
    assert "ValueError" in exc.value.detail

# --- ai_service ---
from common.ai_service import AIService, _get_env, MODEL_CONFIG

def test_get_env_keys():
    env = _get_env()
    assert "API_TYPE" in env and "OPENAI_API_KEY" in env

@pytest.mark.parametrize("model_name,requested", [
    (m, cfg["token_limit"] * 2) for m, cfg in MODEL_CONFIG.items()
])
def test_clamp_tokens(model_name, requested):
    svc = AIService()
    clamped = svc._clamp_tokens(model_name, requested)
    assert clamped <= MODEL_CONFIG[model_name]["token_limit"]

# --- translation_service ---
from common.translation_service import translate_text

@patch("common.translation_service.call_generative_ai")
def test_translate_text_nonempty(mock_ai):
    f = asyncio.Future()
    f.set_result("Hello")
    mock_ai.return_value = f
    result = translate_text("こんにちは", target_lang="en")
    assert result == "Hello"
    mock_ai.assert_called_once()

def test_translate_text_empty():
    assert translate_text("", target_lang="en") == ""

# --- logging_setup ---
from common.logging_setup import setup_logging

def test_uvicorn_loggers_share_handlers():
    setup_logging(level="DEBUG")
    root_handlers = logging.getLogger().handlers
    uv_error = logging.getLogger("uvicorn.error")
    uv_access = logging.getLogger("uvicorn.access")
    assert uv_error.handlers == root_handlers
    assert uv_access.handlers == root_handlers
    assert uv_error.level == logging.DEBUG
    assert uv_access.level == logging.DEBUG

# --- cost_tracker ---
from common.cost_tracker import get_price, record
from decimal import Decimal
from common.cost_tracker import log

def test_get_price_known_unknown():
    assert get_price("o4-mini") == Decimal("0.0000030")
    assert get_price("nonexistent") == Decimal("0.0")

@patch("backend.core.cost_tracker.log")
def test_record_logs_and_returns(mock_log):
    cost = record("o3-mini", tokens=100, project="P", step="S")
    assert isinstance(cost, Decimal)
    mock_log.info.assert_called()
