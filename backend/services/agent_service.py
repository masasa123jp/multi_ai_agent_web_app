# backend/src/services/agent_service.py

import httpx
import logging
from typing import Dict, Any

from common.ai_service import call_generative_ai

logger = logging.getLogger("backend.services.agent_service")
BASE_URL = "http://localhost"

def call_code_generation_agent(prompt: str, project_name: str, model_name: str) -> str:
    url = f"{BASE_URL}:8001/generate_code"
    payload = {"prompt": prompt, "project_name": project_name, "model_name": model_name}
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json().get("code", "")

def call_ui_generation_agent(prompt: str, project_name: str, model_name: str) -> str:
    url = f"{BASE_URL}:8002/generate_ui"
    payload = {"prompt": prompt, "project_name": project_name, "model_name": model_name}
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json().get("ui", "")

def call_qa_agent(code: str, ui: str, model_name: str) -> str:
    url = f"{BASE_URL}:8003/run_qa"
    payload = {"code": code, "ui": ui, "model_name": model_name}
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json().get("report", "")

def call_security_agent(code: str, ui: str, model_name: str) -> str:
    url = f"{BASE_URL}:8004/scan_security"
    payload = {"code": code, "ui": ui, "model_name": model_name}
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json().get("report", "")

def call_it_consulting_agent(prompt: str, project_name: str, model_name: str) -> str:
    url = f"{BASE_URL}:8005/advice"
    payload = {"prompt": prompt, "project_name": project_name, "model_name": model_name}
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json().get("recommendation", "")

def call_dba_agent(prompt: str, project_name: str, model_name: str) -> str:
    url = f"{BASE_URL}:8006/design_schema"
    payload = {"prompt": prompt, "project_name": project_name, "model_name": model_name}
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json().get("sql_script", "")

def call_pm_agent(project_name: str, timeline: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    url = f"{BASE_URL}:8007/schedule"
    payload = {"project_name": project_name, "timeline": timeline, "model_name": model_name}
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()

def call_stakeholder_agent(feedback_context: Dict[str, Any], model_name: str, mode: str = "detail") -> str:
    url = f"{BASE_URL}:8008/collect_feedback"
    payload = {
        "feedback_context": feedback_context,
        "mode": mode,
        "model_name": model_name
    }
    logger.info("Calling Stakeholder Agent at %s with payload %s", url, payload)
    resp = httpx.post(url, json=payload)
    resp.raise_for_status()
    return resp.json().get("feedback_summary", "")
