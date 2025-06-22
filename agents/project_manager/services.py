"""
agents.project_manager_agent.services
────────────────────────────────────────────────────────────────────────────
LLM を活用して 3 イテレーション（1 週間スプリント×3）の簡易アジャイル
スケジュールを作成する。
"""
from __future__ import annotations

import json
import textwrap
from typing import Dict

from common.ai_service import call_generative_ai
from .models import ScheduleRequest


async def create_schedule(req: ScheduleRequest) -> Dict[str, str]:
    """
    Timeline 情報をもとに CSV スケジュールを生成し文字列で返す。
    """
    # ----- 入力 JSON を整形しプロンプトに含める -----
    timeline_json = json.dumps(req.timeline, ensure_ascii=False, indent=2)

    prompt = textwrap.dedent(
        f"""
        You are a PMP-certified project manager.

        ## Project
        {req.project_name}

        ## Context
        (High-level goals / feedback)
        ```json
        {timeline_json}
        ```

        ## Task
        Create an Agile roadmap for three 1-week sprints.
        Columns: milestone,start,end,owners (comma-separated owner names).

        ## Output Rules
        * Return exactly one fenced-code block labelled `csv:title=schedule.csv`.
        * No Markdown outside the code block.
        """
    ).strip()

    csv_result: str = await call_generative_ai(
        model=req.model_name,
        prompt=prompt,
        max_tokens=16_384,
    )

    return {"schedule": csv_result}
