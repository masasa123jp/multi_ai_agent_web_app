"""
Alembic env.py (async) ― SQLAlchemy 2.0 公式レシピ準拠
"""

from __future__ import annotations
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

from backend.db.async_engine import ASYNC_DB_URL
from backend.db.base import Base  # ← MetaData 取得用
from backend import models        # noqa: F401  ← 全モデル import 必須

from sqlalchemy.ext.asyncio import (
    create_async_engine,
)


config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode with async engine."""
    connectable = create_async_engine(
        ASYNC_DB_URL,
        poolclass=pool.NullPool,
    )

    async def do_run(connection: Connection):
        async with connection.begin():
            await connection.run_sync(target_metadata.create_all)

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite 互換オプション
        )

        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(do_run(connectable))

run_migrations_online()
