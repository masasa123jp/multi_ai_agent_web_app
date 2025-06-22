"""
agents.code_patch.services
────────────────────────────────────────────────────────────────────────────
LLM を用いて「差分パッチ」ではなく *修正後の完全なソースコード* を返す実装。
"""

from __future__ import annotations

import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import PatchCodeRequest


async def patch_code(req: PatchCodeRequest) -> Dict[str, str]:
    """
    LLM に修正方針と元コードを渡し、修正済みコード全文を受け取る。
    返値は orchestrator が期待する `{"patched_code": "..."}`
    """
    prompt = textwrap.dedent(
        f"""
        You are an expert Python developer.

        ## Original Source
        ```python
        {req.source_code}
        ```

        ## Requested Fix / Enhancement
        {req.instructions}

        ## Output specification
        1. Produce **only** the fully patched code – do not include commentary.
        2. Return in one fenced code block labelled `python:title=patched_code.py`.
        3. Do **not** omit any part of the original functionality unless explicitly told.

        Remember: Nothing but the code block.
        """
    ).strip()

    patched_code: str = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
        temperature=0.3,          # 低温で determinism を優先
    )

    return {"patched_code": patched_code}
