# backend/models/cost_log.py
from __future__ import annotations
import datetime as _dt
from decimal import Decimal

from sqlalchemy import Column, DateTime, DECIMAL, Integer, String
from backend.models.core import Base  # 既存 Base

class CostLog(Base):
    """
    1 AI 呼び出し = 1 行
    """
    __table_args__ = {"schema": "agentbased"}
    __tablename__ = "cost_log"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(128), index=True, nullable=False)
    step_name    = Column(String(64), nullable=False)
    model_name   = Column(String(32), nullable=False)
    tokens       = Column(Integer, nullable=False)
    cost         = Column(DECIMAL(10, 6), nullable=False)
    created_at   = Column(DateTime, default=_dt.datetime.utcnow, nullable=False)
