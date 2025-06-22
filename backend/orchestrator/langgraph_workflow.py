# backend/orchestrator/langgraph_workflow.py
"""
LangGraph-based Orchestrator
─────────────────────────────────────────────────────────────
* 各 AI エージェント呼び出しを StateGraph で組み合わせる。
* QA / Security 結果を判定し、max_loops までコード修正ループを実施。
* 逐次コールバック・コスト集計・ZIP 生成などを一括管理。
"""
from __future__ import annotations
import inspect
import logging
import re
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, START, END

from backend.config.settings import get_settings
from backend.services.log_archive_service import save_log_archive
from backend.services.zip_service import build_zip_bundle
from common.agent_http import AgentHTTPError, post_json
from common.cost_tracker import record as record_cost

logger = logging.getLogger("orchestrator.langgraph_workflow")
settings = get_settings()

# ---------- WebSocket などへのステップ完了通知フック --------------------------
_ON_STEP: Optional[Callable[[str, str, Any], Awaitable[None]]] = None


def set_on_step(cb: Optional[Callable[[str, str, Any], Awaitable[None]]]) -> None:
    """外部 UI からステップ完了時のコールバックを挿入するユーティリティ"""
    global _ON_STEP
    _ON_STEP = cb


# ---------- ワークフロー状態定義 ---------------------------------------------
class WorkflowState(TypedDict, total=False):
    # 固定パラメータ
    messages:       List[Dict[str, Any]]
    requirement:    str
    project_name:   str
    model_name:     str
    max_cost:       float
    workflow_id:    int
    mode:           str
    max_loops:      int
    loop_count:     int
    total_cost:     float

    # 動的アウトプット
    feedback_summary: str
    schedule:         str
    advice:           str
    dba_script:       str
    ui:               str
    code:             str
    qa_report:        str
    security_report:  str
    patched_code:     str


# ---------- 各エージェントのベース URL ---------------------------------------
AGENT_URLS = {
    "stakeholder": settings.agent_stakeholder_url,
    "pm":          settings.agent_pm_url,
    "it":          settings.agent_itc_url,
    "dba":         settings.agent_dba_url,
    "ui":          settings.agent_ui_url,
    "code":        settings.agent_code_url,
    "qa":          settings.agent_qa_url,
    "security":    settings.agent_sec_url,
    "patch":       settings.agent_patch_url,
}

# --------------------------------------------------------------------------- #
# 共通: エージェント呼び出しラッパー
# --------------------------------------------------------------------------- #
async def call_agent(
    agent: str,
    path: str,
    payload: Dict[str, Any],
    state_key: str,
    s: WorkflowState,
) -> WorkflowState:
    """
    任意エージェントへ POST してレスポンス JSON を受け取り、
    `state_key` に該当する値を WorkflowState に書き戻す。
    * コストを USD 換算し累積
    * _ON_STEP が設定されていれば（非同期）コールバック
    """
    url = f"{AGENT_URLS[agent]}{path}"
    t0 = time.time()
    try:
        res = await post_json(url, payload,
                              timeout=settings.request_timeout,
                              max_retries=settings.max_retries)
    except AgentHTTPError as exc:              # ← 失敗は上位で捕捉
        logger.error("Agent %s error: %s", agent, exc, exc_info=True)
        raise

    elapsed = time.time() - t0
    tokens  = res.get("usage", {}).get("total_tokens", 0)
    cost    = record_cost(res.get("model_name", s["model_name"]),
                          tokens, s["project_name"], path.lstrip("/"))

    if _ON_STEP:
        info = {**res, "seconds": elapsed, "cost": cost,
                "total_cost": s["total_cost"] + cost}
        cb_res = _ON_STEP(agent, path.lstrip("/"), info)
        if inspect.isawaitable(cb_res):
            await cb_res

    # state 更新
    return {
        **s,
        state_key: res.get(state_key, ""),
        "messages": s["messages"] + [{
            "agent":   agent,
            "step":    path,
            "seconds": elapsed,
            "cost":    cost,
        }],
        "total_cost": s["total_cost"] + cost,
    }

# --------------------------------------------------------------------------- #
# LangGraph DAG 構築
# --------------------------------------------------------------------------- #
builder = StateGraph(WorkflowState)

def _init(s: WorkflowState) -> WorkflowState:
    """入力パラメータを初期 WorkflowState に展開"""
    init = s["messages"][0]
    return {
        **s,
        "requirement":  init["requirement"],
        "project_name": init["project_name"],
        "model_name":   init.get("model_name", "o4-mini"),
        "max_cost":     init.get("max_cost", 1.0),
        "workflow_id":  init["workflow_id"],
        "mode":         init.get("mode", "detail"),
        "max_loops":    init.get("max_loops", 3),
        "loop_count":   0,
        "total_cost":   0.0,
        # プレースホルダー
        "feedback_summary": "",
        "schedule": "", "advice": "", "dba_script": "",
        "ui": "", "code": "", "qa_report": "", "security_report": "",
        "patched_code": "",
    }

builder.add_node("init", _init)
builder.add_edge(START, "init")

# ---------- フロントロード部分（要件 → 1st コード生成まで） -------------------
front_steps = [
    ("stakeholder", "/collect_feedback", "feedback_summary"),
    ("pm",          "/schedule",         "schedule"),
    ("it",          "/advice",           "advice"),
    ("dba",         "/design_schema",    "dba_script"),
    ("ui",          "/generate_ui",      "ui"),
]

prev = "init"
for agent, path, key in front_steps:
    node = f"{agent}_step"
    builder.add_node(
        node,
        lambda s, a=agent, p=path, k=key: call_agent(
            a, p,
            {"requirement": s["requirement"], "project_name": s["project_name"],
             "model_name": s["model_name"]},
            k, s,
        ),
    )
    builder.add_edge(prev, node)
    prev = node

# ---------- ループ本体（code → qa → security） -------------------------------
def _code_step(s: WorkflowState) -> WorkflowState:
    """コード生成 or パッチ適用結果を code に反映"""
    # patched_code があればそれをベースに次 QA へ回す
    payload = {
        "project_name": s["project_name"],
        "prompt":       s["requirement"],
        "model_name":   s["model_name"],
        "db_schema":    s["dba_script"],
        "ui_design":    s["ui"],
    }
    # patched_code が空なら通常コード生成 / 非空なら再生成をスキップ
    state_key = "code"
    if s.get("patched_code"):
        # すでに修正コードが state にある → 何もしない
        return s
    return call_agent("code", "/generate_code", payload, state_key, s)

builder.add_node("code_step", _code_step)
builder.add_edge(prev, "code_step")

# QA
builder.add_node(
    "qa_step",
    lambda s: call_agent(
        "qa", "/run_qa",
        {"project_name": s["project_name"],
         "requirement":  s["requirement"],
         "code":         s["code"],
         "model_name":   s["model_name"]},
        "qa_report", s,
    ),
)
builder.add_edge("code_step", "qa_step")

# Security
builder.add_node(
    "sec_step",
    lambda s: call_agent(
        "security", "/scan_security",
        {"code": s["code"], "ui": s["ui"], "model_name": s["model_name"]},
        "security_report", s,
    ),
)
builder.add_edge("qa_step", "sec_step")

# ---------- ループ判定 --------------------------------------------------------
def _evaluate(s: WorkflowState) -> WorkflowState:
    """
    QA / Security レポートに「問題なし」が含まれない、
    かつ max_loops 未到達なら loop フラグを立てる。
    """
    need_fix = True
    ok_pattern = re.compile(r"(?:問題なし|No issues)", re.IGNORECASE)
    if ok_pattern.search(s["qa_report"]) and ok_pattern.search(s["security_report"]):
        need_fix = False

    loop_next = need_fix and (s["loop_count"] < s["max_loops"])
    return {**s, "loop_next": loop_next}

builder.add_node("evaluate", _evaluate)
builder.add_edge("sec_step", "evaluate")

# ---------- 条件付き遷移 ------------------------------------------------------
def _increment_loop(s: WorkflowState) -> WorkflowState:
    """パッチ用 instructions を生成し loop_count++"""
    instruction = f"以下のQA/Security指摘を修正してください。\nQA:\n{s['qa_report']}\nSecurity:\n{s['security_report']}"
    return {**s, "patched_code": "", "loop_count": s["loop_count"] + 1,
            "instructions": instruction}

builder.add_node(
    "patch_step",
    lambda s: call_agent(
        "patch", "/patch_code",
        {"source_code": s["code"],
         "instructions": s["instructions"],
         "model_name": s["model_name"]},
        "patched_code", s,
    ),
)

# 条件エッジ: loop_next が True → patch_step, False → END
builder.add_conditional_edges(
    "evaluate",
    lambda s: "loop" if s["loop_next"] else "done",
    {
        "loop": "increment_loop",
        "done": END,
    },
)
builder.add_node("increment_loop", _increment_loop)
builder.add_edge("increment_loop", "patch_step")
# パッチ適用後、再び QA → Security へ
builder.add_edge("patch_step", "code_step")

compiled_graph = builder.compile()

# --------------------------------------------------------------------------- #
# 外部呼び出し用エントリポイント
# --------------------------------------------------------------------------- #
async def execute_workflow(
    requirement: str,
    project_name: str,
    model_name: str,
    max_cost: float,
    workflow_id: int,
    max_loops: int,
    on_step: Optional[Callable[[str, str, Any], Awaitable[None]]] = None,
    mode: str = "detail",
) -> WorkflowState:
    """LangGraph を非同期実行し、完了後 ZIP アーカイブを生成する"""
    global _ON_STEP
    _ON_STEP = on_step

    try:
        init_state: WorkflowState = {
            "messages": [{
                "requirement":  requirement,
                "project_name": project_name,
                "model_name":   model_name,
                "max_cost":     max_cost,
                "workflow_id":  workflow_id,
                "mode":         mode,
                "max_loops":    max_loops,
            }]
        }
        result = await compiled_graph.ainvoke(init_state)

        # ZIP 圧縮 & DB 保存
        zip_bytes = build_zip_bundle(project_name, workflow_id, result)
        archive_id = save_log_archive(project_name, workflow_id, zip_bytes)

        result["messages"].append({"archive_id": archive_id})
        return {**result, "archive_id": archive_id}
    finally:
        _ON_STEP = None
