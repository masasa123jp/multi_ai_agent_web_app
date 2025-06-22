# orchestrator/config.py

"""
orchestrator/config.py
────────────────────────────────────────────────────────────────────────
LangGraphワークフローおよびオーケストレータの設定情報を集約するモジュール。

- 各AIエージェントのエンドポイントURL
- タイムアウト、リトライ回数などの通信パラメータ
- ZIP出力に関する設定
"""
from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field

class OrchestratorSettings(BaseSettings):
    # 各種AIエージェントのベースURL
    agent_stakeholder_url: AnyUrl = Field(..., env="AGENT_STAKEHOLDER_URL")
    agent_pm_url:          AnyUrl = Field(..., env="AGENT_PM_URL")
    agent_itc_url:         AnyUrl = Field(..., env="AGENT_ITC_URL")
    agent_dba_url:         AnyUrl = Field(..., env="AGENT_DBA_URL")
    agent_ui_url:          AnyUrl = Field(..., env="AGENT_UI_URL")
    agent_code_url:        AnyUrl = Field(..., env="AGENT_CODE_URL")
    agent_qa_url:          AnyUrl = Field(..., env="AGENT_QA_URL")
    agent_sec_url:         AnyUrl = Field(..., env="AGENT_SEC_URL")
    agent_patch_url:       AnyUrl = Field(..., env="AGENT_PATCH_URL")

    # HTTPリクエストのタイムアウト（秒）
    request_timeout: int    = Field(120, env="REQUEST_TIMEOUT")
    # エージェント呼び出しのリトライ回数
    max_retries:      int   = Field(2,   env="MAX_RETRIES")

    # ZIP保存先のパス（未使用ならデフォルト）
    zip_storage_path: str   = Field("/var/tmp", env="ZIP_STORAGE_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 設定オブジェクトのインスタンス
settings = OrchestratorSettings()
