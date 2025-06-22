# backend/services/agent_client.py
"""

各 AI エージェントへの HTTP 呼び出しユーティリティ。

ポート／パスは run_all.bat と統合サーバ設定に合わせています。
呼び出し順:
    stakeholder → pm → it_consulting → dba → ui → code → patch → qa → security

エンドポイントマッピング:
    stakeholder:   http://127.0.0.1:8008  (POST /generate)
    pm:            http://127.0.0.1:8007  (POST /plan)
    it:            http://127.0.0.1:8005  (POST /advise)
    dba:           http://127.0.0.1:8006  (POST /design)
    ui:            http://127.0.0.1:8002  (POST /generate)
    code:          http://127.0.0.1:8001  (POST /generate)
    patch:         http://127.0.0.1:8009  (POST /patch)
    qa:            http://127.0.0.1:8003  (POST /test)
    security:      http://127.0.0.1:8004  (POST /scan)

- すべて POST /json
- タイムアウト 120 秒
- エラー時 {"error": "..."} を返す
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, AsyncGenerator

from common.agent_http import post_json, post_json_sync, AgentHTTPError
from backend.config.settings import get_settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
settings = get_settings()

# ───────────────────────────────────────
# 各エージェントのエンドポイントマッピング
# ───────────────────────────────────────
AGENT_ENDPOINTS: Dict[str, str] = {
    "stakeholder": str(settings.agent_stakeholder_url)+ "/collect_feedback",
    "pm":          str(settings.agent_pm_url)         + "/schedule",
    "it":          str(settings.agent_itc_url)        + "/advice",
    "dba":         str(settings.agent_dba_url)        + "/design_schema",
    "ui":          str(settings.agent_ui_url)         + "/generate_ui",
    "code":        str(settings.agent_code_url)       + "/generate_code",
    "patch":       str(settings.agent_patch_url)      + "/patch_code",
    "qa":          str(settings.agent_qa_url)         + "/run_qa",
    "security":    str(settings.agent_sec_url)        + "/scan_security",
}

# ───────────────────────────────────────
# 非同期呼び出しヘルパ
# ───────────────────────────────────────
async def _call_agent_async(agent_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    非同期で指定エージェントに JSON POST リクエストを送信し、
    レスポンス JSON を dict で返します。

    HTTPError は AgentHTTPError として巻き上げられます。
    """
    url = AGENT_ENDPOINTS[agent_key]
    base, path = url.rsplit("/", 1)
    try:
        return await post_json(
            base,
            "/" + path,
            payload,
            timeout=settings.request_timeout,
            max_retries=settings.max_retries,
        )
    except AgentHTTPError as exc:
        logger.error("Agent [%s] async call failed: %s", agent_key, exc, exc_info=True)
        return {"error": str(exc)}

# ───────────────────────────────────────
# 同期呼び出しヘルパ
# ───────────────────────────────────────
def _call_agent_sync(agent_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    同期で指定エージェントに JSON POST リクエストを送信し、
    レスポンス JSON を dict で返します。

    CLI や同期コンテキストで利用可能。内部で asyncio を利用します。
    """
    url = AGENT_ENDPOINTS[agent_key]
    base, path = url.rsplit("/", 1)
    try:
        return post_json_sync(
            base,
            "/" + path,
            payload,
            timeout=settings.request_timeout,
            max_retries=settings.max_retries,
        )
    except AgentHTTPError as exc:
        logger.error("Agent [%s] sync call failed: %s", agent_key, exc, exc_info=True)
        return {"error": str(exc)}


# ───────────────────────────────────────
# 非同期ラッパー関数群
# ───────────────────────────────────────
async def call_stakeholder(feedback_context: Dict[str, Any], model: str, mode: str = "detail") -> Dict[str, Any]:
    return await _call_agent_async("stakeholder", {
        "feedback_context": feedback_context,
        "model_name": model,
        "mode": mode,
    })


async def call_pm(project_name: str, timeline: Dict[str, Any], model: str) -> Dict[str, Any]:
    return await _call_agent_async("pm", {
        "project_name": project_name,
        "timeline": timeline,
        "model_name": model,
    })


async def call_it(prompt: str, project_name: str, model: str) -> Dict[str, Any]:
    return await _call_agent_async("it", {
        "prompt": prompt,
        "project_name": project_name,
        "model_name": model,
    })


async def call_dba(prompt: str, project_name: str, model: str) -> Dict[str, Any]:
    return await _call_agent_async("dba", {
        "prompt": prompt,
        "project_name": project_name,
        "model_name": model,
    })


async def call_ui(prompt: str, project_name: str, model: str) -> Dict[str, Any]:
    return await _call_agent_async("ui", {
        "prompt": prompt,
        "project_name": project_name,
        "model_name": model,
    })


async def call_code(prompt: str, project_name: str, model: str, **extra) -> Dict[str, Any]:
    payload = {"prompt": prompt, "project_name": project_name, "model_name": model, **extra}
    return await _call_agent_async("code", payload)


async def call_patch(source_code: str, instructions: str, model: str) -> Dict[str, Any]:
    return await _call_agent_async("patch", {
        "source_code": source_code,
        "instructions": instructions,
        "model_name": model,
    })


async def call_qa(project_name: str, requirement: str, code: str, ui: str, model: str) -> Dict[str, Any]:
    return await _call_agent_async("qa", {
        "project_name": project_name,
        "requirement": requirement,
        "code": code,
        "ui": ui,
        "model_name": model,
    })


async def call_security(code: str, ui: str, model: str) -> Dict[str, Any]:
    return await _call_agent_async("security", {
        "code": code,
        "ui": ui,
        "model_name": model,
    })


# ───────────────────────────────────────
# 同期ラッパー関数群（必要時利用）
# ───────────────────────────────────────
def call_stakeholder_sync(feedback_context: Dict[str, Any], model: str, mode: str = "detail") -> Dict[str, Any]:
    return _call_agent_sync("stakeholder", {"feedback_context": feedback_context, "model_name": model, "mode": mode})


def call_pm_sync(project_name: str, timeline: Dict[str, Any], model: str) -> Dict[str, Any]:
    return _call_agent_sync("pm", {"project_name": project_name, "timeline": timeline, "model_name": model})

# ... 他同期版も同様に定義可能 ...


# ───────────────────────────────────────
# WebSocket ストリーム用ヘルパ
# ───────────────────────────────────────
def _import_execute():
    # 循環参照防止のため関数内インポート
    from backend.orchestrator.langgraph_workflow import execute as execute_full_workflow
    return execute_full_workflow


async def get_agent_stream(db: Session, workflow_id: int) -> AsyncGenerator[str, None]:
    """
    WebSocket 用ストリーミングジェネレータ。
    - 各ステップ毎の JSON 文字列を yield
    - 最終的に archive_id を含む JSON を返却
    """
    yield '{"current_agent": "orchestrator"}'
    yield f"ワークフロー {workflow_id} を開始します..."

    execute_full = _import_execute()
    loop = asyncio.get_running_loop()
    try:
        # バックグラウンドでワークフローを実行
        result: Dict[str, Any] = await loop.run_in_executor(
            None,
            lambda: execute_full(
                requirement="",  # 必要に応じて引数を調整
                project_name="",
                model="",
                max_cost=0.0,
                workflow_id=workflow_id,
                max_loops=0,
            )
        )
    except Exception as e:
        yield f'{{"error": "{str(e)}"}}'
        return

    yield f"ワークフロー {workflow_id} が完了しました。"
    archive_id = result.get("archive_id") or result.get("workflow_id")
    yield f'{{"archive_id": {archive_id}}}'
