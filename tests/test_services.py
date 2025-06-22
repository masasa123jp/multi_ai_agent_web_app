# tests/test_services.py
"""
backend/services/db_service、
backend/services/api_usage_service、
backend/services/agent_client の機能テスト
"""
import pytest
from unittest.mock import patch
from backend.services.db_service import query, query_one, execute
from backend.services.api_usage_service import log_api_usage
from backend.services.agent_client import _post, get_agent_stream

# db_service
@patch("backend.services.db_service.psycopg2.connect")
def test_query_and_query_one(mock_conn):
    mock_c = mock_conn.return_value.cursor.return_value
    mock_c.description = True
    mock_c.fetchall.return_value = [{"a":1}]
    assert query("select") == [{"a":1}]
    mock_c.fetchone.return_value = {"b":2}
    assert query_one("select") == {"b":2}

@patch("backend.services.db_service.psycopg2.connect")
def test_execute_commits(mock_conn):
    mock_conn.return_value.cursor.return_value.execute.return_value = None
    execute("update")
    mock_conn.return_value.commit.assert_called()

# api_usage_service
@patch("psycopg2.connect")
def test_log_api_usage(mock_connect):
    mock_conn = mock_connect.return_value
    mock_cur = mock_conn.cursor.return_value
    log_api_usage("m",10,0.01,"d")
    mock_conn.commit.assert_called()
    mock_cur.execute.assert_called()

# agent_client
def test_post_unknown_agent():
    data = _post("unknown","/x",{})
    assert "error" in data

@patch("backend.services.agent_client.httpx.post")
def test_post_http_error(mock_post):
    mock_post.side_effect = Exception("fail")
    data = _post("stakeholder","/x",{})
    assert "error" in data

@patch("backend.services.agent_client.httpx.stream")
def test_get_agent_stream_exception(mock_stream):
    mock_stream.side_effect = Exception("fail")
    chunks = list(get_agent_stream("stakeholder","/x",{}))
    assert any("error" in c for c in chunks)
