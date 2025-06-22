# agents/code_generation/services.py

"""
agents.code_generation.services
────────────────────────────────────────────────────────────────────────────
• コアの “生成ロジック” を実装。
• common.ai_service.call_generative_ai() を呼び、DBスキーマ・UI設計を含む
  プロンプトテンプレートを組み立ててLLMへ投げる。
"""

from __future__ import annotations
import textwrap
from typing import Any, Dict

from common.ai_service import call_generative_ai
from .models import CodeGenRequest

async def generate_code(req: CodeGenRequest) -> Dict[str, Any]:
    """
    LLM へプロンプトを投げてソースコードを生成。
    プロンプトには以下を含める：
      - 要件(req.prompt)
      - プロジェクト名(req.project_name)
      - DBスキーマDDL(req.db_schema)
      - UI設計(req.ui_design) のHTML/CSS
    """
    # 1) プロンプト組み立て
    prompt = textwrap.dedent(f"""
    # Role
    You are a senior Python engineer with deep expertise in backend and frontend integration.

    # Requirement
    {req.prompt}

    # Additional Information
    - Project Name: {req.project_name}
    - Database Schema (DDL):
    {req.db_schema or 'N/A'}

    - UI Design (HTML/CSS):
    {req.ui_design or 'N/A'}

    # Task
    1. Generate production-ready, PEP-8-compliant Python source code that implements the requirement.
    2. Use asyncpg for database connections with fully parameterized queries.
    3. Integrate the above DB schema and UI design seamlessly in the generated code.
    4. Return **only** the Python source file contents (no additional commentary).
    """).strip()

    # 2) LLM呼び出し
    llm_res = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
    )

    # 3) レスポンス整形
    return {"code": llm_res}
