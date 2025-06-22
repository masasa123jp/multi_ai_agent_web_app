"""
common/ai_service.py
────────────────────────────────────────────────────────────
OpenAI / Azure OpenAI 汎用ラッパー

* usage.total_tokens を backend/core/cost_tracker.record() へ転送し、
  プロジェクト単位・ステップ単位のコストを DB に永続化。
* 呼び出し元は kwargs で `project_name` と `step_name` を必ず渡すこと。
* httpx.AsyncClient をシングルトンで保持して TLS ハンドシェイクを削減。
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
import openai
from openai import AzureOpenAI

from common.cost_tracker import record as record_cost  # 非同期セッション化対応済み

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# モデル設定
# ──────────────────────────────────────────────────────────────
HIGH_REASONING_ALIAS: Dict[str, str] = {
    "o3-mini-high": "o3-mini",
    "o4-mini-high": "o4-mini",
}

MODEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "gpt-4o":            {"token_limit": 32_768, "defaults": {"temperature": 0.7, "top_p": 1.0}},
    "gpt-4o-mini":       {"token_limit": 8_192,  "defaults": {"temperature": 0.7, "top_p": 1.0}},
    "o4-mini":           {"token_limit": 8_192,  "defaults": {"temperature": 1.0, "top_p": 0.9}},
    "gpt-4.1":           {"token_limit": 16_384, "defaults": {"temperature": 0.7, "top_p": 1.0}},
    "gpt-4.5":           {"token_limit": 32_768, "defaults": {"temperature": 0.7, "top_p": 1.0}},
    "o3":                {"token_limit": 16_384, "defaults": {"temperature": 0.7, "top_p": 1.0}},
    "o3-mini":           {"token_limit": 8_192,  "defaults": {"temperature": 1.0, "top_p": 0.9}},
    "o1":                {"token_limit": 4_096,  "defaults": {"temperature": 1.0, "top_p": 0.9}},
    "o1-mini":           {"token_limit": 4_096,  "defaults": {"temperature": 1.0, "top_p": 0.9}},
}

# “-high” エイリアスにも同じ設定をコピー
for alias, base in HIGH_REASONING_ALIAS.items():
    if base in MODEL_CONFIG and alias not in MODEL_CONFIG:
        MODEL_CONFIG[alias] = MODEL_CONFIG[base].copy()

# top_k を使うモデル
MODELS_USE_TOP_K = {"o1", "o1-mini"}

# ──────────────────────────────────────────────────────────────
# シングルトン httpx.AsyncClient
# ──────────────────────────────────────────────────────────────
_httpx_client: httpx.AsyncClient | None = None


def _get_httpx_client() -> httpx.AsyncClient:
    """
    HTTP/2 + Connection pooling 付きのクライアントを 1 つだけ生成。
    """
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.AsyncClient(
            http2=True,
            timeout=30,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            headers={"User-Agent": "agent-webapp/1.0"},
        )
    return _httpx_client


# ──────────────────────────────────────────────────────────────
# 環境変数ヘルパ
# ──────────────────────────────────────────────────────────────
def _get_env() -> Dict[str, str]:
    return {
        "API_TYPE":                 os.getenv("API_TYPE", "openai"),
        "OPENAI_API_KEY":           os.getenv("OPENAI_API_KEY", ""),
        "AZURE_OPENAI_API_KEY":     os.getenv("AZURE_OPENAI_API_KEY", ""),
        "AZURE_OPENAI_API_BASE":    os.getenv("AZURE_OPENAI_API_BASE", ""),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION", ""),
    }


# ──────────────────────────────────────────────────────────────
# AIService
# ──────────────────────────────────────────────────────────────
class AIService:
    """
    OpenAI / AzureOpenAI の薄いラッパ。

    * 呼び出し後に total_tokens を cost_tracker へ送信
    """

    def __init__(self) -> None:
        env = _get_env()
        self.api_type = env["API_TYPE"]
        self.client   = self._init_client(env)

    # ---------- クライアント初期化 ----------
    def _init_client(self, env: Dict[str, str]) -> Any:
        if self.api_type == "openai":
            key = env["OPENAI_API_KEY"]
            if not key:
                raise RuntimeError("OPENAI_API_KEY が設定されていません。")
            openai.api_type = "openai"
            openai.api_key  = key
            # OpenAI 公式ラッパは非同期で internal に httpx を使う
            return openai.chat.completions  # type: ignore[attr-defined]

        if self.api_type == "azure":
            required = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_BASE", "AZURE_OPENAI_API_VERSION"]
            if not all(env[k] for k in required):
                raise RuntimeError("Azure OpenAI 環境変数が不足しています。")
            openai.api_type    = "azure"
            openai.api_key     = env["AZURE_OPENAI_API_KEY"]
            openai.api_base    = env["AZURE_OPENAI_API_BASE"]
            openai.api_version = env["AZURE_OPENAI_API_VERSION"]
            return AzureOpenAI(
                api_key=env["AZURE_OPENAI_API_KEY"],
                api_version=env["AZURE_OPENAI_API_VERSION"],
                http_client=_get_httpx_client(),
            ).chat.completions

        raise RuntimeError(f"Unsupported API_TYPE: {self.api_type}")

    # ---------- トークン上限 ----------
    def _clamp_tokens(self, model: str, requested: int) -> int:
        limit = MODEL_CONFIG.get(model, {}).get("token_limit", 2048)
        if requested > limit:
            logger.warning(
                "requested max_tokens=%d exceeds limit=%d for model=%s; clamping",
                requested, limit, model
            )
        return min(requested, limit)

    # ---------- メインメソッド ----------
    async def call_generative_ai(
        self,
        *,
        model: str,
        messages: Optional[List[Dict[str, str]]] = None,
        prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        timeout: float = 60.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        project_name, step_name を kwargs で受け取り、cost_tracker へ転送。
        """
        project_name: str = kwargs.pop("project_name", "unknown")
        step_name:    str = kwargs.pop("step_name",    "unknown")

        # --- “-high” エイリアス解決 ---
        reasoning_effort = None
        if model in HIGH_REASONING_ALIAS:
            reasoning_effort = "high"
            model = HIGH_REASONING_ALIAS[model]

        # --- メッセージ組み立て ---
        if messages is None:
            if prompt is None:
                raise ValueError("messages または prompt を指定してください。")
            messages = [{"role": "user", "content": prompt}]

        # --- モデル設定 & デフォルト ---
        cfg       = MODEL_CONFIG.get(model, {})
        defaults  = cfg.get("defaults", {})
        temperature = temperature if temperature is not None else defaults.get("temperature", 0.7)
        top_p       = top_p       if top_p       is not None else defaults.get("top_p", 1.0)

        # --- max_tokens 決定 ---
        if max_tokens is None:
            max_tokens = cfg.get("token_limit", 2048)
        max_tokens = self._clamp_tokens(model, max_tokens)

        # --- リクエストパラメータ ---
        params: Dict[str, Any] = {
            "model":       model,
            "messages":    messages,
            "temperature": temperature,
            **kwargs,
        }
        # top_k / top_p
        if model in MODELS_USE_TOP_K:
            params["top_k"] = top_k if top_k is not None else int(top_p * max_tokens)
        elif not model.startswith("o"):
            params["top_p"] = top_p
        # max_tokens
        params["max_completion_tokens" if model.startswith("o") else "max_tokens"] = max_tokens
        # reasoning_effort
        if reasoning_effort:
            params["reasoning_effort"] = reasoning_effort

        # --- API 呼び出し ---
        try:
            if hasattr(self.client, "acreate"):  # async supported
                resp = await asyncio.wait_for(self.client.acreate(**params), timeout=timeout)
            else:  # sync -> offload to thread
                resp = await asyncio.wait_for(
                    asyncio.to_thread(self.client.create, **params),
                    timeout=timeout
                )

            # --- レスポンス解析 ---
            choice   = resp.choices[0]
            content  = (
                choice.message.content.strip()
                if hasattr(choice, "message")
                else getattr(choice, "text", "").strip()
            )
            usage    = getattr(resp, "usage", None)
            tokens   = int(getattr(usage, "total_tokens", 0) or 0)

            # ---------- コスト記録 ----------
            total_cost = 0.0
            if tokens:
                total_cost = record_cost(
                    model_name=model,
                    tokens=tokens,
                    project=project_name,
                    step=step_name,
                )
                logger.debug(
                    "Cost recorded: project=%s step=%s tokens=%d cost=%s",
                    project_name, step_name, tokens, total_cost
                )

            return {"content": content, "usage": usage, "total_cost": total_cost}

        except Exception as e:
            logger.exception("AI API error: %s", e)
            raise


# ──────────────────────────────────────────────────────────────
# シンプルラッパー
# ──────────────────────────────────────────────────────────────
ai_service = AIService()


async def call_generative_ai(**kwargs) -> str:
    """
    service.call() の syntactic sugar。文字列のみ返す。
    """
    res = await ai_service.call_generative_ai(**kwargs)
    return res["content"]
