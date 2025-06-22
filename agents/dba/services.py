"""
agents.dba_agent.services
────────────────────────────────────────────────────────────────────────────
LLM を呼び出して PostgreSQL 用 DDL とサンプルデータを生成するサービス層。
"""
from __future__ import annotations

import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import DesignSchemaRequest


async def design_schema(req: DesignSchemaRequest) -> Dict[str, str]:
    """
    LLM へプロンプトを投げて SQL を生成し、辞書 {"dba_script": "..."} を返す。

    Parameters
    ----------
    req : DesignSchemaRequest
        フロント／オーケストレーターから渡されるリクエストモデル。

    Returns
    -------
    Dict[str, str]
        {"dba_script": "```sql:title=schema.sql\nCREATE TABLE ..."}
    """
    # ----- プロンプト組み立て -----
    prompt = textwrap.dedent(
        f"""
        You are an experienced PostgreSQL DBA.

        ## Project
        {req.project_name}

        ## Requirements
        {req.prompt}

        ## Output Format
        * Provide `CREATE TABLE` statements with primary/foreign keys.
        * Use lower_snake_case for identifiers.
        * Include at least one composite index or partial index if applicable.
        * Append 3–5 sample INSERT statements per table.
        * Wrap everything in **one** fenced code block labelled
          `sql:title=schema.sql`.
        * Do NOT output any commentary outside the code block.
        """
    ).strip()

    # ----- LLM 呼び出し -----
    sql_script: str = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,  # DDL は比較的長くなるためトークン多め
    )

    return {"dba_script": sql_script}
