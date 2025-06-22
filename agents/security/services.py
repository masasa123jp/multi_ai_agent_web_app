# agents/security/services.py

"""
agents.security_agent.services
────────────────────────────────────────────────────────────────────────────
LLM による OWASP Top10 観点の静的解析を実施し、
scanner.py で追加検査を実行、最終的な Markdown レポートを組み立てる。
"""
from __future__ import annotations

import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import SecurityScanRequest
from .scanner import run_static_scans  # ★ 追加：独自スキャナ呼び出し ★

async def scan_security(req: SecurityScanRequest) -> Dict[str, str]:
    """
    1) LLM による初期脆弱性レポート生成
    2) scanner.run_static_scans でコード解析を実行
    3) スキャナ結果をレポート末尾に追加
    """
    # ── ① LLM レポート生成 ────────────────────────────────────────────────
    prompt = textwrap.dedent(
        f"""
        You are a seasoned AppSec engineer knowledgeable about OWASP Top 10
        and Python security best-practices.

        ## Source Code
        ```python
        {req.code}
        ```

        ## UI (if any)
        ```html
        {req.ui}
        ```

        ## Task
        * Identify potential vulnerabilities (OWASP A01–A10).
        * Explain exploit scenarios and potential impact.
        * Propose concrete remediation with code snippets.

        ## Output
        * Markdown report in Japanese.
        * Structure:
            - 概要
            - 発見された問題一覧 (表形式: CWE, 重要度, 行番号付近)
            - 詳細分析 & 修正例
        * Wrap the whole report in a fenced code block
          labelled `md:title=security_report.md`.
        """
    ).strip()

    llm_report: str = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
    )

    # ── ② 独自スキャナ実行 ────────────────────────────────────────────────
    scanner_results = run_static_scans(req.code)

    # ── ③ 最終レポート組み立て ────────────────────────────────────────────
    final_report = "\n\n".join([
        llm_report,
        "```text:title=scanner_results.txt",
        scanner_results.strip(),
        "```"
    ])

    return {"security_report": final_report}
