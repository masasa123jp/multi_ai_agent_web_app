"""
backend/config/settings.py
────────────────────────────────────────────────────────────────────────────
`.env` からアプリケーション全体の設定を読み込み・バリデーションするモジュール。
- **Pydantic BaseSettings** で環境変数を型安全に取り込む  
- **必要最小限のフィールド** のみ定義し、派生情報はプロパティで計算  
- **ALLOW_ORIGINS** は JSON / カンマ区切り / ワイルドカード の 3 形式を許容  
- **Agent URL 群** は個別フィールド → `agent_urls` / `agent_ports` に整理  
- **OpenTelemetry** のエンドポイントを追加  
"""

from __future__ import annotations

import json
from typing import List, Dict

from pydantic import Field, AnyUrl
from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    # ────────────────────────── 基本 HTTP サーバ設定 ───────────────────────────
    host: str = Field("127.0.0.1", alias="HOST")
    port: int = Field(5000, alias="PORT")
    debug: bool = Field(False, alias="DEBUG")

    # ────────────────────────── データベース接続 ───────────────────────────────
    database_url: str = Field(..., alias="DATABASE_URL")
    pg_user: str = Field(..., alias="PG_USER")
    pg_pw: str = Field(..., alias="PG_PW")
    pg_host: str = Field(..., alias="PG_HOST")
    pg_port: str = Field(..., alias="PG_PORT")
    pg_db: str = Field(..., alias="PG_DB")
    pg_schema: str = Field(..., alias="PG_SCHEMA")

    # ────────────────────────── オーケストレーター ────────────────────────────
    orchestrator_port: int = Field(4010, alias="ORCHESTRATOR_PORT")
    request_timeout: int = Field(120, alias="REQUEST_TIMEOUT")
    max_retries: int = Field(2, alias="MAX_RETRIES")

    # ────────────────────────── OpenAI / Azure OpenAI ─────────────────────────
    api_type: str = Field("openai", alias="API_TYPE")
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    azure_openai_api_key: str = Field("", alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_base: str | None = Field(None, alias="AZURE_OPENAI_API_BASE")
    azure_openai_api_version: str | None = Field(None, alias="AZURE_OPENAI_API_VERSION")
    use_translation_on_azure: bool = Field(False, alias="USE_TRANSLATION_ON_AZURE")

    # ────────────────────────── 認証 / セキュリティ ───────────────────────────
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    patch_service_token: str | None = Field(None, alias="PATCH_SERVICE_TOKEN")

    # ────────────────────────── CORS ─────────────────────────────────────────
    allow_origins_raw: str = Field("*", alias="ALLOW_ORIGINS")

    # ────────────────────────── Agent URL 群 ─────────────────────────────────
    agent_code_url:          AnyUrl = Field(..., alias="AGENT_CODE_URL")
    agent_ui_url:            AnyUrl = Field(..., alias="AGENT_UI_URL")
    agent_qa_url:            AnyUrl = Field(..., alias="AGENT_QA_URL")
    agent_sec_url:           AnyUrl = Field(..., alias="AGENT_SEC_URL")
    agent_itc_url:           AnyUrl = Field(..., alias="AGENT_ITC_URL")
    agent_dba_url:           AnyUrl = Field(..., alias="AGENT_DBA_URL")
    agent_pm_url:            AnyUrl = Field(..., alias="AGENT_PM_URL")
    agent_stakeholder_url:   AnyUrl = Field(..., alias="AGENT_STAKEHOLDER_URL")
    agent_patch_url:         AnyUrl = Field(..., alias="AGENT_PATCH_URL")

    # ────────────────────────── Observability / Telemetry ────────────────────
    otel_exporter_otlp_endpoint: AnyUrl = Field(
        "http://localhost:4318", alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )

    # ────────────────────────── 派生プロパティ ────────────────────────────────
    @property
    def api_base_url(self) -> str:
        """自身（FastAPI サーバ）のベース URL"""
        return f"http://{self.host}:{self.port}"

    @property
    def allow_origins(self) -> List[str]:
        """
        ALLOW_ORIGINS をリストに正規化  
        - `*` あるいは `[*]` → ワイルドカード  
        - JSON 配列文字列 → そのまま  
        - カンマ区切り文字列 → 分割  
        """
        raw = self.allow_origins_raw.strip()

        if raw in {"*", "[*]"}:
            return ["*"]

        if raw.startswith("[") and raw.endswith("]"):
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"ALLOW_ORIGINS の JSON 解析に失敗: {exc}") from exc

        # カンマ区切り
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def agent_urls(self) -> Dict[str, str]:
        """
        エージェント種別 → URL の辞書を返却。  
        呼び出し側で種類を列挙する際に活用する。
        """
        return {
            "code_generation":   str(self.agent_code_url),
            "ui_generation":     str(self.agent_ui_url),
            "qa":                str(self.agent_qa_url),
            "security":          str(self.agent_sec_url),
            "it_consulting":     str(self.agent_itc_url),
            "dba":               str(self.agent_dba_url),
            "pm":                str(self.agent_pm_url),
            "stakeholder":       str(self.agent_stakeholder_url),
            "patch":             str(self.agent_patch_url),
        }

    @property
    def agent_ports(self) -> Dict[str, int]:
        """
        `agent_urls` からポート番号だけを抽出した辞書を生成。  
        例: `{"code_generation": 8001, ...}`
        """
        def _port(url: str) -> int:
            try:
                return int(url.rsplit(":", 1)[1])
            except (IndexError, ValueError) as exc:
                raise ValueError(f"URL からポートを抽出できません: {url}") from exc

        return {k: _port(v) for k, v in self.agent_urls.items()}

    # ────────────────────────── Pydantic の設定 ─────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",
        case_sensitive=False,   # .env のキーは大文字小文字を区別しない
        extra="ignore",         # 未定義の環境変数は無視
    )


# ────────────────────── アプリ全体で共有する Singleton ─────────────────────
settings = Settings()


def get_settings() -> Settings:
    """
    FastAPI の `Depends` から呼び出すためのヘルパ。  
    例:
        @app.get("/")
        async def root(cfg: Settings = Depends(get_settings)):
            return {"db": cfg.database_url}
    """
    return settings
