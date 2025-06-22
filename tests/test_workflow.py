# tests/test_workflow.py
"""
backend/orchestrator/langgraph_workflow によるノード・エッジ構築とループ制御
(call_agent モック含む)
"""
import pytest
import asyncio
from backend.orchestrator.langgraph_workflow import builder, compiled_graph
from unittest.mock import patch

def test_builder_states_and_edges_exist():
    states = set(builder._states.keys())
    for expected in ["init","stakeholder","pm","itc","dba_design","ui_build","code_gen","qa","sec_scan","patch"]:
        assert expected in states
    edges = {(s,d) for s,d,_ in builder._edges}
    assert ("init","stakeholder") in edges
    assert ("patch","stakeholder") in edges or ("patch","init") in edges

@pytest.mark.asyncio
async def test_execute_loop_limit(monkeypatch):
    async def fake_call(agent_name, endpoint, payload, key, state):
        return {key:"", "messages": state["messages"] + [{"agent":agent_name}]}
    monkeypatch.setattr("backend.orchestrator.langgraph_workflow.call_agent", fake_call)
    init = {"messages":[{"requirement":"r","project_name":"p","model":"m","max_cost":0.1,"workflow_id":1,"mode":"detail"}]}
    result = await compiled_graph.ainvoke({**init, "loop_count":0, "max_loops":1})
    assert result.get("loop_count",0) <= 1
