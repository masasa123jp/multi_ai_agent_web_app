#!/usr/bin/env python
# init_test_db.py

"""
SQLite テストデータベース (test.db) 作成スクリプト

• SQLAlchemy の Declarative Base (backend/db/base.py の Base) をベースにテーブルを生成
• 既存の test.db があれば上書き
• 非同期エンジンを使わず、同期的に metadata.create_all() を実行
"""

import os
import sys

from sqlalchemy import create_engine
from backend.config.settings import get_settings
from backend.db.base import Base            # ← ここを修正
# 各モデルモジュールをインポートすることで、Base.metadata に登録されるようにする
import backend.models
# 必要に応じて他のモデルもここにインポート

def main():
    # 1) 設定から DATABASE_URL を取得
    settings = get_settings()
    url = settings.database_url

    # 2) SQLite の場合は aiosqlite を同期ドライバに置換
    if url.startswith("sqlite+aiosqlite"):
        url = url.replace("sqlite+aiosqlite", "sqlite")
    # ファイルパスをプロジェクトルートに固定
    db_path = os.path.abspath("test.db")
    if os.path.exists(db_path):
        print(f"既存の {db_path} を削除します…")
        os.remove(db_path)

    # 3) エンジン生成
    engine = create_engine(url, echo=True, future=True)

    # 4) テーブル作成
    print("テーブルを作成中…")
    Base.metadata.create_all(engine)
    print("test.db の初期化が完了しました。")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("初期化中にエラーが発生しました。", file=sys.stderr)
        raise
