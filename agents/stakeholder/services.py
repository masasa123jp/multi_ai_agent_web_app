"""
agents.stakeholder_agent.services
────────────────────────────────────────────────────────────────────────────
• エンドユーザからの自然言語要件を “エンジニアに伝わる粒度” に整理するロジック。
• LLM へのプロンプト生成と post-process を実装。
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import json
import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import CollectFeedbackRequest


async def summarize_feedback(req: CollectFeedbackRequest) -> Dict[str, str]:
    """
    LLM にコンテキストを渡し、要件を構造化したサマリーを返す。
    """
    ctx_json = json.dumps(req.feedback_context.__root__, ensure_ascii=False, indent=2)

    prompt = textwrap.dedent(
        f"""
        # Role
        You are an expert requirements analyst.

        # Raw Context (JSON)
        {ctx_json}

        # Task
        1. Extract the *core functional requirements* in concise Japanese.
        2. List any *non-functional requirements* (security, performance, UX…).
        3. Flag open questions or ambiguities.

        # Output format
        ```
        ## Functional Requirements
        - ...

        ## Non-Functional Requirements
        - ...

        ## Open Questions
        - ...
        ```
        Return strictly in the above format. No additional commentary.
        """
    ).strip()

    summary = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
    )
    return {"feedback_summary": summary}
