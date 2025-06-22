# common/observability.py

"""
============================================================
Observability ユーティリティモジュール
------------------------------------------------------------
プロジェクト全体で OpenTelemetry の初期化・計装を一元管理。

統合内容:
  • 旧 backend/telemetry.py の設定を取り込み
  • common/observability.py の未使用コードを削除
  • FastAPI, HTTPX, SQLAlchemy, Logging の自動計装
  • OTLP SpanExporter／MetricExporter への送出設定

使い方:
    from common.observability import init_observability
    init_observability(
        service_name="my-service",
        fastapi_app=app,
        sqlalchemy_engine=db_engine
    )

============================================================
"""

from __future__ import annotations

import os
import logging

from fastapi import FastAPI
from sqlalchemy.engine import Engine as _SyncEngine
from sqlalchemy.ext.asyncio import AsyncEngine as _AsyncEngine

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# OTLP エンドポイント設定 (環境変数で上書き可)
# ──────────────────────────────────────────────────────────────
_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")


def init_observability(
    service_name: str,
    *,
    fastapi_app: FastAPI | None = None,
    sqlalchemy_engine: _SyncEngine | _AsyncEngine | None = None,
    export_interval_millis: int = 10_000,
) -> None:
    """
    OpenTelemetry Tracing/Metric/Logging を初期化。

    Parameters
    ----------
    service_name : str
        Grafana Tempo / Loki 等で識別可能なサービス名。
    fastapi_app : FastAPI | None
        FastAPI アプリを自動計装対象に追加する場合に指定。
    sqlalchemy_engine : Engine | None
        SQLAlchemy (同期 or 非同期) を自動計装対象に追加する場合に指定。
    export_interval_millis : int
        メトリクスエクスポート間隔 (ミリ秒)。
    """
    # リソース属性をサービス名のみで固定
    resource = Resource.create({"service.name": service_name})

    # ── TracerProvider (分散トレース) 設定 ────────────────────────
    tracer_provider = TracerProvider(resource=resource)
    tracer_exporter = OTLPSpanExporter(endpoint=f"{_OTLP_ENDPOINT}/v1/traces")
    tracer_provider.add_span_processor(BatchSpanProcessor(tracer_exporter))
    trace.set_tracer_provider(tracer_provider)

    # ── MeterProvider (メトリクス) 設定 ──────────────────────────
    metric_exporter = OTLPMetricExporter(endpoint=f"{_OTLP_ENDPOINT}/v1/metrics")
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=export_interval_millis,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    # ── Logging 自動計装 ────────────────────────────────────────
    LoggingInstrumentor().instrument(set_logging_format=True)

    # ── FastAPI 自動計装 ────────────────────────────────────────
    if fastapi_app is not None:
        FastAPIInstrumentor().instrument_app(
            fastapi_app,
            excluded_urls=".*\\.ico,.*\\.png"
        )

    # ── HTTPX クライアント自動計装 ───────────────────────────────
    HTTPXClientInstrumentor().instrument()

    # ── SQLAlchemy 自動計装 ────────────────────────────────────
    if sqlalchemy_engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)

    logger.info(
        "Observability initialized (service.name=%s, endpoint=%s)",
        service_name,
        _OTLP_ENDPOINT,
    )
