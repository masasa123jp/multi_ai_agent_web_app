"""
agents.ui_generation.services
────────────────────────────────────────────────────────────────────────────
• LLM プロンプト生成ロジックをここに集約。
• “pure HTML + CSS” を要求し、React 依存を避ける（ユーザ指定に準拠）。
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import UIGenRequest


async def generate_ui(req: UIGenRequest) -> Dict[str, str]:
    """
    LLM にプロンプトを投げ、シンプルな HTML/CSS UI を生成する。
    """

    prompt = textwrap.dedent(
        f"""
        ## Role
        You are an expert front-end engineer.

        ## Project
        {req.project_name}

        ## Requirement
        {req.prompt}

        ## Constraints
        - Use **pure HTML5** and **CSS3** only (no React / TypeScript).
        - JavaScript is allowed *only* for minimal interactivity (optional).
        - All resources must be self-contained (no CDN).
        - Theme preference: {req.theme or 'default'}.
        - Framework: {req.framework} (if 'vanilla', no external class libs).

        ## Output Format
        Return the full content of a single HTML file -- DO NOT wrap in markdown
        or commentary.  Just the raw code.
        """
    ).strip()

    ui_html = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
    )
    return {"ui": ui_html}
