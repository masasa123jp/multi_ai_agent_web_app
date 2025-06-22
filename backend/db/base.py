"""
backend/db/base.py
──────────────────────────────────────────────────────────────
全 ORM モデル共通の Declarative Base クラス。
SQLAlchemy 2.0 スタイル推奨の `registry()` + `mapped_as_dataclass` にも
対応できるが、今回はシンプルな DeclarativeBase を採用。
"""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """プロジェクト全体で継承する基底クラス"""
    pass
