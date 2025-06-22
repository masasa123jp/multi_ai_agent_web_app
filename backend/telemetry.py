# backend/telemetry.py
"""
============================================================
 OpenTelemetry 初期化ユーティリティ
------------------------------------------------------------
プロジェクト全体で分散トレーシング・メトリクス・ログ自動計装を一元管理します。

■ 使い方
-------------------------------------------------------------------------------
from backend.telemetry import init_otel
init_otel(
    "my-service",                  # Grafana Tempo / Loki 上で識別するサービス名
    fastapi_app=app,               # 任意: 自動計装したい FastAPI インスタンス
    sqlalchemy_engine=db_engine,   # 任意: 自動計装したい SQLAlchemy Engine
)

Parameters
----------
service_name : str
    Tempo/Loki など上で表示されるサービス名。必須。
fastapi_app : fastapi.FastAPI | None
    自動トレース対象にする FastAPI アプリ。省略可。
sqlalchemy_engine : sqlalchemy.engine.Engine | None
    自動トレース対象にする SQLAlchemy Engine。省略可。
============================================================
"""

from __future__ import annotations

import logging
import os

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# OTLP エクスポータの送信先。環境変数で上書き可。
# デフォルトはローカルの OTLP Collector (http://localhost:4318)
# ──────────────────────────────────────────────────────────────
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")


def init_otel(
    service_name: str,
    *,
    fastapi_app=None,
    sqlalchemy_engine=None,
) -> None:
    """
    OpenTelemetry SDK / Exporter / Instrumentation を初期化する。

    - トレース: OTLPSpanExporter + BatchSpanProcessor
    - メトリクス: OTLPMetricExporter + PeriodicExportingMetricReader
    - ロギング: LoggingInstrumentor (構造化ログ → Loki 等)
    - HTTP クライアント: HTTPXClientInstrumentor
    - FastAPI: FastAPIInstrumentor
    - SQLAlchemy: SQLAlchemyInstrumentor

    Parameters
    ----------
    service_name : str
        Tempo/Loki 上で識別できるサービス名
    fastapi_app : fastapi.FastAPI | None
        自動トレース対象にする FastAPI アプリインスタンス (省略可)
    sqlalchemy_engine : sqlalchemy.engine.Engine | None
        トレース対象にする SQLAlchemy Engine (省略可)
    """

    # ── 1. Resource 属性を生成 ───────────────────────────────────
    #    - OpenTelemetry リソース仕様では service.name に必ず文字列を
    #      指定することが求められるため、インスタンスではなく文字列を設定
    resource = Resource.create({
        "service.name": service_name,
    })

    # ── 2. Trace Provider 設定 ──────────────────────────────────
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=f"{OTLP_ENDPOINT}/v1/traces")
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # ── 3. Metric Provider 設定 ─────────────────────────────────
    metric_exporter = OTLPMetricExporter(endpoint=f"{OTLP_ENDPOINT}/v1/metrics")
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=10_000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # ── 4. ロギング自動計装 ──────────────────────────────────────
    #    - 構造化ログ出力フォーマットを OTLP に合わせて自動設定
    LoggingInstrumentor().instrument(set_logging_format=True)

    # ── 5. HTTPX クライアント自動計装 ────────────────────────────
    HTTPXClientInstrumentor().instrument()

    # ── 6. FastAPI アプリ自動計装 ────────────────────────────────
    if fastapi_app is not None:
        FastAPIInstrumentor().instrument_app(
            fastapi_app,
            excluded_urls=".*\\.ico,.*\\.png",  # 静的アセットを計測対象外
        )

    # ── 7. SQLAlchemy Engine 自動計装 ───────────────────────────
    if sqlalchemy_engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)

    # ── 8. 初期化完了ログ ────────────────────────────────────────
    logger.info(
        "OpenTelemetry 初期化完了 (service.name=%s, endpoint=%s)",
        service_name,
        OTLP_ENDPOINT,
    )
