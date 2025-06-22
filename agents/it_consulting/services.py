"""
agents.it_consulting_agent.services
────────────────────────────────────────────────────────────────────────────
• PMI-PMBOK、ISO/IEC 25010、OWASP SAMM 等を参照しつつ
  ベストプラクティスを提示する LLM プロンプト生成ロジック。
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import AdviceRequest


async def generate_advice(req: AdviceRequest) -> Dict[str, str]:
    """
    LLM に相談内容を渡し、IT コンサル観点でのアドバイスを返す。
    """
    prompt = textwrap.dedent(
        f"""
        ## Role
        You are a senior IT consultant (PMP + CISSP).

        ## Project
        {req.project_name}

        ## Question
        {req.prompt}

        ## Deliverable
        Provide actionable recommendations covering:
        - Architecture & scalability
        - Security & compliance
        - Cost optimisation
        - Team / process (Agile, DevSecOps)

        Format in GitHub-flavoured Markdown with H2/H3 headings.
        """
    ).strip()

    advice = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
    )
    return {"advice": advice}
