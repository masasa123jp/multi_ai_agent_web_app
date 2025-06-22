# tests/test_models.py
"""
SQLAlchemy ORM モデル（Project, User など）のテーブル・カラム定義検証
"""
import pytest
from backend.models.project import Project
from backend.models.user import User

def test_project_model_columns():
    cols = [c.name for c in Project.__table__.columns]
    for expected in ("user_email","name","description"):
        assert expected in cols

def test_user_model_columns():
    cols = [c.name for c in User.__table__.columns]
    for expected in ("email","username","password_hash"):
        assert expected in cols
