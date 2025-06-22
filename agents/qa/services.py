# agents/qa/services.py

"""
agents.qa_agent.services
────────────────────────────────────────────────────────────────────────────
LLM にテストコードの生成と結果サマリーを依頼し，qa_report を返す。
さらにテストを実際に実行し、結果をレポートに含める。
"""
from __future__ import annotations

import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import QARunRequest
from .test_runner import run_tests  # ← テスト実行ユーティリティ

async def run_qa(req: QARunRequest) -> Dict[str, str]:
    """
    1) LLM に QA レポート（テスト方針・pytest コード・不具合提案）を生成させる
    2) test_runner.run_tests で生成コードを実行しテスト結果を取得
    3) 最終レポートにテスト実行結果を追記して返却
    """
    # ── ① LLM に委ねる QA レポート生成 ─────────────────────────────────
    prompt = textwrap.dedent(
        f"""
        You are a senior QA engineer proficient in Python testing with pytest.

        ## Project
        {req.project_name}

        ## Functional Requirement
        {req.requirement}

        ## Source Code
        ```python
        {req.code}
        ```

        ## Task
        1. Draft robust pytest tests covering edge cases and error handling.
        2. Reason about likely failure points or anti-patterns.
        3. Output a concise QA report in Japanese that includes:
           - テスト方針の要約
           - 生成したテストケース (pytest コード) fenced python:title=test_<name>.py
           - 想定される不具合やリファクタリング提案
        4. Wrap entire report in a single fenced code block labelled `md:title=qa_report.md`.
        """
    ).strip()

    qa_report: str = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
    )

    # ── ② 実際に pytest を実行 ─────────────────────────────────────────
    #    テストコードは LLM レポート内のコードブロックから抽出する
    test_output = run_tests(req.code)

    # ── ③ レポートにテスト実行結果を追記 ────────────────────────────────
    full_report = "\n".join([
        qa_report,
        "```text:title=test_results.txt",
        test_output.strip(),
        "```"
    ])

    return {"qa_report": full_report}
